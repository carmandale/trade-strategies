"""SQLAlchemy models for trading strategy application."""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import Column, String, Integer, DECIMAL, Boolean, DateTime, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .config import Base
import enum

class StrategyType(str, enum.Enum):
    """Enum for strategy types."""
    BULL_CALL = "bull_call"
    IRON_CONDOR = "iron_condor"
    BUTTERFLY = "butterfly"

class TradeStatus(str, enum.Enum):
    """Enum for trade status."""
    OPEN = "open"
    CLOSED = "closed"

# User model removed for Phase 1 - single user application
# Will be added in Phase 2 for multi-user support

class Strategy(Base):
    """Strategy configuration model."""
    __tablename__ = "strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    strategy_type = Column(String(50), nullable=False)  # 'iron_condor', 'bull_call', 'butterfly'
    symbol = Column(String(10), nullable=False, server_default='SPY')
    parameters = Column(JSONB, nullable=False)  # Flexible storage for strategy-specific params
    is_active = Column(Boolean, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships (no user for Phase 1)
    backtests = relationship("Backtest", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategy")
    
    @classmethod
    def get_active_strategies(cls, db_session):
        """Get all active strategies."""
        return db_session.query(cls).filter(cls.is_active == True).all()
    
    @classmethod
    def get_by_type(cls, db_session, strategy_type: str):
        """Get strategies by type."""
        return db_session.query(cls).filter(cls.strategy_type == strategy_type).all()
    
    def get_recent_backtests(self, db_session, limit: int = 5):
        """Get recent backtests for this strategy."""
        return db_session.query(Backtest).filter(
            Backtest.strategy_id == self.id
        ).order_by(Backtest.created_at.desc()).limit(limit).all()
    
    def get_trades_count(self, db_session) -> int:
        """Get total number of trades for this strategy."""
        return db_session.query(Trade).filter(Trade.strategy_id == self.id).count()
    
    def calculate_total_pnl(self, db_session) -> Optional[Decimal]:
        """Calculate total realized P&L for this strategy."""
        from sqlalchemy import func
        result = db_session.query(func.sum(Trade.realized_pnl)).filter(
            Trade.strategy_id == self.id,
            Trade.realized_pnl.isnot(None)
        ).scalar()
        return result if result is not None else Decimal('0.00')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy to dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'strategy_type': self.strategy_type,
            'symbol': self.symbol,
            'parameters': self.parameters,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Backtest(Base):
    """Backtest result model."""
    __tablename__ = "backtests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    timeframe = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    parameters = Column(JSONB, nullable=False)  # Backtest-specific parameters
    results = Column(JSONB, nullable=False)  # Detailed results including metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")
    
    @classmethod
    def get_by_timeframe(cls, db_session, timeframe: str):
        """Get backtests by timeframe."""
        return db_session.query(cls).filter(cls.timeframe == timeframe).all()
    
    @classmethod
    def get_recent_backtests(cls, db_session, limit: int = 10):
        """Get most recent backtests across all strategies."""
        return db_session.query(cls).order_by(cls.created_at.desc()).limit(limit).all()
    
    def get_win_rate(self) -> Optional[float]:
        """Extract win rate from results."""
        return self.results.get('win_rate') if self.results else None
    
    def get_total_pnl(self) -> Optional[float]:
        """Extract total P&L from results."""
        return self.results.get('total_pnl') if self.results else None
    
    def get_sharpe_ratio(self) -> Optional[float]:
        """Extract Sharpe ratio from results."""
        return self.results.get('sharpe_ratio') if self.results else None
    
    def get_trades_count(self) -> Optional[int]:
        """Extract trades count from results."""
        return self.results.get('trades_count') if self.results else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert backtest to dictionary."""
        return {
            'id': str(self.id),
            'strategy_id': str(self.strategy_id),
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'timeframe': self.timeframe,
            'parameters': self.parameters,
            'results': self.results,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Trade(Base):
    """Actual trade execution model."""
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True)
    trade_date = Column(DateTime, nullable=False)
    entry_time = Column(DateTime, nullable=False)  # Using TIME type for time-only
    exit_time = Column(DateTime, nullable=True)
    symbol = Column(String(10), nullable=False, server_default='SPY')
    strategy_type = Column(String(50), nullable=False)
    strikes = Column(JSONB, nullable=False)  # Array of strike prices
    contracts = Column(Integer, nullable=False)
    entry_price = Column(DECIMAL(10, 2), nullable=False)
    exit_price = Column(DECIMAL(10, 2), nullable=True)
    credit_debit = Column(DECIMAL(10, 2), nullable=False)
    realized_pnl = Column(DECIMAL(10, 2), nullable=True)
    status = Column(String(20), server_default='open')  # 'open', 'closed'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships (no user for Phase 1)
    strategy = relationship("Strategy", back_populates="trades")

class MarketDataCache(Base):
    """Market data caching model."""
    __tablename__ = "market_data_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), nullable=False)
    data_date = Column(DateTime, nullable=False)
    data_type = Column(String(50), nullable=False)  # 'intraday', 'daily', 'options'
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Unique constraint on symbol, data_date, data_type
    __table_args__ = (
        UniqueConstraint('symbol', 'data_date', 'data_type'),
    )