"""Strategy backtesting API routes with database integration."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal
from datetime import datetime, timedelta, date
import yfinance as yf
import pandas as pd

from database.config import get_db
from database.models import Strategy, Backtest, Trade

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

class TimeFrame(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class StrategyType(str, Enum):
    IRON_CONDOR = "iron_condor"
    BULL_CALL = "bull_call"

# Database-backed strategy models
class StrategyCreate(BaseModel):
    """Request model for creating a new strategy."""
    name: str = Field(..., min_length=1, max_length=100)
    strategy_type: StrategyType
    symbol: str = Field(default="SPY", min_length=1, max_length=10)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)

class StrategyUpdate(BaseModel):
    """Request model for updating a strategy."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class StrategyResponse(BaseModel):
    """Response model for strategy data."""
    id: str
    name: str
    strategy_type: str
    symbol: str
    parameters: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BacktestRequest(BaseModel):
    symbol: str = "SPY"
    strategy_type: StrategyType
    timeframe: TimeFrame
    days_back: int = 30
    strategy_id: Optional[str] = None

class BacktestResult(BaseModel):
    symbol: str
    strategy_type: str
    timeframe: str
    total_pnl: float
    win_rate: float
    total_trades: int
    avg_pnl_per_trade: float

@router.post("/backtest", response_model=BacktestResult)
async def backtest_strategy(request: BacktestRequest):
    """Run backtest for specified strategy and timeframe."""
    try:
        # Get market data
        ticker = yf.Ticker(request.symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days_back)
        
        hist_data = ticker.history(start=start_date, end=end_date)
        
        if hist_data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.symbol}")
        
        # Quick backtesting logic based on existing patterns
        if request.strategy_type == StrategyType.IRON_CONDOR:
            result = _backtest_iron_condor(hist_data, request.timeframe)
        else:
            result = _backtest_bull_call(hist_data, request.timeframe)
        
        return BacktestResult(
            symbol=request.symbol,
            strategy_type=request.strategy_type.value,
            timeframe=request.timeframe.value,
            **result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _backtest_iron_condor(data: pd.DataFrame, timeframe: TimeFrame) -> dict:
    """Basic Iron Condor backtesting logic."""
    # Simplified logic based on existing scripts
    strikes = _get_strikes_for_timeframe(timeframe)
    
    total_trades = len(data) - 1
    wins = 0
    total_pnl = 0.0
    
    for i in range(len(data) - 1):
        current_price = data.iloc[i]['Close']
        next_price = data.iloc[i + 1]['Close']
        
        # Calculate strikes based on current price
        put_strike_short = current_price * strikes['put_short']
        call_strike_short = current_price * strikes['call_short']
        
        # Determine if trade was profitable (price stayed between strikes)
        if put_strike_short <= next_price <= call_strike_short:
            wins += 1
            pnl = strikes['credit']
        else:
            pnl = -strikes['max_loss']
        
        total_pnl += pnl
    
    win_rate = wins / total_trades if total_trades > 0 else 0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate * 100, 2),
        "total_trades": total_trades,
        "avg_pnl_per_trade": round(avg_pnl, 2)
    }

def _backtest_bull_call(data: pd.DataFrame, timeframe: TimeFrame) -> dict:
    """Basic Bull Call backtesting logic."""
    # Simplified bull call logic
    total_trades = len(data) - 1
    wins = 0
    total_pnl = 0.0
    
    for i in range(len(data) - 1):
        current_price = data.iloc[i]['Close']
        next_price = data.iloc[i + 1]['Close']
        
        # Bull call profits when price goes up
        if next_price > current_price:
            wins += 1
            pnl = 50  # Simplified profit
        else:
            pnl = -25  # Simplified loss
        
        total_pnl += pnl
    
    win_rate = wins / total_trades if total_trades > 0 else 0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate * 100, 2),
        "total_trades": total_trades,
        "avg_pnl_per_trade": round(avg_pnl, 2)
    }

def _get_strikes_for_timeframe(timeframe: TimeFrame) -> dict:
    """Get strike configuration based on timeframe."""
    if timeframe == TimeFrame.DAILY:
        return {
            "put_short": 0.975,
            "call_short": 1.02,
            "credit": 25,
            "max_loss": 475
        }
    elif timeframe == TimeFrame.WEEKLY:
        return {
            "put_short": 0.965,
            "call_short": 1.03,
            "credit": 75,
            "max_loss": 425
        }
    else:  # MONTHLY
        return {
            "put_short": 0.94,
            "call_short": 1.05,
            "credit": 150,
            "max_loss": 350
        }