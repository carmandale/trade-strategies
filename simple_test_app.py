#!/usr/bin/env python3
"""
Minimal test application for Railway deployment debugging.
This helps isolate Railway deployment issues by testing with the simplest possible FastAPI app.
"""
from fastapi import FastAPI
import os

app = FastAPI(title="Railway Test App")

@app.get("/")
async def root():
    return {
        "message": "Railway deployment test successful!",
        "port": os.getenv("PORT", "unknown"),
        "app": "simple_test_app"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "railway-test",
        "port": os.getenv("PORT", "unknown")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)