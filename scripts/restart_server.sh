#!/bin/bash

set -e

# Variables
APP_DIR="/home/ubuntu/Multi-Exchange-Connector-API"
CONFIG="/home/ubuntu/scripts/config.json"
IMAGE_NAME="multiexchange_api"
CONTAINER_NAME="multiexchange_apiv2"
NETWORK_NAME="multiexchange_network"

# Stop and remove container
docker container stop $IMAGE_NAME >/dev/null 2>&1 || true
docker container rm $IMAGE_NAME >/dev/null 2>&1 || true

# Rebuild and run image
docker build -t "$IMAGE_NAME" .
docker run -d --name "$CONTAINER_NAME" --network "$NETWORK_NAME" -p 127.0.0.1:8000:8001 "$IMAGE_NAME"

# Reload nginx
sudo nginx -t
sudo systemctl reload nginx

echo "Server restart complete. Your application should be available at http//$DOMAIN/" 