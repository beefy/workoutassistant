#!/bin/bash

# Script to update usernames in configuration files
# Run this after forking the repository to set up your own usernames

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 WorkoutAssistant Configuration Setup${NC}\n"

# Function to prompt for input with validation
prompt_for_input() {
    local prompt="$1"
    local var_name="$2"
    local example="$3"
    local input=""
    
    while [ -z "$input" ]; do
        echo -e "${YELLOW}$prompt${NC}"
        if [ ! -z "$example" ]; then
            echo -e "Example: $example"
        fi
        read -p "> " input
        if [ -z "$input" ]; then
            echo -e "${RED}This field is required. Please enter a value.${NC}\n"
        fi
    done
    
    eval "$var_name='$input'"
}

# Get user inputs
prompt_for_input "Enter your GitHub username:" "GITHUB_USERNAME" "john-doe"
prompt_for_input "Enter your DockerHub username:" "DOCKERHUB_USERNAME" "johndoe"

echo -e "\n${YELLOW}Updating configuration files...${NC}"

# Update docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    sed -i.backup "s/YOUR_DOCKERHUB_USERNAME/$DOCKERHUB_USERNAME/g" docker-compose.yml
    echo -e "${GREEN}✅ Updated docker-compose.yml${NC}"
else
    echo -e "${RED}❌ docker-compose.yml not found${NC}"
fi

# Update deploy.sh
if [ -f "deploy.sh" ]; then
    sed -i.backup "s/YOUR_DOCKERHUB_USERNAME/$DOCKERHUB_USERNAME/g" deploy.sh
    sed -i.backup "s/YOUR_GITHUB_USERNAME/$GITHUB_USERNAME/g" deploy.sh
    echo -e "${GREEN}✅ Updated deploy.sh${NC}"
else
    echo -e "${RED}❌ deploy.sh not found${NC}"
fi

# Update README.md
if [ -f "README.md" ]; then
    sed -i.backup "s/YOUR_USERNAME/$GITHUB_USERNAME/g" README.md
    sed -i.backup "s/YOUR_DOCKERHUB_USERNAME/$DOCKERHUB_USERNAME/g" README.md
    sed -i.backup "s/YOUR_GITHUB_USERNAME/$GITHUB_USERNAME/g" README.md
    echo -e "${GREEN}✅ Updated README.md${NC}"
else
    echo -e "${RED}❌ README.md not found${NC}"
fi

# Update status.sh
if [ -f "status.sh" ]; then
    sed -i.backup "s/YOUR_USERNAME/$GITHUB_USERNAME/g" status.sh
    echo -e "${GREEN}✅ Updated status.sh${NC}"
else
    echo -e "${RED}❌ status.sh not found${NC}"
fi

echo -e "\n${GREEN}🎉 Configuration updated successfully!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Set up GitHub repository secrets:"
echo "   - DOCKERHUB_USERNAME: $DOCKERHUB_USERNAME"
echo "   - DOCKERHUB_TOKEN: (create at https://hub.docker.com/settings/security)"
echo ""
echo "2. Create DockerHub repository: $DOCKERHUB_USERNAME/workoutassistant"
echo ""
echo "3. Commit and push your changes:"
echo "   git add ."
echo "   git commit -m 'Configure usernames for deployment'"
echo "   git push origin main"
echo ""
echo "4. GitHub Actions will automatically build and push your Docker image!"

# Offer to remove backup files
echo -e "\n${YELLOW}Remove backup files? (y/N)${NC}"
read -p "> " remove_backups
if [[ $remove_backups =~ ^[Yy]$ ]]; then
    rm -f *.backup
    echo -e "${GREEN}✅ Backup files removed${NC}"
fi