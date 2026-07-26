# Render Deployment Guide for Crop Yield Predictor API

## Steps to Deploy to Render:

### 1. Create a Render Account
- Go to https://render.com and sign up (free tier available)

### 2. Connect Your GitHub Repository
- Click "New +" → "Web Service"
- Connect your GitHub repo
- Select the repository: `linear_regression_model`

### 3. Configure the Service
- **Name**: `crop-yield-predictor` (or your preferred name)
- **Environment**: Python 3
- **Region**: Select closest to you
- **Branch**: `main`
- **Build Command**: `pip install -r summative/API/requirements.txt`
- **Start Command**: `cd summative/API && python -m uvicorn prediction:app --host 0.0.0.0 --port $PORT`

### 4. Environment Variables (Optional)
- You don't need any for this basic setup

### 5. Deploy
- Click "Create Web Service"
- Wait for deployment to complete (2-3 minutes)
- Once live, you'll get a URL like: `https://crop-yield-predictor.onrender.com`

### 6. Test the Deployment
- Go to: `https://<your-service-name>.onrender.com/docs`
- You should see the Swagger UI

### 7. Update Your Flutter App
- After getting your Render URL, update `lib/main.dart`:
  ```dart
  const String kApiBaseUrl = "https://<your-service-name>.onrender.com";
  ```

## Notes:
- Free tier Render instances spin down after 15 minutes of inactivity
- Model files are included in the repository, so they'll be available after deployment
- CORS is configured to allow the deployed URL and localhost for development

## Your Service URL
Once deployed, your API documentation will be at:
`https://<your-service-name>.onrender.com/docs`
