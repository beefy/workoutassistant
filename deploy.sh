#!/bin/bash

# Docker deployment script for Raspberry Pi
# This script sets up Docker, pulls the image, and starts the container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 WorkoutAssistant Docker Deployment Script${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Please don't run this script as root${NC}"
    exit 1
fi

# Check if .variables file exists
if [ ! -f "$HOME/.variables" ]; then
    echo -e "${YELLOW}⚠️ Warning: $HOME/.variables file not found${NC}"
    echo "Please create this file with your environment variables before continuing."
    echo "Example content:"
    echo "GMAIL_ADDRESS=your-email@gmail.com"
    echo "GMAIL_APP_PASSWORD=your-app-password"
    echo "# ... other variables ..."
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed. You may need to log out and back in.${NC}"
fi

# Install Docker Compose if not present
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p ~/workoutassistant/{data,models,logs}

# Download docker-compose.yml if not present
if [ ! -f ~/workoutassistant/docker-compose.yml ]; then
    echo -e "${YELLOW}📥 Downloading docker-compose.yml...${NC}"
    curl -L "https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/workoutassistant/main/docker-compose.yml" -o ~/workoutassistant/docker-compose.yml
fi

cd ~/workoutassistant

# Set the Docker image name (replace YOUR_DOCKERHUB_USERNAME with your actual username)
export DOCKER_IMAGE="${DOCKER_IMAGE:-YOUR_DOCKERHUB_USERNAME/workoutassistant:latest}"

# Pull the latest image
echo -e "${YELLOW}🐳 Pulling Docker image...${NC}"
docker pull $DOCKER_IMAGE

# Start the containers
echo -e "${YELLOW}🚀 Starting containers...${NC}"
docker compose up -d

# Create systemd service for auto-startup
echo -e "${YELLOW}⚙️ Setting up auto-startup service...${NC}"
sudo tee /etc/systemd/system/workoutassistant.service > /dev/null <<EOF
[Unit]
Description=WorkoutAssistant Docker Container
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$HOME/workoutassistant
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
User=$USER
Group=$USER
Environment=DOCKER_IMAGE=${DOCKER_IMAGE}

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable workoutassistant.service

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}📊 Container status:${NC}"
docker compose ps

echo -e "\n${YELLOW}💡 Useful commands:${NC}"
echo "  Check logs: docker compose logs -f workoutassistant"
echo "  Stop: docker compose down"
echo "  Restart: docker compose restart"
echo "  Update: docker compose pull && docker compose up -d"
echo "  Service status: sudo systemctl status workoutassistant.service"