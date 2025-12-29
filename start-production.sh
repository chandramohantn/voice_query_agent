#!/bin/bash

# Production Voice Query Agent with Twilio Integration
# Starts all required services with proper monitoring and logging

set -e  # Exit on any error

# Configuration
LOG_DIR="logs"
PID_DIR="pids"

# Create directories
mkdir -p $LOG_DIR $PID_DIR

echo "🚀 Starting Voice Query Agent - Production Mode"
echo "================================================"

# Function to check if service is running
check_service() {
    local port=$1
    local name=$2
    
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port already in use by $name"
        return 1
    fi
    return 0
}

# Function to start service with logging
start_service() {
    local script=$1
    local name=$2
    local port=$3
    local pid_file="$PID_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"
    
    echo "Starting $name on port $port..."
    
    # Check if port is available
    if ! check_service $port $name; then
        echo "❌ Cannot start $name - port $port in use"
        return 1
    fi
    
    # Start service in background with logging
    nohup python3 $script > $log_file 2>&1 &
    local pid=$!
    echo $pid > $pid_file
    
    # Wait and verify startup
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo "✅ $name started successfully (PID: $pid)"
        return 0
    else
        echo "❌ $name failed to start"
        return 1
    fi
}

# Function to stop all services
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    
    for pid_file in $PID_DIR/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat $pid_file)
            local name=$(basename $pid_file .pid)
            
            if kill -0 $pid 2>/dev/null; then
                kill $pid
                echo "   Stopped $name (PID: $pid)"
            fi
            rm -f $pid_file
        fi
    done
    
    echo "✅ All services stopped"
    exit 0
}

# Set trap for cleanup on exit
trap cleanup SIGINT SIGTERM EXIT

# Check virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating .venv..."
    source .venv/bin/activate
fi

# Install/update dependencies
echo "📦 Checking dependencies..."
pip install -r backend/requirements.txt -q

echo ""
echo "🔧 Starting services..."

# 1. Main WebSocket Server (Gemini Proxy)
if start_service "backend/main.py" "gemini-proxy" "8080"; then
    echo "   📡 Gemini proxy ready for browser clients"
else
    echo "❌ Failed to start Gemini proxy - aborting"
    exit 1
fi

# 2. Twilio Webhook Handler
if start_service "backend/twilio_handler.py" "twilio-webhooks" "8082"; then
    echo "   📞 Twilio webhook handler ready"
else
    echo "❌ Failed to start Twilio webhooks - aborting"
    exit 1
fi

# 3. Media Stream Handler
if start_service "backend/media_stream_handler.py" "media-streams" "8083"; then
    echo "   🎵 Media stream handler ready"
else
    echo "❌ Failed to start media streams - aborting"
    exit 1
fi

echo ""
echo "✅ All services running successfully!"
echo "================================================"
echo "📊 Service Status:"
echo "   🌐 Gemini Proxy:     http://localhost:8080 (WebSocket)"
echo "   📞 Twilio Webhooks:  http://localhost:8082 (HTTP)"
echo "   🎵 Media Streams:    ws://localhost:8083 (WebSocket)"
echo ""
echo "📋 Frontend Access:"
echo "   🖥️  Browser Client:   http://localhost:8001 (start with: cd frontend && python3 -m http.server 8001)"
echo ""
echo "🔧 Twilio Configuration:"
echo "   📱 Webhook URL:      https://your-domain.com/incoming-call"
echo "   🎤 Media Stream:     wss://your-domain.com:8083/media-stream"
echo ""
echo "📊 Monitoring:"
echo "   📄 Logs:            tail -f logs/*.log"
echo "   🔍 Health Check:    curl http://localhost:8082/health"
echo ""
echo "Press Ctrl+C to stop all services..."

# Keep script running and monitor services
while true; do
    sleep 10
    
    # Check if all services are still running
    all_running=true
    for pid_file in $PID_DIR/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat $pid_file)
            if ! kill -0 $pid 2>/dev/null; then
                local name=$(basename $pid_file .pid)
                echo "⚠️  Service $name (PID: $pid) has stopped unexpectedly"
                all_running=false
            fi
        fi
    done
    
    if [ "$all_running" = false ]; then
        echo "❌ Some services have failed - check logs in $LOG_DIR/"
        break
    fi
done
