#!/bin/bash

config="/home/ubuntu/scripts/config.json"
env_file="/home/ubuntu/"

# Variables
network_name="multiexchange_network"
volume_name="multiexchange_volume"
redis="multiexchange_redis_v1"

# Configure 
if [ -f "$config" ]; then
    echo "Config file found."
    
    if [[ -s "$config" ]]; then
        NETWORK=$(jq -r '.network' $config)
        VOLUME=$(jq -r '.volume' $config)
        REDIS=$(jq -r '.redis' $config)
        FIRST_TIME=$(jq -r '.first_time' $config)
        echo "FIRST TIME: $FIRST_TIME"

        if [[ "$NETWORK" == "false" ]]; then
            echo "Setting up network"

            docker network create $network_name --driver bridge --subnet 10.0.0.0/24
            sudo jq '.network = true' "$config" | sudo tee "$config.tmp" > /dev/null && sudo mv "$config.tmp" "$config"
        fi

        if [[ "$VOLUME" == "false" ]]; then
            echo "Setting up volume"
            docker volume create $volume_name

            sudo jq '.volume = true' "$config" | sudo tee "$config.tmp" > /dev/null && sudo mv "$config.tmp" "$config"
        fi

        if [[ "$REDIS" == "false" ]]; then
            echo "Setting up redis"
            docker-compose -f /home/ubuntu/Multi-Exchange-Connector-API/docker-compose.yml build redis
            docker-compose -f /home/ubuntu/Multi-Exchange-Connector-API/docker-compose.yml up -d --no-deps redis

            sudo jq '.redis = true' "$config" | sudo tee "$config.tmp" > /dev/null && sudo mv "$config.tmp" "$config"
        fi

        if [[ "$FIRST_TIME" == "true" ]]; then
            echo "Running first time setup"
            git clone https://github.com/ElStevenn/Multi-Exchange-Connector-API.git /home/ubuntu/Multi-Exchange-Connector-API
            mkdir -p /home/ubuntu/Multi-Exchange-Connector-API/src/security
            openssl genpkey -algorithm RSA -out /home/ubuntu/Multi-Exchange-Connector-API/src/security/private_key.pem -pkeyopt rsa_keygen_bits:4096
            openssl rsa -pubout -in /home/ubuntu/Multi-Exchange-Connector-API/src/security/private_key.pem -out /home/ubuntu/Multi-Exchange-Connector-API/src/security/public_key.pem
            
            git config --global --add safe.directory /home/ubuntu/Multi-Exchange-Connector-API

        else
            echo "not first time"
            git config --global --add safe.directory /home/ubuntu/Multi-Exchange-Connector-API
            sleep 2
        fi
    else
        echo "Config file is empty."
        exit 1
    fi


else
    echo "Config file not found"
    exit 1
fi