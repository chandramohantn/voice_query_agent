# Changelog

All notable changes to this project will be documented in this file.

## [2025-12-05] - Add Environment Variable Configuration for Frontend

### Added
- `frontend/env.template.js` for environment variable template
- `frontend/docker-entrypoint.sh` to generate env.js at runtime
- `.env.example` file with all required environment variables
- `BACKEND_URL` environment variable for configuring WebSocket endpoint

### Changed
- Frontend now reads configuration from environment variables via `window.ENV`
- `script.js` updated to use `window.ENV` for PROXY_URL, PROJECT_ID, MODEL, and API_HOST
- Frontend Dockerfile uses custom entrypoint to inject environment variables
- docker-compose.yml passes environment variables to frontend container
- All frontend configuration now externalized (no hardcoded values)

### Benefits
- Easy deployment to different environments without code changes
- Backend URL configurable per environment
- All sensitive/environment-specific values in .env file

## [2025-12-02] - Containerize Application with Docker

### Added
- `backend/Dockerfile` for Python WebSocket server containerization
- `backend/.dockerignore` to exclude unnecessary files from Docker image
- `frontend/Dockerfile` with nginx for serving static files
- `frontend/.dockerignore` for frontend container
- `docker-compose.yml` to orchestrate backend and frontend services
- `build-and-test.sh` script for automated build, deployment, and testing
- `cleanup.sh` script to stop all services

### Changed
- Backend now reads `PORT` and `BIND_HOST` from environment variables
- Backend binds to 0.0.0.0 instead of localhost for container networking
- Removed project ID query parameter from SERVICE_URL (not supported by Gemini API)
- Frontend now served via nginx container on port 8001
- Backend runs on port 8080

### Infrastructure
- Backend: Python 3.11-slim Docker image
- Frontend: nginx:alpine Docker image
- Both services managed via docker-compose

## [2025-11-29] - Move Project ID to Backend

### Changed
- Backend now loads `GOOGLE_CLOUD_PROJECT_ID` from .env file
- Project ID included in WebSocket SERVICE_URL as query parameter

### Removed
- Project ID input field from frontend UI
- Project ID handling logic from script.js

## [2025-11-29] - Remove Video and Screen Sharing Features

### Removed
- Screen share button and functionality from UI
- Video preview section (video and canvas elements)
- `LiveVideoManager` class for webcam functionality
- `LiveScreenManager` class for screen capture functionality
- Related JavaScript functions: `startScreenCapture()`, `screenShareBtnClick()`
- Video/screen frame capture and processing code

### Changed
- Application now supports audio-only interaction via microphone

## [2025-11-29] - Simplified Frontend UI

### Removed
- Camera input dropdown and camera button from UI
- Text message input field and send button
- Model response type selector (Audio/Text radio buttons)
- Related JavaScript functions: `cameraBtnClick()`, `newUserMessage()`, `newCameraSelected()`, `getAvailableCameras()`, `setAvailableCamerasOptions()`

### Changed
- Frontend now focuses on voice-only interaction with microphone and screen sharing

## [2025-11-29] - Authentication Moved to Backend

### Changed
- Moved Google Cloud access token authentication from frontend to backend
- Backend now loads `GOOGLE_CLOUD_TOKEN` from .env file
- Removed access token input field from frontend UI
- Simplified WebSocket connection flow - no token exchange needed between frontend and backend

### Added
- `python-dotenv` dependency for environment variable management

### Removed
- Access token input field from index.html
- Token handling logic from script.js and gemini-live-api.js
- Bearer token from WebSocket initial setup messages
