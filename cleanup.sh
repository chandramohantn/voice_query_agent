#!/bin/bash

echo "Stopping all services..."

# Stop docker-compose services
docker-compose down

echo "✓ All services stopped"
