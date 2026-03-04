#!/bin/bash

cd ~/Code/workoutassistant

echo "$(date): Checking for image updates..."
# Capture current image IDs with more detail
BEFORE_IMAGES=$(docker compose images --format "{{.Repository}}:{{.Tag}}@{{.ID}}")

# Force pull latest images (bypasses cache)
echo "$(date): Pulling latest images..."
docker compose pull --quiet

# Check if any images changed
AFTER_IMAGES=$(docker compose images --format "{{.Repository}}:{{.Tag}}@{{.ID}}")

if [ "$BEFORE_IMAGES" != "$AFTER_IMAGES" ]; then
    echo "$(date): New images detected, restarting containers..."
    echo "Previous images: $BEFORE_IMAGES"
    echo "New images: $AFTER_IMAGES"
    docker compose up -d
    echo "$(date): Cleaning up old images..."
    docker image prune -f
else
    echo "$(date): No updates found, containers unchanged"
    echo "Current images: $BEFORE_IMAGES"
fi

echo "$(date): Update check complete"
echo "---"
