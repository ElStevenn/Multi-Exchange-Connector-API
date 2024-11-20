provider "aws" {
  region = "eu-south-2"
}

resource "aws_instance" "bitget_layer" {
  ami                   = "ami-08a361410fcb2f861"
  instance_type         = "t3.medium"
  
  # PENDNET THINKS TO HANDLE
  # - Providers: 
  #   - Install Docker
  #   - Install K8s
  #   - Set needed datetimes and variables
  #   - Create public and private key as "private_key.pem" and "public_key.pem"
}
