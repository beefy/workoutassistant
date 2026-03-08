# syntax=docker/dockerfile:1.4
# Multi-stage build to minimize image size
FROM --platform=$TARGETPLATFORM python:3.11-slim AS builder
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install system dependencies and build tools in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    cmake \
    libffi-dev \
    libssl-dev \
    libopenblas-dev \
    liblapack-dev \
    libsodium-dev \
    libopus-dev \
    pkg-config \
    curl \
    git \
    chromium \
    chromium-driver \
    wget \
    ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Rust for crypto packages
RUN --mount=type=cache,target=/root/.cargo/registry \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Set environment variables for building packages
# Configure CMAKE for target architecture
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        echo "Configuring for ARM64"; \
        export CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS -DCMAKE_BUILD_TYPE=Release -DCMAKE_SYSTEM_PROCESSOR=aarch64 -DLLAMA_NATIVE=OFF"; \
    else \
        echo "Configuring for AMD64"; \
        export CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS -DCMAKE_BUILD_TYPE=Release"; \
    fi && \
    echo $CMAKE_ARGS > /tmp/cmake_args
ENV FORCE_CMAKE=1
ENV LLAMA_NO_METAL=1
ENV LLAMA_NO_CUDA=1

# Copy requirements and install Python packages
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cargo/registry \
    export CMAKE_ARGS=$(cat /tmp/cmake_args) && \
    pip install --upgrade pip setuptools wheel && \
    # Simple installation - let pip/cmake auto-detect everything
    pip install -r requirements.txt

# Production stage
FROM --platform=$TARGETPLATFORM python:3.11-slim AS production
ARG TARGETPLATFORM

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    sqlite3 \
    wget \
    ffmpeg \
    libopenblas0 \
    libsodium23 \
    libopus0 \
    libffi8 \
    avahi-daemon \
    && rm -rf /var/lib/apt/lists/* \
    && systemctl enable avahi-daemon

# Create non-root user
RUN useradd --create-home --shell /bin/bash workoutassistant

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory and create directories
WORKDIR /app
RUN mkdir -p models data src/generated_images logs && \
    chown -R workoutassistant:workoutassistant /app

# Copy application files
COPY --chown=workoutassistant:workoutassistant src/ ./src/
COPY --chown=workoutassistant:workoutassistant LICENSE README.md docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Switch to non-root user
USER workoutassistant

# Create volume mount points
VOLUME ["/app/data", "/app/models", "/app/src/generated_images", "/app/.secrets"]

# Environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import psutil; exit(0 if any('main.py' in cmd for cmd in [' '.join(p.cmdline()) for p in psutil.process_iter()]) else 1)" || exit 1

EXPOSE 8080
ENTRYPOINT ["./docker-entrypoint.sh"]