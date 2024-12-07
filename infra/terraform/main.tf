provider "aws" {
  region = "eu-south-2"
}

# Key pair
resource "aws_key_pair" "instance_pub_key" {
  key_name   = "multiexchange_key"
  public_key = file("../../src/security/instance_key.pub")
}


resource "aws_iam_role" "ssm_role" {
  name = "ssm_full_acces_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_full_access" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMFullAccess"
}


# Data Source for AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_iam_instance_profile" "cli_permissions" {
  name = "cli_permissions"
}

data "aws_security_group" "paus-security-group" {
  name = "paus-security-group"
  id = "sg-0ceebb5821128f97d"
}

resource "aws_instance" "multiexchange_api" {
  ami                   = data.aws_ami.ubuntu.id
  instance_type         = "t3.medium"
  key_name              = aws_key_pair.instance_pub_key.key_name
  subnet_id             = var.subnet_id
  vpc_security_group_ids = [data.aws_security_group.paus-security-group.id]

  iam_instance_profile = data.aws_iam_instance_profile.cli_permissions.name

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = "Exchange connector"
    Type = "Routing"
  }

  provisioner "local-exec" {
    command = "tar -czf /tmp/multi-exchange.tar.gz -C /home/mrpau/Desktop/Secret_Project/other_layers Multi-Exchange-Connector-API"
  }

  provisioner "file" {
    source      = "/tmp/multi-exchange.tar.gz"
    destination = "/home/ubuntu/multi-exchange.tar.gz"
    
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = self.public_ip
    }
  }

  provisioner "remote-exec" {
    inline = [
      "tar -xzf /home/ubuntu/multi-exchange.tar.gz -C /home/ubuntu/",
      "rm /home/ubuntu/multi-exchange.tar.gz",
      "chmod +x /home/ubuntu/multi-exchange/scripts/*",
      # CI
      "./home/ubuntu/multi-exchange/scripts/user_data.sh"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = self.public_ip
    }

  }

}
