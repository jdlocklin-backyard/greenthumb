# Agent Service Dockerfile
# Autonomous worker for scheduled tasks and data collection
#
# Build: docker build -t greenthumb-agent .
# Run: docker run -d --name agent greenthumb-agent

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# curl: health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 agentuser && \
    chown -R agentuser:agentuser /app

USER agentuser

# Health check
# Verify the agent process is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the agent
CMD ["python", "worker.py"]
