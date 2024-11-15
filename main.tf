provider "aws" {
  region = "eu-south-2"
}

resource "aws_instance" "bitget_layer" {
  ami                   = "ami-08a361410fcb2f861"
  instance_type         = "t3.medium"
  

}