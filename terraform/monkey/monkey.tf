terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "6.0.0-beta1"
    }
  }
}

provider "aws" {
  region = "eu-west-1"
}

resource "aws_instance" "monkey" {
  ami           = "ami-03d8b47244d950bbb"  
  instance_type = "t2.micro"
  key_name      = "switches"       
  
  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo yum install -y docker
              sudo systemctl start docker
              sudo systemctl enable docker
              sudo usermod -a -G docker ec2-user
              sudo yum install python -y
              EOF


  tags = {
    Name = "TerraformEC2"
  }
}
output "ec2_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.monkey.public_ip
}
