import { useState, useEffect, useRef, useCallback } from 'react';

export interface WebSocketMessage {
	type: 'strategy_update' | 'subscription_confirmed' | 'unsubscription_confirmed' | 'error' | 'pong' | 'update_error';
	strategy_id?: string;
	data?: any;
	message?: string;
	error?: string;
	timestamp?: string;
	update_frequency?: number;
}

export interface StrategySubscription {
	symbol: string;
	expiration: string;
	strategy_type: 'iron_condor' | 'bull_call_spread';
	put_short_strike?: number;
	put_long_strike?: number;
	call_short_strike?: number;
	call_long_strike?: number;
	long_strike?: number;
	short_strike?: number;
	contracts?: number;
}

interface UseStrategyWebSocketOptions {
	/** WebSocket server URL */
	url?: string;
	/** Auto-reconnect on disconnect (default: true) */
	autoReconnect?: boolean;
	/** Reconnect delay in milliseconds (default: 3000) */
	reconnectDelay?: number;
	/** Maximum reconnect attempts (default: 5) */
	maxReconnectAttempts?: number;
	/** Heartbeat interval in milliseconds (default: 30000) */
	heartbeatInterval?: number;
	/** Enable console logging (default: false) */
	debug?: boolean;
}

interface UseStrategyWebSocketReturn {
	/** Current connection state */
	isConnected: boolean;
	/** Current connection status */
	connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
	/** Last received strategy update */
	lastUpdate: any | null;
	/** Last error message */
	error: string | null;
	/** Subscribe to a strategy */
	subscribe: (params: StrategySubscription) => void;
	/** Unsubscribe from a strategy */
	unsubscribe: (strategyId: string) => void;
	/** Manually connect to WebSocket */
	connect: () => void;
	/** Manually disconnect from WebSocket */
	disconnect: () => void;
	/** Active strategy subscriptions */
	activeSubscriptions: Set<string>;
}

const DEFAULT_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/strategies';

export const useStrategyWebSocket = (options: UseStrategyWebSocketOptions = {}): UseStrategyWebSocketReturn => {
	const {
		url = DEFAULT_WS_URL,
		autoReconnect = true,
		reconnectDelay = 3000,
		maxReconnectAttempts = 5,
		heartbeatInterval = 30000,
		debug = false
	} = options;

	const [isConnected, setIsConnected] = useState(false);
	const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
	const [lastUpdate, setLastUpdate] = useState<any | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [activeSubscriptions, setActiveSubscriptions] = useState<Set<string>>(new Set());

	const wsRef = useRef<WebSocket | null>(null);
	const reconnectAttemptRef = useRef(0);
	const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
	const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
	const messageQueueRef = useRef<any[]>([]);

	const log = useCallback((message: string, data?: any) => {
		if (debug) {
			console.log(`[WebSocket] ${message}`, data || '');
		}
	}, [debug]);

	const sendMessage = useCallback((message: any) => {
		if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
			wsRef.current.send(JSON.stringify(message));
			log('Sent message:', message);
		} else {
			// Queue message if not connected
			messageQueueRef.current.push(message);
			log('Queued message (not connected):', message);
		}
	}, [log]);

	const processMessageQueue = useCallback(() => {
		while (messageQueueRef.current.length > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
			const message = messageQueueRef.current.shift();
			sendMessage(message);
		}
	}, [sendMessage]);

	const startHeartbeat = useCallback(() => {
		stopHeartbeat();
		heartbeatIntervalRef.current = setInterval(() => {
			sendMessage({ action: 'ping' });
		}, heartbeatInterval);
		log('Heartbeat started');
	}, [heartbeatInterval, sendMessage, log]);

	const stopHeartbeat = useCallback(() => {
		if (heartbeatIntervalRef.current) {
			clearInterval(heartbeatIntervalRef.current);
			heartbeatIntervalRef.current = null;
			log('Heartbeat stopped');
		}
	}, [log]);

	const handleMessage = useCallback((event: MessageEvent) => {
		try {
			const message: WebSocketMessage = JSON.parse(event.data);
			log('Received message:', message);

			switch (message.type) {
				case 'strategy_update':
					setLastUpdate(message.data);
					setError(null);
					break;

				case 'subscription_confirmed':
					if (message.strategy_id) {
						setActiveSubscriptions(prev => new Set(prev).add(message.strategy_id!));
					}
					break;

				case 'unsubscription_confirmed':
					if (message.strategy_id) {
						setActiveSubscriptions(prev => {
							const newSet = new Set(prev);
							newSet.delete(message.strategy_id!);
							return newSet;
						});
					}
					break;

				case 'error':
				case 'update_error':
					setError(message.message || message.error || 'Unknown error');
					break;

				case 'pong':
					// Heartbeat response received
					break;

				default:
					log('Unknown message type:', message.type);
			}
		} catch (err) {
			console.error('Failed to parse WebSocket message:', err);
		}
	}, [log]);

	const connect = useCallback(() => {
		if (wsRef.current?.readyState === WebSocket.OPEN) {
			log('Already connected');
			return;
		}

		setConnectionStatus('connecting');
		setError(null);

		try {
			wsRef.current = new WebSocket(url);
			log('Connecting to:', url);

			wsRef.current.onopen = () => {
				log('Connected');
				setIsConnected(true);
				setConnectionStatus('connected');
				setError(null);
				reconnectAttemptRef.current = 0;
				
				// Process any queued messages
				processMessageQueue();
				
				// Start heartbeat
				startHeartbeat();
			};

			wsRef.current.onmessage = handleMessage;

			wsRef.current.onerror = (event) => {
				console.error('WebSocket error:', event);
				setError('WebSocket connection error');
				setConnectionStatus('error');
			};

			wsRef.current.onclose = (event) => {
				log('Disconnected', { code: event.code, reason: event.reason });
				setIsConnected(false);
				setConnectionStatus('disconnected');
				stopHeartbeat();

				// Clear subscriptions on disconnect
				setActiveSubscriptions(new Set());

				// Auto-reconnect logic
				if (autoReconnect && reconnectAttemptRef.current < maxReconnectAttempts) {
					reconnectAttemptRef.current++;
					log(`Reconnecting... (attempt ${reconnectAttemptRef.current}/${maxReconnectAttempts})`);
					
					reconnectTimeoutRef.current = setTimeout(() => {
						connect();
					}, reconnectDelay);
				} else if (reconnectAttemptRef.current >= maxReconnectAttempts) {
					setError(`Failed to reconnect after ${maxReconnectAttempts} attempts`);
					setConnectionStatus('error');
				}
			};
		} catch (err) {
			console.error('Failed to create WebSocket:', err);
			setError('Failed to create WebSocket connection');
			setConnectionStatus('error');
		}
	}, [url, autoReconnect, reconnectDelay, maxReconnectAttempts, handleMessage, processMessageQueue, startHeartbeat, stopHeartbeat, log]);

	const disconnect = useCallback(() => {
		log('Disconnecting...');
		
		// Clear reconnect timeout
		if (reconnectTimeoutRef.current) {
			clearTimeout(reconnectTimeoutRef.current);
			reconnectTimeoutRef.current = null;
		}

		// Stop heartbeat
		stopHeartbeat();

		// Close WebSocket
		if (wsRef.current) {
			wsRef.current.close();
			wsRef.current = null;
		}

		setIsConnected(false);
		setConnectionStatus('disconnected');
		setActiveSubscriptions(new Set());
		reconnectAttemptRef.current = 0;
	}, [stopHeartbeat, log]);

	const subscribe = useCallback((params: StrategySubscription) => {
		const message = {
			action: 'subscribe',
			strategy_params: params
		};
		sendMessage(message);
		log('Subscribing to strategy:', params);
	}, [sendMessage, log]);

	const unsubscribe = useCallback((strategyId: string) => {
		const message = {
			action: 'unsubscribe',
			strategy_id: strategyId
		};
		sendMessage(message);
		log('Unsubscribing from strategy:', strategyId);
	}, [sendMessage, log]);

	// Auto-connect on mount if desired
	useEffect(() => {
		connect();

		return () => {
			disconnect();
		};
	}, []); // Only run on mount/unmount

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			if (reconnectTimeoutRef.current) {
				clearTimeout(reconnectTimeoutRef.current);
			}
			if (heartbeatIntervalRef.current) {
				clearInterval(heartbeatIntervalRef.current);
			}
		};
	}, []);

	return {
		isConnected,
		connectionStatus,
		lastUpdate,
		error,
		subscribe,
		unsubscribe,
		connect,
		disconnect,
		activeSubscriptions
	};
};