
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="qwiklabs-gcp-03-82491e646971"
REGION="${REGION:-us-central1}"      # use the region shown in your lab
SERVICE="mapsagent"

gcloud config set project "$PROJECT_ID"

gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  aiplatform.googleapis.com

# Let the Cloud Run runtime service account call Vertex AI (Gemini + Maps grounding)
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user" --condition=None >/dev/null

# Build from the Dockerfile and deploy
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}"
# If geocode_address needs a Maps API key, add: ,GOOGLE_MAPS_API_KEY=<key>