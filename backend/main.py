import asyncio
import json
import os
import ssl

import websockets
from websockets.legacy.protocol import WebSocketCommonProtocol
from websockets.legacy.server import WebSocketServerProtocol
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.auth.transport.requests import Request

load_dotenv()

HOST = "us-central1-aiplatform.googleapis.com"
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
SERVICE_URL = f"wss://{HOST}/ws/google.cloud.aiplatform.v1beta1.LlmBidiService/BidiGenerateContent"
SERVICE_ACCOUNT_KEY = os.getenv("SERVICE_ACCOUNT_KEY", None)
BEARER_TOKEN = os.getenv("GOOGLE_CLOUD_TOKEN", None)
PORT = int(os.getenv("PORT", "8080"))
BIND_HOST = os.getenv("BIND_HOST", "0.0.0.0")
SSL_CERT = os.getenv("SSL_CERT", None)
SSL_KEY = os.getenv("SSL_KEY", None)

DEBUG = True


def get_access_token():
    """Get access token from service account or use provided token."""
    if SERVICE_ACCOUNT_KEY and os.path.exists(SERVICE_ACCOUNT_KEY):
        print(f"Using service account key: {SERVICE_ACCOUNT_KEY}")
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_KEY,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(Request())
        return credentials.token
    elif BEARER_TOKEN:
        print("Using provided bearer token")
        return BEARER_TOKEN
    else:
        raise ValueError("No authentication method provided. Set SERVICE_ACCOUNT_KEY or GOOGLE_CLOUD_TOKEN")


async def proxy_task(
    client_websocket: WebSocketCommonProtocol, server_websocket: WebSocketCommonProtocol
) -> None:
    """
    Forwards messages from one WebSocket connection to another.

    Args:
        client_websocket: The WebSocket connection from which to receive messages.
        server_websocket: The WebSocket connection to which to send messages.
    """
    async for message in client_websocket:
        try:
            data = json.loads(message)
            
            # Log transcription messages with detailed structure
            if "serverContent" in data:
                server_content = data["serverContent"]
                if "inputTranscription" in server_content:
                    transcription = server_content["inputTranscription"]
                    if transcription.get("text"):
                        print(f"🎤 INPUT TRANSCRIPTION: {transcription['text']}")
                if "outputTranscription" in server_content:
                    transcription = server_content["outputTranscription"]
                    if transcription.get("text"):
                        print(f"🔊 OUTPUT TRANSCRIPTION: {transcription['text']}")
            
            # Log setup and non-audio messages for debugging
            if DEBUG and "realtimeInput" not in data:
                if "setup" in data:
                    print("Setup message:", data)
                elif "serverContent" in data and not data["serverContent"].get("modelTurn", {}).get("parts", [{}])[0].get("inlineData"):
                    print("Server message:", data)
                
            await server_websocket.send(json.dumps(data))
        except Exception as e:
            print(f"Error processing message: {e}")

    await server_websocket.close()


async def create_proxy(client_websocket: WebSocketCommonProtocol) -> None:
    """
    Establishes a WebSocket connection to the server and creates two tasks for
    bidirectional message forwarding between the client and the server.

    Args:
        client_websocket: The WebSocket connection of the client.
    """
    
    token = get_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    async with websockets.connect(
        SERVICE_URL, additional_headers=headers
    ) as server_websocket:
        client_to_server_task = asyncio.create_task(
            proxy_task(client_websocket, server_websocket)
        )
        server_to_client_task = asyncio.create_task(
            proxy_task(server_websocket, client_websocket)
        )
        await asyncio.gather(client_to_server_task, server_to_client_task)


async def handle_client(client_websocket: WebSocketServerProtocol) -> None:
    """
    Handles a new client connection and establishes a proxy connection to the server.

    Args:
        client_websocket: The WebSocket connection of the client.
    """
    print("New connection...")
    await create_proxy(client_websocket)


async def main() -> None:
    """
    Starts the WebSocket server and listens for incoming client connections.
    """
    print("Starting Voice Query Agent Backend...")
    print(f"PROJECT_ID: {PROJECT_ID}")
    print(f"SERVICE_ACCOUNT_KEY: {SERVICE_ACCOUNT_KEY}")
    print(f"BEARER_TOKEN exists: {bool(BEARER_TOKEN)}")
    
    ssl_context = None
    if SSL_CERT and SSL_KEY:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(SSL_CERT, SSL_KEY)
        print(f"Running secure websocket server (wss) {BIND_HOST}:{PORT}...")
    else:
        print(f"Running websocket server (ws) {BIND_HOST}:{PORT}...")
    
    async with websockets.serve(handle_client, BIND_HOST, PORT, ssl=ssl_context):
        print("WebSocket server started successfully!")
        # Run forever
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
