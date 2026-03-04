#!/bin/bash

cd ~/Code/workoutassistant
echo "$(date): Pulling latest images..."
docker compose pull --quiet

echo "$(date): Starting containers with latest images..."
docker compose up -d

echo "$(date): Cleaning up old images..."
docker image prune -f

echo "$(date): Update check complete"
echo "---"
