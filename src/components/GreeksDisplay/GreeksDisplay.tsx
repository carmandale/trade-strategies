import React from 'react';
import { TrendingUp, TrendingDown, Activity, Clock, Zap } from 'lucide-react';

export interface Greeks {
	delta: number;
	gamma: number;
	theta: number;
	vega: number;
	rho?: number;
}

interface GreeksDisplayProps {
	greeks: Greeks;
	/** Compact display mode for inline use */
	compact?: boolean;
	/** Show labels for each Greek */
	showLabels?: boolean;
	/** Custom className for styling */
	className?: string;
}

export const GreeksDisplay: React.FC<GreeksDisplayProps> = ({
	greeks,
	compact = false,
	showLabels = true,
	className = ''
}) => {
	const formatGreek = (value: number, isTheta: boolean = false): string => {
		// Theta is typically negative and represents daily decay
		if (isTheta) {
			return value.toFixed(2);
		}
		// Other Greeks
		return value >= 0 ? `+${value.toFixed(3)}` : value.toFixed(3);
	};

	const getGreekColor = (value: number, greek: string): string => {
		if (greek === 'theta') {
			// Theta is usually negative (time decay)
			return value < 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400';
		}
		// For other Greeks, color based on positive/negative
		return value >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
	};

	const getGreekIcon = (greek: string) => {
		switch (greek) {
			case 'delta':
				return <TrendingUp className="w-4 h-4" />;
			case 'gamma':
				return <Activity className="w-4 h-4" />;
			case 'theta':
				return <Clock className="w-4 h-4" />;
			case 'vega':
				return <Zap className="w-4 h-4" />;
			default:
				return null;
		}
	};

	const getGreekDescription = (greek: string): string => {
		switch (greek) {
			case 'delta':
				return 'Price sensitivity';
			case 'gamma':
				return 'Delta change rate';
			case 'theta':
				return 'Time decay (per day)';
			case 'vega':
				return 'Volatility sensitivity';
			case 'rho':
				return 'Interest rate sensitivity';
			default:
				return '';
		}
	};

	if (compact) {
		return (
			<div className={`flex items-center gap-3 text-sm ${className}`}>
				<span className="text-gray-500 dark:text-gray-400">Greeks:</span>
				<span className={getGreekColor(greeks.delta, 'delta')}>
					Δ {formatGreek(greeks.delta)}
				</span>
				<span className={getGreekColor(greeks.gamma, 'gamma')}>
					Γ {formatGreek(greeks.gamma)}
				</span>
				<span className={getGreekColor(greeks.theta, 'theta')}>
					Θ {formatGreek(greeks.theta, true)}
				</span>
				<span className={getGreekColor(greeks.vega, 'vega')}>
					V {formatGreek(greeks.vega)}
				</span>
				{greeks.rho !== undefined && (
					<span className={getGreekColor(greeks.rho, 'rho')}>
						ρ {formatGreek(greeks.rho)}
					</span>
				)}
			</div>
		);
	}

	return (
		<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 ${className}`}>
			<h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 uppercase tracking-wide">
				Option Greeks
			</h3>
			
			<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
				{/* Delta */}
				<div className="space-y-1">
					<div className="flex items-center gap-2">
						{getGreekIcon('delta')}
						<span className="text-xs font-medium text-gray-500 dark:text-gray-400">
							Delta (Δ)
						</span>
					</div>
					<div className={`text-lg font-bold ${getGreekColor(greeks.delta, 'delta')}`}>
						{formatGreek(greeks.delta)}
					</div>
					{showLabels && (
						<div className="text-xs text-gray-500 dark:text-gray-400">
							{getGreekDescription('delta')}
						</div>
					)}
				</div>

				{/* Gamma */}
				<div className="space-y-1">
					<div className="flex items-center gap-2">
						{getGreekIcon('gamma')}
						<span className="text-xs font-medium text-gray-500 dark:text-gray-400">
							Gamma (Γ)
						</span>
					</div>
					<div className={`text-lg font-bold ${getGreekColor(greeks.gamma, 'gamma')}`}>
						{formatGreek(greeks.gamma)}
					</div>
					{showLabels && (
						<div className="text-xs text-gray-500 dark:text-gray-400">
							{getGreekDescription('gamma')}
						</div>
					)}
				</div>

				{/* Theta */}
				<div className="space-y-1">
					<div className="flex items-center gap-2">
						{getGreekIcon('theta')}
						<span className="text-xs font-medium text-gray-500 dark:text-gray-400">
							Theta (Θ)
						</span>
					</div>
					<div className={`text-lg font-bold ${getGreekColor(greeks.theta, 'theta')}`}>
						${formatGreek(greeks.theta, true)}
					</div>
					{showLabels && (
						<div className="text-xs text-gray-500 dark:text-gray-400">
							{getGreekDescription('theta')}
						</div>
					)}
				</div>

				{/* Vega */}
				<div className="space-y-1">
					<div className="flex items-center gap-2">
						{getGreekIcon('vega')}
						<span className="text-xs font-medium text-gray-500 dark:text-gray-400">
							Vega (V)
						</span>
					</div>
					<div className={`text-lg font-bold ${getGreekColor(greeks.vega, 'vega')}`}>
						{formatGreek(greeks.vega)}
					</div>
					{showLabels && (
						<div className="text-xs text-gray-500 dark:text-gray-400">
							{getGreekDescription('vega')}
						</div>
					)}
				</div>

				{/* Rho (optional) */}
				{greeks.rho !== undefined && (
					<div className="space-y-1">
						<div className="flex items-center gap-2">
							<span className="text-xs font-medium text-gray-500 dark:text-gray-400">
								Rho (ρ)
							</span>
						</div>
						<div className={`text-lg font-bold ${getGreekColor(greeks.rho, 'rho')}`}>
							{formatGreek(greeks.rho)}
						</div>
						{showLabels && (
							<div className="text-xs text-gray-500 dark:text-gray-400">
								{getGreekDescription('rho')}
							</div>
						)}
					</div>
				)}
			</div>

			{/* Additional information */}
			<div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
				<p className="text-xs text-gray-500 dark:text-gray-400">
					Greeks represent the sensitivity of the option's price to various factors. 
					Values shown are for the entire position.
				</p>
			</div>
		</div>
	);
};

// Simplified inline Greeks display for use in cards
export const GreeksBadge: React.FC<{ greeks: Greeks; className?: string }> = ({ greeks, className = '' }) => {
	return (
		<div className={`inline-flex items-center gap-2 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs ${className}`}>
			<span className="font-medium text-gray-600 dark:text-gray-400">Δ</span>
			<span className={greeks.delta >= 0 ? 'text-green-600' : 'text-red-600'}>
				{greeks.delta.toFixed(2)}
			</span>
			<span className="text-gray-400">|</span>
			<span className="font-medium text-gray-600 dark:text-gray-400">Θ</span>
			<span className="text-red-600">
				${Math.abs(greeks.theta).toFixed(0)}
			</span>
		</div>
	);
};