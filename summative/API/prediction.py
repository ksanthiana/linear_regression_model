"""
African Crop Yield Prediction API
====================================
Serves the OLS Linear Regression model trained in
summative/linear_regression/multivariate.ipynb on HarvestStat Africa
crop statistics (33 countries, 26 crop groups, 1980-2022).

Endpoints:
  GET  /                -> health/info
  POST /predict          -> predict yield (t/ha) for one crop observation
  POST /retrain           -> upload new labeled data (CSV) to retrain the model in place

Run locally:
  uv run uvicorn prediction:app --reload

Docs (Swagger UI): http://<host>/docs
"""

import io
import json
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---------------------------------------------------------------------------
# Paths & model loading
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "best_model.pkl"
METADATA_PATH = BASE_DIR / "model" / "metadata.json"
TRAINING_DATA_PATH = BASE_DIR / "model" / "training_data.csv"

with open(METADATA_PATH) as f:
    METADATA = json.load(f)

CATEGORICAL_FEATURES = METADATA["categorical_features"]
NUMERIC_FEATURES = METADATA["numeric_features"]
FEATURE_ORDER = METADATA["feature_order"]
CATEGORIES = METADATA["categories"]
RANGES = METADATA["feature_ranges"]

CountryT = str
ProductT = str
SeasonT = str
ProdSystemT = str


def load_model():
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        training_data = pd.read_csv(TRAINING_DATA_PATH)
        X = training_data[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
        y = training_data["yield"]
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
                ("num", StandardScaler(), NUMERIC_FEATURES),
            ]
        )
        pipe = Pipeline([("prep", preprocessor), ("model", LinearRegression())])
        pipe.fit(X_train, y_train)
        joblib.dump(pipe, MODEL_PATH)
        return pipe


model = load_model()

# ---------------------------------------------------------------------------
# App & CORS
# ---------------------------------------------------------------------------
app = FastAPI(
    title="African Crop Yield Prediction API",
    description=(
        "Predicts crop yield (metric tons/hectare) from country, crop type, "
        "season, farming system, timing, and plot area, using a linear "
        "regression model trained on 196k+ harmonized subnational crop "
        "observations across 33 African countries (HarvestStat Africa)."
    ),
    version="1.0.0",
)

# CORS reasoning (see README / video for full explanation):
# - allow_origins is an explicit allow-list, NOT "*". The Flutter mobile app
#   itself is a native client and is not subject to browser CORS at all, so
#   the only real consumers of this policy are: (a) the hosted Swagger UI
#   (same-origin, browser always allows this) and (b) a local Flutter *web*
#   build during development, served from localhost. We list those explicit
#   origins instead of a wildcard so a malicious third-party website cannot
#   embed a hidden fetch() call against this API using a victim's browser.
# - allow_methods is restricted to what the API actually exposes (GET/POST).
# - allow_headers is restricted to what the client actually needs to send.
# - allow_credentials=False because this API is stateless and uses no
#   cookies/auth sessions, so there is nothing to protect by allowing
#   credentialed cross-origin requests -- turning it on would only widen
#   the attack surface for no functional benefit.
ALLOWED_ORIGINS = [
    "http://localhost:3000",     # local Flutter web dev server
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "https://crop-yield-predictor.onrender.com",  # replace with your deployed Render URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Pydantic request/response schemas
# ---------------------------------------------------------------------------
class CropObservation(BaseModel):
    """One subnational crop-season observation."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "country": "Burundi",
            "product": "Maize",
            "season_name": "Main",
            "crop_production_system": "Rainfed (PS)",
            "planting_year": 2022,
            "planting_month": 9,
            "harvest_year": 2023,
            "harvest_month": 2,
            "area": 1500.0,
        }
    })

    country: CountryT = Field(..., description="Country")
    product: ProductT = Field(..., description="Crop type")
    season_name: SeasonT = Field(..., description="Growing season label")
    crop_production_system: ProdSystemT = Field(..., description="Farming/production system")
    planting_year: int = Field(..., ge=int(RANGES["planting_year"][0]), le=int(RANGES["planting_year"][1]) + 1)
    planting_month: int = Field(..., ge=1, le=12)
    harvest_year: int = Field(..., ge=int(RANGES["harvest_year"][0]), le=int(RANGES["harvest_year"][1]) + 1)
    harvest_month: int = Field(..., ge=1, le=12)
    area: float = Field(..., ge=RANGES["area"][0], le=RANGES["area"][1], description="Plot/observation area in hectares")

class PredictionResponse(BaseModel):
    predicted_yield_t_per_ha: float
    model_used: str


class RetrainResponse(BaseModel):
    message: str
    rows_used_total: int
    new_rows_added: int
    test_rmse: float
    test_r2: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "African Crop Yield Prediction API is running.",
        "docs": "/docs",
        "model": METADATA["best_model_name"],
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(obs: CropObservation):
    try:
        row = obs.model_dump()
        row["season_length_months"] = (
            (row["harvest_year"] - row["planting_year"]) * 12
            + (row["harvest_month"] - row["planting_month"])
        )
        df = pd.DataFrame([row])[FEATURE_ORDER]
        pred = float(model.predict(df)[0])
        # Yield cannot be physically negative; the underlying linear model has
        # no such constraint, so we clip at the API boundary.
        pred = max(0.0, pred)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Prediction failed: {exc}") from exc

    return PredictionResponse(predicted_yield_t_per_ha=round(pred, 3), model_used=METADATA["best_model_name"])


@app.post("/retrain", response_model=RetrainResponse)
async def retrain(file: UploadFile = File(...)):
    """
    Upload a CSV of new labeled crop observations (same columns as
    FEATURE_ORDER + a 'yield' target column) to retrain the deployed
    Linear Regression model on existing + new data.
    """
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    raw = await file.read()
    try:
        new_data = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}") from exc

    required_cols = set(FEATURE_ORDER + ["yield"])
    missing = required_cols - set(new_data.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"Uploaded CSV is missing columns: {sorted(missing)}")

    existing = pd.read_csv(TRAINING_DATA_PATH)
    combined = pd.concat([existing, new_data[FEATURE_ORDER + ["yield"]]], ignore_index=True).dropna()

    X = combined[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y = combined["yield"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ]
    )
    pipe = Pipeline([("prep", preprocessor), ("model", LinearRegression())])
    pipe.fit(X_train, y_train)

    preds = pipe.predict(X_test)
    test_rmse = float(mean_squared_error(y_test, preds) ** 0.5)
    test_r2 = float(r2_score(y_test, preds))

    joblib.dump(pipe, MODEL_PATH)
    combined.to_csv(TRAINING_DATA_PATH, index=False)

    global model
    model = pipe

    return RetrainResponse(
        message="Model retrained successfully on existing + new data.",
        rows_used_total=len(combined),
        new_rows_added=len(new_data),
        test_rmse=round(test_rmse, 4),
        test_r2=round(test_r2, 4),
    )
