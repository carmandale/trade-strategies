"""WebSocket API routes for real-time strategy updates."""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timezone, date
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from services.ib_strategy_calculator import ib_strategy_calculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Connection manager for WebSocket clients
class StrategyWebSocketManager:
    """Manages WebSocket connections for real-time strategy updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.strategy_subscriptions: Dict[str, Set[WebSocket]] = {}
        self.client_subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.client_subscriptions[websocket] = set()
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all strategy subscriptions
        if websocket in self.client_subscriptions:
            for strategy_id in self.client_subscriptions[websocket]:
                if strategy_id in self.strategy_subscriptions:
                    self.strategy_subscriptions[strategy_id].discard(websocket)
                    if not self.strategy_subscriptions[strategy_id]:
                        del self.strategy_subscriptions[strategy_id]
            del self.client_subscriptions[websocket]
        
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    def subscribe_to_strategy(self, websocket: WebSocket, strategy_id: str):
        """Subscribe a client to strategy updates."""
        if strategy_id not in self.strategy_subscriptions:
            self.strategy_subscriptions[strategy_id] = set()
        
        self.strategy_subscriptions[strategy_id].add(websocket)
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].add(strategy_id)
        
        logger.info(f"Client subscribed to strategy {strategy_id}")
    
    def unsubscribe_from_strategy(self, websocket: WebSocket, strategy_id: str):
        """Unsubscribe a client from strategy updates."""
        if strategy_id in self.strategy_subscriptions:
            self.strategy_subscriptions[strategy_id].discard(websocket)
            if not self.strategy_subscriptions[strategy_id]:
                del self.strategy_subscriptions[strategy_id]
        
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].discard(strategy_id)
        
        logger.info(f"Client unsubscribed from strategy {strategy_id}")
    
    async def broadcast_to_strategy(self, strategy_id: str, data: Dict[str, Any]):
        """Broadcast data to all clients subscribed to a strategy."""
        if strategy_id not in self.strategy_subscriptions:
            return
        
        message = json.dumps(data)
        disconnected_clients = []
        
        for websocket in self.strategy_subscriptions[strategy_id]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {str(e)}")
                disconnected_clients.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            self.disconnect(websocket)
    
    async def send_to_client(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send data to a specific client."""
        try:
            message = json.dumps(data)
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket client: {str(e)}")
            self.disconnect(websocket)

# Global WebSocket manager instance
websocket_manager = StrategyWebSocketManager()

@router.websocket("/strategies")
async def websocket_strategies_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time strategy updates.
    
    Protocol:
    - Client connects to /ws/strategies
    - Client sends subscription messages: {"action": "subscribe", "strategy_params": {...}}
    - Server sends real-time updates: {"type": "strategy_update", "data": {...}}
    - Client can unsubscribe: {"action": "unsubscribe", "strategy_id": "..."}
    """
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "subscribe":
                await handle_strategy_subscription(websocket, message)
            elif action == "unsubscribe":
                await handle_strategy_unsubscription(websocket, message)
            elif action == "ping":
                await websocket_manager.send_to_client(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            else:
                await websocket_manager.send_to_client(websocket, {
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_manager.disconnect(websocket)

async def handle_strategy_subscription(websocket: WebSocket, message: Dict[str, Any]):
    """Handle client subscription to strategy updates."""
    try:
        strategy_params = message.get("strategy_params", {})
        
        # Validate required parameters
        required_params = ["symbol", "expiration", "strategy_type"]
        missing_params = [p for p in required_params if p not in strategy_params]
        if missing_params:
            await websocket_manager.send_to_client(websocket, {
                "type": "error",
                "message": f"Missing required parameters: {', '.join(missing_params)}"
            })
            return
        
        # Parse strategy parameters
        symbol = strategy_params["symbol"]
        expiration_str = strategy_params["expiration"]
        strategy_type = strategy_params["strategy_type"]
        
        try:
            expiration = datetime.fromisoformat(expiration_str.replace('Z', '+00:00')).date()
        except ValueError:
            await websocket_manager.send_to_client(websocket, {
                "type": "error", 
                "message": "Invalid expiration date format. Use ISO format."
            })
            return
        
        # Generate strategy ID for subscription tracking
        strategy_id = f"{strategy_type}_{symbol}_{expiration}"
        
        # Subscribe client to strategy updates
        websocket_manager.subscribe_to_strategy(websocket, strategy_id)
        
        # Send initial calculation
        if strategy_type == "iron_condor":
            await send_iron_condor_update(websocket, strategy_id, strategy_params, expiration)
        elif strategy_type == "bull_call_spread":
            await send_bull_call_spread_update(websocket, strategy_id, strategy_params, expiration)
        else:
            await websocket_manager.send_to_client(websocket, {
                "type": "error",
                "message": f"Unsupported strategy type: {strategy_type}"
            })
            return
        
        # Start periodic updates for this strategy
        asyncio.create_task(periodic_strategy_updates(strategy_id, strategy_params, expiration))
        
        await websocket_manager.send_to_client(websocket, {
            "type": "subscription_confirmed",
            "strategy_id": strategy_id,
            "update_frequency": 5
        })
    
    except Exception as e:
        logger.error(f"Error handling strategy subscription: {str(e)}")
        await websocket_manager.send_to_client(websocket, {
            "type": "error",
            "message": "Failed to subscribe to strategy updates"
        })

async def handle_strategy_unsubscription(websocket: WebSocket, message: Dict[str, Any]):
    """Handle client unsubscription from strategy updates."""
    try:
        strategy_id = message.get("strategy_id")
        if not strategy_id:
            await websocket_manager.send_to_client(websocket, {
                "type": "error",
                "message": "Missing strategy_id for unsubscription"
            })
            return
        
        websocket_manager.unsubscribe_from_strategy(websocket, strategy_id)
        
        await websocket_manager.send_to_client(websocket, {
            "type": "unsubscription_confirmed",
            "strategy_id": strategy_id
        })
    
    except Exception as e:
        logger.error(f"Error handling strategy unsubscription: {str(e)}")
        await websocket_manager.send_to_client(websocket, {
            "type": "error",
            "message": "Failed to unsubscribe from strategy updates"
        })

async def send_iron_condor_update(websocket: WebSocket, strategy_id: str, 
                                  strategy_params: Dict[str, Any], expiration: date):
    """Send Iron Condor strategy update to client."""
    try:
        # Extract Iron Condor parameters
        symbol = strategy_params["symbol"]
        put_short_strike = strategy_params.get("put_short_strike")
        put_long_strike = strategy_params.get("put_long_strike")
        call_short_strike = strategy_params.get("call_short_strike")
        call_long_strike = strategy_params.get("call_long_strike")
        contracts = strategy_params.get("contracts", 1)
        
        if not all([put_short_strike, put_long_strike, call_short_strike, call_long_strike]):
            await websocket_manager.send_to_client(websocket, {
                "type": "error",
                "message": "Missing Iron Condor strike prices"
            })
            return
        
        # Calculate Iron Condor with live updates enabled
        result = ib_strategy_calculator.calculate_iron_condor(
            symbol=symbol,
            expiration=expiration,
            put_short_strike=put_short_strike,
            put_long_strike=put_long_strike,
            call_short_strike=call_short_strike,
            call_long_strike=call_long_strike,
            contracts=contracts,
            include_live_updates=True
        )
        
        # Send update to client
        await websocket_manager.send_to_client(websocket, {
            "type": "strategy_update",
            "strategy_id": strategy_id,
            "data": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error sending Iron Condor update: {str(e)}")
        await websocket_manager.send_to_client(websocket, {
            "type": "error",
            "message": f"Failed to calculate Iron Condor: {str(e)}"
        })

async def send_bull_call_spread_update(websocket: WebSocket, strategy_id: str,
                                       strategy_params: Dict[str, Any], expiration: date):
    """Send Bull Call Spread strategy update to client."""
    try:
        # Extract Bull Call Spread parameters
        symbol = strategy_params["symbol"]
        long_strike = strategy_params.get("long_strike")
        short_strike = strategy_params.get("short_strike") 
        contracts = strategy_params.get("contracts", 1)
        
        if not all([long_strike, short_strike]):
            await websocket_manager.send_to_client(websocket, {
                "type": "error",
                "message": "Missing Bull Call Spread strike prices"
            })
            return
        
        # Calculate Bull Call Spread
        result = ib_strategy_calculator.calculate_bull_call_spread(
            symbol=symbol,
            expiration=expiration,
            long_strike=long_strike,
            short_strike=short_strike,
            contracts=contracts
        )
        
        # Add live update metadata
        result.update({
            "subscription_id": strategy_id,
            "update_frequency": 5,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "live_updates_enabled": True
        })
        
        # Send update to client
        await websocket_manager.send_to_client(websocket, {
            "type": "strategy_update",
            "strategy_id": strategy_id,
            "data": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error sending Bull Call Spread update: {str(e)}")
        await websocket_manager.send_to_client(websocket, {
            "type": "error",
            "message": f"Failed to calculate Bull Call Spread: {str(e)}"
        })

async def periodic_strategy_updates(strategy_id: str, strategy_params: Dict[str, Any], 
                                    expiration: date, update_interval: int = 5):
    """Send periodic updates for a subscribed strategy."""
    try:
        while strategy_id in websocket_manager.strategy_subscriptions:
            await asyncio.sleep(update_interval)
            
            # Check if anyone is still subscribed
            if strategy_id not in websocket_manager.strategy_subscriptions:
                break
            
            # Calculate and broadcast updated strategy data
            strategy_type = strategy_params["strategy_type"]
            
            try:
                if strategy_type == "iron_condor":
                    result = ib_strategy_calculator.calculate_iron_condor(
                        symbol=strategy_params["symbol"],
                        expiration=expiration,
                        put_short_strike=strategy_params["put_short_strike"],
                        put_long_strike=strategy_params["put_long_strike"],
                        call_short_strike=strategy_params["call_short_strike"],
                        call_long_strike=strategy_params["call_long_strike"],
                        contracts=strategy_params.get("contracts", 1),
                        include_live_updates=True
                    )
                elif strategy_type == "bull_call_spread":
                    result = ib_strategy_calculator.calculate_bull_call_spread(
                        symbol=strategy_params["symbol"],
                        expiration=expiration,
                        long_strike=strategy_params["long_strike"],
                        short_strike=strategy_params["short_strike"],
                        contracts=strategy_params.get("contracts", 1)
                    )
                    # Add live update metadata for Bull Call Spread
                    result.update({
                        "subscription_id": strategy_id,
                        "update_frequency": update_interval,
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "live_updates_enabled": True
                    })
                else:
                    continue
                
                # Broadcast to all subscribers
                await websocket_manager.broadcast_to_strategy(strategy_id, {
                    "type": "strategy_update",
                    "strategy_id": strategy_id,
                    "data": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            except Exception as e:
                logger.error(f"Error in periodic update for {strategy_id}: {str(e)}")
                # Send error to subscribers
                await websocket_manager.broadcast_to_strategy(strategy_id, {
                    "type": "update_error",
                    "strategy_id": strategy_id,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    except Exception as e:
        logger.error(f"Error in periodic updates task for {strategy_id}: {str(e)}")

# Health check endpoint for WebSocket service
@router.get("/health")
async def websocket_health_check():
    """Health check endpoint for WebSocket service."""
    return {
        "status": "healthy",
        "service": "websocket_strategies",
        "active_connections": len(websocket_manager.active_connections),
        "active_subscriptions": len(websocket_manager.strategy_subscriptions),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }