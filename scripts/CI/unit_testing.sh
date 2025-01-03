#!/bin/bash

container_name="multiexchange_apiv2"

echo "Running unit tests..."

# Set the correct working directory
work_dir="/src/src"

# Check if getting tables works
# echo -e "\nChecking databases..."
# docker cp /home/ubuntu/Multi-Exchange-Connector-API/src/app/database/database.py $container_name:$work_dir/app/database/database.py
# docker exec -it -w $work_dir $container_name python -m app.database.database

# sleep 2

# Check if proxy works
echo -e "\nTesting proxy..."
docker cp /home/ubuntu/Multi-Exchange-Connector-API/src/app/proxy.py $container_name:$work_dir/app/proxy.py
docker exec -it -w $work_dir $container_name python -m app.proxy
