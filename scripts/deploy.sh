#!/bin/bash

# A helper script to deploy this app to Google Cloud Run
# Usage: ./scripts/deploy.sh [PROJECT_ID] [REGION]

PROJECT_ID=$1
REGION=${2:-us-central1}
SERVICE_NAME="healx-backend"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./scripts/deploy.sh [PROJECT_ID] [REGION]"
    echo "Please provide your Google Cloud Project ID."
    exit 1
fi

echo "========================================================"
echo " Deploying to Google Cloud Run"
echo " Project: $PROJECT_ID"
echo " Region:  $REGION"
echo "========================================================"

# 1. Build the container image using Cloud Build
echo "Step 1: Building Container Image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME . --project $PROJECT_ID

if [ $? -ne 0 ]; then
    echo "Build failed."
    exit 1
fi

# 2. Deploy to Cloud Run
# Note: In a real scenario, you would link a Cloud SQL instance here using:
# --add-cloudsql-instances [INSTANCE_CONNECTION_NAME]
# --set-env-vars DATABASE_URL="postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/INSTANCE_CONNECTION_NAME"

echo "Step 2: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --set-env-vars FIREBASE_STORAGE_BUCKET="${PROJECT_ID}.appspot.com" \
    --set-env-vars LOG_LEVEL="info"

# NOTE: Database connection isn't set here because it involves sensitive passwords.
# You must go to the Cloud Console and set the DATABASE_URL environment variable manually
# after the first deployment, pointing to your Cloud SQL instance.

echo "========================================================"
echo "Deployment Complete!"
echo "IMPORTANT: Go to https://console.cloud.google.com/run"
echo "1. Select '$SERVICE_NAME'"
echo "2. Edit & Deploy New Revision"
echo "3. Add your DATABASE_URL environment variable pointing to Cloud SQL"
echo "========================================================"
