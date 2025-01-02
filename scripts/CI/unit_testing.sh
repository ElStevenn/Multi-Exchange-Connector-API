#!/bin/bash

container_name="multiexchange_apiv2"

echo "Running unit tests..."

# Check if getting tables works
docker cp /home/ubuntu/Multi-Exchange-Connector-API/src/app/database/database.py $multiexchange_apiv2:/src/app/database/database.py