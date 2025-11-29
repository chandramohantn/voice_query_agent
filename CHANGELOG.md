# Changelog

All notable changes to this project will be documented in this file.

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
