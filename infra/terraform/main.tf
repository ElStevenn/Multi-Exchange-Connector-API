provider "aws" {
  region = "eu-south-2"
}

# Key pair
resource "aws_key_pair" "instance_pub_key" {
  key_name   = "multiexchange_key"
  public_key = file("../../src/security/instance_key.pub")
}

resource "aws_iam_role" "ssm_role" {
  name = "ssm_full_acces_role_lol"
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


data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}


data "aws_security_group" "paus-security-group" {
  name = "paus-security-group"
  id   = "sg-0ceebb5821128f97d" # Turn it into a variable 
}


data "aws_iam_instance_profile" "ssm-fullacces" {
  name = "ssm-fullacces"
}

resource "aws_eip" "main_api_eip" {
  provider = aws
  # No arguments; this resource is managed by importing the existing EIP.

  tags = {
    Name = "Multi Exchange Connector API"
  }
}

resource "aws_instance" "multiexchange_api" {
  ami                    = var.ami_id
  instance_type          = "t3.medium"
  key_name               = aws_key_pair.instance_pub_key.key_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [data.aws_security_group.paus-security-group.id]
  iam_instance_profile   = data.aws_iam_instance_profile.ssm-fullacces.name

  tags = {
    Name = "Multi Exchange Layer"
    Type = "Routing"
  }

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  lifecycle {
    ignore_changes = [ami]
  }

  provisioner "local-exec" {
    command = <<EOT
      git -C /home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API add . &&
      git -C /home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API commit -m "${var.commit_message}" &&
      git -C /home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API push -u origin main
    EOT
  }

  provisioner "file" {
    source      = "/home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API/scripts"
    destination = "/home/ubuntu/scripts"
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = self.public_ip
    }
  }

  provisioner "file" {
    source      = "/home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API/scripts/config.json"
    destination = "/home/ubuntu/scripts/config.json"
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = self.public_ip
    }
  }


  provisioner "remote-exec" {
    inline = [
      "sudo chmod +x /home/ubuntu/scripts/CI/*",
      "sudo chmod 644 /home/ubuntu/scripts/config.json",
      "bash /home/ubuntu/scripts/CI/source.sh"
    ]
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = self.public_ip
    }
  }
   provisioner "file" {
    source      = "/home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API/src/.env"
    destination = "/home/ubuntu/Multi-Exchange-Connector-API/src/.env"
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = self.public_ip
    }
  }
}

resource "aws_eip_association" "main_api_eip_assoc" {
  instance_id   = aws_instance.multiexchange_api.id
  allocation_id = aws_eip.main_api_eip.id

  depends_on = [
    aws_instance.multiexchange_api,
    aws_eip.main_api_eip
  ]
}

resource "null_resource" "post_eip_setup" {
  depends_on = [aws_eip_association.main_api_eip_assoc]

  provisioner "remote-exec" {
    inline = [
      "sudo chmod +x /home/ubuntu/scripts/CI/*",
      "sudo chmod 644 /home/ubuntu/scripts/config.json",
      "sudo usermod -aG docker ubuntu",
      "sudo systemctl restart docker",
      "sudo chmod 666 /var/run/docker.sock",
      "bash /home/ubuntu/scripts/CI/build.sh"
    ]
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = aws_eip.main_api_eip.public_ip
    }
  }
}


resource "null_resource" "update_container" {
  depends_on = [aws_eip_association.main_api_eip_assoc]
  triggers = {
    manual_trigger = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOT
      git -C /home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API add . &&
      git -C /home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API commit -m "${var.commit_message}" &&
      git -C /home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API push -u origin main
    EOT
  }

  provisioner "file" {
    source      = "/home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API/scripts/CI"
    destination = "/home/ubuntu/scripts"
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = aws_eip.main_api_eip.public_ip
    }
  }

  provisioner "file" {
    source      = "/home/mrpau/Desktop/Secret_Project/other_layers/Multi-Exchange-Connector-API/src/.env"
    destination = "/home/ubuntu/Multi-Exchange-Connector-API/src/.env"
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = aws_eip.main_api_eip.public_ip
    }
  }

  provisioner "remote-exec" {
    inline = [
      "git -C /home/ubuntu/Multi-Exchange-Connector-API reset --hard",
      "git -C /home/ubuntu/Multi-Exchange-Connector-API config pull.rebase false",
      "git -C /home/ubuntu/Multi-Exchange-Connector-API pull origin main",
      # "bash /home/ubuntu/scripts/CI/build.sh",
      "chmod +x /home/ubuntu/scripts/*",
      "bash /home/ubuntu/scripts/restart_server.sh"
    ]
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key")
      host        = aws_eip.main_api_eip.public_ip
    }
  }
}

output "elastic_ip" {
  value       = aws_eip.main_api_eip.public_ip
  description = "The Elastic IP address associated with the EC2 instance."
}
