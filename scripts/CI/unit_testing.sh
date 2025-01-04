#!/bin/bash

# Variables
api_container_name="multiexchange_apiv2"
celery_container_name="multiexchange_celery"

test_celery=true
test_database=false


echo "Running unit tests..."

# Set the correct working directory
work_dir="/src/src"

# Check if getting tables works
if [ "$test_database" == "true" ]; then
echo -e "\nChecking databases..."
docker cp /home/ubuntu/Multi-Exchange-Connector-API/src/app/database/database.py $api_container_name:$work_dir/app/database/database.py
docker exec -it -w $work_dir $api_container_name python -m app.database.database
sleep 2
fi




# Check if proxy works
echo -e "\nTesting proxy..."
docker cp /home/ubuntu/Multi-Exchange-Connector-API/src/app/proxy.py $api_container_name:$work_dir/app/proxy.py
docker exec -it -w $work_dir $api_container_name python -m app.proxy
sleep 2


# Celery test if gets data
if [ "$test_celery" == "true" ]; then
    echo -e "\nTesting Celery..."
    docker exec -it -w $work_dir $celery_container_name python -m app.celery_app.run

fi