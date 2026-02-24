#!/bin/bash
set -e

# Source environment variables from secrets file if it exists
if [ -f "/app/.secrets/.variables" ]; then
    echo "Loading environment variables from .secrets/.variables"
    set -a  # automatically export all variables
    source /app/.secrets/.variables
    set +a
else
    echo "Warning: No .secrets/.variables file found. Make sure to mount your secrets."
fi

# Create models directory if it doesn't exist
mkdir -p /app/models

# Check if models exist, download if missing
echo "Checking for required models..."

# Phi-3-mini 4k model
if [ ! -f "/app/models/Phi-3-mini-4k-instruct-q4.gguf" ]; then
    echo "Downloading Phi-3-mini 4k model..."
    wget -O /app/models/Phi-3-mini-4k-instruct-q4.gguf \
        "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
fi

# Phi-3-mini 128k model (optional, for longer context)
if [ ! -f "/app/models/Phi-3-mini-128k-instruct-ft.i1-Q4_K_M.gguf" ]; then
    echo "Downloading Phi-3-mini 128k model..."
    wget -O /app/models/Phi-3-mini-128k-instruct-ft.i1-Q4_K_M.gguf \
        "https://huggingface.co/mradermacher/Phi-3-mini-128k-instruct-ft-i1-GGUF/resolve/main/Phi-3-mini-128k-instruct-ft.i1-Q4_K_M.gguf"
fi

# Create SQLite database tables if database doesn't exist
DB_PATH="/app/data/database.db"
if [ ! -f "$DB_PATH" ]; then
    echo "Initializing database..."
    PYTHONPATH=/app/src python /app/src/scripts/create_tables.py
fi

# Function to handle graceful shutdown
cleanup() {
    echo "Received shutdown signal, gracefully stopping..."
    if [ ! -z "$MAIN_PID" ]; then
        kill -TERM "$MAIN_PID" 2>/dev/null || true
        wait "$MAIN_PID" 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT SIGQUIT

echo "Starting workout assistant..."

# Start the main application with proper logging
PYTHONPATH=/app/src python /app/src/main.py > /app/logs/output.log 2>&1 &
MAIN_PID=$!

# Wait for the main process to finish
wait "$MAIN_PID"