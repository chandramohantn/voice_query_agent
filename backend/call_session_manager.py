import asyncio
import json
import logging
import websockets
from typing import Dict, Optional
from virtual_client import VirtualWebSocketClient

logger = logging.getLogger(__name__)

class CallSession:
    """Represents an active phone call session"""
    
    def __init__(self, call_sid: str, stream_sid: str, twilio_websocket):
        self.call_sid = call_sid
        self.stream_sid = stream_sid
        self.twilio_websocket = twilio_websocket
        self.virtual_client: Optional[VirtualWebSocketClient] = None
        self.connected = False
        
        logger.info(f"Created call session - CallSid: {call_sid}, StreamSid: {stream_sid}")
    
    async def start_gemini_connection(self):
        """Start connection to Gemini via virtual client"""
        try:
            self.virtual_client = VirtualWebSocketClient(self.call_sid)
            
            # Set up callbacks
            self.virtual_client.on_audio_response = self.send_audio_to_twilio
            self.virtual_client.on_text_response = self.handle_text_response
            self.virtual_client.on_error = self.handle_error
            
            # Connect to Gemini
            await self.virtual_client.connect()
            self.connected = True
            
            logger.info(f"Gemini connection established for call {self.call_sid}")
            
        except Exception as e:
            logger.error(f"Failed to start Gemini connection: {e}")
            self.connected = False
    
    async def send_audio_to_gemini(self, base64_mulaw: str):
        """Send audio from Twilio to Gemini"""
        if self.virtual_client and self.connected:
            await self.virtual_client.send_audio_from_twilio(base64_mulaw)
    
    async def send_audio_to_twilio(self, base64_mulaw: str):
        """Send audio response from Gemini back to Twilio"""
        try:
            if self.twilio_websocket:
                # Create Twilio media message
                media_message = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {
                        "payload": base64_mulaw
                    }
                }
                
                await self.twilio_websocket.send(json.dumps(media_message))
                logger.debug(f"Sent audio to Twilio for call {self.call_sid}")
                
        except Exception as e:
            logger.error(f"Error sending audio to Twilio: {e}")
    
    def handle_text_response(self, text: str):
        """Handle text responses from Gemini (for logging/debugging)"""
        logger.info(f"Gemini text response for call {self.call_sid}: {text}")
    
    def handle_error(self, error: str):
        """Handle errors from virtual client"""
        logger.error(f"Virtual client error for call {self.call_sid}: {error}")
        self.connected = False
    
    async def cleanup(self):
        """Clean up the call session"""
        if self.virtual_client:
            await self.virtual_client.disconnect()
        
        self.connected = False
        logger.info(f"Cleaned up call session {self.call_sid}")


class CallSessionManager:
    """Manages active call sessions"""
    
    def __init__(self):
        self.active_sessions: Dict[str, CallSession] = {}
        logger.info("Call session manager initialized")
    
    async def create_session(self, call_sid: str, stream_sid: str, twilio_websocket) -> CallSession:
        """Create a new call session"""
        try:
            session = CallSession(call_sid, stream_sid, twilio_websocket)
            
            # Start Gemini connection
            await session.start_gemini_connection()
            
            # Store session
            self.active_sessions[stream_sid] = session
            
            logger.info(f"Created session for call {call_sid} with stream {stream_sid}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, stream_sid: str) -> Optional[CallSession]:
        """Get an active session by stream ID"""
        return self.active_sessions.get(stream_sid)
    
    async def end_session(self, stream_sid: str):
        """End and cleanup a call session"""
        session = self.active_sessions.get(stream_sid)
        if session:
            await session.cleanup()
            del self.active_sessions[stream_sid]
            logger.info(f"Ended session for stream {stream_sid}")
    
    async def cleanup_all_sessions(self):
        """Cleanup all active sessions"""
        for stream_sid in list(self.active_sessions.keys()):
            await self.end_session(stream_sid)
        
        logger.info("All sessions cleaned up")
    
    def get_active_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_sessions)

# Global session manager instance
session_manager = CallSessionManager()
