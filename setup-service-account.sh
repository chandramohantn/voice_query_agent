#!/bin/bash

set -e

echo "========================================="
echo "Service Account Setup Script"
echo "========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID from .env or prompt
if [ -f .env ]; then
    PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT_ID .env | cut -d '=' -f2)
fi

if [ -z "$PROJECT_ID" ]; then
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
fi

echo "Using Project ID: $PROJECT_ID"
echo ""

# Set the project
gcloud config set project $PROJECT_ID

SERVICE_ACCOUNT_NAME="voice-agent-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="service-account-key.json"

echo "Step 1: Creating service account..."
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    echo "✓ Service account already exists: $SERVICE_ACCOUNT_EMAIL"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Voice Query Agent Service Account" \
        --project=$PROJECT_ID
    echo "✓ Service account created: $SERVICE_ACCOUNT_EMAIL"
fi

echo ""
echo "Step 2: Granting Vertex AI User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/aiplatform.user" \
    --condition=None \
    > /dev/null 2>&1

echo "✓ Role granted: roles/aiplatform.user"

echo ""
echo "Step 3: Creating service account key..."
if [ -f "$KEY_FILE" ]; then
    read -p "Key file already exists. Overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping key creation"
        exit 0
    fi
    rm $KEY_FILE
fi

gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

echo "✓ Service account key created: $KEY_FILE"

echo ""
echo "========================================="
echo "✓ Setup Complete!"
echo "========================================="
echo ""
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "Key File: $KEY_FILE"
echo ""
echo "Next steps:"
echo "1. Rebuild backend: docker-compose build backend"
echo "2. Restart services: docker-compose up -d"
echo "3. Check logs: docker-compose logs backend"
echo ""
echo "Note: Keep $KEY_FILE secure and never commit it to git!"
