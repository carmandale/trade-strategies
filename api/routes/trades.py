"""Trade management API routes with database integration."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from database.config import get_db
from database.models import Trade, Strategy

router = APIRouter(prefix="/api/trades", tags=["trades"])

# Pydantic models for API requests/responses
class TradeCreate(BaseModel):
    """Request model for creating a new trade."""
    trade_date: date
    entry_time: Optional[str] = None
    symbol: str = Field(..., min_length=1, max_length=10)
    strategy_type: str = Field(..., min_length=1)
    strikes: List[float] = Field(..., min_items=1)
    contracts: int = Field(..., gt=0)
    entry_price: Decimal = Field(..., gt=0)
    credit_debit: Decimal
    status: str = Field(default="open", regex="^(open|closed|expired)$")
    notes: Optional[str] = None
    strategy_id: Optional[str] = None
    exit_price: Optional[Decimal] = None
    exit_time: Optional[str] = None
    realized_pnl: Optional[Decimal] = None

class TradeUpdate(BaseModel):
    """Request model for updating an existing trade."""
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    strategy_type: Optional[str] = None
    strikes: Optional[List[float]] = None
    contracts: Optional[int] = Field(None, gt=0)
    entry_price: Optional[Decimal] = Field(None, gt=0)
    credit_debit: Optional[Decimal] = None
    status: Optional[str] = Field(None, regex="^(open|closed|expired)$")
    notes: Optional[str] = None
    exit_price: Optional[Decimal] = None
    exit_time: Optional[str] = None
    realized_pnl: Optional[Decimal] = None

class TradeResponse(BaseModel):
    """Response model for trade data."""
    id: str
    trade_date: date
    entry_time: Optional[str]
    symbol: str
    strategy_type: str
    strikes: List[float]
    contracts: int
    entry_price: Decimal
    credit_debit: Decimal
    status: str
    notes: Optional[str]
    strategy_id: Optional[str]
    exit_price: Optional[Decimal]
    exit_time: Optional[str]
    realized_pnl: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TradeCloseRequest(BaseModel):
    """Request model for closing a trade."""
    exit_price: Decimal = Field(..., gt=0)
    exit_time: Optional[str] = None
    notes: Optional[str] = None

@router.post("/", response_model=TradeResponse, status_code=201)
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    """Create a new trade."""
    try:
        # Validate strategy_id if provided
        if trade.strategy_id:
            strategy = db.query(Strategy).filter(Strategy.id == trade.strategy_id).first()
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Create new trade
        db_trade = Trade(
            trade_date=trade.trade_date,
            entry_time=trade.entry_time,
            symbol=trade.symbol.upper(),
            strategy_type=trade.strategy_type,
            strikes=trade.strikes,
            contracts=trade.contracts,
            entry_price=trade.entry_price,
            credit_debit=trade.credit_debit,
            status=trade.status,
            notes=trade.notes,
            strategy_id=trade.strategy_id,
            exit_price=trade.exit_price,
            exit_time=trade.exit_time,
            realized_pnl=trade.realized_pnl
        )
        
        db.add(db_trade)
        db.commit()
        db.refresh(db_trade)
        
        return db_trade
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating trade: {str(e)}")

@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, regex="^(open|closed|expired)$"),
    symbol: Optional[str] = Query(None, min_length=1, max_length=10),
    strategy_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get trades with optional filtering."""
    try:
        query = db.query(Trade)
        
        # Apply filters
        if status:
            query = query.filter(Trade.status == status)
        if symbol:
            query = query.filter(Trade.symbol == symbol.upper())
        if strategy_type:
            query = query.filter(Trade.strategy_type == strategy_type)
        if start_date:
            query = query.filter(Trade.trade_date >= start_date)
        if end_date:
            query = query.filter(Trade.trade_date <= end_date)
        
        # Apply pagination and ordering
        trades = query.order_by(Trade.trade_date.desc(), Trade.created_at.desc()).offset(offset).limit(limit).all()
        
        return trades
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trades: {str(e)}")

@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: str, db: Session = Depends(get_db)):
    """Get a specific trade by ID."""
    try:
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        return trade
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trade: {str(e)}")

@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(trade_id: str, trade_update: TradeUpdate, db: Session = Depends(get_db)):
    """Update an existing trade."""
    try:
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        # Update only provided fields
        update_data = trade_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "symbol" and value:
                value = value.upper()
            setattr(trade, field, value)
        
        db.commit()
        db.refresh(trade)
        
        return trade
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating trade: {str(e)}")

@router.post("/{trade_id}/close", response_model=TradeResponse)
async def close_trade(trade_id: str, close_request: TradeCloseRequest, db: Session = Depends(get_db)):
    """Close a trade with exit details."""
    try:
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        if trade.status == "closed":
            raise HTTPException(status_code=400, detail="Trade is already closed")
        
        # Use the model's close_trade method
        trade.close_trade(
            exit_price=close_request.exit_price,
            exit_time=close_request.exit_time,
            notes=close_request.notes
        )
        
        db.commit()
        db.refresh(trade)
        
        return trade
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error closing trade: {str(e)}")

@router.delete("/{trade_id}")
async def delete_trade(trade_id: str, db: Session = Depends(get_db)):
    """Delete a trade."""
    try:
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        db.delete(trade)
        db.commit()
        
        return {"message": "Trade deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting trade: {str(e)}")

@router.get("/stats/summary")
async def get_trade_stats(
    db: Session = Depends(get_db),
    symbol: Optional[str] = Query(None),
    strategy_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Get trading statistics summary."""
    try:
        query = db.query(Trade)
        
        # Apply filters
        if symbol:
            query = query.filter(Trade.symbol == symbol.upper())
        if strategy_type:
            query = query.filter(Trade.strategy_type == strategy_type)
        if start_date:
            query = query.filter(Trade.trade_date >= start_date)
        if end_date:
            query = query.filter(Trade.trade_date <= end_date)
        
        trades = query.all()
        
        if not trades:
            return {
                "total_trades": 0,
                "open_trades": 0,
                "closed_trades": 0,
                "total_realized_pnl": 0,
                "win_rate": 0,
                "avg_pnl_per_trade": 0
            }
        
        # Calculate statistics
        total_trades = len(trades)
        open_trades = len([t for t in trades if t.status == "open"])
        closed_trades = len([t for t in trades if t.status == "closed"])
        
        realized_trades = [t for t in trades if t.realized_pnl is not None]
        total_realized_pnl = sum(t.realized_pnl for t in realized_trades) if realized_trades else Decimal('0')
        
        winning_trades = len([t for t in realized_trades if t.realized_pnl > 0])
        win_rate = (winning_trades / len(realized_trades) * 100) if realized_trades else 0
        
        avg_pnl_per_trade = total_realized_pnl / len(realized_trades) if realized_trades else Decimal('0')
        
        return {
            "total_trades": total_trades,
            "open_trades": open_trades,
            "closed_trades": closed_trades,
            "total_realized_pnl": float(total_realized_pnl),
            "win_rate": round(win_rate, 2),
            "avg_pnl_per_trade": float(avg_pnl_per_trade)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating trade stats: {str(e)}")