import React from 'react'
import { StrategyCardProps } from '../types/strategy'
import { TrendingUp, TrendingDown, Activity, Target, Calendar, DollarSign } from 'lucide-react'

export const StrategyCard: React.FC<StrategyCardProps> = ({ 
	strategy, 
	onClick, 
	showDetails = false 
}) => {
	const { performance } = strategy
	
	// Format currency values
	const formatCurrency = (value: number): string => {
		const sign = value >= 0 ? '+' : ''
		return `${sign}$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
	}
	
	// Format percentage values
	const formatPercentage = (value: number): string => {
		return `${value.toFixed(1)}%`
	}
	
	// Get color for P&L display
	const getPnlColor = (pnl: number): string => {
		return pnl >= 0 ? 'text-green-600' : 'text-red-600'
	}
	
	// Get strategy type display name
	const getStrategyTypeName = (type: string): string => {
		return type === 'iron_condor' ? 'Iron Condor' : 'Bull Call Spread'
	}
	
	// Get timeframe display name
	const getTimeframeName = (timeframe: string): string => {
		const names: Record<string, string> = {
			daily: 'Daily (0DTE)',
			weekly: 'Weekly',
			monthly: 'Monthly'
		}
		return names[timeframe] || timeframe
	}

	return (
    <div 
			className={`
				bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 
				p-6 shadow-sm hover:shadow-md transition-all duration-200
				${onClick ? 'cursor-pointer hover:border-blue-300 dark:hover:border-blue-600' : ''}
			`}
            data-testid={`strategy-card-${strategy.timeframe}`}
            onClick={onClick}
            role={onClick ? 'button' : 'article'}
			tabIndex={onClick ? 0 : undefined}
			onKeyDown={onClick ? (e) => {
				if (e.key === 'Enter' || e.key === ' ') {
					e.preventDefault()
					onClick()
				}
			} : undefined}
		>
			{/* Header */}
			<div className="flex items-start justify-between mb-4">
				<div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1" aria-label={`strategy-${strategy.timeframe}`}>
                        {strategy.name}
                    </h3>
					<div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
						<span className="flex items-center gap-1">
							<Target className="w-4 h-4" />
							{getStrategyTypeName(strategy.strategy_type)}
						</span>
						<span className="flex items-center gap-1" aria-hidden="true">
							<Calendar className="w-4 h-4" />
							{getTimeframeName(strategy.timeframe)}
						</span>
					</div>
				</div>
				<div className="flex items-center gap-2">
					<span className="text-sm font-medium text-gray-600 dark:text-gray-400">
						{strategy.symbol}
					</span>
					{strategy.is_active && (
						<div className="w-2 h-2 bg-green-500 rounded-full" />
					)}
				</div>
			</div>

			{/* Performance Metrics */}
			<div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
				{/* Total P&L */}
				<div className="text-center">
					<div className="flex items-center justify-center gap-1 mb-1">
						<DollarSign className="w-4 h-4 text-gray-500" />
						<span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
							Total P&L
						</span>
					</div>
					<div className={`text-lg font-bold ${getPnlColor(performance.total_pnl)}`}>
						{formatCurrency(performance.total_pnl)}
					</div>
				</div>

				{/* Win Rate */}
				<div className="text-center">
					<div className="flex items-center justify-center gap-1 mb-1">
						<Target className="w-4 h-4 text-gray-500" />
						<span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
							Win Rate
						</span>
					</div>
					<div className="text-lg font-bold text-blue-600 dark:text-blue-400">
						{formatPercentage(performance.win_rate)}
					</div>
				</div>

				{/* Avg P&L */}
				<div className="text-center">
					<div className="flex items-center justify-center gap-1 mb-1">
						{performance.avg_pnl_per_trade >= 0 ? (
							<TrendingUp className="w-4 h-4 text-gray-500" />
						) : (
							<TrendingDown className="w-4 h-4 text-gray-500" />
						)}
						<span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
							Avg Trade
						</span>
					</div>
					<div className={`text-lg font-bold ${getPnlColor(performance.avg_pnl_per_trade)}`}>
						{formatCurrency(performance.avg_pnl_per_trade)}
					</div>
				</div>

				{/* Total Trades */}
				<div className="text-center">
					<div className="flex items-center justify-center gap-1 mb-1">
						<Activity className="w-4 h-4 text-gray-500" />
						<span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
							Trades
						</span>
					</div>
					<div className="text-lg font-bold text-gray-900 dark:text-white">
						{performance.total_trades}
					</div>
				</div>
			</div>

			{/* Additional Details (if showDetails is true) */}
			{showDetails && (
				<div className="pt-4 border-t border-gray-100 dark:border-gray-700">
					<div className="grid grid-cols-2 gap-4 text-sm">
						{performance.sharpe_ratio && (
							<div>
								<span className="text-gray-600 dark:text-gray-400">Sharpe Ratio:</span>
								<span className="font-medium text-gray-900 dark:text-white ml-2">
									{performance.sharpe_ratio.toFixed(2)}
								</span>
							</div>
						)}
						{performance.max_drawdown && (
							<div>
								<span className="text-gray-600 dark:text-gray-400">Max Drawdown:</span>
								<span className={`font-medium ml-2 ${getPnlColor(performance.max_drawdown)}`}>
									{formatCurrency(performance.max_drawdown)}
								</span>
							</div>
						)}
					</div>
					
					{/* Strategy Parameters */}
					{Object.keys(strategy.parameters).length > 0 && (
						<div className="mt-3">
							<span className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 block">
								Parameters
							</span>
							<div className="text-xs text-gray-600 dark:text-gray-400">
								{JSON.stringify(strategy.parameters, null, 2).replace(/[{}",]/g, '').trim()}
							</div>
						</div>
					)}
				</div>
			)}
		</div>
	)
}