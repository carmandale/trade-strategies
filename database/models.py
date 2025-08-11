"""SQLAlchemy models for trading strategy application."""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    Integer,
    DECIMAL,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from sqlalchemy.sql import func
from .config import Base
import enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
from sqlalchemy import text as sa_text
from sqlalchemy import CheckConstraint

# PostgreSQL-native types (project standard)
UUIDType = PG_UUID(as_uuid=True)
UUID_SERVER_DEFAULT = sa_text('gen_random_uuid()')
JSONType = PG_JSONB

class StrategyType(str, enum.Enum):
    """Enum for strategy types."""
    BULL_CALL = "bull_call"
    IRON_CONDOR = "iron_condor"
    BUTTERFLY = "butterfly"

class TradeStatus(str, enum.Enum):
    """Enum for trade status."""
    OPEN = "open"
    CLOSED = "closed"

class AIRecommendation(str, enum.Enum):
    """Enum for AI assessment recommendations."""
    GO = "GO"
    CAUTION = "CAUTION"
    NO_GO = "NO-GO"

class ReasoningEffort(str, enum.Enum):
    """Enum for AI reasoning effort levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# User model removed for Phase 1 - single user application
# Will be added in Phase 2 for multi-user support

class Strategy(Base):
    """Strategy configuration model."""
    __tablename__ = "strategies"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    name = Column(String(255), nullable=False)
    strategy_type = Column(String(50), nullable=False)  # 'iron_condor', 'bull_call', 'butterfly'
    symbol = Column(String(10), nullable=False, server_default='SPY')
    parameters = Column(JSONType, nullable=False)  # Flexible storage for strategy-specific params
    is_active = Column(Boolean, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships (no user for Phase 1)
    backtests = relationship("Backtest", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategy")

    # Indexes to support common queries
    __table_args__ = (
        Index('idx_strategies_type', 'strategy_type'),
        Index('idx_strategies_symbol', 'symbol'),
    )
    
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
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    strategy_id = Column(UUIDType, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    timeframe = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    parameters = Column(JSONType, nullable=False)  # Backtest-specific parameters
    results = Column(JSONType, nullable=False)  # Detailed results including metrics
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
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    strategy_id = Column(UUIDType, ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True)
    trade_date = Column(DateTime, nullable=False)
    entry_time = Column(DateTime, nullable=False)  # Using TIME type for time-only
    exit_time = Column(DateTime, nullable=True)
    symbol = Column(String(10), nullable=False, server_default='SPY')
    strategy_type = Column(String(50), nullable=False)
    strikes = Column(JSONType, nullable=False)  # Array of strike prices
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

    # Indexes for common query patterns and to satisfy schema tests
    __table_args__ = (
        Index('idx_trades_date', 'trade_date'),
        Index('idx_trades_status', 'status'),
        Index('idx_trades_strategy_type', 'strategy_type'),
    )
    
    @classmethod
    def get_open_trades(cls, db_session):
        """Get all open trades."""
        return db_session.query(cls).filter(cls.status == 'open').all()
    
    @classmethod
    def get_closed_trades(cls, db_session):
        """Get all closed trades."""
        return db_session.query(cls).filter(cls.status == 'closed').all()
    
    @classmethod
    def get_trades_by_symbol(cls, db_session, symbol: str):
        """Get trades for a specific symbol."""
        return db_session.query(cls).filter(cls.symbol == symbol).all()
    
    @classmethod
    def get_trades_by_date_range(cls, db_session, start_date: datetime, end_date: datetime):
        """Get trades within a date range."""
        return db_session.query(cls).filter(
            cls.trade_date >= start_date,
            cls.trade_date <= end_date
        ).all()
    
    @classmethod
    def calculate_total_pnl(cls, db_session) -> Optional[Decimal]:
        """Calculate total realized P&L across all trades."""
        from sqlalchemy import func
        result = db_session.query(func.sum(cls.realized_pnl)).filter(
            cls.realized_pnl.isnot(None)
        ).scalar()
        return result if result is not None else Decimal('0.00')
    
    def close_trade(self, exit_price: Decimal, exit_time: datetime = None, notes: str = None):
        """Close the trade with exit price and time."""
        self.exit_price = exit_price
        self.exit_time = exit_time or datetime.utcnow()
        self.status = 'closed'
        if notes:
            self.notes = f"{self.notes or ''}\n{notes}".strip()
        
        # Calculate realized P&L based on strategy type
        self.realized_pnl = self._calculate_pnl()
    
    def _calculate_pnl(self) -> Optional[Decimal]:
        """Calculate P&L based on strategy type and prices."""
        if not self.exit_price or not self.entry_price:
            return None
        
        price_diff = self.exit_price - self.entry_price
        
        if self.strategy_type in ['bull_call', 'bear_put']:
            # Long positions: profit when price goes up
            return price_diff * self.contracts * 100  # 100 shares per contract
        elif self.strategy_type == 'iron_condor':
            # Iron condor: profit when price stays between strikes
            # For now, use simple credit - debit calculation
            return self.credit_debit * self.contracts * 100
        else:
            # Default calculation
            return price_diff * self.contracts * 100
    
    def is_profitable(self) -> Optional[bool]:
        """Check if the trade is profitable."""
        if self.realized_pnl is None:
            return None
        return self.realized_pnl > 0
    
    def get_duration_days(self) -> Optional[int]:
        """Get trade duration in days."""
        if not self.exit_time:
            return None
        return (self.exit_time.date() - self.trade_date.date()).days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return {
            'id': str(self.id),
            'strategy_id': str(self.strategy_id) if self.strategy_id else None,
            'trade_date': self.trade_date.isoformat() if self.trade_date else None,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'symbol': self.symbol,
            'strategy_type': self.strategy_type,
            'strikes': self.strikes,
            'contracts': self.contracts,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'exit_price': float(self.exit_price) if self.exit_price else None,
            'credit_debit': float(self.credit_debit) if self.credit_debit else None,
            'realized_pnl': float(self.realized_pnl) if self.realized_pnl else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MarketDataCache(Base):
    """Market data caching model."""
    __tablename__ = "market_data_cache"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    symbol = Column(String(10), nullable=False)
    data_date = Column(DateTime, nullable=False)
    data_type = Column(String(50), nullable=False)  # 'intraday', 'daily', 'options'
    data = Column(JSONType, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Unique constraint on symbol, data_date, data_type
    __table_args__ = (
        UniqueConstraint('symbol', 'data_date', 'data_type'),
        Index('idx_market_cache_symbol_date', 'symbol', 'data_date'),
        Index('idx_market_cache_expires', 'expires_at'),
    )
    
    @classmethod
    def get_cached_data(cls, db_session, symbol: str, data_date: datetime, data_type: str):
        """Get cached data if not expired."""
        entry = db_session.query(cls).filter(
            cls.symbol == symbol,
            cls.data_date == data_date,
            cls.data_type == data_type,
            cls.expires_at > datetime.utcnow()
        ).first()
        return entry.data if entry else None
    
    @classmethod
    def cache_data(cls, db_session, symbol: str, data_date: datetime, data_type: str, 
                   data: Dict[str, Any], expires_at: datetime):
        """Cache market data with expiration."""
        # Delete existing entry if it exists
        existing = db_session.query(cls).filter(
            cls.symbol == symbol,
            cls.data_date == data_date,
            cls.data_type == data_type
        ).first()
        if existing:
            db_session.delete(existing)
        
        # Create new cache entry
        cache_entry = cls(
            symbol=symbol,
            data_date=data_date,
            data_type=data_type,
            data=data,
            expires_at=expires_at
        )
        db_session.add(cache_entry)
        return cache_entry
    
    @classmethod
    def cleanup_expired(cls, db_session) -> int:
        """Remove expired cache entries."""
        count = db_session.query(cls).filter(
            cls.expires_at <= datetime.utcnow()
        ).count()
        
        db_session.query(cls).filter(
            cls.expires_at <= datetime.utcnow()
        ).delete()
        
        return count
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return self.expires_at <= datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary."""
        return {
            'id': str(self.id),
            'symbol': self.symbol,
            'data_date': self.data_date.isoformat() if self.data_date else None,
            'data_type': self.data_type,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired()
        }