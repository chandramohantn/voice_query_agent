#!/bin/sh

# Generate env.js from environment variables
cat > /usr/share/nginx/html/env.js << EOF
window.ENV = {
    BACKEND_URL: "${BACKEND_URL:-ws://localhost:8080}",
    PROJECT_ID: "${PROJECT_ID:-gen-lang-client-0427088816}",
    MODEL: "${MODEL:-gemini-2.0-flash-live-preview-04-09}",
    API_HOST: "${API_HOST:-us-central1-aiplatform.googleapis.com}"
};
EOF

# Start nginx
exec nginx -g 'daemon off;'
