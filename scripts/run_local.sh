#!/bin/bash

# Restart Container
image_name=bitget_api
container_name=bitget_apiv1

# Stop and remove container
docker container stop $container_name
docker container rm $container_name

# Remove image
docker image rm $image_name

# Test
echo "Test? (y/n)"
read test
if [ "$test" == "y" ]; then
    echo "Nothing to test"
fi

echo "Build and Deploy (y/n)?"
read res1

if [ "$res1" == "y" ];then
    # Build and run image
    docker build -t $image_name .
    docker run -d --name $container_name -p 8001:8001 $image_name

    # Debug
    echo "Wanna see the logs?(y/n)"
    read see_lgs
    if [ "$see_lgs" == "y" ]; then
        docker logs --follow $container_name
    fi
else
    echo "OK."
fi