import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, AlertCircle, Activity } from 'lucide-react';
import { ibConnectionApi, ConnectionStatus } from '../../api/ib-connection';

interface ConnectionStatusIndicatorProps {
	/** Polling interval in milliseconds (default: 5000) */
	pollingInterval?: number;
	/** Show detailed status text */
	showDetails?: boolean;
	/** Compact mode for navbar/header display */
	compact?: boolean;
	/** Custom className for styling */
	className?: string;
}

export const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({
	pollingInterval = 5000,
	showDetails = true,
	compact = false,
	className = ''
}) => {
	const [status, setStatus] = useState<ConnectionStatus>({ connected: false });
	const [isChecking, setIsChecking] = useState(false);
	const [lastChecked, setLastChecked] = useState<Date | null>(null);

	useEffect(() => {
		// Initial check
		checkStatus();

		// Set up polling
		const interval = setInterval(checkStatus, pollingInterval);

		return () => clearInterval(interval);
	}, [pollingInterval]);

	const checkStatus = async () => {
		try {
			setIsChecking(true);
			const connectionStatus = await ibConnectionApi.getConnectionStatus();
			setStatus(connectionStatus);
			setLastChecked(new Date());
		} catch (error) {
			console.error('Failed to check IB connection status:', error);
			setStatus({ 
				connected: false, 
				error: 'Unable to check connection status' 
			});
		} finally {
			setIsChecking(false);
		}
	};

	const getStatusColor = () => {
		if (status.connected) return 'text-green-500';
		if (status.error) return 'text-red-500';
		return 'text-gray-400';
	};

	const getStatusIcon = () => {
		if (isChecking) {
			return <Activity className="animate-pulse" size={compact ? 16 : 20} />;
		}
		if (status.connected) {
			return <Wifi size={compact ? 16 : 20} />;
		}
		if (status.error) {
			return <AlertCircle size={compact ? 16 : 20} />;
		}
		return <WifiOff size={compact ? 16 : 20} />;
	};

	const getStatusText = () => {
		if (status.connected) {
			if (status.account_info) {
				return `IB Connected (${status.account_info.account_id})`;
			}
			return 'IB Connected';
		}
		if (status.error) {
			return 'IB Connection Error';
		}
		return 'IB Disconnected';
	};

	const getDetailedStatus = () => {
		if (!showDetails || compact) return null;

		const details = [];
		
		if (status.connected && status.host && status.port) {
			details.push(`${status.host}:${status.port}`);
		}
		
		if (status.account_info?.account_type) {
			details.push(status.account_info.account_type);
		}
		
		if (status.last_heartbeat) {
			const heartbeat = new Date(status.last_heartbeat);
			const now = new Date();
			const secondsAgo = Math.floor((now.getTime() - heartbeat.getTime()) / 1000);
			
			if (secondsAgo < 60) {
				details.push(`Active ${secondsAgo}s ago`);
			} else {
				details.push(`Active ${Math.floor(secondsAgo / 60)}m ago`);
			}
		}
		
		if (status.error && !status.connected) {
			details.push(status.error);
		}
		
		return details.length > 0 ? details.join(' • ') : null;
	};

	if (compact) {
		return (
			<div 
				className={`flex items-center gap-2 ${className}`}
				title={getStatusText()}
			>
				<span className={getStatusColor()}>
					{getStatusIcon()}
				</span>
				{!compact && (
					<span className="text-sm font-medium">
						{status.connected ? 'IB' : ''}
					</span>
				)}
			</div>
		);
	}

	return (
		<div className={`flex flex-col ${className}`}>
			<div className="flex items-center gap-2">
				<span className={getStatusColor()}>
					{getStatusIcon()}
				</span>
				<span className={`font-medium ${status.connected ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'}`}>
					{getStatusText()}
				</span>
			</div>
			{showDetails && getDetailedStatus() && (
				<div className="ml-7 text-sm text-gray-500 dark:text-gray-400">
					{getDetailedStatus()}
				</div>
			)}
		</div>
	);
};

// Mini indicator for use in headers/navbars
export const ConnectionStatusBadge: React.FC<{ className?: string }> = ({ className = '' }) => {
	const [connected, setConnected] = useState(false);

	useEffect(() => {
		const checkConnection = async () => {
			try {
				const status = await ibConnectionApi.getConnectionStatus();
				setConnected(status.connected);
			} catch {
				setConnected(false);
			}
		};

		checkConnection();
		const interval = setInterval(checkConnection, 10000);
		return () => clearInterval(interval);
	}, []);

	if (!connected) return null;

	return (
		<div className={`flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900 rounded-full ${className}`}>
			<div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
			<span className="text-xs font-medium text-green-700 dark:text-green-300">IB Live</span>
		</div>
	);
};