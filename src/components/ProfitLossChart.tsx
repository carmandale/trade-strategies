import React, { useMemo } from 'react'
import {
	LineChart,
	Line,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	ResponsiveContainer,
	ReferenceLine
} from 'recharts'
import { Loader2 } from 'lucide-react'
import {
	generatePnLCurve,
	calculateBreakevenPoints,
	getMaxProfitLoss,
	type IronCondorPosition,
	type PnLDataPoint
} from '../utils/ironCondorCalculations'

interface ProfitLossChartProps {
	position: IronCondorPosition
	currentPrice: number
	loading?: boolean
	height?: number
	className?: string
}

const formatCurrency = (value: number): string => {
	const sign = value >= 0 ? '+' : ''
	return `${sign}$${Math.abs(value).toLocaleString('en-US', {
		minimumFractionDigits: 0,
		maximumFractionDigits: 0
	})}`
}

const formatPrice = (value: number): string => {
	return `$${value.toLocaleString('en-US', {
		minimumFractionDigits: 0,
		maximumFractionDigits: 0
	})}`
}

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
	if (active && payload && payload.length) {
		const data = payload[0].payload as PnLDataPoint
		return (
			<div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
				<p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
					Price: {formatPrice(data.price)}
				</p>
				<p className="text-sm">
					<span className="text-gray-600 dark:text-gray-400">P/L: </span>
					<span className={`font-medium ${
						data.pnl >= 0 
							? 'text-green-600 dark:text-green-400' 
							: 'text-red-600 dark:text-red-400'
					}`}>
						{formatCurrency(data.pnl)}
					</span>
				</p>
			</div>
		)
	}
	return null
}

export const ProfitLossChart: React.FC<ProfitLossChartProps> = ({
	position,
	currentPrice,
	loading = false,
	height = 400,
	className = ''
}) => {
	// Calculate P/L curve data
	const chartData = useMemo(() => {
		if (!position || loading) return []
		return generatePnLCurve(position)
	}, [position, loading])

	// Calculate key metrics
	const breakevens = useMemo(() => calculateBreakevenPoints(position), [position])
	const { maxProfit, maxLoss } = useMemo(() => getMaxProfitLoss(position), [position])

	if (loading) {
		return (
			<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
				<div className="flex items-center justify-center" style={{ height }}>
					<div className="text-center">
						<Loader2 data-testid="loading-spinner" className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-2" />
						<p className="text-gray-600 dark:text-gray-400">Loading chart data...</p>
					</div>
				</div>
			</div>
		)
	}

	if (!chartData || chartData.length === 0) {
		return (
			<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
				<div className="flex items-center justify-center" style={{ height }}>
					<div className="text-center">
						<div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-3">
							<LineChart className="w-8 h-8 text-gray-400" />
						</div>
						<h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
							No Data Available
						</h3>
						<p className="text-gray-600 dark:text-gray-400">
							No P/L data to display
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
						Profit/Loss Chart
					</h3>
					<p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
						Iron Condor Strategy at Expiration
					</p>
				</div>
			</div>

			{/* Key Metrics */}
			<div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
				<div className="text-center">
					<p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
						Max Profit:
					</p>
					<p className="text-lg font-bold text-green-600 dark:text-green-400">
						{formatCurrency(maxProfit)}
					</p>
				</div>
				<div className="text-center">
					<p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
						Max Loss:
					</p>
					<p className="text-lg font-bold text-red-600 dark:text-red-400">
						{formatCurrency(maxLoss)}
					</p>
				</div>
				<div className="text-center lg:col-span-2">
					<p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
						Breakevens:
					</p>
					<p className="text-lg font-bold text-gray-900 dark:text-gray-100">
						{formatPrice(breakevens.lowerBreakeven)} / {formatPrice(breakevens.upperBreakeven)}
					</p>
				</div>
			</div>

			{/* Chart */}
			<div style={{ height }}>
				<ResponsiveContainer width="100%" height="100%">
					<LineChart
						data={chartData}
						margin={{ top: 5, right: 30, left: 20, bottom: 20 }}
					>
						<CartesianGrid 
							strokeDasharray="3 3" 
							className="opacity-30"
							stroke="currentColor"
						/>
						<XAxis
							dataKey="price"
							className="text-xs"
							stroke="currentColor"
							tick={{ fontSize: 12 }}
							tickFormatter={formatPrice}
						/>
						<YAxis
							className="text-xs"
							stroke="currentColor"
							tick={{ fontSize: 12 }}
							tickFormatter={formatCurrency}
						/>
						<Tooltip content={<CustomTooltip />} />
						
						{/* Zero P/L line */}
						<ReferenceLine 
							y={0} 
							stroke="currentColor" 
							strokeDasharray="2 2" 
							className="opacity-50"
						/>
						
						{/* Breakeven lines */}
						<ReferenceLine 
							x={breakevens.lowerBreakeven} 
							stroke="#f59e0b" 
							strokeDasharray="5 5"
							label="Lower Breakeven"
							className="opacity-70"
						/>
						<ReferenceLine 
							x={breakevens.upperBreakeven} 
							stroke="#f59e0b" 
							strokeDasharray="5 5"
							label="Upper Breakeven"
							className="opacity-70"
						/>
						
						{/* Current price line */}
						<ReferenceLine 
							x={currentPrice} 
							stroke="#3b82f6" 
							strokeWidth={2}
							label="Current Price"
							className="opacity-80"
						/>
						
						{/* P/L curve */}
						<Line
							type="monotone"
							dataKey="pnl"
							stroke="#10b981"
							strokeWidth={3}
							dot={false}
							activeDot={{ 
								r: 5, 
								stroke: "#10b981",
								strokeWidth: 2,
								fill: "white"
							}}
						/>
					</LineChart>
				</ResponsiveContainer>
			</div>

			{/* Legend */}
			<div className="mt-4 flex items-center justify-center space-x-6 text-xs text-gray-500 dark:text-gray-400">
				<div className="flex items-center space-x-2">
					<div className="w-4 h-0.5 bg-green-500"></div>
					<span>P/L Curve</span>
				</div>
				<div className="flex items-center space-x-2">
					<div className="w-4 h-0.5 bg-yellow-500 opacity-70" style={{ 
						backgroundImage: 'repeating-linear-gradient(to right, transparent, transparent 2px, currentColor 2px, currentColor 4px)' 
					}}></div>
					<span>Breakeven</span>
				</div>
				<div className="flex items-center space-x-2">
					<div className="w-4 h-0.5 bg-blue-500"></div>
					<span>Current Price</span>
				</div>
			</div>
		</div>
	)
}