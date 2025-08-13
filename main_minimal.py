#!/usr/bin/env python3
"""
Minimal FastAPI application for Railway deployment.
This is a bulletproof version that should work on Railway.
"""
from fastapi import FastAPI
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trade Strategies API",
    description="Railway deployment test",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint - shows deployment info."""
    port = os.getenv("PORT", "unknown")
    logger.info(f"Root endpoint called - running on port {port}")
    return {
        "message": "Trade Strategies API - Railway Deployment",
        "status": "online",
        "version": "1.0.0",
        "port": port,
        "environment": "railway"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment monitoring."""
    port = os.getenv("PORT", "unknown")
    logger.info(f"Health check called - port {port}")
    return {
        "status": "healthy",
        "service": "trade-strategies-api",
        "version": "1.0.0",
        "port": port
    }

@app.get("/test")
async def test_endpoint():
    """Additional test endpoint to verify routing works."""
    return {
        "message": "Test endpoint working",
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)