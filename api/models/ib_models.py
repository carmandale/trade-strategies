"""Interactive Brokers database models."""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

Base = declarative_base()


class IBSettings(Base):
	"""Interactive Brokers connection settings."""
	__tablename__ = "ib_settings"
	
	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
	user_id = Column(Integer, nullable=True)
	host = Column(String(255), default="127.0.0.1")
	port = Column(Integer, default=7497)
	client_id = Column(Integer, default=1)
	account = Column(String(50), nullable=True)
	market_data_type = Column(Integer, default=1)
	auto_connect = Column(Boolean, default=False)
	encrypted_credentials = Column(Text, nullable=True)
	active = Column(Boolean, default=True)  # Added missing field
	connection_timeout = Column(Integer, default=10)  # Added for timeout management
	retry_attempts = Column(Integer, default=3)  # Added for retry logic
	market_data_permissions = Column(JSONB, nullable=True)  # Added for permissions tracking
	created_at = Column(DateTime(timezone=True), default=func.now())
	updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
	
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary."""
		return {
			"id": str(self.id),
			"user_id": self.user_id,
			"host": self.host,
			"port": self.port,
			"client_id": self.client_id,
			"account": self.account,
			"market_data_type": self.market_data_type,
			"auto_connect": self.auto_connect,
			"created_at": self.created_at.isoformat() if self.created_at else None,
			"updated_at": self.updated_at.isoformat() if self.updated_at else None,
		}


class OptionsDataCache(Base):
	"""Options data cache for IB market data."""
	__tablename__ = "options_data_cache"
	
	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
	symbol = Column(String(10), nullable=False)
	strike = Column(DECIMAL(10, 2), nullable=False)
	expiration = Column(DateTime, nullable=False)
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
	ttl_seconds = Column(Integer, default=5)
	created_at = Column(DateTime(timezone=True), default=func.now())
	
	__table_args__ = (
		Index('idx_options_cache_symbol', 'symbol', 'expiration'),
		Index('idx_options_cache_timestamp', 'timestamp'),
	)
	
	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary."""
		return {
			"id": str(self.id),
			"symbol": self.symbol,
			"strike": float(self.strike) if self.strike else None,
			"expiration": self.expiration.isoformat() if self.expiration else None,
			"option_type": self.option_type,
			"bid": float(self.bid) if self.bid else None,
			"ask": float(self.ask) if self.ask else None,
			"last": float(self.last) if self.last else None,
			"volume": self.volume,
			"open_interest": self.open_interest,
			"implied_volatility": float(self.implied_volatility) if self.implied_volatility else None,
			"delta": float(self.delta) if self.delta else None,
			"gamma": float(self.gamma) if self.gamma else None,
			"theta": float(self.theta) if self.theta else None,
			"vega": float(self.vega) if self.vega else None,
			"rho": float(self.rho) if self.rho else None,
			"timestamp": self.timestamp.isoformat() if self.timestamp else None,
			"ttl_seconds": self.ttl_seconds,
		}


class IBConnectionLog(Base):
	"""Log of IB connection events."""
	__tablename__ = "ib_connection_log"
	
	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
	event_type = Column(String(50), nullable=False)
	status = Column(String(20), nullable=False)
	account = Column(String(50), nullable=True)
	error_message = Column(Text, nullable=True)
	event_metadata = Column(JSONB, nullable=True)
	created_at = Column(DateTime(timezone=True), default=func.now())
	
	__table_args__ = (
		Index('idx_ib_log_created', 'created_at'),
		Index('idx_ib_log_event', 'event_type'),
	)