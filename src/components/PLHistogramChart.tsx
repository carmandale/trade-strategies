import React, { useMemo } from 'react'
import {
	BarChart,
	Bar,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	ResponsiveContainer,
	Cell
} from 'recharts'
import { BarChart3, Loader2 } from 'lucide-react'

export interface PLDistributionBin {
	range: string
	count: number
	midpoint: number
}

interface PLHistogramChartProps {
	data: PLDistributionBin[]
	loading?: boolean
	showStats?: boolean
	height?: number
	className?: string
}

const formatCurrency = (value: number): string => {
	const sign = value >= 0 ? '+' : ''
	return `${sign}$${Math.abs(value).toLocaleString('en-US', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	})}`
}

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
	if (active && payload && payload.length) {
		const data = payload[0].payload
		return (
			<div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
				<p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
					P/L Range: {data.range}
				</p>
				<div className="space-y-1">
					<p className="text-sm">
						<span className="text-gray-600 dark:text-gray-400">Trades: </span>
						<span className="font-medium text-gray-900 dark:text-gray-100">
							{data.count}
						</span>
					</p>
					<p className="text-sm">
						<span className="text-gray-600 dark:text-gray-400">Midpoint: </span>
						<span className={`font-medium ${
							data.midpoint >= 0 
								? 'text-green-600 dark:text-green-400' 
								: 'text-red-600 dark:text-red-400'
						}`}>
							{formatCurrency(data.midpoint)}
						</span>
					</p>
				</div>
			</div>
		)
	}
	return null
}

export const PLHistogramChart: React.FC<PLHistogramChartProps> = ({
	data,
	loading = false,
	showStats = false,
	height = 300,
	className = ''
}) => {
	// Calculate statistics
	const stats = useMemo(() => {
		if (!data || data.length === 0) return null

		const totalTrades = data.reduce((sum, bin) => sum + bin.count, 0)
		const mostCommonBin = data.reduce((max, bin) => 
			bin.count > max.count ? bin : max, data[0]
		)
		
		const profitableBins = data.filter(bin => bin.midpoint > 0)
		const profitableTrades = profitableBins.reduce((sum, bin) => sum + bin.count, 0)
		const winRate = totalTrades > 0 ? (profitableTrades / totalTrades) * 100 : 0

		return {
			totalTrades,
			mostCommonRange: mostCommonBin.range,
			winRate: winRate.toFixed(1)
		}
	}, [data])

	// Get bar colors based on P/L
	const getBarColor = (midpoint: number) => {
		if (midpoint > 100) return '#10b981' // Strong green for big profits
		if (midpoint > 0) return '#34d399'   // Light green for small profits
		if (midpoint > -100) return '#fbbf24' // Yellow for small losses
		return '#ef4444' // Red for big losses
	}

	if (loading) {
		return (
			<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
				<div className="flex items-center justify-center" style={{ height }}>
					<div className="text-center">
						<Loader2 className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-2" />
						<p className="text-gray-600 dark:text-gray-400">Loading histogram data...</p>
					</div>
				</div>
			</div>
		)
	}

	if (!data || data.length === 0) {
		return (
			<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
				<div className="flex items-center justify-center" style={{ height }}>
					<div className="text-center">
						<div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-3">
							<BarChart3 className="w-8 h-8 text-gray-400" />
						</div>
						<h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
							No Data Available
						</h3>
						<p className="text-gray-600 dark:text-gray-400">
							No profit/loss distribution data to display
						</p>
					</div>
				</div>
			</div>
		)
	}

	return (
		<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
			{/* Header */}
			<div className="flex items-center justify-between mb-4">
				<div>
					<h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
						Profit/Loss Distribution
					</h3>
					{stats && (
						<div className="flex items-center space-x-4 mt-1">
							<span className="text-sm text-gray-600 dark:text-gray-400">
								Win Rate:
							</span>
							<span className="text-sm font-medium text-green-600 dark:text-green-400">
								{stats.winRate}%
							</span>
							<span className="text-sm text-gray-600 dark:text-gray-400">
								Total Trades: {stats.totalTrades}
							</span>
						</div>
					)}
				</div>
			</div>

			{/* Chart */}
			<div style={{ height }}>
				<ResponsiveContainer width="100%" height="100%">
					<BarChart
						data={data}
						margin={{ top: 5, right: 30, left: 20, bottom: 20 }}
					>
						<CartesianGrid 
							strokeDasharray="3 3" 
							className="opacity-30"
							stroke="currentColor"
						/>
						<XAxis
							dataKey="range"
							className="text-xs"
							stroke="currentColor"
							tick={{ fontSize: 10 }}
							angle={-45}
							textAnchor="end"
							height={60}
						/>
						<YAxis
							className="text-xs"
							stroke="currentColor"
							tick={{ fontSize: 12 }}
							label={{ 
								value: 'Number of Trades', 
								angle: -90, 
								position: 'insideLeft',
								textAnchor: 'middle'
							}}
						/>
						<Tooltip content={<CustomTooltip />} />
						
						<Bar dataKey="count" radius={[2, 2, 0, 0]}>
							{data.map((entry, index) => (
								<Cell 
									key={`cell-${index}`} 
									fill={getBarColor(entry.midpoint)}
								/>
							))}
						</Bar>
					</BarChart>
				</ResponsiveContainer>
			</div>

			{/* Statistics */}
			{showStats && stats && (
				<div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
					<h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
						Distribution Statistics
					</h4>
					<div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
						<div>
							<span className="text-gray-600 dark:text-gray-400">Total Trades:</span>
							<div className="font-medium text-gray-900 dark:text-gray-100">
								{stats.totalTrades}
							</div>
						</div>
						<div>
							<span className="text-gray-600 dark:text-gray-400">Win Rate:</span>
							<div className="font-medium text-green-600 dark:text-green-400">
								{stats.winRate}%
							</div>
						</div>
						<div>
							<span className="text-gray-600 dark:text-gray-400">Most Common Range:</span>
							<div className="font-medium text-gray-900 dark:text-gray-100">
								{stats.mostCommonRange}
							</div>
						</div>
					</div>
				</div>
			)}

			{/* Legend */}
			<div className="mt-4 flex items-center justify-center space-x-6 text-xs text-gray-500 dark:text-gray-400">
				<div className="flex items-center space-x-1">
					<div className="w-3 h-3 bg-red-500 rounded-sm"></div>
					<span>Large Loss</span>
				</div>
				<div className="flex items-center space-x-1">
					<div className="w-3 h-3 bg-yellow-400 rounded-sm"></div>
					<span>Small Loss</span>
				</div>
				<div className="flex items-center space-x-1">
					<div className="w-3 h-3 bg-green-400 rounded-sm"></div>
					<span>Small Profit</span>
				</div>
				<div className="flex items-center space-x-1">
					<div className="w-3 h-3 bg-green-600 rounded-sm"></div>
					<span>Large Profit</span>
				</div>
			</div>
		</div>
	)
}