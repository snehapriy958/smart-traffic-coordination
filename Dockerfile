# ==============================================================================
# Smart Traffic Coordination System — Backend & Microscopic Simulation Dockerfile
# Multi-stage container with Ubuntu LTS, Eclipse SUMO, Python 3.11/3.12, and PyTorch
# ==============================================================================

FROM ubuntu:22.04 AS runtime

# Prevent interactive prompts during apt installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kolkata

# Install system utilities, Python 3, Eclipse SUMO and TraCI
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    dumb-init \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    && mkdir -p /etc/apt/trusted.gpg.d \
    && curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x7604B28616B7E70EC0E6D840C32412BB1ADB414B" | gpg --dearmor -o /etc/apt/trusted.gpg.d/sumo.gpg \
    && echo "deb [signed-by=/etc/apt/trusted.gpg.d/sumo.gpg] https://ppa.launchpadcontent.net/sumo/stable/ubuntu jammy main" > /etc/apt/sources.list.d/sumo.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    sumo \
    sumo-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure SUMO environment variables
ENV SUMO_HOME=/usr/share/sumo
ENV PYTHONPATH="${SUMO_HOME}/tools:/app:${PYTHONPATH}"
ENV PATH="${SUMO_HOME}/bin:${PATH}"

# Configure application runtime
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=false
ENV STRUCTURED_LOGGING=true
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python production dependencies
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip3 install --no-cache-dir -r requirements.txt

# Create application user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app/data /app/outputs && \
    chown -R appuser:appuser /app

# Copy application source code and assets
COPY --chown=appuser:appuser backend /app/backend
COPY --chown=appuser:appuser common /app/common
COPY --chown=appuser:appuser traffic_service /app/traffic_service
COPY --chown=appuser:appuser sumo /app/sumo
COPY --chown=appuser:appuser checkpoints /app/checkpoints
COPY --chown=appuser:appuser outputs /app/outputs
COPY --chown=appuser:appuser scripts /app/scripts
COPY --chown=appuser:appuser .env.example /app/.env.example

# Drop privileges to non-root user
USER appuser

EXPOSE 8000

# Health check probing the FastAPI /api/health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Process supervision with dumb-init for graceful SIGINT/SIGTERM handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
