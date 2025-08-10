import React from 'react'
import { StrategyListProps } from '../types/strategy'
import { StrategyCard } from './StrategyCard'
import { AlertCircle, Loader2, TrendingUp } from 'lucide-react'

export const StrategyList: React.FC<StrategyListProps> = ({
	strategies,
	loading = false,
	error = null,
	onStrategySelect
}) => {
	// Loading state
    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-12 px-4">
                <Loader2 data-testid="loading-spinner" className="w-8 h-8 animate-spin text-blue-600 mb-4" />
                <p className="text-gray-600 dark:text-gray-400 text-center">
                    Loading strategies...
                </p>
            </div>
        )
    }

	// Error state
	if (error) {
		return (
			<div className="flex flex-col items-center justify-center py-12 px-4">
				<AlertCircle className="w-12 h-12 text-red-500 mb-4" />
				<h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
					Error Loading Strategies
				</h3>
				<p className="text-gray-600 dark:text-gray-400 text-center max-w-md">
					{error}
				</p>
				<button 
					onClick={() => window.location.reload()}
					className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
				>
					Try Again
				</button>
			</div>
		)
	}

	// Empty state
	if (!strategies || strategies.length === 0) {
		return (
			<div className="flex flex-col items-center justify-center py-12 px-4">
				<TrendingUp className="w-12 h-12 text-gray-400 mb-4" />
				<h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
					No Strategies Found
				</h3>
				<p className="text-gray-600 dark:text-gray-400 text-center max-w-md">
					No trading strategies are currently available. Create your first strategy to get started.
				</p>
			</div>
		)
	}

	// Calculate summary statistics
	const totalStrategies = strategies.length
	const activeStrategies = strategies.filter(s => s.is_active).length
	const totalPnl = strategies.reduce((sum, s) => sum + s.performance.total_pnl, 0)
	const avgWinRate = strategies.reduce((sum, s) => sum + s.performance.win_rate, 0) / totalStrategies

	return (
		<div className="space-y-6">
			{/* Summary Header */}
			<div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6">
				<h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
					Strategy Portfolio
				</h2>
				<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
					<div className="text-center">
						<div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
							{totalStrategies}
						</div>
						<div className="text-sm text-gray-600 dark:text-gray-400">
							Total Strategies
						</div>
					</div>
					<div className="text-center">
						<div className="text-2xl font-bold text-green-600 dark:text-green-400">
							{activeStrategies}
						</div>
						<div className="text-sm text-gray-600 dark:text-gray-400">
							Active
						</div>
					</div>
					<div className="text-center">
						<div className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
							{totalPnl >= 0 ? '+' : ''}${totalPnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
						</div>
						<div className="text-sm text-gray-600 dark:text-gray-400">
							Total P&L
						</div>
					</div>
					<div className="text-center">
						<div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
							{avgWinRate.toFixed(1)}%
						</div>
						<div className="text-sm text-gray-600 dark:text-gray-400">
							Avg Win Rate
						</div>
					</div>
				</div>
			</div>

            {/* Strategy Cards Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="strategy-list">
				{strategies.map((strategy) => (
					<StrategyCard
						key={strategy.id}
						strategy={strategy}
						onClick={onStrategySelect ? () => onStrategySelect(strategy) : undefined}
						showDetails={false}
					/>
				))}
			</div>

			{/* Footer Info */}
			<div className="text-center text-sm text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-200 dark:border-gray-700">
				Showing {strategies.length} strateg{strategies.length === 1 ? 'y' : 'ies'}
				{activeStrategies !== totalStrategies && (
					<span className="ml-2">
						• {activeStrategies} active, {totalStrategies - activeStrategies} inactive
					</span>
				)}
			</div>
		</div>
	)
}