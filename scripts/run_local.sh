#!/bin/bash

# Restart Container
image_name=multiexchange_api
container_name=multiexchange_apiv2
network=my_network

# Stop and remove container
docker container stop $container_name
docker container rm $container_name

# Remove image
docker image rm $image_name

echo "Build and Deploy (y/n)?"
read res1

if [ "$res1" == "y" ];then
    # Build and run image, and start redis container
    docker build -t $image_name .
    docker run -d --name $container_name -p 8001:8001 --network $network $image_name 

    if [[ $(docker ps -a --filter "name=redis_tasks" --format '{{.Names}}') == "redis_tasks" ]]; then
        docker start redis_tasks # Ensure to have redis container installed
    fi

    # Debug
    echo "Wanna see the logs?(y/n)"
    read see_lgs
    if [ "$see_lgs" == "y" ]; then
        docker logs --follow $container_name
    fi
else
    echo "OK."
fi