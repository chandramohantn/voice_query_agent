#!/bin/bash

# Voice Query Agent - Multi-Service Startup Script

echo "Starting Voice Query Agent with Twilio Integration..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: Virtual environment not detected. Activating .venv..."
    source .venv/bin/activate
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt

# Start services in background
echo "Starting services..."

# 1. Main WebSocket server (existing functionality)
echo "Starting WebSocket server (port 8080)..."
python backend/main.py &
MAIN_PID=$!

# 2. Twilio webhook handler
echo "Starting Twilio webhook handler (port 8082)..."
python backend/twilio_handler.py &
WEBHOOK_PID=$!

# 3. Media stream handler
echo "Starting media stream handler (port 8081)..."
python backend/media_stream_handler.py &
MEDIA_PID=$!

echo ""
echo "All services started successfully!"
echo "- WebSocket Server (Browser): http://localhost:8080"
echo "- Twilio Webhooks: http://localhost:8082"
echo "- Media Streams: ws://localhost:8083"
echo ""
echo "Configure your Twilio phone number webhook URL to:"
echo "  https://your-domain.com/incoming-call"
echo ""
echo "Press Ctrl+C to stop all services..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $MAIN_PID $WEBHOOK_PID $MEDIA_PID 2>/dev/null
    echo "All services stopped."
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for any process to exit
wait
