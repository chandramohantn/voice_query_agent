import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.request_validator import RequestValidator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")

app = FastAPI()

# Twilio request validator for security
validator = RequestValidator(TWILIO_AUTH_TOKEN) if TWILIO_AUTH_TOKEN else None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "twilio-webhook-handler"}

@app.post("/incoming-call")
async def handle_incoming_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...)
):
    """Handle incoming Twilio voice calls"""
    
    logger.info(f"Incoming call - CallSid: {CallSid}, From: {From}, To: {To}")
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Start media stream
    response.say("Hello! You are now connected to the voice agent. Please speak after the tone.")
    
    # Start bidirectional media stream
    start = response.start()
    stream = start.stream(
        url=f"wss://{request.url.hostname}:8083/media-stream",
        track="both_tracks"
    )
    
    # Keep the call alive
    response.pause(length=60)
    
    logger.info(f"Generated TwiML for CallSid: {CallSid}")
    
    return Response(
        content=str(response),
        media_type="application/xml"
    )

@app.post("/call-status")
async def handle_call_status(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...)
):
    """Handle call status updates"""
    
    logger.info(f"Call status update - CallSid: {CallSid}, Status: {CallStatus}")
    
    return {"status": "received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
