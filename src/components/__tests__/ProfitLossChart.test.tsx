import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ProfitLossChart } from '../ProfitLossChart'
import type { IronCondorPosition } from '../../utils/ironCondorCalculations'

// Mock Recharts to avoid SVG rendering issues in tests
vi.mock('recharts', () => ({
	ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
		<div data-testid="responsive-container">{children}</div>
	),
	LineChart: ({ children, data }: { children: React.ReactNode, data: any[] }) => (
		<div data-testid="line-chart" data-points={data?.length || 0}>
			{children}
		</div>
	),
	Line: ({ dataKey, stroke }: { dataKey: string, stroke: string }) => (
		<div data-testid={`line-${dataKey}`} data-stroke={stroke} />
	),
	XAxis: ({ dataKey }: { dataKey: string }) => (
		<div data-testid="x-axis" data-key={dataKey} />
	),
	YAxis: ({ tickFormatter }: { tickFormatter?: (value: number) => string }) => (
		<div data-testid="y-axis" data-formatter={tickFormatter ? 'present' : 'absent'} />
	),
	CartesianGrid: () => <div data-testid="cartesian-grid" />,
	Tooltip: ({ content }: { content: any }) => (
		<div data-testid="tooltip" data-custom-content={content ? 'custom' : 'default'} />
	),
	ReferenceLine: ({ y, x, label }: { y?: number, x?: number, label?: string }) => (
		<div data-testid={`reference-line-${label || 'unlabeled'}`} data-y={y} data-x={x} />
	)
}))

describe('ProfitLossChart', () => {
	const mockPosition: IronCondorPosition = {
		putLongStrike: 4900,
		putShortStrike: 4950,
		callShortStrike: 5050,
		callLongStrike: 5100,
		credit: 25,
		contracts: 1
	}

	const mockCurrentPrice = 5000

	beforeEach(() => {
		vi.clearAllMocks()
	})

	it('should render without crashing', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
		expect(screen.getByTestId('line-chart')).toBeInTheDocument()
	})

	it('should display chart title and subtitle', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		expect(screen.getByText('Profit/Loss Chart')).toBeInTheDocument()
		expect(screen.getByText(/Iron Condor Strategy/)).toBeInTheDocument()
	})

	it('should show loading state', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
				loading={true}
			/>
		)
		
		expect(screen.getByText('Loading chart data...')).toBeInTheDocument()
		expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
	})

	it('should display max profit and max loss in header', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Max profit should be the credit (25)
		expect(screen.getByText(/Max Profit:/)).toBeInTheDocument()
		expect(screen.getByText('+$25')).toBeInTheDocument()
		
		// Max loss should be spread width - credit (50 - 25 = -25)
		expect(screen.getByText(/Max Loss:/)).toBeInTheDocument()
		expect(screen.getByText('-$25')).toBeInTheDocument()
	})

	it('should display breakeven points', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Lower breakeven: 4950 - 25 = 4925
		// Upper breakeven: 5050 + 25 = 5075
		expect(screen.getByText(/Breakevens:/)).toBeInTheDocument()
		expect(screen.getByText('$4,925')).toBeInTheDocument()
		expect(screen.getByText('$5,075')).toBeInTheDocument()
	})

	it('should render chart components with correct data', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Check that chart has data points
		const chart = screen.getByTestId('line-chart')
		const dataPoints = chart.getAttribute('data-points')
		expect(Number(dataPoints)).toBeGreaterThan(0)
		
		// Check axes are configured
		expect(screen.getByTestId('x-axis')).toHaveAttribute('data-key', 'price')
		expect(screen.getByTestId('y-axis')).toHaveAttribute('data-formatter', 'present')
		
		// Check P/L line exists
		expect(screen.getByTestId('line-pnl')).toBeInTheDocument()
	})

	it('should render reference lines for breakevens and current price', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Should have reference lines for breakevens and current price
		expect(screen.getByTestId('reference-line-Lower Breakeven')).toBeInTheDocument()
		expect(screen.getByTestId('reference-line-Upper Breakeven')).toBeInTheDocument()
		expect(screen.getByTestId('reference-line-Current Price')).toBeInTheDocument()
		expect(screen.getByTestId('reference-line-unlabeled')).toBeInTheDocument() // Zero line
	})

	it('should handle empty position gracefully', () => {
		const emptyPosition: IronCondorPosition = {
			putLongStrike: 0,
			putShortStrike: 0,
			callShortStrike: 0,
			callLongStrike: 0,
			credit: 0,
			contracts: 0
		}

		render(
			<ProfitLossChart
				position={emptyPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Should still render without crashing
		expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
	})

	it('should apply custom height and className', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
				height={300}
				className="custom-chart-class"
			/>
		)
		
		const chartContainer = screen.getByTestId('responsive-container').parentElement
		expect(chartContainer).toHaveClass('custom-chart-class')
	})

	it('should show correct profit zones in legend', () => {
		render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Check legend elements
		expect(screen.getByText('P/L Curve')).toBeInTheDocument()
		expect(screen.getByText('Breakeven')).toBeInTheDocument()
		expect(screen.getByText('Current Price')).toBeInTheDocument()
	})

	it('should handle multiple contracts correctly', () => {
		const multiContractPosition = { ...mockPosition, contracts: 2 }
		
		render(
			<ProfitLossChart
				position={multiContractPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Max profit should be doubled
		expect(screen.getByText('+$50')).toBeInTheDocument() // 25 * 2
		expect(screen.getByText('-$50')).toBeInTheDocument() // -25 * 2
	})

	it('should update when position changes', () => {
		const { rerender } = render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Initial max profit
		expect(screen.getByText('+$25')).toBeInTheDocument()
		
		// Update position with different credit
		const updatedPosition = { ...mockPosition, credit: 35 }
		rerender(
			<ProfitLossChart
				position={updatedPosition}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Should show updated max profit
		expect(screen.getByText('+$35')).toBeInTheDocument()
	})

	it('should render with different current prices', () => {
		const { rerender } = render(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={5000}
			/>
		)
		
		// Initial current price reference line
		expect(screen.getByTestId('reference-line-Current Price')).toHaveAttribute('data-y', '5000')
		
		// Update current price
		rerender(
			<ProfitLossChart
				position={mockPosition}
				currentPrice={5100}
			/>
		)
		
		// Should update reference line
		expect(screen.getByTestId('reference-line-Current Price')).toHaveAttribute('data-y', '5100')
	})
})