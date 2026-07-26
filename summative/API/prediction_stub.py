from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Crop Yield Predictor (stub)")


class CropObservation(BaseModel):
    country: str
    product: str
    season_name: str
    crop_production_system: str
    planting_year: int
    planting_month: int
    harvest_year: int
    harvest_month: int
    area: float


@app.get("/")
def root():
    return {"message": "Stub API running", "docs": "/docs", "model": "stub-model-v1"}


@app.post("/predict")
def predict(obs: CropObservation):
    try:
        # Very small deterministic heuristic for demo purposes.
        # Avoid any heavy numeric libs so this runs on low-resource machines.
        months = (obs.harvest_year - obs.planting_year) * 12 + (obs.harvest_month - obs.planting_month)
        area_factor = max(0.0, min(10.0, obs.area / 1500.0))
        pred = round(0.5 + 0.5 * months + 0.2 * area_factor, 3)
        pred = max(0.0, pred)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Prediction failed: {exc}")

    return {"predicted_yield_t_per_ha": pred, "model_used": "stub-model-v1"}
