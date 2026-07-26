# African Crop Yield Prediction

GitHub repository: https://github.com/ksanthiana/linear_regression_model

This repository contains a complete submission for crop yield prediction, including:

- https://colab.research.google.com/drive/1VlZyIWZBxHLf75Ao8CgltGlBqe9Gx0U2?usp=sharing — the notebook used to explore and train the linear regression model
- `summative/API/prediction.py` — the FastAPI backend that serves crop yield predictions and supports model retraining
- `summative/FlutterApp/crop_yield_predictor` — the Flutter application for interacting with the prediction API

## Project Structure

- `summative/linear_regression/` — data exploration, preprocessing, and model training resources
- `summative/API/` — API backend code, model artifacts, and deployment configuration
- `summative/FlutterApp/crop_yield_predictor/` — Flutter frontend application

## Running the API

1. Open a terminal in `summative/API`
2. Install dependencies from `requirements.txt`
3. Run the API:

```bash
uvicorn prediction:app --reload
```

4. Open Swagger UI at `http://127.0.0.1:8000/docs`

## Running the Flutter App

1. Open the Flutter project at `summative/FlutterApp/crop_yield_predictor`
2. Run the app with Flutter tooling:

```bash
flutter run
```

## Notes

- The API expects crop observation input data and returns predicted yield in metric tons per hectare.
- The Flutter app is designed to connect to the prediction API and display results.
