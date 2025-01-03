#!/bin/bash

container_name="multiexchange_apiv2"

echo "Running unit tests..."

# Check if getting tables works
echo "Checking databases"
docker cp /home/ubuntu/Multi-Exchange-Connector-API/src/app/database/database.py $container_name:/src/app/database/database.py
docker exec -it -w / $container_name python -m src.app.database.database

sleep 2

docker logs --follow $container_name
