"""Tests for Interactive Brokers connection manager."""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from api.services.ib_connection_manager import IBConnectionManager
from api.models.ib_models import IBSettings, IBConnectionLog


class TestIBConnectionManager:
	"""Test IBConnectionManager class."""
	
	@pytest.fixture
	def mock_ib_client(self):
		"""Create a mock IB client."""
		with patch('ib_insync.IB') as mock_ib:
			client = Mock()
			client.connect = Mock(return_value=None)
			client.disconnect = Mock(return_value=None)
			client.isConnected = Mock(return_value=True)
			client.reqMarketDataType = Mock()
			client.accountSummary = Mock(return_value=[
				Mock(account='DU123456', tag='NetLiquidation', value='100000.00')
			])
			mock_ib.return_value = client
			yield client
	
	@pytest.fixture
	def connection_manager(self, mock_ib_client):
		"""Create IBConnectionManager instance with mocked client."""
		manager = IBConnectionManager()
		manager.ib_client = mock_ib_client
		return manager
	
	def test_initialization(self):
		"""Test IBConnectionManager initialization."""
		manager = IBConnectionManager()
		assert manager.ib_client is None
		assert manager.is_connected is False
		assert manager.connection_settings is None
		assert manager.reconnect_attempts == 0
		assert manager.max_reconnect_attempts == 3
	
	@patch('api.services.ib_connection_manager.IBConnectionManager.get_db_session')
	def test_load_settings(self, mock_get_db):
		"""Test loading connection settings from database."""
		# Mock database session and context manager
		mock_db = Mock()
		mock_context = Mock()
		mock_context.__enter__ = Mock(return_value=mock_db)
		mock_context.__exit__ = Mock(return_value=None)
		mock_get_db.return_value = mock_context
		
		# Mock settings
		mock_settings = Mock(spec=IBSettings)
		mock_settings.host = '127.0.0.1'
		mock_settings.port = 7497
		mock_settings.client_id = 1
		mock_settings.account = 'DU123456'
		mock_settings.market_data_type = 1
		mock_settings.auto_connect = True
		mock_settings.encrypted_credentials = None
		mock_settings.active = True
		
		mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
		mock_db.expunge = Mock()  # Mock the expunge method
		mock_db.query.return_value.first.return_value = mock_settings  # Also mock direct query().first() call
		
		manager = IBConnectionManager()
		settings = manager.load_settings()
		
		assert settings == mock_settings
		assert manager._connection_settings == mock_settings
		mock_db.query.assert_called_once()
	
	@patch('api.services.ib_connection_manager.IBConnectionManager.get_db_session')
	def test_load_settings_not_found(self, mock_get_db):
		"""Test loading settings when none exist."""
		mock_db = Mock()
		mock_context = Mock()
		mock_context.__enter__ = Mock(return_value=mock_db)
		mock_context.__exit__ = Mock(return_value=None)
		mock_get_db.return_value = mock_context
		mock_db.query.return_value.filter.return_value.first.return_value = None
		
		manager = IBConnectionManager()
		settings = manager.load_settings()
		
		assert settings is None
		assert manager._connection_settings is None  # Check internal cache directly
	
	@patch('api.services.ib_connection_manager.IB')
	@patch('api.services.ib_connection_manager.IBConnectionManager.get_db_session')
	def test_connect_success(self, mock_get_db, mock_ib_class):
		"""Test successful connection to IB."""
		# Setup mock DB with context manager
		mock_db = Mock()
		mock_context = Mock()
		mock_context.__enter__ = Mock(return_value=mock_db)
		mock_context.__exit__ = Mock(return_value=None)
		mock_get_db.return_value = mock_context
		
		# Setup mock settings
		mock_settings = Mock(spec=IBSettings)
		mock_settings.host = '127.0.0.1'
		mock_settings.port = 7497
		mock_settings.client_id = 1
		mock_settings.account = 'DU123456'
		mock_settings.market_data_type = 1
		
		# Setup mock IB client
		mock_client = Mock()
		mock_client.connect = Mock()
		mock_client.isConnected = Mock(return_value=True)
		mock_client.reqMarketDataType = Mock()
		mock_client.accountSummary = Mock(return_value=[
			Mock(account='DU123456', tag='NetLiquidation', value='100000.00')
		])
		mock_ib_class.return_value = mock_client
		
		manager = IBConnectionManager()
		manager.connection_settings = mock_settings
		
		result = manager.connect()
		
		assert result["success"] is True
		assert manager.is_connected is True
		mock_client.connect.assert_called_once_with(
			'127.0.0.1', 7497, clientId=1, timeout=10
		)
		mock_client.reqMarketDataType.assert_called_once_with(1)
		
		# Verify connection log was created
		mock_db.add.assert_called()
		mock_db.commit.assert_called()
	
	@patch('api.services.ib_connection_manager.IB')
	@patch('api.services.ib_connection_manager.IBConnectionManager.get_db_session')
	def test_connect_failure(self, mock_get_db, mock_ib_class):
		"""Test failed connection to IB."""
		# Setup mock DB with context manager
		mock_db = Mock()
		mock_context = Mock()
		mock_context.__enter__ = Mock(return_value=mock_db)
		mock_context.__exit__ = Mock(return_value=None)
		mock_get_db.return_value = mock_context
		
		# Setup mock settings
		mock_settings = Mock(spec=IBSettings)
		mock_settings.host = '127.0.0.1'
		mock_settings.port = 7497
		mock_settings.client_id = 1
		
		# Setup mock IB client to fail
		mock_client = Mock()
		mock_client.connect.side_effect = Exception("Connection refused")
		mock_ib_class.return_value = mock_client
		
		manager = IBConnectionManager()
		manager.connection_settings = mock_settings
		
		result = manager.connect()
		
		assert result["success"] is False
		assert manager.is_connected is False
		
		# Verify error was logged
		mock_db.add.assert_called()
		mock_db.commit.assert_called()
	
	def test_disconnect(self, connection_manager):
		"""Test disconnecting from IB."""
		connection_manager.is_connected = True
		
		connection_manager.disconnect()
		
		assert connection_manager.is_connected is False
		connection_manager.ib_client.disconnect.assert_called_once()
	
	def test_disconnect_when_not_connected(self, connection_manager):
		"""Test disconnect when not connected."""
		connection_manager.is_connected = False
		connection_manager.ib_client = None
		
		# Should not raise error
		connection_manager.disconnect()
		assert connection_manager.is_connected is False
	
	@patch('services.ib_connection_manager.time.sleep')
	def test_reconnect(self, mock_sleep, connection_manager):
		"""Test reconnection logic."""
		connection_manager.is_connected = False
		connection_manager.ib_client.isConnected.side_effect = [False, False, True]
		connection_manager.ib_client.connect = Mock()
		
		# Mock settings
		connection_manager.connection_settings = Mock()
		connection_manager.connection_settings.host = '127.0.0.1'
		connection_manager.connection_settings.port = 7497
		connection_manager.connection_settings.client_id = 1
		
		result = connection_manager.reconnect()
		
		assert result["success"] is True
		assert connection_manager.reconnect_attempts == 1
		mock_sleep.assert_called()
	
	@patch('services.ib_connection_manager.time.sleep')
	def test_reconnect_max_attempts(self, mock_sleep, connection_manager):
		"""Test reconnection with max attempts exceeded."""
		connection_manager.is_connected = False
		connection_manager.ib_client.isConnected.return_value = False
		connection_manager.ib_client.connect = Mock()
		connection_manager.max_reconnect_attempts = 2
		
		# Mock settings
		connection_manager.connection_settings = Mock()
		connection_manager.connection_settings.host = '127.0.0.1'
		connection_manager.connection_settings.port = 7497
		connection_manager.connection_settings.client_id = 1
		
		result = connection_manager.reconnect()
		
		assert result["success"] is False
		assert connection_manager.reconnect_attempts == 2
		assert mock_sleep.call_count == 2
	
	def test_check_connection_healthy(self, connection_manager):
		"""Test connection health check when healthy."""
		connection_manager.is_connected = True
		connection_manager.ib_client.isConnected.return_value = True
		
		is_healthy = connection_manager.check_connection()
		
		assert is_healthy is True
		connection_manager.ib_client.isConnected.assert_called_once()
	
	def test_check_connection_unhealthy(self, connection_manager):
		"""Test connection health check when unhealthy."""
		connection_manager.is_connected = True
		connection_manager.ib_client.isConnected.return_value = False
		
		is_healthy = connection_manager.check_connection()
		
		assert is_healthy is False
		assert connection_manager.is_connected is False
	
	def test_check_connection_no_client(self):
		"""Test connection check with no client."""
		manager = IBConnectionManager()
		manager.is_connected = False
		manager.ib_client = None
		
		is_healthy = manager.check_connection()
		
		assert is_healthy is False
	
	def test_get_account_info(self, connection_manager):
		"""Test getting account information."""
		connection_manager.is_connected = True
		mock_account_data = [
			Mock(account='DU123456', tag='NetLiquidation', value='100000.00'),
			Mock(account='DU123456', tag='TotalCashValue', value='50000.00'),
			Mock(account='DU123456', tag='GrossPositionValue', value='50000.00')
		]
		connection_manager.ib_client.accountSummary.return_value = mock_account_data
		
		account_info = connection_manager.get_account_info()
		
		assert account_info is not None
		assert 'account' in account_info
		assert account_info['account'] == 'DU123456'
		assert 'net_liquidation' in account_info
		assert 'total_cash' in account_info
		assert 'gross_position_value' in account_info
	
	def test_get_account_info_not_connected(self):
		"""Test getting account info when not connected."""
		manager = IBConnectionManager()
		manager.is_connected = False
		
		account_info = manager.get_account_info()
		
		assert account_info is None
	
	@patch('api.services.ib_connection_manager.IBConnectionManager.get_db_session')
	def test_save_settings(self, mock_get_db):
		"""Test saving connection settings."""
		mock_db = Mock()
		mock_context = Mock()
		mock_context.__enter__ = Mock(return_value=mock_db)
		mock_context.__exit__ = Mock(return_value=None)
		mock_get_db.return_value = mock_context
		
		# Mock existing settings query
		mock_db.query.return_value.filter.return_value.first.return_value = None
		
		manager = IBConnectionManager()
		settings_dict = {
			'host': '192.168.1.100',
			'port': 4001,
			'client_id': 2,
			'account': 'DU654321',
			'market_data_type': 3,
			'auto_connect': True
		}
		
		saved = manager.save_settings(settings_dict)
		
		assert saved is True
		mock_db.add.assert_called_once()
		mock_db.commit.assert_called_once()
		assert manager.connection_settings is not None
	
	@patch('api.services.ib_connection_manager.IBConnectionManager.get_db_session')
	def test_update_existing_settings(self, mock_get_db):
		"""Test updating existing connection settings."""
		mock_db = Mock()
		mock_context = Mock()
		mock_context.__enter__ = Mock(return_value=mock_db)
		mock_context.__exit__ = Mock(return_value=None)
		mock_get_db.return_value = mock_context
		
		# Mock existing settings
		existing_settings = Mock(spec=IBSettings)
		existing_settings.host = '127.0.0.1'
		existing_settings.port = 7497
		mock_db.query.return_value.filter.return_value.first.return_value = existing_settings
		
		manager = IBConnectionManager()
		settings_dict = {
			'host': '192.168.1.100',
			'port': 4001
		}
		
		saved = manager.save_settings(settings_dict)
		
		assert saved is True
		assert existing_settings.host == '192.168.1.100'
		assert existing_settings.port == 4001
		mock_db.commit.assert_called_once()
	
	def test_encrypt_credentials(self, connection_manager):
		"""Test credential encryption."""
		password = "mySecretPassword123"
		encrypted = connection_manager.encrypt_credentials(password)
		
		assert encrypted != password
		assert len(encrypted) > 0
		assert isinstance(encrypted, str)
	
	def test_decrypt_credentials(self, connection_manager):
		"""Test credential decryption."""
		password = "mySecretPassword123"
		encrypted = connection_manager.encrypt_credentials(password)
		decrypted = connection_manager.decrypt_credentials(encrypted)
		
		assert decrypted == password
	
	def test_get_connection_status(self, connection_manager):
		"""Test getting connection status."""
		connection_manager.is_connected = True
		connection_manager.connection_settings = Mock()
		connection_manager.connection_settings.account = 'DU123456'
		connection_manager.connection_settings.host = '127.0.0.1'
		connection_manager.connection_settings.port = 7497
		
		status = connection_manager.get_connection_status()
		
		assert status['connected'] is True
		assert status['account'] == 'DU123456'
		assert status['host'] == '127.0.0.1'
		assert status['port'] == 7497
		assert 'last_check' in status
	
	def test_get_connection_status_disconnected(self):
		"""Test getting status when disconnected."""
		manager = IBConnectionManager()
		manager.is_connected = False
		
		status = manager.get_connection_status()
		
		assert status['connected'] is False
		assert status['account'] is None
		assert status['host'] is None
		assert status['port'] is None
	
	@patch('services.ib_connection_manager.asyncio.create_task')
	def test_start_health_monitor(self, mock_create_task, connection_manager):
		"""Test starting health monitor."""
		connection_manager.start_health_monitor(interval=30)
		
		mock_create_task.assert_called_once()
		assert connection_manager.health_monitor_task is not None
	
	def test_stop_health_monitor(self, connection_manager):
		"""Test stopping health monitor."""
		mock_task = Mock()
		mock_task.cancel = Mock()
		connection_manager.health_monitor_task = mock_task
		
		connection_manager.stop_health_monitor()
		
		mock_task.cancel.assert_called_once()
		assert connection_manager.health_monitor_task is None
	
	@patch('api.services.ib_connection_manager.IBConnectionManager.get_db_session')
	def test_log_connection_event(self, mock_get_db, connection_manager):
		"""Test logging connection events."""
		mock_db = Mock()
		mock_context = Mock()
		mock_context.__enter__ = Mock(return_value=mock_db)
		mock_context.__exit__ = Mock(return_value=None)
		mock_get_db.return_value = mock_context
		
		connection_manager._log_connection_event(
			event_type='connect',
			status='success',
			account='DU123456',
			error=None
		)
		
		mock_db.add.assert_called_once()
		mock_db.commit.assert_called_once()
		
		# Check the logged object
		logged_obj = mock_db.add.call_args[0][0]
		assert isinstance(logged_obj, IBConnectionLog)
		assert logged_obj.event_type == 'connect'
		assert logged_obj.status == 'success'
		assert logged_obj.account == 'DU123456'