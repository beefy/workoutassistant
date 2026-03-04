#!/bin/bash

cd ~/Code/workoutassistant

echo "$(date): Checking for image updates..."
# Capture current image IDs
docker compose config --quiet
BEFORE_IMAGES=$(docker compose images --quiet)

# Pull latest images
docker compose pull --quiet

# Check if any images changed
AFTER_IMAGES=$(docker compose images --quiet)

if [ "$BEFORE_IMAGES" != "$AFTER_IMAGES" ]; then
    echo "$(date): New images detected, restarting containers..."
    docker compose up -d
    echo "$(date): Cleaning up old images..."
    docker image prune -f
else
    echo "$(date): No updates found, containers unchanged"
fi

echo "$(date): Update check complete"
echo "---"
