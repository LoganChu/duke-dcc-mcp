# -------- Provider configuration --------
provider "aws" {
  region = "us-east-1"
}

# -------- Create an EC2 instance --------
resource "aws_instance" "ubuntu_server" {
  ami           = "ami-0c02fb55956c7d316"   # Ubuntu 22.04 LTS (us-east-1)
  instance_type = "t3.micro"                # Free-tier eligible instance

  # Make sure you already have this key pair in AWS EC2 -> Key Pairs
  key_name = "my-aws-keypair"

  tags = {
    Name = "terraform-demo"
  }
}

# -------- Output the public IP --------
output "instance_ip" {
  value = aws_instance.ubuntu_server.public_ip
}
