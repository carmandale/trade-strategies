"""SQLAlchemy models for trading strategy application."""
import uuid
from datetime import datetime, timezone, timedelta
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
    data_source = Column(String(20), server_default='estimated')  # 'estimated', 'ib_realtime', 'ib_historical'
    ib_snapshot = Column(JSONType, nullable=True)  # IB market data snapshot at strategy creation
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
            'data_source': self.data_source,
            'ib_snapshot': self.ib_snapshot,
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
        self.exit_time = exit_time or datetime.now(timezone.utc)
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
            cls.expires_at > datetime.now(timezone.utc)
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
            cls.expires_at <= datetime.now(timezone.utc)
        ).count()
        
        db_session.query(cls).filter(
            cls.expires_at <= datetime.now(timezone.utc)
        ).delete()
        
        return count
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return self.expires_at <= datetime.now(timezone.utc)
    
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


class AIAssessment(Base):
    """AI assessment for trading strategies."""
    __tablename__ = "ai_assessments"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    assessment_id = Column(String(100), unique=True, nullable=False)  # Unique identifier for assessment
    strategy_hash = Column(String(200), nullable=False)  # Hash of strategy parameters for caching
    strategy_type = Column(String(50), nullable=False)
    symbol = Column(String(10), nullable=False)
    strategy_params = Column(JSONType, nullable=False)  # Complete strategy parameters
    recommendation = Column(Enum(AIRecommendation), nullable=False)
    confidence = Column(Integer, nullable=False)  # 0-100
    reasoning = Column(JSONType, nullable=False)  # Structured reasoning with supporting/risk factors
    market_conditions = Column(JSONType, nullable=False)  # Market snapshot at assessment time
    model_used = Column(String(50), server_default='gpt-5')
    token_usage = Column(Integer, nullable=True)
    cost_usd = Column(DECIMAL(10, 4), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Assessment expiration time
    
    # Constraints
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 100', name='check_confidence_range'),
        Index('idx_ai_assessments_strategy_hash', 'strategy_hash'),
        Index('idx_ai_assessments_expires', 'expires_at'),
    )
    
    @classmethod
    def get_cached_assessment(cls, db_session, strategy_hash: str):
        """Get cached assessment if not expired."""
        assessment = db_session.query(cls).filter(
            cls.strategy_hash == strategy_hash,
            cls.expires_at > datetime.now(timezone.utc)
        ).first()
        return assessment
    
    def is_expired(self) -> bool:
        """Check if assessment is expired."""
        return self.expires_at <= datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to dictionary."""
        # Extract market_regime from market_conditions if it exists
        market_regime = ''
        if self.market_conditions and isinstance(self.market_conditions, dict):
            market_regime = self.market_conditions.get('market_regime', '')
        
        return {
            'id': str(self.id),
            'assessment_id': self.assessment_id,
            'strategy_hash': self.strategy_hash,
            'strategy_type': self.strategy_type,
            'symbol': self.symbol,
            'strategy_params': self.strategy_params,
            'recommendation': self.recommendation.value if self.recommendation else None,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'market_regime': market_regime,  # Add the missing field
            'market_conditions': self.market_conditions,
            'model_used': self.model_used,
            'token_usage': self.token_usage,
            'cost_usd': float(self.cost_usd) if self.cost_usd else None,
            'processing_time_ms': self.processing_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired()
        }


class AISettings(Base):
    """AI settings configuration."""
    __tablename__ = "ai_settings"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    user_id = Column(Integer, nullable=True)  # NULL for single-user app, ready for Phase 2
    model = Column(String(50), server_default='gpt-5')
    temperature = Column(DECIMAL(3, 2), server_default='0.30')  # 0.00 to 1.00
    max_tokens = Column(Integer, server_default='800')
    cache_ttl = Column(Integer, server_default='300')  # 5 minutes default
    reasoning_effort = Column(Enum(ReasoningEffort), default=ReasoningEffort.MEDIUM)
    auto_assess = Column(Boolean, server_default='false')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('temperature >= 0 AND temperature <= 1', name='check_temperature_range'),
        CheckConstraint('max_tokens > 0 AND max_tokens <= 4096', name='check_max_tokens_range'),
        CheckConstraint('cache_ttl >= 0 AND cache_ttl <= 3600', name='check_cache_ttl_range'),
    )
    
    @classmethod
    def get_settings(cls, db_session, user_id: Optional[int] = None):
        """Get settings for user or default settings."""
        settings = db_session.query(cls).filter(cls.user_id == user_id).first()
        if not settings:
            # Create default settings if none exist
            settings = cls(user_id=user_id)
            db_session.add(settings)
            db_session.commit()
        return settings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'model': self.model,
            'temperature': float(self.temperature) if self.temperature else None,
            'max_tokens': self.max_tokens,
            'cache_ttl': self.cache_ttl,
            'reasoning_effort': self.reasoning_effort.value if self.reasoning_effort else None,
            'auto_assess': self.auto_assess,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AIUsageLog(Base):
    """AI usage tracking for monitoring and cost control."""
    __tablename__ = "ai_usage_log"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    assessment_id = Column(String(100), nullable=True)  # Reference to assessment
    operation = Column(String(50), nullable=False)  # 'assess_strategy', 'market_analysis', etc.
    model = Column(String(50), nullable=False)
    tokens_input = Column(Integer, nullable=False)
    tokens_output = Column(Integer, nullable=False)
    tokens_total = Column(Integer, nullable=False)
    cost_usd = Column(DECIMAL(10, 4), nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_ai_usage_log_created', 'created_at'),
        Index('idx_ai_usage_log_assessment', 'assessment_id'),
    )
    
    @classmethod
    def get_usage_stats(cls, db_session, start_date: datetime = None, end_date: datetime = None):
        """Get usage statistics for a date range."""
        query = db_session.query(
            func.count(cls.id).label('total_requests'),
            func.sum(cls.tokens_total).label('total_tokens'),
            func.sum(cls.cost_usd).label('total_cost'),
            func.avg(cls.response_time_ms).label('avg_response_time'),
            func.sum(func.cast(cls.success, Integer)).label('successful_requests')
        )
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        result = query.first()
        return {
            'total_requests': result.total_requests or 0,
            'total_tokens': result.total_tokens or 0,
            'total_cost': float(result.total_cost) if result.total_cost else 0.0,
            'avg_response_time': float(result.avg_response_time) if result.avg_response_time else 0.0,
            'successful_requests': result.successful_requests or 0,
            'success_rate': (result.successful_requests / result.total_requests * 100) if result.total_requests else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert usage log to dictionary."""
        return {
            'id': str(self.id),
            'assessment_id': self.assessment_id,
            'operation': self.operation,
            'model': self.model,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'tokens_total': self.tokens_total,
            'cost_usd': float(self.cost_usd) if self.cost_usd else None,
            'response_time_ms': self.response_time_ms,
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MarketDataSnapshot(Base):
    """Market data snapshot for AI assessment context."""
    __tablename__ = "market_data_snapshots"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    snapshot_id = Column(String(100), unique=True, nullable=False)
    spx_price = Column(DECIMAL(10, 2), nullable=False)
    spx_change = Column(DECIMAL(10, 2), nullable=False)
    spx_change_percent = Column(DECIMAL(5, 2), nullable=False)
    spy_price = Column(DECIMAL(10, 2), nullable=True)  # Allow null for existing records
    spy_change = Column(DECIMAL(10, 2), nullable=True)  # Allow null for existing records
    spy_change_percent = Column(DECIMAL(5, 2), nullable=True)  # Allow null for existing records
    vix_level = Column(DECIMAL(10, 2), nullable=False)
    vix_change = Column(DECIMAL(10, 2), nullable=False)
    volume = Column(Integer, nullable=False)
    volume_vs_avg = Column(DECIMAL(5, 2), nullable=False)  # Ratio vs average volume
    technical_indicators = Column(JSONType, nullable=False)  # RSI, moving averages, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_market_snapshots_expires', 'expires_at'),
    )
    
    @classmethod
    def get_latest_snapshot(cls, db_session):
        """Get the most recent valid market snapshot."""
        snapshot = db_session.query(cls).filter(
            cls.expires_at > datetime.now(timezone.utc)
        ).order_by(cls.created_at.desc()).first()
        return snapshot
    
    def is_expired(self) -> bool:
        """Check if snapshot is expired."""
        return self.expires_at <= datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            'id': str(self.id),
            'snapshot_id': self.snapshot_id,
            'spx_price': float(self.spx_price) if self.spx_price else None,
            'spx_change': float(self.spx_change) if self.spx_change else None,
            'spx_change_percent': float(self.spx_change_percent) if self.spx_change_percent else None,
            'spy_price': float(self.spy_price) if self.spy_price else None,
            'spy_change': float(self.spy_change) if self.spy_change else None,
            'spy_change_percent': float(self.spy_change_percent) if self.spy_change_percent else None,
            'vix_level': float(self.vix_level) if self.vix_level else None,
            'vix_change': float(self.vix_change) if self.vix_change else None,
            'volume': self.volume,
            'volume_vs_avg': float(self.volume_vs_avg) if self.volume_vs_avg else None,
            'technical_indicators': self.technical_indicators,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired()
        }


# ==================== Interactive Brokers Integration Models ====================

class IBSettings(Base):
    """Interactive Brokers connection configuration."""
    __tablename__ = "ib_settings"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    user_id = Column(Integer, nullable=True)  # NULL for single-user app, ready for Phase 2
    host = Column(String(255), server_default='127.0.0.1')
    port = Column(Integer, server_default='7497')
    client_id = Column(Integer, server_default='1')
    account = Column(String(50), nullable=True)
    market_data_type = Column(Integer, server_default='1')
    auto_connect = Column(Boolean, server_default='false')
    encrypted_credentials = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_ib_settings_user', 'user_id'),
    )
    
    @classmethod
    def get_settings(cls, db_session, user_id: Optional[int] = None):
        """Get IB settings for user or default settings."""
        settings = db_session.query(cls).filter(cls.user_id == user_id).first()
        return settings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'host': self.host,
            'port': self.port,
            'client_id': self.client_id,
            'account': self.account,
            'market_data_type': self.market_data_type,
            'auto_connect': self.auto_connect,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class OptionsDataCache(Base):
    """Cache for real-time options data from IB."""
    __tablename__ = "options_data_cache"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    symbol = Column(String(10), nullable=False)
    strike = Column(DECIMAL(10, 2), nullable=False)
    expiration = Column(DateTime, nullable=False)  # Date only
    option_type = Column(String(4), nullable=False)  # 'call' or 'put'
    bid = Column(DECIMAL(10, 2), nullable=True)
    ask = Column(DECIMAL(10, 2), nullable=True)
    last = Column(DECIMAL(10, 2), nullable=True)
    volume = Column(Integer, nullable=True)
    open_interest = Column(Integer, nullable=True)
    implied_volatility = Column(DECIMAL(6, 4), nullable=True)
    delta = Column(DECIMAL(6, 4), nullable=True)
    gamma = Column(DECIMAL(8, 6), nullable=True)
    theta = Column(DECIMAL(8, 2), nullable=True)
    vega = Column(DECIMAL(8, 2), nullable=True)
    rho = Column(DECIMAL(8, 2), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    ttl_seconds = Column(Integer, server_default='5')  # Time to live in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('symbol', 'strike', 'expiration', 'option_type', 'timestamp'),
        CheckConstraint("option_type IN ('call', 'put')", name='check_option_type'),
        Index('idx_options_cache_symbol', 'symbol', 'expiration'),
        Index('idx_options_cache_timestamp', 'timestamp'),
    )
    
    @classmethod
    def get_cached_data(cls, db_session, symbol: str, strike: Decimal, 
                       expiration: datetime, option_type: str):
        """Get cached data if not expired."""
        current_time = datetime.now(timezone.utc)
        entry = db_session.query(cls).filter(
            cls.symbol == symbol,
            cls.strike == strike,
            cls.expiration == expiration,
            cls.option_type == option_type,
            cls.timestamp >= current_time - timedelta(seconds=5)  # Default 5 second TTL
        ).order_by(cls.timestamp.desc()).first()
        return entry
    
    @classmethod
    def cleanup_expired(cls, db_session) -> int:
        """Remove expired cache entries."""
        current_time = datetime.now(timezone.utc)
        expired = db_session.query(cls).filter(
            cls.timestamp < current_time - timedelta(seconds=300)  # Keep max 5 minutes
        )
        count = expired.count()
        expired.delete()
        return count
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        current_time = datetime.now(timezone.utc)
        age_seconds = (current_time - self.timestamp).total_seconds()
        return age_seconds > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary."""
        return {
            'id': str(self.id),
            'symbol': self.symbol,
            'strike': float(self.strike) if self.strike else None,
            'expiration': self.expiration.isoformat() if self.expiration else None,
            'option_type': self.option_type,
            'bid': float(self.bid) if self.bid else None,
            'ask': float(self.ask) if self.ask else None,
            'last': float(self.last) if self.last else None,
            'volume': self.volume,
            'open_interest': self.open_interest,
            'implied_volatility': float(self.implied_volatility) if self.implied_volatility else None,
            'delta': float(self.delta) if self.delta else None,
            'gamma': float(self.gamma) if self.gamma else None,
            'theta': float(self.theta) if self.theta else None,
            'vega': float(self.vega) if self.vega else None,
            'rho': float(self.rho) if self.rho else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_expired': self.is_expired()
        }


class HistoricalOptionsData(Base):
    """Historical options data from IB for backtesting."""
    __tablename__ = "historical_options_data"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    symbol = Column(String(10), nullable=False)
    strike = Column(DECIMAL(10, 2), nullable=False)
    expiration = Column(DateTime, nullable=False)  # Date only
    option_type = Column(String(4), nullable=False)  # 'call' or 'put'
    date = Column(DateTime, nullable=False)  # Date of the data
    open = Column(DECIMAL(10, 2), nullable=True)
    high = Column(DECIMAL(10, 2), nullable=True)
    low = Column(DECIMAL(10, 2), nullable=True)
    close = Column(DECIMAL(10, 2), nullable=True)
    volume = Column(Integer, nullable=True)
    open_interest = Column(Integer, nullable=True)
    implied_volatility = Column(DECIMAL(6, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('symbol', 'strike', 'expiration', 'option_type', 'date'),
        CheckConstraint("option_type IN ('call', 'put')", name='check_hist_option_type'),
        Index('idx_historical_options_symbol', 'symbol', 'date'),
        Index('idx_historical_options_range', 'symbol', 'date', 'strike'),
    )
    
    @classmethod
    def get_date_range(cls, db_session, symbol: str, start_date: datetime, end_date: datetime):
        """Get historical data for a date range."""
        return db_session.query(cls).filter(
            cls.symbol == symbol,
            cls.date >= start_date,
            cls.date <= end_date
        ).order_by(cls.date).all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert historical data to dictionary."""
        return {
            'id': str(self.id),
            'symbol': self.symbol,
            'strike': float(self.strike) if self.strike else None,
            'expiration': self.expiration.isoformat() if self.expiration else None,
            'option_type': self.option_type,
            'date': self.date.isoformat() if self.date else None,
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'close': float(self.close) if self.close else None,
            'volume': self.volume,
            'open_interest': self.open_interest,
            'implied_volatility': float(self.implied_volatility) if self.implied_volatility else None
        }


class IBConnectionLog(Base):
    """IB connection event logging."""
    __tablename__ = "ib_connection_log"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4, server_default=UUID_SERVER_DEFAULT)
    event_type = Column(String(50), nullable=False)  # connect, disconnect, error, heartbeat
    status = Column(String(20), nullable=False)  # success, error, warning
    account = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    event_metadata = Column(JSONType, nullable=True)  # Additional event data (renamed from metadata)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_ib_log_created', 'created_at'),
        Index('idx_ib_log_event', 'event_type'),
    )
    
    @classmethod
    def get_recent_logs(cls, db_session, limit: int = 100):
        """Get recent connection logs."""
        return db_session.query(cls).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def log_event(cls, db_session, event_type: str, status: str, 
                  account: Optional[str] = None, error_message: Optional[str] = None,
                  metadata: Optional[Dict] = None):
        """Create a new log entry."""
        log = cls(
            event_type=event_type,
            status=status,
            account=account,
            error_message=error_message,
            event_metadata=metadata
        )
        db_session.add(log)
        db_session.commit()
        return log
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            'id': str(self.id),
            'event_type': self.event_type,
            'status': self.status,
            'account': self.account,
            'error_message': self.error_message,
            'metadata': self.event_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
