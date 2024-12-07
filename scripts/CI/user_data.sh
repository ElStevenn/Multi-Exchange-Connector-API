#!/bin/bash

sudo apt update -y
sudo timedatectl set-timezone Europe/Madrid
sudo apt install -y unzip curl jq

# Install jq
if ! command -v jq &> /dev/null; then
  sudo apt install jq -y
fi

# Install Docker & Dependencies
sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

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
echo "AWS CLI version: $(aws --version)"
