"""Pydantic models for Iron Condor strategy API responses."""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import date
from decimal import Decimal

class StrikePrices(BaseModel):
    """Strike prices for Iron Condor trades."""
    put_long: float = Field(..., description="Long put strike price")
    put_short: float = Field(..., description="Short put strike price")
    call_short: float = Field(..., description="Short call strike price") 
    call_long: float = Field(..., description="Long call strike price")

class TradeDetail(BaseModel):
    """Individual trade details for Iron Condor strategy."""
    id: str = Field(..., description="Unique trade identifier")
    entry_date: Optional[str] = Field(None, description="Trade entry date (YYYY-MM-DD)")
    expiration_date: Optional[str] = Field(None, description="Options expiration date (YYYY-MM-DD)")
    strikes: StrikePrices = Field(..., description="Strike prices for the Iron Condor")
    credit_received: float = Field(..., description="Credit received for the trade")
    pnl: float = Field(..., description="Profit/Loss for the trade")
    outcome: str = Field(..., description="Trade outcome: 'win', 'loss', or 'unknown'")

class DateRange(BaseModel):
    """Date range for strategy data."""
    start: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")

class StrategyMetadata(BaseModel):
    """Metadata for strategy timeframe."""
    timeframe: str = Field(..., description="Strategy timeframe: daily, weekly, or monthly")
    total_trades: int = Field(..., description="Total number of trades in timeframe")
    date_range: DateRange = Field(..., description="Date range of trades")

class PerformanceMetrics(BaseModel):
    """Performance metrics for strategy."""
    win_rate: float = Field(..., ge=0.0, le=1.0, description="Win rate as decimal (0.0 to 1.0)")
    total_pnl: float = Field(..., description="Total profit/loss")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown (negative value)")
    average_trade: float = Field(..., description="Average profit/loss per trade")

class TimeframeStrategy(BaseModel):
    """Strategy data for a specific timeframe."""
    metadata: StrategyMetadata = Field(..., description="Timeframe metadata")
    performance: PerformanceMetrics = Field(..., description="Performance metrics")
    trades: List[TradeDetail] = Field(..., description="List of trades")

class IronCondorStrategyResponse(BaseModel):
    """Response model for Iron Condor strategy data across all timeframes."""
    strategies: Dict[str, TimeframeStrategy] = Field(
        ..., 
        description="Strategy data by timeframe (daily, weekly, monthly)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategies": {
                    "daily": {
                        "metadata": {
                            "timeframe": "daily",
                            "total_trades": 252,
                            "date_range": {
                                "start": "2023-01-01",
                                "end": "2024-12-31"
                            }
                        },
                        "performance": {
                            "win_rate": 0.73,
                            "total_pnl": 15420.50,
                            "sharpe_ratio": 1.45,
                            "max_drawdown": -2340.75,
                            "average_trade": 61.19
                        },
                        "trades": [
                            {
                                "id": "trade-1",
                                "entry_date": "2024-01-02",
                                "expiration_date": "2024-01-02",
                                "strikes": {
                                    "put_long": 4725,
                                    "put_short": 4730,
                                    "call_short": 4780,
                                    "call_long": 4785
                                },
                                "credit_received": 1.25,
                                "pnl": 125.00,
                                "outcome": "win"
                            }
                        ]
                    }
                }
            }
        }

class TimeframeStrategyResponse(BaseModel):
    """Response model for single timeframe strategy data."""
    metadata: StrategyMetadata = Field(..., description="Timeframe metadata")
    performance: PerformanceMetrics = Field(..., description="Performance metrics")
    trades: List[TradeDetail] = Field(..., description="List of trades")

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "timeframe": "daily",
                    "total_trades": 252,
                    "date_range": {
                        "start": "2023-01-01",
                        "end": "2024-12-31"
                    }
                },
                "performance": {
                    "win_rate": 0.73,
                    "total_pnl": 15420.50,
                    "sharpe_ratio": 1.45,
                    "max_drawdown": -2340.75,
                    "average_trade": 61.19
                },
                "trades": [
                    {
                        "id": "trade-1",
                        "entry_date": "2024-01-02", 
                        "expiration_date": "2024-01-02",
                        "strikes": {
                            "put_long": 4725,
                            "put_short": 4730,
                            "call_short": 4780,
                            "call_long": 4785
                        },
                        "credit_received": 1.25,
                        "pnl": 125.00,
                        "outcome": "win"
                    }
                ]
            }
        }

class TimeframeMetrics(BaseModel):
    """Performance metrics for a single timeframe in summary."""
    win_rate: float = Field(..., ge=0.0, le=1.0, description="Win rate as decimal")
    pnl: float = Field(..., description="Total profit/loss for timeframe")

class PerformanceSummary(BaseModel):
    """Aggregated performance summary across all timeframes."""
    total_trades: int = Field(..., description="Total trades across all timeframes")
    overall_win_rate: float = Field(..., ge=0.0, le=1.0, description="Overall win rate")
    total_pnl: float = Field(..., description="Total profit/loss across all timeframes")
    best_timeframe: Optional[str] = Field(None, description="Best performing timeframe")
    worst_drawdown: float = Field(..., description="Worst drawdown across all timeframes")

class PerformanceSummaryResponse(BaseModel):
    """Response model for aggregated performance metrics."""
    summary: PerformanceSummary = Field(..., description="Aggregated performance summary")
    by_timeframe: Dict[str, TimeframeMetrics] = Field(
        ..., 
        description="Performance metrics by timeframe"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "total_trades": 756,
                    "overall_win_rate": 0.71,
                    "total_pnl": 42860.25,
                    "best_timeframe": "weekly",
                    "worst_drawdown": -4120.30
                },
                "by_timeframe": {
                    "daily": {"win_rate": 0.73, "pnl": 15420.50},
                    "weekly": {"win_rate": 0.74, "pnl": 18340.75},
                    "monthly": {"win_rate": 0.65, "pnl": 9099.00}
                }
            }
        }

# Request models for validation
class IronCondorQueryParams(BaseModel):
    """Query parameters for Iron Condor endpoints."""
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Number of trades to return")
    offset: Optional[int] = Field(0, ge=0, description="Pagination offset")

class TimeframeQueryParams(BaseModel):
    """Query parameters for timeframe-specific endpoints."""
    start_date: Optional[str] = Field(None, description="Filter start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Filter end date (YYYY-MM-DD)")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Number of trades to return")
    offset: Optional[int] = Field(0, ge=0, description="Pagination offset")