#!/bin/bash

echo "Setting up SSL for backend..."

# Create backend ssl directory
mkdir -p backend/ssl

# Copy SSL certificates from frontend
cp frontend/ssl/nginx.crt backend/ssl/server.crt
cp frontend/ssl/nginx.key backend/ssl/server.key

echo "✓ SSL certificates copied to backend/ssl/"
echo "  - Certificate: backend/ssl/server.crt"
echo "  - Private Key: backend/ssl/server.key"
