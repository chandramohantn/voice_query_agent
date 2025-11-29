# Changelog

All notable changes to this project will be documented in this file.

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
