#!/bin/bash

set -e

# Variables
APP_DIR="/home/ubuntu/Multi-Exchange-Connector-API"
CONFIG="/home/ubuntu/scripts/config.json"
IMAGE_NAME="multiexchange_api"
CONTAINER_NAME="multiexchange_apiv2"
NETWORK_NAME="multiexchange_network"
DOMAIN="multiexchange.pauservices.top"

# Stop and remove container using the correct container name
docker container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker container rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

# Build API
docker-compose -f /home/ubuntu/Multi-Exchange-Connector-API/docker-compose.yml build api
docker-compose -f /home/ubuntu/Multi-Exchange-Connector-API/docker-compose.yml up -d --no-deps api

# Build Celery (worker)
docker-compose -f /home/ubuntu/Multi-Exchange-Connector-API/docker-compose.yml build celery
docker-compose -f /home/ubuntu/Multi-Exchange-Connector-API/docker-compose.yml up -d --no-deps celery

# Build Celery Beat (scheduler)
docker-compose -f /home/ubuntu/Multi-Exchange-Connector-API/docker-compose.yml build celery-beat
docker-compose -f /home/ubuntu/Multi-Exchange-Connector-API/docker-compose.yml up -d --no-deps celery-beat


# Reload Nginx to apply any new configurations
sudo nginx -t
sudo systemctl reload nginx

echo "Server restart complete. Your application should be available at http://$DOMAIN/"
