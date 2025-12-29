import asyncio
import json
import logging
import websockets
from websockets.legacy.server import WebSocketServerProtocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioMediaStreamHandler:
    """Handles Twilio media stream WebSocket connections"""
    
    def __init__(self):
        self.active_streams = {}
    
    async def handle_media_stream(self, websocket: WebSocketServerProtocol, path: str):
        """Handle incoming Twilio media stream WebSocket connection"""
        
        logger.info(f"New media stream connection from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                event = data.get("event")
                
                if event == "connected":
                    logger.info("Media stream connected")
                    
                elif event == "start":
                    stream_sid = data.get("streamSid")
                    call_sid = data.get("start", {}).get("callSid")
                    logger.info(f"Media stream started - StreamSid: {stream_sid}, CallSid: {call_sid}")
                    
                    # Store stream info
                    self.active_streams[stream_sid] = {
                        "call_sid": call_sid,
                        "websocket": websocket
                    }
                    
                elif event == "media":
                    # Audio data received from Twilio
                    stream_sid = data.get("streamSid")
                    payload = data.get("media", {}).get("payload")
                    
                    # For now, just log that we received audio
                    logger.debug(f"Received audio data from StreamSid: {stream_sid}, Length: {len(payload) if payload else 0}")
                    
                elif event == "stop":
                    stream_sid = data.get("streamSid")
                    logger.info(f"Media stream stopped - StreamSid: {stream_sid}")
                    
                    # Clean up
                    if stream_sid in self.active_streams:
                        del self.active_streams[stream_sid]
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Media stream connection closed")
        except Exception as e:
            logger.error(f"Error in media stream handler: {e}")

# Global handler instance
media_handler = TwilioMediaStreamHandler()

async def start_media_stream_server():
    """Start the media stream WebSocket server"""
    logger.info("Starting Twilio media stream server on port 8083...")
    
    async with websockets.serve(
        media_handler.handle_media_stream,
        "0.0.0.0",
        8083
    ):
        logger.info("Media stream server started successfully!")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(start_media_stream_server())
