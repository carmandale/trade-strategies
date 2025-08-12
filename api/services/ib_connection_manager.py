"""Interactive Brokers connection manager service."""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.ib_models import IBSettings, IBConnectionLog
import os
from contextlib import contextmanager
try:
	from ib_insync import IB, util
except ImportError:
	IB = None
	util = None

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/trade_strategies")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class IBConnectionManager:
	"""Manages Interactive Brokers connection and settings."""
	
	def __init__(self):
		self.is_connected = False
		self.account = None
		self.ib_client = None
		self._connection_settings = None
		self.reconnect_attempts = 0
		self.max_reconnect_attempts = 3
		logger.info("IBConnectionManager initialized")
	
	@contextmanager
	def get_db_session(self):
		"""Get database session with proper cleanup."""
		session = SessionLocal()
		try:
			yield session
		except Exception as e:
			session.rollback()
			logger.error(f"Database error: {e}")
			raise
		finally:
			session.close()
	
	@property
	def connection_settings(self) -> Optional[IBSettings]:
		"""Get current connection settings with fresh database session."""
		try:
			with self.get_db_session() as session:
				settings = session.query(IBSettings).first()
				if settings:
					# Detach from session to avoid lazy loading issues
					session.expunge(settings)
				return settings
		except Exception as e:
			logger.error(f"Error getting connection settings: {e}")
			return None
	
	def load_settings(self) -> Optional[IBSettings]:
		"""Load connection settings from database."""
		try:
			with self.get_db_session() as session:
				settings = session.query(IBSettings).filter(IBSettings.active == True).first()
				if settings:
					# Detach from session to avoid lazy loading issues
					session.expunge(settings)
					self._connection_settings = settings
				return settings
		except Exception as e:
			logger.error(f"Failed to load IB settings: {e}")
			return None
	
	def get_connection_status(self) -> Dict[str, Any]:
		"""Get current connection status."""
		try:
			settings = self.connection_settings
			return {
				"connected": self.is_connected,
				"account": self.account,
				"host": settings.host if settings else None,
				"port": settings.port if settings else None,
				"last_check": datetime.utcnow().isoformat() + "Z"
			}
		except Exception as e:
			logger.error(f"Error getting connection status: {e}")
			return {
				"connected": False,
				"account": None,
				"host": None,
				"port": None,
				"error": str(e),
				"last_check": datetime.utcnow().isoformat() + "Z"
			}
	
	def save_settings(self, settings_data: Dict[str, Any]) -> bool:
		"""Save IB connection settings to database."""
		try:
			with self.get_db_session() as session:
				# Check if settings already exist
				existing = session.query(IBSettings).first()
				
				if existing:
					# Update existing settings
					for key, value in settings_data.items():
						if hasattr(existing, key):
							setattr(existing, key, value)
					existing.updated_at = datetime.utcnow()
				else:
					# Create new settings
					new_settings = IBSettings(**settings_data)
					session.add(new_settings)
				
				session.commit()
				logger.info("IB settings saved successfully")
				return True
				
		except Exception as e:
			logger.error(f"Error saving settings: {e}")
			return False
	
	def connect(self) -> Dict[str, Any]:
		"""Connect to Interactive Brokers."""
		try:
			settings = self.connection_settings
			if not settings:
				return {
					"success": False,
					"message": "No connection settings found",
					"status": self.get_connection_status()
				}
			
			# Log connection attempt
			self._log_connection_event("connect_attempt", "attempting", settings.account)
			
			logger.info(f"Attempting to connect to IB at {settings.host}:{settings.port}")
			
			# Check if ib_insync is available
			if IB is None:
				logger.warning("ib_insync not available, using simulation mode")
				# Simulate successful connection for testing
				self.is_connected = True
				self.account = settings.account
			else:
				# Actual IB connection using ib_insync
				if self.ib_client:
					self.disconnect()
				
				self.ib_client = IB()
				try:
					self.ib_client.connect(
						host=settings.host,
						port=settings.port,
						clientId=settings.client_id,
						timeout=10
					)
					
					if self.ib_client.isConnected():
						# Set market data type
						if hasattr(settings, 'market_data_type'):
							self.ib_client.reqMarketDataType(settings.market_data_type)
						
						# Get account info
						account_summary = self.ib_client.accountSummary()
						if account_summary:
							self.account = account_summary[0].account
						else:
							self.account = settings.account
						
						self.is_connected = True
						self.reconnect_attempts = 0
					else:
						raise Exception("Failed to connect to IB")
					
				except Exception as e:
					logger.error(f"IB connection failed: {e}")
					if self.ib_client:
						try:
							self.ib_client.disconnect()
						except:
							pass
					self.ib_client = None
					self.is_connected = False
					raise
			
			self._log_connection_event("connect_success", "connected", settings.account)
			
			return {
				"success": True,
				"message": f"Connected to IB account {settings.account}",
				"status": self.get_connection_status()
			}
			
		except Exception as e:
			logger.error(f"Error connecting to IB: {e}")
			self._log_connection_event("connect_error", "error", None, str(e))
			
			return {
				"success": False,
				"message": f"Failed to connect: {str(e)}",
				"status": self.get_connection_status()
			}
	
	def disconnect(self) -> Dict[str, Any]:
		"""Disconnect from Interactive Brokers."""
		try:
			logger.info("Disconnecting from IB")
			
			if self.ib_client and IB is not None:
				try:
					self.ib_client.disconnect()
				except Exception as e:
					logger.warning(f"Error during IB disconnect: {e}")
			
			self.is_connected = False
			self.account = None
			self.ib_client = None
			self.reconnect_attempts = 0
			
			self._log_connection_event("disconnect", "disconnected", None)
			
			return {
				"success": True,
				"message": "Disconnected from IB",
				"status": self.get_connection_status()
			}
			
		except Exception as e:
			logger.error(f"Error disconnecting from IB: {e}")
			return {
				"success": False,
				"message": f"Error during disconnect: {str(e)}",
				"status": self.get_connection_status()
			}
	
	def reconnect(self) -> Dict[str, Any]:
		"""Reconnect to Interactive Brokers."""
		logger.info("Attempting to reconnect to IB")
		disconnect_result = self.disconnect()
		if disconnect_result["success"]:
			return self.connect()
		else:
			return disconnect_result
	
	def check_connection(self) -> bool:
		"""Check if connection to IB is active."""
		if self.ib_client and IB is not None:
			try:
				is_connected = self.ib_client.isConnected()
				self.is_connected = is_connected
				return is_connected
			except:
				self.is_connected = False
				return False
		return self.is_connected
	
	def _log_connection_event(self, event_type: str, status: str, account: Optional[str] = None, error: Optional[str] = None):
		"""Log connection event to database."""
		try:
			with self.get_db_session() as session:
				log_entry = IBConnectionLog(
					event_type=event_type,
					status=status,
					account=account,
					error_message=error,
					event_metadata={
						"timestamp": datetime.utcnow().isoformat(),
						"connection_manager": "IBConnectionManager"
					}
				)
				session.add(log_entry)
				session.commit()
		except Exception as e:
			logger.error(f"Error logging connection event: {e}")
	
	def get_account_info(self) -> Dict[str, Any]:
		"""Get account information from IB."""
		if not self.is_connected:
			return {
				"success": False,
				"message": "Not connected to IB",
				"data": None
			}
		
		try:
			# TODO: Implement actual account info retrieval
			return {
				"success": True,
				"message": "Account info retrieved",
				"data": {
					"account": self.account,
					"connected": self.is_connected,
					"timestamp": datetime.utcnow().isoformat()
				}
			}
		except Exception as e:
			logger.error(f"Error getting account info: {e}")
			return {
				"success": False,
				"message": f"Error: {str(e)}",
				"data": None
			}


# Global instance
ib_connection_manager = IBConnectionManager()