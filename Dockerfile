# Simple test Dockerfile for Railway debugging  
FROM python:3.11-slim

WORKDIR /app

# Install minimal dependencies
RUN pip install fastapi uvicorn[standard]

# Copy only the test app
COPY simple_test_app.py .

# Set port
ENV PORT=8000

# Run the simple app
CMD ["python", "simple_test_app.py"]