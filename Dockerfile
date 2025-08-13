# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and Python packages in one layer
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install fastapi uvicorn[standard]

# Copy only essential files first
COPY requirements.txt .

# Install remaining dependencies
RUN pip install -r requirements.txt

# Copy the entire application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start command - simple and direct
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT