import React, { useState } from 'react'
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react'

export interface PerformanceData {
	totalPL: number
	winRate: number
	totalTrades: number
	avgPLPerTrade: number
	sharpeRatio?: number
	maxDrawdown?: number
	bestTrade?: number
	worstTrade?: number
	consecutiveWins?: number
	consecutiveLosses?: number
}

interface PerformanceMetricsProps {
	data: PerformanceData
	expanded?: boolean
	className?: string
}

const formatCurrency = (value: number): string => {
	const sign = value >= 0 ? '+' : ''
	return `${sign}$${Math.abs(value).toLocaleString('en-US', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	})}`
}

const formatPercentage = (value: number): string => {
	return `${value.toFixed(1)}%`
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
	data,
	expanded: initialExpanded = false,
	className = ''
}) => {
	const [expanded, setExpanded] = useState(initialExpanded)

	const isPositivePL = data.totalPL >= 0
	const isPositiveAvgPL = data.avgPLPerTrade >= 0
	const isGoodWinRate = data.winRate >= 60
	const isGoodSharpe = (data.sharpeRatio || 0) >= 1.0

	return (
		<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
			{/* Header */}
			<div className="flex items-center justify-between mb-6">
				<div className="flex items-center space-x-2">
					<Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
					<h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
						Performance Metrics
					</h3>
				</div>
				<button
					onClick={() => setExpanded(!expanded)}
					className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
				>
					<span>{expanded ? 'Show Less' : 'Show More'}</span>
					{expanded ? (
						<ChevronUp className="w-4 h-4" />
					) : (
						<ChevronDown className="w-4 h-4" />
					)}
				</button>
			</div>

			{/* Core Metrics Grid */}
			<div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
				{/* Total P/L */}
				<div className="text-center">
					<div className="flex items-center justify-center mb-2">
						{isPositivePL ? (
							<TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
						) : (
							<TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />
						)}
					</div>
					<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
						Total P/L
					</div>
					<div className={`text-2xl font-bold ${
						isPositivePL 
							? 'text-green-600 dark:text-green-400' 
							: 'text-red-600 dark:text-red-400'
					}`}>
						{formatCurrency(data.totalPL)}
					</div>
				</div>

				{/* Win Rate */}
				<div className="text-center">
					<div className="flex items-center justify-center mb-2">
						<div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white ${
							isGoodWinRate ? 'bg-green-600' : 'bg-yellow-500'
						}`}>
							%
						</div>
					</div>
					<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
						Win Rate
					</div>
					<div className={`text-2xl font-bold ${
						isGoodWinRate 
							? 'text-green-600 dark:text-green-400' 
							: 'text-yellow-600 dark:text-yellow-400'
					}`}>
						{formatPercentage(data.winRate)}
					</div>
				</div>

				{/* Total Trades */}
				<div className="text-center">
					<div className="flex items-center justify-center mb-2">
						<div className="w-5 h-5 bg-blue-600 dark:bg-blue-400 rounded-full flex items-center justify-center text-xs font-bold text-white">
							#
						</div>
					</div>
					<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
						Total Trades
					</div>
					<div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
						{data.totalTrades.toLocaleString()}
					</div>
				</div>

				{/* Avg P/L per Trade */}
				<div className="text-center">
					<div className="flex items-center justify-center mb-2">
						<DollarSign className={`w-5 h-5 ${
							isPositiveAvgPL 
								? 'text-green-600 dark:text-green-400' 
								: 'text-red-600 dark:text-red-400'
						}`} />
					</div>
					<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
						Avg P/L per Trade
					</div>
					<div className={`text-2xl font-bold ${
						isPositiveAvgPL 
							? 'text-green-600 dark:text-green-400' 
							: 'text-red-600 dark:text-red-400'
					}`}>
						{formatCurrency(data.avgPLPerTrade)}
					</div>
				</div>
			</div>

			{/* Advanced Metrics (Expandable) */}
			{expanded && (
				<>
					<div className="border-t border-gray-200 dark:border-gray-700 pt-6">
						<h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">
							Advanced Analytics
						</h4>
						
						<div className="grid grid-cols-2 md:grid-cols-3 gap-6">
							{/* Sharpe Ratio */}
							{data.sharpeRatio !== undefined && (
								<div>
									<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
										Sharpe Ratio
									</div>
									<div className={`text-lg font-semibold ${
										isGoodSharpe 
											? 'text-green-600 dark:text-green-400' 
											: 'text-yellow-600 dark:text-yellow-400'
									}`}>
										{data.sharpeRatio.toFixed(2)}
									</div>
									<div className="text-xs text-gray-500 dark:text-gray-400">
										{isGoodSharpe ? 'Excellent' : 'Good'}
									</div>
								</div>
							)}

							{/* Max Drawdown */}
							{data.maxDrawdown !== undefined && (
								<div>
									<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
										Max Drawdown
									</div>
									<div className="text-lg font-semibold text-red-600 dark:text-red-400">
										${Math.abs(data.maxDrawdown).toLocaleString('en-US', { 
											minimumFractionDigits: 2 
										})}
									</div>
									<div className="text-xs text-gray-500 dark:text-gray-400">
										Risk Metric
									</div>
								</div>
							)}

							{/* Best Trade */}
							{data.bestTrade !== undefined && (
								<div>
									<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
										Best Trade
									</div>
									<div className="text-lg font-semibold text-green-600 dark:text-green-400">
										{formatCurrency(data.bestTrade)}
									</div>
									<div className="text-xs text-gray-500 dark:text-gray-400">
										Best Single Trade
									</div>
								</div>
							)}

							{/* Worst Trade */}
							{data.worstTrade !== undefined && (
								<div>
									<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
										Worst Trade
									</div>
									<div className="text-lg font-semibold text-red-600 dark:text-red-400">
										${Math.abs(data.worstTrade).toLocaleString('en-US', { 
											minimumFractionDigits: 2 
										})}
									</div>
									<div className="text-xs text-gray-500 dark:text-gray-400">
										Worst Single Trade
									</div>
								</div>
							)}

							{/* Consecutive Wins */}
							{data.consecutiveWins !== undefined && (
								<div>
									<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
										Consecutive Wins
									</div>
									<div className="text-lg font-semibold text-green-600 dark:text-green-400">
										{data.consecutiveWins}
									</div>
									<div className="text-xs text-gray-500 dark:text-gray-400">
										Max Win Streak
									</div>
								</div>
							)}

							{/* Consecutive Losses */}
							{data.consecutiveLosses !== undefined && (
								<div>
									<div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
										Consecutive Losses
									</div>
									<div className="text-lg font-semibold text-red-600 dark:text-red-400">
										{data.consecutiveLosses}
									</div>
									<div className="text-xs text-gray-500 dark:text-gray-400">
										Max Loss Streak
									</div>
								</div>
							)}
						</div>
					</div>

					{/* Performance Assessment */}
					<div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
						<h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
							Performance Assessment
						</h4>
						<div className="flex flex-wrap gap-2">
							{isPositivePL && (
								<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
									Profitable Strategy
								</span>
							)}
							{isGoodWinRate && (
								<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
									High Win Rate
								</span>
							)}
							{isGoodSharpe && (
								<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
									Good Risk-Adjusted Returns
								</span>
							)}
							{data.totalTrades >= 50 && (
								<span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
									Statistically Significant
								</span>
							)}
						</div>
					</div>
				</>
			)}
		</div>
	)
}