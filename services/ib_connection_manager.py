"""Interactive Brokers connection manager."""
import logging
import time
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ib_insync import IB, util
from database.config import get_db_session
from database.models import IBSettings, IBConnectionLog

logger = logging.getLogger(__name__)

# Enable asyncio compatibility for Jupyter/IPython environments
util.startLoop()


class IBConnectionManager:
	"""Manages Interactive Brokers API connections."""
	
	def __init__(self):
		"""Initialize the connection manager."""
		self.ib_client: Optional[IB] = None
		self.is_connected: bool = False
		self.connection_settings: Optional[IBSettings] = None
		self.reconnect_attempts: int = 0
		self.max_reconnect_attempts: int = 3
		self.health_monitor_task: Optional[asyncio.Task] = None
		self._encryption_key: Optional[bytes] = None
	
	def load_settings(self) -> Optional[IBSettings]:
		"""Load connection settings from database.
		
		Returns:
			IBSettings object or None if not found
		"""
		try:
			with next(get_db_session()) as db:
				settings = db.query(IBSettings).filter(
					IBSettings.user_id == None  # Default settings for now
				).first()
				
				if settings:
					self.connection_settings = settings
					logger.info(f"Loaded IB settings for account {settings.account}")
				else:
					logger.warning("No IB connection settings found in database")
				
				return settings
		except Exception as e:
			logger.error(f"Failed to load IB settings: {str(e)}")
			return None
	
	def connect(self) -> bool:
		"""Connect to Interactive Brokers.
		
		Returns:
			True if connection successful, False otherwise
		"""
		try:
			if not self.connection_settings:
				self.load_settings()
			
			if not self.connection_settings:
				logger.error("No connection settings available")
				return False
			
			# Create IB client if not exists
			if not self.ib_client:
				self.ib_client = IB()
			
			# Connect to IB Gateway or TWS
			logger.info(f"Connecting to IB at {self.connection_settings.host}:{self.connection_settings.port}")
			self.ib_client.connect(
				self.connection_settings.host,
				self.connection_settings.port,
				clientId=self.connection_settings.client_id,
				timeout=10
			)
			
			# Verify connection
			if self.ib_client.isConnected():
				self.is_connected = True
				self.reconnect_attempts = 0
				
				# Set market data type
				self.ib_client.reqMarketDataType(self.connection_settings.market_data_type)
				
				# Get account info to verify connection
				account_summary = self.ib_client.accountSummary()
				if account_summary:
					account = account_summary[0].account if account_summary else self.connection_settings.account
					logger.info(f"Successfully connected to IB account {account}")
					
					# Log successful connection
					self._log_connection_event(
						event_type='connect',
						status='success',
						account=account,
						metadata={'host': self.connection_settings.host, 'port': self.connection_settings.port}
					)
				else:
					logger.warning("Connected but could not retrieve account info")
				
				return True
			else:
				logger.error("Failed to establish connection to IB")
				self._log_connection_event(
					event_type='connect',
					status='failed',
					error_message='Connection not established'
				)
				return False
				
		except Exception as e:
			logger.error(f"Connection error: {str(e)}")
			self._log_connection_event(
				event_type='connect',
				status='error',
				error_message=str(e)
			)
			return False
	
	def disconnect(self):
		"""Disconnect from Interactive Brokers."""
		try:
			if self.ib_client:
				self.ib_client.disconnect()
				logger.info("Disconnected from IB")
				
				self._log_connection_event(
					event_type='disconnect',
					status='success',
					account=self.connection_settings.account if self.connection_settings else None
				)
			
			self.is_connected = False
			
		except Exception as e:
			logger.error(f"Error during disconnect: {str(e)}")
			self._log_connection_event(
				event_type='disconnect',
				status='error',
				error_message=str(e)
			)
	
	def reconnect(self) -> bool:
		"""Attempt to reconnect to IB.
		
		Returns:
			True if reconnection successful, False otherwise
		"""
		logger.info("Attempting to reconnect to IB...")
		
		while self.reconnect_attempts < self.max_reconnect_attempts:
			self.reconnect_attempts += 1
			logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
			
			# Disconnect first if connected
			if self.ib_client:
				try:
					self.ib_client.disconnect()
				except:
					pass
			
			# Wait before reconnecting
			time.sleep(2 ** self.reconnect_attempts)  # Exponential backoff
			
			# Try to connect
			if self.connect():
				logger.info("Reconnection successful")
				return True
		
		logger.error(f"Failed to reconnect after {self.max_reconnect_attempts} attempts")
		self._log_connection_event(
			event_type='reconnect',
			status='failed',
			error_message=f'Max attempts ({self.max_reconnect_attempts}) exceeded'
		)
		return False
	
	def check_connection(self) -> bool:
		"""Check if connection is healthy.
		
		Returns:
			True if connected and healthy, False otherwise
		"""
		try:
			if not self.ib_client:
				return False
			
			is_healthy = self.ib_client.isConnected()
			
			if not is_healthy and self.is_connected:
				logger.warning("Connection lost to IB")
				self.is_connected = False
				self._log_connection_event(
					event_type='health_check',
					status='disconnected',
					error_message='Connection lost'
				)
			
			return is_healthy
			
		except Exception as e:
			logger.error(f"Error checking connection: {str(e)}")
			return False
	
	def get_account_info(self) -> Optional[Dict[str, Any]]:
		"""Get account information from IB.
		
		Returns:
			Dictionary with account details or None if not connected
		"""
		if not self.is_connected or not self.ib_client:
			logger.warning("Not connected to IB")
			return None
		
		try:
			account_summary = self.ib_client.accountSummary()
			
			if not account_summary:
				return None
			
			# Parse account summary into dictionary
			account_info = {}
			for item in account_summary:
				if item.tag == 'NetLiquidation':
					account_info['net_liquidation'] = float(item.value)
				elif item.tag == 'TotalCashValue':
					account_info['total_cash'] = float(item.value)
				elif item.tag == 'GrossPositionValue':
					account_info['gross_position_value'] = float(item.value)
				elif item.tag == 'AvailableFunds':
					account_info['available_funds'] = float(item.value)
				elif item.tag == 'BuyingPower':
					account_info['buying_power'] = float(item.value)
				
				if 'account' not in account_info:
					account_info['account'] = item.account
			
			return account_info
			
		except Exception as e:
			logger.error(f"Error getting account info: {str(e)}")
			return None
	
	def save_settings(self, settings_dict: Dict[str, Any]) -> bool:
		"""Save or update connection settings.
		
		Args:
			settings_dict: Dictionary with connection settings
		
		Returns:
			True if saved successfully, False otherwise
		"""
		try:
			with next(get_db_session()) as db:
				# Check if settings already exist
				existing = db.query(IBSettings).filter(
					IBSettings.user_id == None  # Default settings
				).first()
				
				if existing:
					# Update existing settings
					for key, value in settings_dict.items():
						if hasattr(existing, key):
							setattr(existing, key, value)
					settings = existing
				else:
					# Create new settings
					settings = IBSettings(**settings_dict)
					db.add(settings)
				
				db.commit()
				self.connection_settings = settings
				logger.info("IB settings saved successfully")
				return True
				
		except Exception as e:
			logger.error(f"Failed to save settings: {str(e)}")
			return False
	
	def encrypt_credentials(self, password: str) -> str:
		"""Encrypt credentials for storage.
		
		Args:
			password: Plain text password
		
		Returns:
			Encrypted password as base64 string
		"""
		if not self._encryption_key:
			# Generate encryption key from a fixed salt (in production, use env variable)
			salt = b'trade-strategies-ib-salt'  # In production, load from environment
			kdf = PBKDF2HMAC(
				algorithm=hashes.SHA256(),
				length=32,
				salt=salt,
				iterations=100000,
			)
			key = base64.urlsafe_b64encode(kdf.derive(b'trade-strategies-key'))
			self._encryption_key = key
		
		f = Fernet(self._encryption_key)
		encrypted = f.encrypt(password.encode())
		return base64.b64encode(encrypted).decode()
	
	def decrypt_credentials(self, encrypted_password: str) -> str:
		"""Decrypt stored credentials.
		
		Args:
			encrypted_password: Base64 encoded encrypted password
		
		Returns:
			Decrypted password
		"""
		if not self._encryption_key:
			# Generate encryption key from a fixed salt
			salt = b'trade-strategies-ib-salt'
			kdf = PBKDF2HMAC(
				algorithm=hashes.SHA256(),
				length=32,
				salt=salt,
				iterations=100000,
			)
			key = base64.urlsafe_b64encode(kdf.derive(b'trade-strategies-key'))
			self._encryption_key = key
		
		f = Fernet(self._encryption_key)
		encrypted_bytes = base64.b64decode(encrypted_password.encode())
		decrypted = f.decrypt(encrypted_bytes)
		return decrypted.decode()
	
	def get_connection_status(self) -> Dict[str, Any]:
		"""Get current connection status.
		
		Returns:
			Dictionary with connection status details
		"""
		status = {
			'connected': self.is_connected,
			'account': None,
			'host': None,
			'port': None,
			'last_check': datetime.now(timezone.utc).isoformat()
		}
		
		if self.connection_settings:
			status['account'] = self.connection_settings.account
			status['host'] = self.connection_settings.host
			status['port'] = self.connection_settings.port
		
		if self.is_connected:
			# Try to get live account info
			account_info = self.get_account_info()
			if account_info:
				status['account_info'] = account_info
		
		return status
	
	async def _health_monitor_loop(self, interval: int = 60):
		"""Background task to monitor connection health.
		
		Args:
			interval: Check interval in seconds
		"""
		while True:
			try:
				await asyncio.sleep(interval)
				
				if self.is_connected:
					is_healthy = self.check_connection()
					
					if not is_healthy:
						logger.warning("Connection unhealthy, attempting reconnect...")
						self.reconnect()
				
			except asyncio.CancelledError:
				logger.info("Health monitor task cancelled")
				break
			except Exception as e:
				logger.error(f"Health monitor error: {str(e)}")
	
	def start_health_monitor(self, interval: int = 60):
		"""Start background health monitoring.
		
		Args:
			interval: Check interval in seconds
		"""
		if not self.health_monitor_task:
			self.health_monitor_task = asyncio.create_task(
				self._health_monitor_loop(interval)
			)
			logger.info(f"Started health monitor with {interval}s interval")
	
	def stop_health_monitor(self):
		"""Stop background health monitoring."""
		if self.health_monitor_task:
			self.health_monitor_task.cancel()
			self.health_monitor_task = None
			logger.info("Stopped health monitor")
	
	def _log_connection_event(self, 
							  event_type: str,
							  status: str,
							  account: Optional[str] = None,
							  error_message: Optional[str] = None,
							  metadata: Optional[Dict[str, Any]] = None):
		"""Log connection event to database.
		
		Args:
			event_type: Type of event (connect, disconnect, etc.)
			status: Event status (success, error, etc.)
			account: Account ID if available
			error_message: Error message if applicable
			metadata: Additional event metadata
		"""
		try:
			with next(get_db_session()) as db:
				log_entry = IBConnectionLog(
					event_type=event_type,
					status=status,
					account=account,
					error_message=error_message,
					event_metadata=metadata
				)
				db.add(log_entry)
				db.commit()
		except Exception as e:
			logger.error(f"Failed to log connection event: {str(e)}")


# Singleton instance
ib_connection_manager = IBConnectionManager()