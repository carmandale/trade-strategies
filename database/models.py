"""SQLAlchemy models for trading strategy application."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DECIMAL, Boolean, DateTime, Text, ForeignKey, Enum
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

class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    strategies = relationship("Strategy", back_populates="user")
    trades = relationship("Trade", back_populates="user")

class Strategy(Base):
    """Strategy configuration model."""
    __tablename__ = "strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    strategy_type = Column(Enum(StrategyType), nullable=False)
    strikes = Column(JSONB, nullable=False)  # Store strike prices as JSON
    contracts = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    backtests = relationship("Backtest", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategies")

class Backtest(Base):
    """Backtest result model."""
    __tablename__ = "backtests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    analysis_date = Column(DateTime, nullable=False)
    entry_time = Column(String(10), nullable=False)  # "09:30"
    exit_time = Column(String(10), nullable=False)   # "16:00"
    results = Column(JSONB, nullable=False)  # P/L, metrics, chart data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")

class Trade(Base):
    """Actual trade execution model."""
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=True)
    execution_date = Column(DateTime, nullable=False)
    entry_price = Column(DECIMAL(10, 2), nullable=True)
    exit_price = Column(DECIMAL(10, 2), nullable=True)
    pnl = Column(DECIMAL(10, 2), nullable=True)
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    notes = Column(Text, nullable=True)
    contracts = Column(Integer, nullable=False, default=1)
    
    # Store original trade data for compatibility
    strategy_type = Column(String(50), nullable=False)  # For legacy compatibility
    strikes_data = Column(JSONB, nullable=False)  # Store strikes as JSON
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")