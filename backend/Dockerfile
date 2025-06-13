FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads processed exports cache

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Add logging configuration
ENV GUNICORN_CMD_ARGS="--access-logfile=- --error-logfile=- --log-level=info"
ENV UVICORN_LOGGING_CONFIG=None

# Cloud Run uses port 8080
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:$PORT/api/health || exit 1

# Use gunicorn for production with explicit host and port binding
CMD exec gunicorn main:app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 0 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output
