import React, { useState, useMemo } from 'react'
import {
	LineChart,
	Line,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	ResponsiveContainer,
	ReferenceLine,
	Brush
} from 'recharts'
import { ZoomIn, ZoomOut, RotateCcw, Loader2 } from 'lucide-react'

export interface EquityDataPoint {
	date: string
	cumulativePL: number
	dailyPL: number
}

interface EquityCurveChartProps {
	data: EquityDataPoint[]
	loading?: boolean
	showZoom?: boolean
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

const formatDate = (dateStr: string): string => {
	const date = new Date(dateStr)
	return date.toLocaleDateString('en-US', { 
		month: 'short', 
		day: 'numeric',
		year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
	})
}

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
	if (active && payload && payload.length) {
		const data = payload[0].payload
		return (
			<div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
				<p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
					{formatDate(label)}
				</p>
				<div className="space-y-1">
					<p className="text-sm">
						<span className="text-gray-600 dark:text-gray-400">Cumulative P/L: </span>
						<span className={`font-medium ${
							data.cumulativePL >= 0 
								? 'text-green-600 dark:text-green-400' 
								: 'text-red-600 dark:text-red-400'
						}`}>
							{formatCurrency(data.cumulativePL)}
						</span>
					</p>
					<p className="text-sm">
						<span className="text-gray-600 dark:text-gray-400">Daily P/L: </span>
						<span className={`font-medium ${
							data.dailyPL >= 0 
								? 'text-green-600 dark:text-green-400' 
								: 'text-red-600 dark:text-red-400'
						}`}>
							{formatCurrency(data.dailyPL)}
						</span>
					</p>
				</div>
			</div>
		)
	}
	return null
}

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({
	data,
	loading = false,
	showZoom = false,
	height = 400,
	className = ''
}) => {
	const [zoomLevel, setZoomLevel] = useState(1)
	const [brushSelection, setBrushSelection] = useState<{startIndex?: number, endIndex?: number}>({})

	// Calculate derived metrics
	const chartData = useMemo(() => {
		return data.map(point => ({
			...point,
			formattedDate: formatDate(point.date),
			// Add moving average for trend line (7-day)
			movingAverage: data
				.slice(Math.max(0, data.indexOf(point) - 6), data.indexOf(point) + 1)
				.reduce((sum, p) => sum + p.cumulativePL, 0) / 
				Math.min(7, data.indexOf(point) + 1)
		}))
	}, [data])

	const maxDrawdown = useMemo(() => {
		let peak = 0
		let maxDD = 0
		for (const point of data) {
			if (point.cumulativePL > peak) {
				peak = point.cumulativePL
			}
			const drawdown = peak - point.cumulativePL
			if (drawdown > maxDD) {
				maxDD = drawdown
			}
		}
		return maxDD
	}, [data])

	const handleZoomIn = () => {
		setZoomLevel(prev => Math.min(prev * 1.5, 5))
	}

	const handleZoomOut = () => {
		setZoomLevel(prev => Math.max(prev / 1.5, 0.5))
	}

	const handleResetZoom = () => {
		setZoomLevel(1)
		setBrushSelection({})
	}

	if (loading) {
		return (
			<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
				<div className="flex items-center justify-center" style={{ height }}>
					<div className="text-center">
						<Loader2 className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-2" />
						<p className="text-gray-600 dark:text-gray-400">Loading chart data...</p>
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
							<LineChart className="w-8 h-8 text-gray-400" />
						</div>
						<h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
							No Data Available
						</h3>
						<p className="text-gray-600 dark:text-gray-400">
							No equity curve data to display
						</p>
					</div>
				</div>
			</div>
		)
	}

	const finalValue = data[data.length - 1]?.cumulativePL || 0
	const isPositive = finalValue >= 0

	return (
		<div className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
			{/* Header */}
			<div className="flex items-center justify-between mb-4">
				<div>
					<h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
						Equity Curve
					</h3>
					<div className="flex items-center space-x-4 mt-1">
						<span className="text-sm text-gray-600 dark:text-gray-400">
							Final P/L:
						</span>
						<span className={`text-lg font-bold ${
							isPositive 
								? 'text-green-600 dark:text-green-400' 
								: 'text-red-600 dark:text-red-400'
						}`}>
							{formatCurrency(finalValue)}
						</span>
						{maxDrawdown > 0 && (
							<>
								<span className="text-sm text-gray-600 dark:text-gray-400">
									Max DD:
								</span>
								<span className="text-sm font-medium text-red-600 dark:text-red-400">
									-${maxDrawdown.toLocaleString('en-US', { minimumFractionDigits: 2 })}
								</span>
							</>
						)}
					</div>
				</div>
				
				{showZoom && (
					<div className="flex items-center space-x-2">
						<button
							onClick={handleZoomIn}
							aria-label="Zoom In"
							className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
						>
							<ZoomIn className="w-4 h-4" />
						</button>
						<button
							onClick={handleZoomOut}
							aria-label="Zoom Out"
							className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
						>
							<ZoomOut className="w-4 h-4" />
						</button>
						<button
							onClick={handleResetZoom}
							className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
						>
							Reset Zoom
						</button>
					</div>
				)}
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
							dataKey="formattedDate"
							className="text-xs"
							stroke="currentColor"
							tick={{ fontSize: 12 }}
							angle={-45}
							textAnchor="end"
							height={60}
						/>
						<YAxis
							className="text-xs"
							stroke="currentColor"
							tick={{ fontSize: 12 }}
							tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
						/>
						<Tooltip content={<CustomTooltip />} />
						
						{/* Zero line reference */}
						<ReferenceLine 
							y={0} 
							stroke="currentColor" 
							strokeDasharray="2 2" 
							className="opacity-50"
						/>
						
						{/* Main equity curve */}
						<Line
							type="monotone"
							dataKey="cumulativePL"
							stroke={isPositive ? "#10b981" : "#ef4444"}
							strokeWidth={2}
							dot={false}
							activeDot={{ 
								r: 4, 
								stroke: isPositive ? "#10b981" : "#ef4444",
								strokeWidth: 2,
								fill: "white"
							}}
						/>
						
						{/* 7-day moving average trend line */}
						<Line
							type="monotone"
							dataKey="movingAverage"
							stroke="#6b7280"
							strokeWidth={1}
							strokeDasharray="5 5"
							dot={false}
							activeDot={false}
						/>
						
						{/* Brush for zooming */}
						{showZoom && (
							<Brush
								dataKey="formattedDate"
								height={30}
								stroke="#6b7280"
								onChange={(range) => setBrushSelection(range)}
							/>
						)}
					</LineChart>
				</ResponsiveContainer>
			</div>

			{/* Chart info */}
			<div className="mt-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
				<span>
					{data.length} data points • {formatDate(data[0].date)} to {formatDate(data[data.length - 1].date)}
				</span>
				<div className="flex items-center space-x-4">
					<div className="flex items-center space-x-1">
						<div className="w-3 h-0.5 bg-green-500"></div>
						<span>Equity Curve</span>
					</div>
					<div className="flex items-center space-x-1">
						<div className="w-3 h-0.5 bg-gray-400 opacity-60" style={{ backgroundImage: 'repeating-linear-gradient(to right, transparent, transparent 2px, currentColor 2px, currentColor 4px)' }}></div>
						<span>7-Day MA</span>
					</div>
				</div>
			</div>
		</div>
	)
}