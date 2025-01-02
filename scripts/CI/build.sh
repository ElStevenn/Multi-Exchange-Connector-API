#!/bin/bash

set -e

# Variables
DOMAIN="arvitrage.pauservices.top" 
EMAIL="paumat17@gmail.com"
APP_DIR="/home/ubuntu/Multi-Exchange-Connector-API"
CONFIG="/home/ubuntu/scripts/config.json"
IMAGE_NAME="multiexchange_api"
CONTAINER_NAME="multiexchange_apiv2"
NETWORK_NAME="multiexchange_network"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
NGINX_CONF="$NGINX_CONF_DIR/multiexchange"

# Read configuration
FIRST_TIME=$(jq -r '.first_time' "$CONFIG")

# Ensure Nginx configuration directories exist
sudo mkdir -p "$NGINX_CONF_DIR" "$NGINX_ENABLED_DIR"

# Stop and remove container
docker container stop $CONTAINER_NAME >/dev/null 2>&1 || true
docker container rm $CONTAINER_NAME >/dev/null 2>&1 || true
docker image rm $IMAGE_NAME >/dev/null 2>&1 || true

# Update configuration file if it exists
if [ -f "$CONFIG" ]; then
    jq '.api = false' "$CONFIG" | sudo tee "$CONFIG.tmp" > /dev/null && sudo mv "$CONFIG.tmp" "$CONFIG"
fi

# Allow Nginx through the firewall
sudo ufw allow 'Nginx Full' || true

cd $APP_DIR
docker build -t "$IMAGE_NAME" .
docker run -d --name "$CONTAINER_NAME" --network "$NETWORK_NAME" -p 127.0.0.1:8000:8001 "$IMAGE_NAME"

# Create Nginx server block for HTTP (temporary for Certbot)
sudo bash -c "cat > $NGINX_CONF" <<EOL
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Enable the Nginx configuration
sudo ln -sf "$NGINX_CONF" "$NGINX_ENABLED_DIR/fundy_api"
sudo rm -f /etc/nginx/sites-enabled/default || true

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
