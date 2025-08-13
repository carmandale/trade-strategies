# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN uv pip install --system -r requirements.txt

# Copy all application code
COPY api/ ./api/
COPY database/ ./database/
COPY services/ ./services/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY *.py ./

# Debug: List files to verify copy worked
RUN echo "=== Files copied to container ===" && find . -type f -name "*.py" | head -20

# Debug: Verify main module exists
RUN echo "=== Testing import ===" && python -c "import api.main; print('✅ api.main imported successfully')"

# Create a default PORT if Railway doesn't set it
ENV PORT=8000

# Run the application (Railway sets PORT env var)
CMD ["sh", "-c", "echo 'Starting with PORT=' && echo $PORT && python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT"]