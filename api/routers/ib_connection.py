"""Interactive Brokers connection API endpoints."""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from api.services.ib_connection_manager import ib_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ib", tags=["Interactive Brokers"])


# Request/Response Models
class ConnectionResponse(BaseModel):
	"""Connection operation response."""
	success: bool
	message: str
	status: Dict[str, Any]


class HealthResponse(BaseModel):
	"""Health check response."""
	healthy: bool
	connected: bool
	message: Optional[str] = None


class SettingsUpdate(BaseModel):
	"""IB connection settings update."""
	host: Optional[str] = None
	port: Optional[int] = None
	client_id: Optional[int] = None
	account: Optional[str] = None
	market_data_type: Optional[int] = None
	auto_connect: Optional[bool] = None


class CredentialsUpdate(BaseModel):
	"""IB credentials update."""
	username: str
	password: str


class MonitorResponse(BaseModel):
	"""Monitor operation response."""
	success: bool
	message: str


# Connection Management Endpoints
@router.get("/connection/status")
async def get_connection_status():
	"""Get current IB connection status.
	
	Returns:
		Current connection status including account info if connected
	"""
	try:
		status = ib_connection_manager.get_connection_status()
		return status
	except Exception as e:
		logger.error(f"Error getting connection status: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/connection/connect", response_model=ConnectionResponse)
async def connect_to_ib():
	"""Connect to Interactive Brokers.
	
	Returns:
		Connection response with status
	"""
	try:
		result = ib_connection_manager.connect()
		
		if result["success"]:
			return ConnectionResponse(
				success=True,
				message=result["message"],
				status=result["status"]
			)
		else:
			raise HTTPException(
				status_code=500, 
				detail=result["message"]
			)
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Connection error: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/connection/disconnect", response_model=ConnectionResponse)
async def disconnect_from_ib():
	"""Disconnect from Interactive Brokers.
	
	Returns:
		Disconnection response with status
	"""
	try:
		result = ib_connection_manager.disconnect()
		
		return ConnectionResponse(
			success=result["success"],
			message=result["message"],
			status=result["status"]
		)
	except Exception as e:
		logger.error(f"Disconnection error: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/connection/reconnect", response_model=ConnectionResponse)
async def reconnect_to_ib():
	"""Reconnect to Interactive Brokers.
	
	Returns:
		Reconnection response with status
	"""
	try:
		result = ib_connection_manager.reconnect()
		
		if result["success"]:
			return ConnectionResponse(
				success=True,
				message=result["message"],
				status=result["status"]
			)
		else:
			raise HTTPException(
				status_code=500,
				detail=result["message"]
			)
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Reconnection error: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/connection/health", response_model=HealthResponse)
async def check_connection_health():
	"""Check IB connection health.
	
	Returns:
		Health status of the connection
	"""
	try:
		is_healthy = ib_connection_manager.check_connection()
		is_connected = ib_connection_manager.is_connected
		
		if is_healthy:
			return HealthResponse(
				healthy=True,
				connected=is_connected,
				message="Connection is healthy"
			)
		else:
			raise HTTPException(
				status_code=503,
				detail="Connection is unhealthy",
				headers={"Retry-After": "30"}
			)
	except HTTPException:
		# Return the health status even if unhealthy
		return HealthResponse(
			healthy=False,
			connected=False,
			message="Connection is unhealthy"
		)
	except Exception as e:
		logger.error(f"Health check error: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


# Settings Management Endpoints
@router.get("/settings")
async def get_ib_settings():
	"""Get current IB connection settings.
	
	Returns:
		Current connection settings
	"""
	try:
		settings = ib_connection_manager.connection_settings
		
		if not settings:
			# Try to load from database
			settings = ib_connection_manager.load_settings()
		
		if settings:
			return settings.to_dict()
		else:
			raise HTTPException(status_code=404, detail="No IB settings found")
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting settings: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_ib_settings(settings: SettingsUpdate):
	"""Update IB connection settings.
	
	Args:
		settings: New settings to apply
	
	Returns:
		Success response
	"""
	try:
		# Convert to dict and remove None values
		settings_dict = {k: v for k, v in settings.model_dump().items() if v is not None}
		
		success = ib_connection_manager.save_settings(settings_dict)
		
		if success:
			return {
				"success": True,
				"message": "Settings updated successfully"
			}
		else:
			raise HTTPException(status_code=500, detail="Failed to save settings")
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error updating settings: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/credentials")
async def save_encrypted_credentials(credentials: CredentialsUpdate):
	"""Save encrypted IB credentials.
	
	Args:
		credentials: Username and password to encrypt and save
	
	Returns:
		Success response
	"""
	try:
		# Encrypt the password
		encrypted = ib_connection_manager.encrypt_credentials(credentials.password)
		
		# Save to settings
		success = ib_connection_manager.save_settings({
			'encrypted_credentials': encrypted
		})
		
		if success:
			return {
				"success": True,
				"message": "Credentials encrypted and saved"
			}
		else:
			raise HTTPException(status_code=500, detail="Failed to save credentials")
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error saving credentials: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


# Account Information Endpoints
@router.get("/account")
async def get_account_info():
	"""Get IB account information.
	
	Returns:
		Account details including balances and positions
	"""
	try:
		if not ib_connection_manager.is_connected:
			raise HTTPException(status_code=503, detail="Not connected to IB")
		
		account_info = ib_connection_manager.get_account_info()
		
		if account_info:
			return account_info
		else:
			raise HTTPException(status_code=404, detail="Account information not available")
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting account info: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


# Monitoring Endpoints
@router.post("/monitor/start", response_model=MonitorResponse)
async def start_health_monitor(interval: int = Query(default=60, ge=10, le=300)):
	"""Start health monitoring for IB connection.
	
	Args:
		interval: Check interval in seconds (10-300)
	
	Returns:
		Success response
	"""
	try:
		ib_connection_manager.start_health_monitor(interval)
		
		return MonitorResponse(
			success=True,
			message=f"Health monitor started with interval: {interval} seconds"
		)
	except Exception as e:
		logger.error(f"Error starting health monitor: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/stop", response_model=MonitorResponse)
async def stop_health_monitor():
	"""Stop health monitoring for IB connection.
	
	Returns:
		Success response
	"""
	try:
		ib_connection_manager.stop_health_monitor()
		
		return MonitorResponse(
			success=True,
			message="Health monitor stopped"
		)
	except Exception as e:
		logger.error(f"Error stopping health monitor: {str(e)}")
		raise HTTPException(status_code=500, detail=str(e))