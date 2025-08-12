"""Interactive Brokers connection management service."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from database.config import get_db_session
from database.models import IBSettings, IBConnectionLog

logger = logging.getLogger(__name__)


class IBConnectionService:
	"""Service for managing Interactive Brokers connections."""
	
	def __init__(self):
		"""Initialize the IB connection service."""
		self.connection = None
		self.is_connected = False
		self.account = None
		self.settings = None
	
	def load_settings(self, user_id: Optional[int] = None) -> Optional[IBSettings]:
		"""Load IB settings from database.
		
		Args:
			user_id: Optional user ID for multi-user support (Phase 2)
		
		Returns:
			IBSettings object if found, None otherwise
		"""
		with next(get_db_session()) as db:
			self.settings = IBSettings.get_settings(db, user_id)
			if self.settings:
				logger.info(f"Loaded IB settings for host {self.settings.host}:{self.settings.port}")
			else:
				logger.warning("No IB settings found in database")
			return self.settings
	
	def save_settings(self, 
					 host: str = "127.0.0.1",
					 port: int = 7497,
					 client_id: int = 1,
					 account: Optional[str] = None,
					 market_data_type: int = 1,
					 auto_connect: bool = False,
					 user_id: Optional[int] = None) -> IBSettings:
		"""Save or update IB settings in database.
		
		Args:
			host: IB Gateway/TWS host address
			port: IB Gateway/TWS port (7497 for paper, 7496 for live)
			client_id: Client ID for connection
			account: IB account number
			market_data_type: Market data type (1=live, 2=frozen, 3=delayed)
			auto_connect: Whether to auto-connect on startup
			user_id: Optional user ID for multi-user support
		
		Returns:
			Updated IBSettings object
		"""
		with next(get_db_session()) as db:
			settings = db.query(IBSettings).filter(IBSettings.user_id == user_id).first()
			
			if settings:
				# Update existing settings
				settings.host = host
				settings.port = port
				settings.client_id = client_id
				settings.account = account
				settings.market_data_type = market_data_type
				settings.auto_connect = auto_connect
				settings.updated_at = datetime.now(timezone.utc)
			else:
				# Create new settings
				settings = IBSettings(
					user_id=user_id,
					host=host,
					port=port,
					client_id=client_id,
					account=account,
					market_data_type=market_data_type,
					auto_connect=auto_connect
				)
				db.add(settings)
			
			db.commit()
			db.refresh(settings)
			self.settings = settings
			logger.info(f"Saved IB settings for {host}:{port}")
			return settings
	
	def log_event(self, 
				  event_type: str,
				  status: str,
				  error_message: Optional[str] = None,
				  metadata: Optional[Dict[str, Any]] = None):
		"""Log an IB connection event to the database.
		
		Args:
			event_type: Type of event (connect, disconnect, error, heartbeat)
			status: Status of the event (success, error, warning)
			error_message: Optional error message
			metadata: Optional additional metadata
		"""
		with next(get_db_session()) as db:
			log_entry = IBConnectionLog.log_event(
				db,
				event_type=event_type,
				status=status,
				account=self.account,
				error_message=error_message,
				metadata=metadata
			)
			logger.info(f"Logged IB event: {event_type} - {status}")
			return log_entry
	
	def connect(self) -> bool:
		"""Connect to Interactive Brokers.
		
		This is a placeholder for actual IB connection logic.
		Will be implemented with ib_insync in Task 2.
		
		Returns:
			True if connection successful, False otherwise
		"""
		if not self.settings:
			self.load_settings()
		
		if not self.settings:
			logger.error("No IB settings available for connection")
			self.log_event("connect", "error", "No settings configured")
			return False
		
		try:
			# Placeholder for actual IB connection
			# Will be replaced with ib_insync implementation
			logger.info(f"Connecting to IB at {self.settings.host}:{self.settings.port}")
			
			# Simulate successful connection for now
			self.is_connected = True
			self.account = self.settings.account or "DEMO123456"
			
			self.log_event(
				"connect",
				"success",
				metadata={
					"host": self.settings.host,
					"port": self.settings.port,
					"client_id": self.settings.client_id
				}
			)
			
			logger.info(f"Successfully connected to IB account {self.account}")
			return True
			
		except Exception as e:
			logger.error(f"Failed to connect to IB: {str(e)}")
			self.log_event("connect", "error", str(e))
			self.is_connected = False
			return False
	
	def disconnect(self):
		"""Disconnect from Interactive Brokers."""
		if self.is_connected:
			try:
				# Placeholder for actual disconnection
				self.is_connected = False
				self.log_event("disconnect", "success")
				logger.info("Disconnected from IB")
			except Exception as e:
				logger.error(f"Error during IB disconnection: {str(e)}")
				self.log_event("disconnect", "error", str(e))
	
	def check_connection(self) -> bool:
		"""Check if connection to IB is active.
		
		Returns:
			True if connected, False otherwise
		"""
		if not self.is_connected:
			return False
		
		try:
			# Placeholder for actual connection check
			# Will be replaced with ib_insync heartbeat
			self.log_event("heartbeat", "success")
			return True
		except Exception as e:
			logger.error(f"Connection check failed: {str(e)}")
			self.log_event("heartbeat", "error", str(e))
			self.is_connected = False
			return False
	
	def get_connection_status(self) -> Dict[str, Any]:
		"""Get current connection status.
		
		Returns:
			Dictionary with connection status information
		"""
		return {
			"connected": self.is_connected,
			"account": self.account,
			"host": self.settings.host if self.settings else None,
			"port": self.settings.port if self.settings else None,
			"last_check": datetime.now(timezone.utc).isoformat()
		}


# Singleton instance
ib_connection_service = IBConnectionService()