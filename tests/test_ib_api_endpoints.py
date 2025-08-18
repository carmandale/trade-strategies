"""Tests for Interactive Brokers API endpoints."""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from api.main import app

client = TestClient(app)


class TestIBConnectionEndpoints:
	"""Test IB connection API endpoints."""
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_get_connection_status(self, mock_manager):
		"""Test GET /api/v1/ib/connection/status endpoint."""
		# Mock connection status
		mock_manager.get_connection_status.return_value = {
			'connected': True,
			'account': 'DU123456',
			'host': '127.0.0.1',
			'port': 7497,
			'last_check': datetime.now(timezone.utc).isoformat(),
			'account_info': {
				'net_liquidation': 100000.00,
				'total_cash': 50000.00,
				'buying_power': 200000.00
			}
		}
		
		response = client.get("/api/v1/ib/connection/status")
		
		assert response.status_code == 200
		data = response.json()
		assert data['connected'] is True
		assert data['account'] == 'DU123456'
		assert data['host'] == '127.0.0.1'
		assert data['port'] == 7497
		assert 'account_info' in data
		assert data['account_info']['net_liquidation'] == 100000.00
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_get_connection_status_disconnected(self, mock_manager):
		"""Test status endpoint when disconnected."""
		mock_manager.get_connection_status.return_value = {
			'connected': False,
			'account': None,
			'host': None,
			'port': None,
			'last_check': datetime.now(timezone.utc).isoformat()
		}
		
		response = client.get("/api/v1/ib/connection/status")
		
		assert response.status_code == 200
		data = response.json()
		assert data['connected'] is False
		assert data['account'] is None
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_connect_to_ib(self, mock_manager):
		"""Test POST /api/v1/ib/connection/connect endpoint."""
		mock_manager.connect.return_value = {
			"success": True,
			"message": "Connected to IB account DU123456",
			"status": {
				'connected': True,
				'account': 'DU123456',
				'host': '127.0.0.1',
				'port': 7497,
				'last_check': datetime.now(timezone.utc).isoformat()
			}
		}
		
		response = client.post("/api/v1/ib/connection/connect")
		
		assert response.status_code == 200
		data = response.json()
		assert data['success'] is True
		assert 'Connected to IB' in data['message']
		assert data['status']['connected'] is True
		mock_manager.connect.assert_called_once()
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_connect_to_ib_failure(self, mock_manager):
		"""Test connect endpoint when connection fails."""
		mock_manager.connect.return_value = {
			"success": False,
			"message": "Failed to connect to IB",
			"status": {
				'connected': False,
				'account': None,
				'host': None,
				'port': None,
				'last_check': datetime.now(timezone.utc).isoformat()
			}
		}
		
		response = client.post("/api/v1/ib/connection/connect")
		
		assert response.status_code == 500
		data = response.json()
		assert 'detail' in data
		assert 'Failed to connect' in data['detail']
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_disconnect_from_ib(self, mock_manager):
		"""Test POST /api/v1/ib/connection/disconnect endpoint."""
		mock_manager.disconnect.return_value = {
			"success": True,
			"message": "Disconnected from IB",
			"status": {
				'connected': False,
				'account': None,
				'host': None,
				'port': None,
				'last_check': datetime.now(timezone.utc).isoformat()
			}
		}
		
		response = client.post("/api/v1/ib/connection/disconnect")
		
		assert response.status_code == 200
		data = response.json()
		assert data['success'] is True
		assert 'Disconnected' in data['message']
		assert data['status']['connected'] is False
		mock_manager.disconnect.assert_called_once()
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_reconnect_to_ib(self, mock_manager):
		"""Test POST /api/v1/ib/connection/reconnect endpoint."""
		mock_manager.reconnect.return_value = {
			"success": True,
			"message": "Connected to IB account DU123456",
			"status": {
				'connected': True,
				'account': 'DU123456',
				'host': '127.0.0.1',
				'port': 7497,
				'last_check': datetime.now(timezone.utc).isoformat()
			}
		}
		
		response = client.post("/api/v1/ib/connection/reconnect")
		
		assert response.status_code == 200
		data = response.json()
		assert data['success'] is True
		assert 'Connected' in data['message']
		assert data['status']['connected'] is True
		mock_manager.reconnect.assert_called_once()
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_reconnect_to_ib_failure(self, mock_manager):
		"""Test reconnect endpoint when reconnection fails."""
		mock_manager.reconnect.return_value = {
			"success": False,
			"message": "Failed to connect to IB",
			"status": {
				'connected': False,
				'account': None,
				'host': None,
				'port': None,
				'last_check': datetime.now(timezone.utc).isoformat()
			}
		}
		
		response = client.post("/api/v1/ib/connection/reconnect")
		
		assert response.status_code == 500
		data = response.json()
		assert 'detail' in data
		assert 'Failed to connect' in data['detail']
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_check_connection_health(self, mock_manager):
		"""Test GET /api/v1/ib/connection/health endpoint."""
		mock_manager.check_connection.return_value = True
		mock_manager.is_connected = True
		
		response = client.get("/api/v1/ib/connection/health")
		
		assert response.status_code == 200
		data = response.json()
		assert data['healthy'] is True
		assert data['connected'] is True
		mock_manager.check_connection.assert_called_once()
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_check_connection_unhealthy(self, mock_manager):
		"""Test health endpoint when connection is unhealthy."""
		mock_manager.check_connection.return_value = False
		mock_manager.is_connected = False
		
		response = client.get("/api/v1/ib/connection/health")
		
		assert response.status_code == 503
		data = response.json()
		assert data['healthy'] is False
		assert data['connected'] is False
		mock_manager.check_connection.assert_called_once()


class TestIBSettingsEndpoints:
	"""Test IB settings API endpoints."""
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_get_ib_settings(self, mock_manager):
		"""Test GET /api/v1/ib/settings endpoint."""
		mock_settings = Mock()
		mock_settings.to_dict.return_value = {
			'id': 'test-id',
			'host': '127.0.0.1',
			'port': 7497,
			'client_id': 1,
			'account': 'DU123456',
			'market_data_type': 1,
			'auto_connect': False,
			'created_at': datetime.now(timezone.utc).isoformat(),
			'updated_at': datetime.now(timezone.utc).isoformat()
		}
		mock_manager.connection_settings = mock_settings
		
		response = client.get("/api/v1/ib/settings")
		
		assert response.status_code == 200
		data = response.json()
		assert data['host'] == '127.0.0.1'
		assert data['port'] == 7497
		assert data['account'] == 'DU123456'
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_get_ib_settings_not_found(self, mock_manager):
		"""Test settings endpoint when no settings exist."""
		mock_manager.connection_settings = None
		mock_manager.load_settings.return_value = None
		
		response = client.get("/api/v1/ib/settings")
		
		assert response.status_code == 404
		data = response.json()
		assert 'detail' in data
		assert 'No IB settings found' in data['detail']
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_update_ib_settings(self, mock_manager):
		"""Test PUT /api/v1/ib/settings endpoint."""
		mock_manager.save_settings.return_value = True
		
		settings_data = {
			'host': '192.168.1.100',
			'port': 4001,
			'client_id': 2,
			'account': 'DU654321',
			'market_data_type': 3,
			'auto_connect': True
		}
		
		response = client.put("/api/v1/ib/settings", json=settings_data)
		
		assert response.status_code == 200
		data = response.json()
		assert data['success'] is True
		assert data['message'] == 'Settings updated successfully'
		mock_manager.save_settings.assert_called_once_with(settings_data)
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_update_ib_settings_failure(self, mock_manager):
		"""Test settings update when save fails."""
		mock_manager.save_settings.return_value = False
		
		settings_data = {
			'host': '192.168.1.100',
			'port': 4001
		}
		
		response = client.put("/api/v1/ib/settings", json=settings_data)
		
		assert response.status_code == 500
		data = response.json()
		assert 'detail' in data
		assert 'Failed to save settings' in data['detail']
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_save_encrypted_credentials(self, mock_manager):
		"""Test POST /api/v1/ib/settings/credentials endpoint."""
		mock_manager.encrypt_credentials.return_value = 'encrypted_password_123'
		mock_manager.save_settings.return_value = True
		
		credentials_data = {
			'username': 'testuser',
			'password': 'testpass123'
		}
		
		response = client.post("/api/v1/ib/settings/credentials", json=credentials_data)
		
		assert response.status_code == 200
		data = response.json()
		assert data['success'] is True
		assert data['message'] == 'Credentials encrypted and saved'
		mock_manager.encrypt_credentials.assert_called_once_with('testpass123')
		
		# Verify save_settings was called with encrypted data
		save_call_args = mock_manager.save_settings.call_args[0][0]
		assert 'encrypted_credentials' in save_call_args
		assert save_call_args['encrypted_credentials'] == 'encrypted_password_123'


class TestIBAccountEndpoints:
	"""Test IB account information endpoints."""
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_get_account_info(self, mock_manager):
		"""Test GET /api/v1/ib/account endpoint."""
		mock_manager.is_connected = True
		mock_manager.get_account_info.return_value = {
			'account': 'DU123456',
			'net_liquidation': 100000.00,
			'total_cash': 50000.00,
			'gross_position_value': 50000.00,
			'available_funds': 45000.00,
			'buying_power': 200000.00
		}
		
		response = client.get("/api/v1/ib/account")
		
		assert response.status_code == 200
		data = response.json()
		assert data['account'] == 'DU123456'
		assert data['net_liquidation'] == 100000.00
		assert data['total_cash'] == 50000.00
		assert data['buying_power'] == 200000.00
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_get_account_info_not_connected(self, mock_manager):
		"""Test account endpoint when not connected."""
		mock_manager.is_connected = False
		
		response = client.get("/api/v1/ib/account")
		
		assert response.status_code == 503
		data = response.json()
		assert 'detail' in data
		assert 'Not connected to IB' in data['detail']
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_get_account_info_no_data(self, mock_manager):
		"""Test account endpoint when no data available."""
		mock_manager.is_connected = True
		mock_manager.get_account_info.return_value = None
		
		response = client.get("/api/v1/ib/account")
		
		assert response.status_code == 404
		data = response.json()
		assert 'detail' in data
		assert 'Account information not available' in data['detail']


class TestIBMonitoringEndpoints:
	"""Test IB monitoring endpoints."""
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_start_health_monitor(self, mock_manager):
		"""Test POST /api/v1/ib/monitor/start endpoint."""
		mock_manager.start_health_monitor.return_value = None
		
		response = client.post("/api/v1/ib/monitor/start?interval=30")
		
		assert response.status_code == 200
		data = response.json()
		assert data['success'] is True
		assert data['message'] == 'Health monitor started with interval: 30 seconds'
		mock_manager.start_health_monitor.assert_called_once_with(30)
	
	@patch('api.routers.ib_connection.ib_connection_manager')
	def test_stop_health_monitor(self, mock_manager):
		"""Test POST /api/v1/ib/monitor/stop endpoint."""
		mock_manager.stop_health_monitor.return_value = None
		
		response = client.post("/api/v1/ib/monitor/stop")
		
		assert response.status_code == 200
		data = response.json()
		assert data['success'] is True
		assert data['message'] == 'Health monitor stopped'
		mock_manager.stop_health_monitor.assert_called_once()