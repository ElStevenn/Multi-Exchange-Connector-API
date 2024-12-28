#!/bin/bash
sudo apt update -y
sudo timedatectl set-timezone Europe/Madrid
sudo apt install -y unzip curl jq

# Install jq if not already installed
if ! command -v jq &> /dev/null; then
  sudo apt install jq -y
fi

install_docker() {
    # Function to install Docker

    echo "Docker is not installed. Installing Docker and dependencies..."
    sudo apt-get update -y
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    sudo usermod -aG docker "$USER"
    echo "Docker installation complete. Please log out and back in to use Docker without sudo."
}

if ! command -v docker &> /dev/null; then
    install_docker
else
    echo "Docker is installsed"
fi


# Install AWS CLI
if ! command -v aws &> /dev/null; then
  echo "AWS CLI not found. Installing..."
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip awscliv2.zip
  sudo ./aws/install
  if ! command -v aws &> /dev/null; then
    echo "AWS CLI installation failed."
    exit 1
  fi
fi


