import React, { useEffect, useState } from 'react';
import { useStrategyWebSocket, StrategySubscription } from '../../hooks/useStrategyWebSocket';
import { GreeksDisplay, Greeks } from '../GreeksDisplay';
import { Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';

interface LiveStrategyUpdatesProps {
	/** Strategy parameters to subscribe to */
	subscription: StrategySubscription;
	/** Show connection status */
	showConnectionStatus?: boolean;
	/** Enable debug logging */
	debug?: boolean;
	/** Custom className */
	className?: string;
}

export const LiveStrategyUpdates: React.FC<LiveStrategyUpdatesProps> = ({
	subscription,
	showConnectionStatus = true,
	debug = false,
	className = ''
}) => {
	const {
		isConnected,
		connectionStatus,
		lastUpdate,
		error,
		subscribe,
		unsubscribe,
		connect,
		disconnect,
		activeSubscriptions
	} = useStrategyWebSocket({ debug });

	const [isSubscribed, setIsSubscribed] = useState(false);
	const [updateCount, setUpdateCount] = useState(0);

	// Subscribe to strategy when connected
	useEffect(() => {
		if (isConnected && !isSubscribed) {
			subscribe(subscription);
			setIsSubscribed(true);
		}
	}, [isConnected, isSubscribed, subscription, subscribe]);

	// Track update count
	useEffect(() => {
		if (lastUpdate) {
			setUpdateCount(prev => prev + 1);
		}
	}, [lastUpdate]);

	// Generate strategy ID for tracking
	const strategyId = `${subscription.strategy_type}_${subscription.symbol}_${subscription.expiration}`;

	const getConnectionIcon = () => {
		switch (connectionStatus) {
			case 'connected':
				return <Wifi className="text-green-500" size={20} />;
			case 'connecting':
				return <RefreshCw className="text-yellow-500 animate-spin" size={20} />;
			case 'error':
				return <AlertCircle className="text-red-500" size={20} />;
			default:
				return <WifiOff className="text-gray-400" size={20} />;
		}
	};

	const getConnectionText = () => {
		switch (connectionStatus) {
			case 'connected':
				return 'Live Updates Active';
			case 'connecting':
				return 'Connecting...';
			case 'error':
				return 'Connection Error';
			default:
				return 'Disconnected';
		}
	};

	const formatCurrency = (value: number): string => {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		}).format(value);
	};

	return (
		<div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
			{/* Header with connection status */}
			{showConnectionStatus && (
				<div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
					<div className="flex items-center gap-3">
						{getConnectionIcon()}
						<div>
							<p className="font-medium text-gray-900 dark:text-white">
								{getConnectionText()}
							</p>
							{isConnected && (
								<p className="text-xs text-gray-500 dark:text-gray-400">
									Updates: {updateCount} • Subscribed to: {strategyId}
								</p>
							)}
						</div>
					</div>
					<button
						onClick={() => isConnected ? disconnect() : connect()}
						className="px-3 py-1 text-sm rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
					>
						{isConnected ? 'Disconnect' : 'Connect'}
					</button>
				</div>
			)}

			{/* Error display */}
			{error && (
				<div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
					<div className="flex items-center gap-2">
						<AlertCircle className="text-red-500" size={16} />
						<p className="text-sm text-red-700 dark:text-red-300">{error}</p>
					</div>
				</div>
			)}

			{/* Strategy data display */}
			{lastUpdate ? (
				<div className="space-y-4">
					{/* Strategy header */}
					<div>
						<h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
							{lastUpdate.strategy_type === 'iron_condor' ? 'Iron Condor' : 'Bull Call Spread'}
						</h3>
						<div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
							<span>Symbol: {lastUpdate.symbol}</span>
							<span>Expiration: {lastUpdate.expiration}</span>
							<span>Contracts: {lastUpdate.contracts}</span>
						</div>
					</div>

					{/* Price and P&L */}
					<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
						<div>
							<p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Net Credit</p>
							<p className="text-lg font-bold text-green-600 dark:text-green-400">
								{formatCurrency(lastUpdate.net_credit || 0)}
							</p>
						</div>
						<div>
							<p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Max Profit</p>
							<p className="text-lg font-bold text-green-600 dark:text-green-400">
								{formatCurrency(lastUpdate.max_profit || 0)}
							</p>
						</div>
						<div>
							<p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Max Loss</p>
							<p className="text-lg font-bold text-red-600 dark:text-red-400">
								{formatCurrency(lastUpdate.max_loss || 0)}
							</p>
						</div>
						<div>
							<p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Probability of Profit</p>
							<p className="text-lg font-bold text-blue-600 dark:text-blue-400">
								{((lastUpdate.probability_of_profit || 0) * 100).toFixed(1)}%
							</p>
						</div>
					</div>

					{/* Greeks display */}
					{lastUpdate.greeks && (
						<GreeksDisplay 
							greeks={lastUpdate.greeks as Greeks}
							showLabels={true}
						/>
					)}

					{/* Legs information */}
					{lastUpdate.legs && lastUpdate.legs.length > 0 && (
						<div>
							<h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
								Option Legs
							</h4>
							<div className="space-y-2">
								{lastUpdate.legs.map((leg: any, index: number) => (
									<div 
										key={index}
										className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded"
									>
										<div className="flex items-center gap-3">
											<span className={`px-2 py-1 text-xs font-medium rounded ${
												leg.action === 'buy' 
													? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
													: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
											}`}>
												{leg.action.toUpperCase()}
											</span>
											<span className="text-sm font-medium text-gray-900 dark:text-white">
												{leg.strike} {leg.option_type.toUpperCase()}
											</span>
										</div>
										<div className="text-right">
											<p className="text-sm font-medium text-gray-900 dark:text-white">
												{formatCurrency(leg.mid_price || 0)}
											</p>
											{leg.bid && leg.ask && (
												<p className="text-xs text-gray-500 dark:text-gray-400">
													{formatCurrency(leg.bid)} / {formatCurrency(leg.ask)}
												</p>
											)}
										</div>
									</div>
								))}
							</div>
						</div>
					)}

					{/* Data source indicator */}
					<div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
						<div className="flex items-center gap-2">
							<div className={`w-2 h-2 rounded-full ${
								lastUpdate.data_source === 'ib_realtime' 
									? 'bg-green-500 animate-pulse' 
									: lastUpdate.data_source === 'mixed'
									? 'bg-yellow-500'
									: 'bg-gray-400'
							}`} />
							<span className="text-xs text-gray-500 dark:text-gray-400">
								Data Source: {lastUpdate.data_source || 'Unknown'}
							</span>
						</div>
						{lastUpdate.last_updated && (
							<span className="text-xs text-gray-500 dark:text-gray-400">
								Updated: {new Date(lastUpdate.last_updated).toLocaleTimeString()}
							</span>
						)}
					</div>
				</div>
			) : (
				<div className="text-center py-8">
					<p className="text-gray-500 dark:text-gray-400">
						{isConnected ? 'Waiting for strategy updates...' : 'Connect to receive live updates'}
					</p>
				</div>
			)}
		</div>
	);
};