# Multi-stage build to minimize image size
FROM python:3.11-slim as builder

# Install system dependencies 
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash workoutassistant

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    sqlite3 \
    wget \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash workoutassistant

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/models /app/data /app/src/generated_images logs && \
    chown -R workoutassistant:workoutassistant /app

# Copy application source code
COPY --chown=workoutassistant:workoutassistant src/ ./src/
COPY --chown=workoutassistant:workoutassistant LICENSE README.md ./

# Switch to non-root user
USER workoutassistant

# Create volume mount points for data persistence and secret management
VOLUME ["/app/data", "/app/models", "/app/src/generated_images", "/app/.secrets"]

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import psutil; import os; exit(0 if any('main.py' in cmd for cmd in [' '.join(p.cmdline()) for p in psutil.process_iter()]) else 1)" || exit 1

# Expose port for health checks (if needed in the future)
EXPOSE 8080

# Environment variables for proper operation
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Setup script to handle model downloads and graceful startup
COPY --chown=workoutassistant:workoutassistant docker-entrypoint.sh /app/
RUN chmod +x docker-entrypoint.sh

# Entry point
ENTRYPOINT ["./docker-entrypoint.sh"]