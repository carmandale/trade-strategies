"""FastAPI application for trading strategy backtesting."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import strategies
import os

app = FastAPI(
    title="Trade Strategies API",
    description="Real-time trading strategy generator and backtesting API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(strategies.router)

@app.get("/")
async def root():
    return {"message": "Trade Strategies API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}