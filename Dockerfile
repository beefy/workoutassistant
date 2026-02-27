# Multi-stage build to minimize image size
FROM python:3.11-slim AS builder

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    ffmpeg \
    build-essential \
    gcc \
    g++ \
    cmake \
    libffi-dev \
    libssl-dev \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust for packages that need it (like cryptography)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash workoutassistant

# Set working directory
WORKDIR /app

# Set environment variables for building packages
ENV CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS"
ENV FORCE_CMAKE=1

# Upgrade pip to latest version
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies with verbose output for debugging
RUN pip install --no-cache-dir --verbose -r requirements.txt

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