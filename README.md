# African Crop Yield Prediction

My mission is to strengthen food security and agricultural infrastructure planning across Africa, including my home country Burundi. Governments, NGOs, and farmers need to know what yield to expect for a given crop, region, season, and farming system so they can decide where to invest in irrigation, storage, and transport before a harvest shortfall becomes a crisis. This project predicts crop yield (metric tons/hectare) from country, crop type, season, production system, timing, and plot area.


- Youtube Demo video link: https://youtu.be/1NryShDMK0c


- https://colab.research.google.com/drive/1VlZyIWZBxHLf75Ao8CgltGlBqe9Gx0U2?usp=sharing this is the notebook used to explore and train the linear regression model


## Public API (Swagger UI)

- **Swagger UI:** https://crop-yield-predictor-3oy8.onrender.com/docs
- **Prediction endpoint:** `POST https://crop-yield-predictor-3oy8.onrender.com/predict`
- **Retraining endpoint:** `POST https://crop-yield-predictor-3oy8.onrender.com/retrain` (upload a CSV of new observations; the model retrains and hot-swaps only if it performs at least as well as the currently deployed model)

> Note: the API runs on Render's free tier, which sleeps after ~15 minutes of inactivity[Uploading linear_regression.ipynb…]()
 the first request after a pause can take up to a minute while the service wakes up.

Example request body for `/predict`:

```json
{
  "country": "Burundi",
  "product": "Maize",
  "season_name": "Main",
  "crop_production_system": "Rainfed (PS)",
  "planting_year": 2022,
  "planting_month": 9,
  "harvest_year": 2023,
  "harvest_month": 2,
  "area": 1500.0
}
```

Every input is type-enforced and range-constrained with Pydantic — `country`, `product`, `season_name`, and `crop_production_system` must be one of the exact categories seen in training (e.g. an unrecognized country like `"Wakanda"` is rejected), `planting_month`/`harvest_month` must be integers 1–12, and `area` must fall within the observed training range. Out-of-range or invalid values return a descriptive `422` error. Predictions are also clipped at 0, since yield cannot be physically negative but the underlying linear model has no such constraint.

### CORS configuration reasoning

The API restricts cross-origin access instead of allowing `*`:

- **Allowed origins:** only local development hosts and the deployed Render domain itself (for Swagger UI). The Flutter *mobile* app sends no `Origin` header, so it is unaffected by this policy either way.
- **Allowed methods:** `GET`, `POST` only the API exposes nothing else.
- **Allowed headers:** `Content-Type` only, which is all the JSON/multipart requests need.
- **Credentials:** disabled — the API is stateless with no cookies or sessions, so credentialed cross-origin requests are refused, reducing attack surface for no functional loss.



## Dataset

- **Source:** [HarvestStat Africa](https://github.com/HarvestStat/HarvestStat-Africa) — a harmonized, open-access subnational crop statistics database compiled from FEWS NET and FAO sources.
- **Size / richness:** 196,042 rows × 10 features (after cleaning) 33 African countries (including Burundi), 26 crop groups, 6 season types, 6 farming systems, spanning 1980–2022. Real-world imperfections included data-entry outliers (e.g. a handful of rows reporting >1 billion hectares) which were identified and filtered.
- **Target:** `yield`  continuous, metric tons per hectare.

The full analysis (visualizations, feature engineering, standardization, and a comparison of SGD linear regression, OLS linear regression, decision tree, random forest, and gradient boosting) is in [`summative/linear_regression/multivariate.ipynb`](summative/linear_regression/multivariate.ipynb). Random Forest achieved the lowest test RMSE, but per this assignment's linear-regression objective, **OLS Linear Regression** (test RMSE ≈ 3.59 t/ha) is the model saved and served by the API — see `summative/linear_regression/artifacts/model_comparison.csv` for the full benchmark.


## Repository structure

```
linear_regression_model/
├── summative/
│   ├── linear_regression/
│   │   ├── multivariate.ipynb      # Task 1: cleaning, EDA, feature engineering, model comparison, training
│   │   ├── crop_yield_raw.csv      # raw source data
│   │   └── artifacts/              # plots, cleaned data, saved model, metadata, comparison table
│   ├── API/
│   │   ├── prediction.py           # Task 2: FastAPI service (predict + prediction.py)
│   │   ├── requirements.txt
│   │   └── model/                  # best_model.pkl, metadata.json, training_data.csv served by the API
│   └── FlutterApp/
│       └── crop_yield_predictor/   # Task 3: single-page Flutter mobile app
├── pyproject.toml                  # uv-managed project
└── uv.lock
```n

## How to run

### 1. Python environment (uv)

```bash
pip install uv          # if uv is not installed
uv sync                 # creates .venv and installs everything
```

### 2. Notebook

```bash
uv run jupyter lab summative/linear_regression/multivariate.ipynb
```

### 3. API (locally)

```bash
cd summative/API
uv run uvicorn prediction:app --reload --port 8000
# Swagger UI: http://127.0.0.1:8000/docs
```

### 4. Mobile app (Flutter)

Prerequisites: [Flutter SDK](https://docs.flutter.dev/get-started/install) and an Android emulator or physical device.

```bash
cd summative/FlutterApp/crop_yield_predictor
flutter pub get
flutter run          # select your emulator/device when prompted
```

The app shows 9 input fields (4 dropdowns for country/crop/season/production system, 5 number fields for timing and area one per model variable), a **Predict** button, and a display area that shows the predicted yield or a clear error message for missing/out-of-range values. The API base URL is set in `lib/main.dart` (`kApiBaseUrl`) and already points to the live Render deployment above, so no configuration is needed to run it as is.
