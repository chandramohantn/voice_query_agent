#!/bin/bash

echo "Generating self-signed SSL certificates..."

# Create ssl directory
mkdir -p frontend/ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout frontend/ssl/nginx.key \
  -out frontend/ssl/nginx.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

if [ $? -eq 0 ]; then
    echo "✓ SSL certificates generated successfully"
    echo "  - Certificate: frontend/ssl/nginx.crt"
    echo "  - Private Key: frontend/ssl/nginx.key"
    echo ""
    echo "Note: This is a self-signed certificate."
    echo "Browsers will show a security warning - this is normal."
    echo "Click 'Advanced' and 'Proceed' to continue."
else
    echo "✗ Failed to generate SSL certificates"
    exit 1
fi
