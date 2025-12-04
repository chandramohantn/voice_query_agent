import asyncio
import json
import os
import ssl

import websockets
from websockets.legacy.protocol import WebSocketCommonProtocol
from websockets.legacy.server import WebSocketServerProtocol
from dotenv import load_dotenv

load_dotenv()

HOST = "us-central1-aiplatform.googleapis.com"
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
SERVICE_URL = f"wss://{HOST}/ws/google.cloud.aiplatform.v1beta1.LlmBidiService/BidiGenerateContent"
BEARER_TOKEN = os.getenv("GOOGLE_CLOUD_TOKEN")
PORT = int(os.getenv("PORT", "8080"))
BIND_HOST = os.getenv("BIND_HOST", "0.0.0.0")
SSL_CERT = os.getenv("SSL_CERT", None)
SSL_KEY = os.getenv("SSL_KEY", None)

DEBUG = False


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
            if DEBUG:
                print("proxying: ", data)
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

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}",
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
    ssl_context = None
    if SSL_CERT and SSL_KEY:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(SSL_CERT, SSL_KEY)
        print(f"Running secure websocket server (wss) {BIND_HOST}:{PORT}...")
    else:
        print(f"Running websocket server (ws) {BIND_HOST}:{PORT}...")
    
    async with websockets.serve(handle_client, BIND_HOST, PORT, ssl=ssl_context):
        # Run forever
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
