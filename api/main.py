"""FastAPI application for trading strategy backtesting."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import strategies
from api.exceptions import setup_exception_handlers
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

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

# Import and include trades router
from api.routes import trades
app.include_router(trades.router)

# Import and include backtests router
from api.routes import backtests
app.include_router(backtests.router)

# Import and include Iron Condor strategy router
from api.routes import iron_condor
from api.routes import market_data
from api.routes import trade_tickets
app.include_router(iron_condor.router)
app.include_router(market_data.router)
app.include_router(trade_tickets.router)

# Set up comprehensive error handling
setup_exception_handlers(app)

@app.get("/")
async def root():
    return {"message": "Trade Strategies API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}