import React, { useMemo } from 'react'
import { AlertTriangle } from 'lucide-react'
import { ProfitLossChart } from './ProfitLossChart'
import {
	strikeConfigToPosition,
	validateStrikeOrder,
	calculateBreakevenPoints,
	type IronCondorPosition
} from '../utils/ironCondorCalculations'
import type { StrikeConfig } from '../types/strategy'

interface StrikeVisualizationProps {
	strikes: StrikeConfig
	currentPrice: number
	credit?: number
	contracts?: number
	loading?: boolean
	height?: number
	className?: string
	showPercentages?: boolean
}

const formatPrice = (value: number): string => {
	return `$${value.toLocaleString('en-US', {
		minimumFractionDigits: 0,
		maximumFractionDigits: 0
	})}`
}

export const StrikeVisualization: React.FC<StrikeVisualizationProps> = ({
	strikes,
	currentPrice,
	credit = 25,
	contracts = 1,
	loading = false,
	height = 400,
	className = '',
	showPercentages = false
}) => {
	// Convert strike percentages to Iron Condor position
	const position = useMemo<IronCondorPosition>(() => {
		return strikeConfigToPosition(strikes, currentPrice, credit, contracts)
	}, [strikes, currentPrice, credit, contracts])

	// Validate strike configuration
	const validation = useMemo(() => {
		return validateStrikeOrder(position)
	}, [position])

	// Calculate breakeven points
	const breakevens = useMemo(() => {
		return calculateBreakevenPoints(position)
	}, [position])

	// Calculate spread widths
	const putSpreadWidth = position.putShortStrike - position.putLongStrike
	const callSpreadWidth = position.callLongStrike - position.callShortStrike

	return (
		<div className={`space-y-6 ${className}`}>
			{/* Header with current price */}
			<div className="flex items-center justify-between">
				<div>
					<h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
						Strike Visualization
					</h3>
					<p className="text-sm text-gray-600 dark:text-gray-400">
						Iron Condor Strategy Analysis
					</p>
				</div>
				<div className="text-right">
					<p className="text-sm text-gray-600 dark:text-gray-400">
						Current Price:
					</p>
					<p className="text-lg font-bold text-gray-900 dark:text-gray-100">
						{formatPrice(currentPrice)}
					</p>
					{loading && (
						<p className="text-xs text-blue-600">
							Calculating...
						</p>
					)}
				</div>
			</div>

			{/* Validation Warnings */}
			{!validation.isValid && (
				<div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
					<div className="flex items-start">
						<AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 mr-3 flex-shrink-0" />
						<div>
							<h4 className="text-sm font-medium text-red-800 dark:text-red-200">
								Invalid Strike Configuration
							</h4>
							<ul className="mt-2 text-sm text-red-700 dark:text-red-300 list-disc list-inside">
								{validation.errors.map((error, index) => (
									<li key={index}>{error}</li>
								))}
							</ul>
						</div>
					</div>
				</div>
			)}

			{/* Strike Information Cards */}
			<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
				{/* Strike Levels */}
				<div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
					<h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
						Strike Levels
					</h4>
					<div className="space-y-2 text-sm">
						<div className="flex justify-between">
							<span className="text-gray-600 dark:text-gray-400">Put Long:</span>
							<span className="font-medium text-gray-900 dark:text-gray-100">
								{formatPrice(position.putLongStrike)}
								{showPercentages && ` (${strikes.put_long_pct}%)`}
							</span>
						</div>
						<div className="flex justify-between">
							<span className="text-gray-600 dark:text-gray-400">Put Short:</span>
							<span className="font-medium text-gray-900 dark:text-gray-100">
								{formatPrice(position.putShortStrike)}
								{showPercentages && ` (${strikes.put_short_pct}%)`}
							</span>
						</div>
						<div className="flex justify-between">
							<span className="text-gray-600 dark:text-gray-400">Call Short:</span>
							<span className="font-medium text-gray-900 dark:text-gray-100">
								{formatPrice(position.callShortStrike)}
								{showPercentages && ` (${strikes.call_short_pct}%)`}
							</span>
						</div>
						<div className="flex justify-between">
							<span className="text-gray-600 dark:text-gray-400">Call Long:</span>
							<span className="font-medium text-gray-900 dark:text-gray-100">
								{formatPrice(position.callLongStrike)}
								{showPercentages && ` (${strikes.call_long_pct}%)`}
							</span>
						</div>
					</div>
				</div>

				{/* Risk Profile */}
				<div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
					<h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
						Risk Profile
					</h4>
					<div className="space-y-2 text-sm">
						<div className="flex justify-between">
							<span className="text-gray-600 dark:text-gray-400">Profit Zone:</span>
							<span className="font-medium text-green-600 dark:text-green-400">
								{formatPrice(position.putShortStrike)} - {formatPrice(position.callShortStrike)}
							</span>
						</div>
						<div className="flex justify-between">
							<span className="text-gray-600 dark:text-gray-400">Breakeven Range:</span>
							<span className="font-medium text-yellow-600 dark:text-yellow-400">
								{formatPrice(breakevens.lowerBreakeven)} - {formatPrice(breakevens.upperBreakeven)}
							</span>
						</div>
						<div className="flex justify-between">
							<span className="text-gray-600 dark:text-gray-400">Credit Received:</span>
							<span className="font-medium text-gray-900 dark:text-gray-100">
								{formatPrice(credit)}
							</span>
						</div>
					</div>
				</div>
			</div>

			{/* Spread Information */}
			<div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
				<h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
					Spread Information
				</h4>
				<div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
					<div className="flex justify-between">
						<span className="text-gray-600 dark:text-gray-400">Put Spread Width:</span>
						<span className="font-medium text-gray-900 dark:text-gray-100">
							{formatPrice(putSpreadWidth)}
						</span>
					</div>
					<div className="flex justify-between">
						<span className="text-gray-600 dark:text-gray-400">Call Spread Width:</span>
						<span className="font-medium text-gray-900 dark:text-gray-100">
							{formatPrice(callSpreadWidth)}
						</span>
					</div>
					<div className="flex justify-between">
						<span className="text-gray-600 dark:text-gray-400">Total Width:</span>
						<span className="font-medium text-gray-900 dark:text-gray-100">
							{formatPrice(position.callLongStrike - position.putLongStrike)}
						</span>
					</div>
					<div className="flex justify-between">
						<span className="text-gray-600 dark:text-gray-400">Contracts:</span>
						<span className="font-medium text-gray-900 dark:text-gray-100">
							{contracts}
						</span>
					</div>
				</div>
			</div>

			{/* Profit/Loss Chart */}
			<ProfitLossChart
				position={position}
				currentPrice={currentPrice}
				loading={loading}
				height={height}
			/>
		</div>
	)
}