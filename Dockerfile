FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for psutil (required for ARM builds)
# These will be removed after installation to keep the image small
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to reduce image size
RUN apt-get purge -y --auto-remove gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY ha_host_monitor ./ha_host_monitor

# Create config directory
RUN mkdir -p /app/config

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the application
CMD ["python", "-m", "ha_host_monitor.main"]
