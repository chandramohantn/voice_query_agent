import asyncio
import json
import logging
import websockets
from typing import Optional, Callable
from audio_converter import AudioConverter

logger = logging.getLogger(__name__)

class VirtualWebSocketClient:
    """
    Virtual WebSocket client that mimics browser behavior for phone calls
    Connects to the existing Gemini proxy and handles audio conversion
    """
    
    def __init__(self, call_sid: str, proxy_url: str = "ws://localhost:8080"):
        self.call_sid = call_sid
        self.proxy_url = proxy_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        
        # Callbacks for handling responses
        self.on_audio_response: Optional[Callable[[str], None]] = None
        self.on_text_response: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        logger.info(f"Created virtual client for call {call_sid}")
    
    async def connect(self):
        """Connect to the existing Gemini WebSocket proxy"""
        try:
            logger.info(f"Connecting to proxy at {self.proxy_url}")
            self.websocket = await websockets.connect(self.proxy_url)
            self.connected = True
            
            # Send initial setup message (same as browser)
            await self.send_setup_message()
            
            # Start listening for responses
            asyncio.create_task(self.listen_for_responses())
            
            logger.info(f"Virtual client connected for call {self.call_sid}")
            
        except Exception as e:
            logger.error(f"Failed to connect virtual client: {e}")
            self.connected = False
            if self.on_error:
                self.on_error(f"Connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from the proxy"""
        if self.websocket and self.connected:
            await self.websocket.close()
            self.connected = False
            logger.info(f"Virtual client disconnected for call {self.call_sid}")
    
    async def send_setup_message(self):
        """Send initial setup message to Gemini (same format as browser)"""
        setup_message = {
            "setup": {
                "model": "projects/gen-lang-client-0427088816/locations/us-central1/publishers/google/models/gemini-2.0-flash-live-preview-04-09",
                "generation_config": {
                    "response_modalities": ["AUDIO"]
                },
                "system_instruction": {
                    "parts": [{"text": "You are a helpful voice assistant answering phone calls. Keep responses concise and natural for voice conversation."}]
                },
                "input_audio_transcription": {},
                "output_audio_transcription": {}
            }
        }
        
        await self.send_message(setup_message)
        logger.info(f"Sent setup message for call {self.call_sid}")
    
    async def send_message(self, message: dict):
        """Send message to Gemini proxy"""
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                if self.on_error:
                    self.on_error(f"Send error: {e}")
    
    async def send_audio_from_twilio(self, base64_mulaw: str):
        """
        Convert Twilio audio and send to Gemini
        
        Args:
            base64_mulaw: Base64 encoded μ-law audio from Twilio
        """
        try:
            # Convert Twilio format to Gemini format
            base64_pcm = AudioConverter.twilio_to_gemini_format(base64_mulaw)
            
            if base64_pcm:
                # Create Gemini audio message
                audio_message = AudioConverter.create_gemini_audio_message(base64_pcm)
                
                # Send to Gemini
                await self.send_message(audio_message)
                
                logger.debug(f"Sent audio to Gemini for call {self.call_sid}")
            
        except Exception as e:
            logger.error(f"Error processing Twilio audio: {e}")
            if self.on_error:
                self.on_error(f"Audio processing error: {e}")
    
    async def listen_for_responses(self):
        """Listen for responses from Gemini and handle them"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_gemini_response(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Gemini connection closed for call {self.call_sid}")
            self.connected = False
        except Exception as e:
            logger.error(f"Error listening for responses: {e}")
            if self.on_error:
                self.on_error(f"Listen error: {e}")
    
    async def handle_gemini_response(self, data: dict):
        """Handle different types of responses from Gemini"""
        try:
            # Check for setup completion
            if data.get("setupComplete"):
                logger.info(f"Setup complete for call {self.call_sid}")
                return
            
            server_content = data.get("serverContent", {})
            
            # Handle transcriptions
            if "inputTranscription" in server_content:
                transcription = server_content["inputTranscription"]
                if transcription.get("text"):
                    logger.info(f"Input transcription: {transcription['text']}")
            
            if "outputTranscription" in server_content:
                transcription = server_content["outputTranscription"]
                if transcription.get("text"):
                    logger.info(f"Output transcription: {transcription['text']}")
                    if self.on_text_response:
                        self.on_text_response(transcription["text"])
            
            # Handle audio responses
            model_turn = server_content.get("modelTurn", {})
            parts = model_turn.get("parts", [])
            
            for part in parts:
                if "inlineData" in part:
                    # This is audio data from Gemini
                    base64_pcm = part["inlineData"]["data"]
                    
                    # Convert to Twilio format
                    base64_mulaw = AudioConverter.gemini_to_twilio_format(base64_pcm)
                    
                    if base64_mulaw and self.on_audio_response:
                        self.on_audio_response(base64_mulaw)
                        logger.debug(f"Sent audio response to Twilio for call {self.call_sid}")
                
                elif "text" in part:
                    # Text response
                    if self.on_text_response:
                        self.on_text_response(part["text"])
        
        except Exception as e:
            logger.error(f"Error handling Gemini response: {e}")
            if self.on_error:
                self.on_error(f"Response handling error: {e}")
