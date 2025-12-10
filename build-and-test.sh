#!/bin/bash

set -e

echo "========================================="
echo "Voice Query Agent - Build & Test Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Build Docker images
echo "Step 1: Building Docker images..."
docker-compose build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

echo ""

# Step 2: Start services with docker-compose
echo "Step 2: Starting services with docker-compose..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Services started${NC}"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Step 3: Test backend WebSocket server
echo ""
echo "Step 3: Testing backend WebSocket server..."

# Check if backend container is running
BACKEND_STATUS=$(docker-compose ps -q backend)
if [ -z "$BACKEND_STATUS" ]; then
    echo -e "${RED}✗ Backend container is not running${NC}"
    docker-compose logs backend
    # docker-compose down
    exit 1
fi

# Check if port 8080 is listening (WebSocket should return 426)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "426" ]; then
    echo -e "${GREEN}✓ Backend WebSocket is listening on port 8080${NC}"
else
    echo -e "${RED}✗ Backend is not accessible on port 8080 (HTTP $HTTP_CODE)${NC}"
    docker-compose logs backend
    # docker-compose down
    exit 1
fi

# Check backend logs for startup message
if docker-compose logs backend | grep -q "Running.*websocket server"; then
    echo -e "${GREEN}✓ Backend started successfully${NC}"
else
    echo -e "${YELLOW}⚠ Backend may not have started correctly${NC}"
    docker-compose logs backend
fi

echo ""

# Step 4: Test frontend server
echo "Step 4: Testing frontend server..."

# Check if frontend container is running
FRONTEND_STATUS=$(docker-compose ps -q frontend)
if [ -z "$FRONTEND_STATUS" ]; then
    echo -e "${RED}✗ Frontend container is not running${NC}"
    docker-compose logs frontend
    docker-compose down
    exit 1
fi

# Wait a bit more for nginx to be ready
sleep 3

# Check if frontend HTTPS is accessible
HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Frontend is accessible on https://localhost${NC}"
else
    # Fallback to HTTP test
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        echo -e "${GREEN}✓ Frontend HTTP redirects to HTTPS (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${RED}✗ Frontend is not accessible (HTTP $HTTP_CODE)${NC}"
        docker-compose logs frontend
        docker-compose down
        exit 1
    fi
fi

echo ""
echo "========================================="
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "========================================="
echo ""
echo "Services are running:"
echo "  - Backend WebSocket: wss://localhost:8080 (secure)"
echo "  - Frontend: https://localhost (HTTPS)"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f frontend"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "Note: Accept the self-signed certificate warning in your browser"
echo ""
