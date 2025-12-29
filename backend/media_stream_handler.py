import asyncio
import json
import logging
import websockets
from websockets.legacy.server import WebSocketServerProtocol
from call_session_manager import session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioMediaStreamHandler:
    """Handles Twilio media stream WebSocket connections with Gemini integration"""
    
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
                    await self.handle_stream_start(data, websocket)
                    
                elif event == "media":
                    await self.handle_media_data(data)
                    
                elif event == "stop":
                    await self.handle_stream_stop(data)
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Media stream connection closed")
        except Exception as e:
            logger.error(f"Error in media stream handler: {e}")
    
    async def handle_stream_start(self, data: dict, websocket):
        """Handle stream start event - create Gemini session"""
        try:
            stream_sid = data.get("streamSid")
            call_sid = data.get("start", {}).get("callSid")
            
            logger.info(f"Media stream started - StreamSid: {stream_sid}, CallSid: {call_sid}")
            
            # Create call session with Gemini connection
            session = await session_manager.create_session(call_sid, stream_sid, websocket)
            
            # Store stream info
            self.active_streams[stream_sid] = {
                "call_sid": call_sid,
                "websocket": websocket,
                "session": session
            }
            
            logger.info(f"Created Gemini session for call {call_sid}")
            
        except Exception as e:
            logger.error(f"Error handling stream start: {e}")
    
    async def handle_media_data(self, data: dict):
        """Handle incoming audio data from Twilio"""
        try:
            stream_sid = data.get("streamSid")
            payload = data.get("media", {}).get("payload")
            
            if not payload:
                return
            
            # Get the session for this stream
            session = session_manager.get_session(stream_sid)
            
            if session and session.connected:
                # Send audio to Gemini via virtual client
                await session.send_audio_to_gemini(payload)
                logger.debug(f"Processed audio for stream {stream_sid}")
            else:
                logger.warning(f"No active session for stream {stream_sid}")
                
        except Exception as e:
            logger.error(f"Error handling media data: {e}")
    
    async def handle_stream_stop(self, data: dict):
        """Handle stream stop event - cleanup session"""
        try:
            stream_sid = data.get("streamSid")
            logger.info(f"Media stream stopped - StreamSid: {stream_sid}")
            
            # End the session
            await session_manager.end_session(stream_sid)
            
            # Clean up local storage
            if stream_sid in self.active_streams:
                del self.active_streams[stream_sid]
                
        except Exception as e:
            logger.error(f"Error handling stream stop: {e}")

# Global handler instance
media_handler = TwilioMediaStreamHandler()

async def start_media_stream_server():
    """Start the media stream WebSocket server"""
    logger.info("Starting Twilio media stream server with Gemini integration on port 8083...")
    
    async with websockets.serve(
        media_handler.handle_media_stream,
        "0.0.0.0",
        8083
    ):
        logger.info("Media stream server started successfully!")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(start_media_stream_server())
