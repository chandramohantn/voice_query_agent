# Voice Query Agent

A voice query agent that enables you to use your voice to talk to Gemini 2.0 through the [Multimodal Live API](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/multimodal-live).

## Architecture

- **Backend (Python WebSockets Server):** Handles authentication and acts as an intermediary between your frontend and the Gemini API.
- **Frontend (HTML/JavaScript):** Provides the user interface and interacts with the backend via WebSockets.

### File Structure

- `backend/main.py`: The Python backend code
- `backend/requirements.txt`: Lists the required Python dependencies

- `frontend/index.html`: The frontend HTML app
- `frontend/script.js`: Main frontend JavaScript code
- `frontend/gemini-live-api.js`: Script for interacting with the Gemini API
- `frontend/live-media-manager.js`: Script for handling media input and output
- `frontend/pcm-processor.js`: Script for processing PCM audio
- `frontend/cookieJar.js`: Script for managing cookies


## Setup instructions

1. Create a new virtual environment and activate it:

    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```

1. Install dependencies:

    ```sh
    pip3 install -r backend/requirements.txt
    ```

1. Start the Python WebSocket server:

    ```sh
    python3 backend/main.py
    ```

1. Start the frontend:

    - Navigate to `script.js` on line 9, `const PROXY_URL = "wss://[THE_URL_YOU_COPIED_WITHOUT_HTTP]";` and replace `PROXY_URL` value with `ws://localhost:8000`. It should look like: `const PROXY_URL = "ws://localhost:8000";`. Note the absence of the second "s" in "wss" as "ws" indicates a non-secure WebSocket connection.
    - Right below on line 10, update `PROJECT_ID` with your Google Cloud project ID.
    - Save the changes you've made to `script.js`
    - Now make sure to open a **separate** terminal window from the backend to run this command (keep the backend server running in the first terminal).

    ```sh
    cd frontend
    python3 -m http.server 8001
    ```

1. Point your browser to the demo app UI based on the output of the terminal. (e.g., it may be `http://localhost:8001`, or it may use a different port.)

1. Get your Google Cloud access token:
   Run the following command in a terminal with gcloud installed to set your project, and to retrieve your access token.

    ```sh
    gcloud config set project YOUR-PROJECT-ID
    gcloud auth print-access-token
    ```

1. Add the model ID and the access token in the .env file:
    Add the above info in the variables: GOOGLE_CLOUD_TOKEN & GOOGLE_CLOUD_PROJECT_ID

1. Connect and interact with the demo:

    - Press the connect button to connect your web app. Now you should be able to interact with Gemini 2.0 with the Multimodal Live API.

1. To interact with the app, you can do the following:

    - Voice input: Press the microphone button to stop speaking. The model will respond via audio. If you would like to mute your microphone, press the button with a slash through the microphone.

