"""Backtest management API routes with database integration."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal
from datetime import datetime, date
import json

from database.config import get_db
from database.models import Backtest, Strategy

router = APIRouter(prefix="/api/backtests", tags=["backtests"])

class TimeFrame(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class BacktestCreate(BaseModel):
    """Request model for creating a new backtest."""
    strategy_id: str = Field(..., min_length=1)
    start_date: date
    end_date: date
    timeframe: TimeFrame
    parameters: Dict[str, Any] = Field(default_factory=dict)

class BacktestUpdate(BaseModel):
    """Request model for updating a backtest."""
    parameters: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None

class BacktestResponse(BaseModel):
    """Response model for backtest data."""
    id: str
    strategy_id: str
    start_date: date
    end_date: date
    timeframe: str
    parameters: Dict[str, Any]
    results: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=BacktestResponse, status_code=201)
async def create_backtest(backtest: BacktestCreate, db: Session = Depends(get_db)):
    """Create a new backtest."""
    try:
        # Validate strategy exists
        strategy = db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Create new backtest
        db_backtest = Backtest(
            strategy_id=backtest.strategy_id,
            start_date=backtest.start_date,
            end_date=backtest.end_date,
            timeframe=backtest.timeframe.value,
            parameters=backtest.parameters
        )
        
        db.add(db_backtest)
        db.commit()
        db.refresh(db_backtest)
        
        return db_backtest
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating backtest: {str(e)}")

@router.get("/", response_model=List[BacktestResponse])
async def get_backtests(
    db: Session = Depends(get_db),
    strategy_id: Optional[str] = Query(None),
    timeframe: Optional[TimeFrame] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get backtests with optional filtering."""
    try:
        query = db.query(Backtest)
        
        # Apply filters
        if strategy_id:
            query = query.filter(Backtest.strategy_id == strategy_id)
        if timeframe:
            query = query.filter(Backtest.timeframe == timeframe.value)
        if start_date:
            query = query.filter(Backtest.start_date >= start_date)
        if end_date:
            query = query.filter(Backtest.end_date <= end_date)
        
        # Apply pagination and ordering
        backtests = query.order_by(Backtest.created_at.desc()).offset(offset).limit(limit).all()
        
        return backtests
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving backtests: {str(e)}")

@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(backtest_id: str, db: Session = Depends(get_db)):
    """Get a specific backtest by ID."""
    try:
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not backtest:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        return backtest
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving backtest: {str(e)}")

@router.put("/{backtest_id}", response_model=BacktestResponse)
async def update_backtest(backtest_id: str, backtest_update: BacktestUpdate, db: Session = Depends(get_db)):
    """Update an existing backtest."""
    try:
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not backtest:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        # Update only provided fields
        update_data = backtest_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(backtest, field, value)
        
        db.commit()
        db.refresh(backtest)
        
        return backtest
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating backtest: {str(e)}")

@router.delete("/{backtest_id}")
async def delete_backtest(backtest_id: str, db: Session = Depends(get_db)):
    """Delete a backtest."""
    try:
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not backtest:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        db.delete(backtest)
        db.commit()
        
        return {"message": "Backtest deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting backtest: {str(e)}")

@router.post("/{backtest_id}/run")
async def run_backtest(backtest_id: str, db: Session = Depends(get_db)):
    """Run a backtest and store results."""
    try:
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not backtest:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        strategy = db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # For now, create mock results
        # In the future, this would integrate with the actual backtesting engine
        mock_results = {
            "total_trades": 25,
            "winning_trades": 17,
            "losing_trades": 8,
            "win_rate": 68.0,
            "total_pnl": 1250.50,
            "avg_pnl_per_trade": 50.02,
            "max_drawdown": -125.75,
            "sharpe_ratio": 1.45,
            "start_date": backtest.start_date.isoformat(),
            "end_date": backtest.end_date.isoformat(),
            "timeframe": backtest.timeframe,
            "strategy_type": strategy.strategy_type,
            "parameters_used": backtest.parameters,
            "run_timestamp": datetime.utcnow().isoformat()
        }
        
        # Update backtest with results
        backtest.results = mock_results
        db.commit()
        db.refresh(backtest)
        
        return {
            "message": "Backtest completed successfully",
            "backtest_id": backtest_id,
            "results": mock_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")

@router.get("/strategy/{strategy_id}", response_model=List[BacktestResponse])
async def get_strategy_backtests(
    strategy_id: str, 
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all backtests for a specific strategy."""
    try:
        # Verify strategy exists
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        backtests = db.query(Backtest).filter(
            Backtest.strategy_id == strategy_id
        ).order_by(Backtest.created_at.desc()).offset(offset).limit(limit).all()
        
        return backtests
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving strategy backtests: {str(e)}")

@router.get("/stats/summary")
async def get_backtest_stats(
    db: Session = Depends(get_db),
    strategy_id: Optional[str] = Query(None),
    timeframe: Optional[TimeFrame] = Query(None)
):
    """Get backtest statistics summary."""
    try:
        query = db.query(Backtest)
        
        # Apply filters
        if strategy_id:
            query = query.filter(Backtest.strategy_id == strategy_id)
        if timeframe:
            query = query.filter(Backtest.timeframe == timeframe.value)
        
        backtests = query.all()
        
        if not backtests:
            return {
                "total_backtests": 0,
                "completed_backtests": 0,
                "avg_win_rate": 0,
                "avg_total_pnl": 0,
                "best_performing_strategy": None
            }
        
        # Calculate statistics
        total_backtests = len(backtests)
        completed_backtests = len([b for b in backtests if b.results])
        
        if completed_backtests > 0:
            completed = [b for b in backtests if b.results]
            win_rates = [b.results.get("win_rate", 0) for b in completed if b.results.get("win_rate")]
            total_pnls = [b.results.get("total_pnl", 0) for b in completed if b.results.get("total_pnl")]
            
            avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0
            avg_total_pnl = sum(total_pnls) / len(total_pnls) if total_pnls else 0
            
            # Find best performing backtest
            best_backtest = max(completed, key=lambda b: b.results.get("total_pnl", 0)) if completed else None
            best_performing_strategy = best_backtest.strategy_id if best_backtest else None
        else:
            avg_win_rate = 0
            avg_total_pnl = 0
            best_performing_strategy = None
        
        return {
            "total_backtests": total_backtests,
            "completed_backtests": completed_backtests,
            "avg_win_rate": round(avg_win_rate, 2),
            "avg_total_pnl": round(avg_total_pnl, 2),
            "best_performing_strategy": best_performing_strategy
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating backtest stats: {str(e)}")