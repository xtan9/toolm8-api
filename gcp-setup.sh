#!/bin/bash
# Google Cloud setup script for Ubuntu VM

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10
sudo apt install -y python3 python3-pip python3-venv git

# Install Docker (optional, for containerized deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Clone your repository
git clone https://github.com/yourusername/toolm8_api.git
cd toolm8_api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-prod.txt

# Create systemd service for auto-start
sudo tee /etc/systemd/system/toolm8-api.service > /dev/null <<EOF
[Unit]
Description=ToolM8 API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/toolm8_api
Environment=PATH=/home/$USER/toolm8_api/venv/bin
ExecStart=/home/$USER/toolm8_api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable toolm8-api
sudo systemctl start toolm8-api

# Configure firewall
sudo ufw allow 8000
sudo ufw allow ssh
sudo ufw --force enable

echo "Setup complete! Your API should be running on port 8000"
echo "Check status with: sudo systemctl status toolm8-api"