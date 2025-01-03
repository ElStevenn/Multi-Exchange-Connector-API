#!/bin/bash

container_name="multiexchange_apiv2"

echo "Running unit tests..."

# Check if getting tables works
echo -e"Checking databases"
docker cp /home/ubuntu/Multi-Exchange-Connector-API/src/app/database/database.py $container_name:/src/app/database/database.py
docker exec -it -w / $container_name python -m src.app.database.database

sleep 2

# Check if proxy works
echo -e "Testing proxy...\n"
docker cp /home/ubuntu/Multi-Exchange-Connector-API/src/app/proxy.py $container_name:/src/app/proxy.py
docker exec -it -w / $container_name python -m src.app.proxy
