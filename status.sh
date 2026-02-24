#!/bin/bash

# WorkoutAssistant System Status Check
# This script checks if WorkoutAssistant is running properly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 WorkoutAssistant System Status Check${NC}\n"

# Check if Docker is installed and running
echo -e "${YELLOW}📦 Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo -e "${GREEN}✅ Docker is installed and running${NC}"
    else
        echo -e "${RED}❌ Docker is installed but not running${NC}"
        echo "Try: sudo systemctl start docker"
        exit 1
    fi
else
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Run the deploy.sh script to install Docker automatically"
    exit 1
fi

# Check if containers are running
echo -e "\n${YELLOW}🐳 Checking containers...${NC}"
cd ~/workoutassistant 2>/dev/null || {
    echo -e "${RED}❌ WorkoutAssistant directory not found at ~/workoutassistant${NC}"
    echo "Run the deploy.sh script first"
    exit 1
}

if docker compose ps | grep -q "workoutassistant.*Up"; then
    echo -e "${GREEN}✅ WorkoutAssistant container is running${NC}"
else
    echo -e "${RED}❌ WorkoutAssistant container is not running${NC}"
    echo "Try: docker compose up -d"
fi

if docker compose ps | grep -q "watchtower.*Up"; then
    echo -e "${GREEN}✅ Watchtower (auto-updater) is running${NC}"
else
    echo -e "${YELLOW}⚠️ Watchtower (auto-updater) is not running${NC}"
fi

# Check secrets file
echo -e "\n${YELLOW}🔐 Checking secrets file...${NC}"
if [ -f "$HOME/.variables" ]; then
    echo -e "${GREEN}✅ Secrets file found at ~/.variables${NC}"
    
    # Check for required variables
    required_vars=("GMAIL_ADDRESS" "GMAIL_APP_PASSWORD" "ADMIN_EMAIL")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$HOME/.variables" 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ Required environment variables are present${NC}"
    else
        echo -e "${YELLOW}⚠️ Missing required variables: ${missing_vars[*]}${NC}"
        echo "Please add these to your ~/.variables file"
    fi
else
    echo -e "${RED}❌ Secrets file not found at ~/.variables${NC}"
    echo "Create this file with your environment variables"
    echo "See .variables.example for template"
fi

# Check if system service is enabled
echo -e "\n${YELLOW}⚙️ Checking auto-startup service...${NC}"
if systemctl is-enabled workoutassistant.service &>/dev/null; then
    echo -e "${GREEN}✅ Auto-startup service is enabled${NC}"
    if systemctl is-active workoutassistant.service &>/dev/null; then
        echo -e "${GREEN}✅ Auto-startup service is active${NC}"
    else
        echo -e "${YELLOW}⚠️ Auto-startup service is enabled but not active${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Auto-startup service is not enabled${NC}"
    echo "Run deploy.sh to set up auto-startup"
fi

# Check container logs for errors
echo -e "\n${YELLOW}📋 Checking recent logs for errors...${NC}"
if docker compose ps | grep -q "workoutassistant.*Up"; then
    error_count=$(docker compose logs --since="1h" workoutassistant 2>/dev/null | grep -i "error\|exception\|failed" | wc -l)
    if [ "$error_count" -eq 0 ]; then
        echo -e "${GREEN}✅ No recent errors in logs${NC}"
    else
        echo -e "${YELLOW}⚠️ Found $error_count error(s) in the last hour${NC}"
        echo "Check logs with: docker compose logs workoutassistant"
    fi
else
    echo -e "${YELLOW}⚠️ Container not running, cannot check logs${NC}"
fi

# Show container resource usage
echo -e "\n${YELLOW}📊 Container resource usage:${NC}"
if docker compose ps | grep -q "workoutassistant.*Up"; then
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" workoutassistant 2>/dev/null || echo "Unable to get stats"
fi

echo -e "\n${BLUE}🎯 Quick Commands:${NC}"
echo "  View logs: docker compose logs -f workoutassistant"
echo "  Restart: docker compose restart"
echo "  Update: docker compose pull && docker compose up -d"
echo "  Stop: docker compose down"