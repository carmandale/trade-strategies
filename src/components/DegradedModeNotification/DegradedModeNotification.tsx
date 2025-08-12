import React, { useState, useEffect } from 'react';
import { AlertTriangle, X, Settings, RefreshCw, WifiOff } from 'lucide-react';
import { ibConnectionApi, ConnectionStatus } from '../../api/ib-connection';

interface DegradedModeNotificationProps {
	/** Whether to show the notification */
	isVisible?: boolean;
	/** Auto-check IB connection status */
	autoCheck?: boolean;
	/** Check interval in milliseconds (default: 10000) */
	checkInterval?: number;
	/** Allow user to dismiss the notification */
	dismissible?: boolean;
	/** Position of the notification */
	position?: 'top' | 'bottom';
	/** Custom className */
	className?: string;
	/** Callback when notification is dismissed */
	onDismiss?: () => void;
	/** Callback when user clicks to configure IB settings */
	onConfigureSettings?: () => void;
}

export const DegradedModeNotification: React.FC<DegradedModeNotificationProps> = ({
	isVisible = true,
	autoCheck = true,
	checkInterval = 10000,
	dismissible = true,
	position = 'top',
	className = '',
	onDismiss,
	onConfigureSettings
}) => {
	const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({ connected: false });
	const [isDismissed, setIsDismissed] = useState(false);
	const [isChecking, setIsChecking] = useState(false);
	const [lastChecked, setLastChecked] = useState<Date | null>(null);

	// Check IB connection status
	const checkConnectionStatus = async () => {
		try {
			setIsChecking(true);
			const status = await ibConnectionApi.getConnectionStatus();
			setConnectionStatus(status);
			setLastChecked(new Date());
		} catch (error) {
			console.error('Failed to check IB connection status:', error);
			setConnectionStatus({ 
				connected: false, 
				error: 'Unable to check connection status' 
			});
		} finally {
			setIsChecking(false);
		}
	};

	// Auto-check connection status
	useEffect(() => {
		if (autoCheck) {
			checkConnectionStatus();
			const interval = setInterval(checkConnectionStatus, checkInterval);
			return () => clearInterval(interval);
		}
	}, [autoCheck, checkInterval]);

	const handleDismiss = () => {
		setIsDismissed(true);
		onDismiss?.();
	};

	const handleRetryConnection = async () => {
		try {
			setIsChecking(true);
			await ibConnectionApi.connect();
			await checkConnectionStatus();
		} catch (error) {
			console.error('Failed to reconnect to IB:', error);
		} finally {
			setIsChecking(false);
		}
	};

	// Don't show if dismissed or IB is connected
	if (!isVisible || isDismissed || connectionStatus.connected) {
		return null;
	}

	const positionClasses = position === 'top' 
		? 'top-4 left-1/2 transform -translate-x-1/2' 
		: 'bottom-4 left-1/2 transform -translate-x-1/2';

	return (
		<div className={`fixed ${positionClasses} z-50 max-w-md w-full mx-4 ${className}`}>
			<div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg shadow-lg p-4">
				<div className="flex items-start gap-3">
					{/* Icon */}
					<div className="flex-shrink-0">
						<AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
					</div>

					{/* Content */}
					<div className="flex-1 min-w-0">
						<h3 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200 mb-1">
							Degraded Mode Active
						</h3>
						<p className="text-sm text-yellow-700 dark:text-yellow-300 mb-3">
							Interactive Brokers connection unavailable. Using estimated option prices and Greeks instead of real-time data.
						</p>

						{/* Connection details */}
						{connectionStatus.error && (
							<div className="text-xs text-yellow-600 dark:text-yellow-400 mb-3 flex items-center gap-2">
								<WifiOff size={12} />
								<span>{connectionStatus.error}</span>
							</div>
						)}

						{/* Action buttons */}
						<div className="flex items-center gap-2">
							<button
								onClick={handleRetryConnection}
								disabled={isChecking}
								className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-yellow-800 dark:text-yellow-200 bg-yellow-100 dark:bg-yellow-800 hover:bg-yellow-200 dark:hover:bg-yellow-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
							>
								{isChecking ? (
									<>
										<RefreshCw className="w-3 h-3 animate-spin" />
										<span>Checking...</span>
									</>
								) : (
									<>
										<RefreshCw className="w-3 h-3" />
										<span>Retry Connection</span>
									</>
								)}
							</button>

							{onConfigureSettings && (
								<button
									onClick={onConfigureSettings}
									className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-yellow-800 dark:text-yellow-200 bg-yellow-100 dark:bg-yellow-800 hover:bg-yellow-200 dark:hover:bg-yellow-700 rounded-md transition-colors"
								>
									<Settings className="w-3 h-3" />
									<span>Settings</span>
								</button>
							)}
						</div>

						{/* Last checked timestamp */}
						{lastChecked && (
							<div className="text-xs text-yellow-600 dark:text-yellow-400 mt-2">
								Last checked: {lastChecked.toLocaleTimeString()}
							</div>
						)}
					</div>

					{/* Dismiss button */}
					{dismissible && (
						<button
							onClick={handleDismiss}
							className="flex-shrink-0 text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200 transition-colors"
							aria-label="Dismiss notification"
						>
							<X className="w-4 h-4" />
						</button>
					)}
				</div>
			</div>
		</div>
	);
};

// Context provider for degraded mode state management
interface DegradedModeContextValue {
	isDegradedMode: boolean;
	connectionStatus: ConnectionStatus;
	showNotification: boolean;
	dismissNotification: () => void;
	checkConnection: () => Promise<void>;
}

const DegradedModeContext = React.createContext<DegradedModeContextValue | null>(null);

export const DegradedModeProvider: React.FC<{ 
	children: React.ReactNode;
	checkInterval?: number;
}> = ({ children, checkInterval = 15000 }) => {
	const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({ connected: false });
	const [showNotification, setShowNotification] = useState(false);

	const checkConnection = async () => {
		try {
			const status = await ibConnectionApi.getConnectionStatus();
			setConnectionStatus(status);
			
			// Show notification if IB is disconnected
			setShowNotification(!status.connected);
		} catch (error) {
			console.error('Failed to check IB connection:', error);
			setConnectionStatus({ connected: false, error: 'Connection check failed' });
			setShowNotification(true);
		}
	};

	useEffect(() => {
		checkConnection();
		const interval = setInterval(checkConnection, checkInterval);
		return () => clearInterval(interval);
	}, [checkInterval]);

	const dismissNotification = () => {
		setShowNotification(false);
	};

	const value: DegradedModeContextValue = {
		isDegradedMode: !connectionStatus.connected,
		connectionStatus,
		showNotification,
		dismissNotification,
		checkConnection
	};

	return (
		<DegradedModeContext.Provider value={value}>
			{children}
		</DegradedModeContext.Provider>
	);
};

// Hook to use degraded mode context
export const useDegradedMode = (): DegradedModeContextValue => {
	const context = React.useContext(DegradedModeContext);
	if (!context) {
		throw new Error('useDegradedMode must be used within a DegradedModeProvider');
	}
	return context;
};

// Simple banner component for inline use
export const DegradedModeBanner: React.FC<{
	className?: string;
	showRetry?: boolean;
	onRetry?: () => void;
}> = ({ className = '', showRetry = true, onRetry }) => {
	const [isVisible, setIsVisible] = useState(false);
	const [isConnected, setIsConnected] = useState(false);

	useEffect(() => {
		const checkStatus = async () => {
			try {
				const status = await ibConnectionApi.getConnectionStatus();
				setIsConnected(status.connected);
				setIsVisible(!status.connected);
			} catch {
				setIsConnected(false);
				setIsVisible(true);
			}
		};

		checkStatus();
		const interval = setInterval(checkStatus, 10000);
		return () => clearInterval(interval);
	}, []);

	if (!isVisible || isConnected) {
		return null;
	}

	return (
		<div className={`bg-yellow-100 dark:bg-yellow-900/20 border-l-4 border-yellow-500 p-3 ${className}`}>
			<div className="flex items-center justify-between">
				<div className="flex items-center gap-2">
					<AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
					<span className="text-sm text-yellow-800 dark:text-yellow-200">
						Using estimated data - IB connection unavailable
					</span>
				</div>
				{showRetry && (
					<button
						onClick={onRetry}
						className="text-xs text-yellow-700 dark:text-yellow-300 hover:text-yellow-900 dark:hover:text-yellow-100 underline"
					>
						Retry
					</button>
				)}
			</div>
		</div>
	);
};