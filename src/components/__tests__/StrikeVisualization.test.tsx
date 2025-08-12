import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { StrikeVisualization } from '../StrikeVisualization'
import type { StrikeConfig } from '../../types/strategy'

// Mock ProfitLossChart to focus on StrikeVisualization integration
vi.mock('../ProfitLossChart', () => ({
	ProfitLossChart: ({ position, currentPrice, loading }: any) => (
		<div 
			data-testid="profit-loss-chart" 
			data-current-price={currentPrice}
			data-loading={loading}
			data-put-long={position.putLongStrike}
			data-put-short={position.putShortStrike}
			data-call-short={position.callShortStrike}
			data-call-long={position.callLongStrike}
			data-credit={position.credit}
			data-contracts={position.contracts}
		>
			Mocked P/L Chart
		</div>
	)
}))

describe('StrikeVisualization', () => {
	const mockStrikes: StrikeConfig = {
		put_long_pct: 96,
		put_short_pct: 98,
		call_short_pct: 102,
		call_long_pct: 104
	}

	const mockCurrentPrice = 5000
	const defaultCredit = 25

	beforeEach(() => {
		vi.clearAllMocks()
	})

	it('should render without crashing', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		expect(screen.getByTestId('profit-loss-chart')).toBeInTheDocument()
		expect(screen.getByText('Strike Visualization')).toBeInTheDocument()
	})

	it('should display current market price', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		expect(screen.getByText('Current Price:')).toBeInTheDocument()
		expect(screen.getByText('$5,000')).toBeInTheDocument()
	})

	it('should convert strike percentages to prices correctly', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		const chart = screen.getByTestId('profit-loss-chart')
		
		// Check converted strike prices (rounded to nearest 5)
		expect(chart).toHaveAttribute('data-put-long', '4800') // 96% of 5000 = 4800
		expect(chart).toHaveAttribute('data-put-short', '4900') // 98% of 5000 = 4900  
		expect(chart).toHaveAttribute('data-call-short', '5100') // 102% of 5000 = 5100
		expect(chart).toHaveAttribute('data-call-long', '5200') // 104% of 5000 = 5200
	})

	it('should use default credit and contracts', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		const chart = screen.getByTestId('profit-loss-chart')
		expect(chart).toHaveAttribute('data-credit', '25') // Default credit
		expect(chart).toHaveAttribute('data-contracts', '1') // Default contracts
	})

	it('should use custom credit when provided', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
				credit={40}
			/>
		)
		
		const chart = screen.getByTestId('profit-loss-chart')
		expect(chart).toHaveAttribute('data-credit', '40')
	})

	it('should use custom contracts when provided', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
				contracts={3}
			/>
		)
		
		const chart = screen.getByTestId('profit-loss-chart')
		expect(chart).toHaveAttribute('data-contracts', '3')
	})

	it('should show loading state', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
				loading={true}
			/>
		)
		
		const chart = screen.getByTestId('profit-loss-chart')
		expect(chart).toHaveAttribute('data-loading', 'true')
		expect(screen.getByText('Calculating...')).toBeInTheDocument()
	})

	it('should display strike levels with proper formatting', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Check strike level display - text is split across elements
		expect(screen.getByText('Strike Levels')).toBeInTheDocument()
		expect(screen.getByText('Put Long:')).toBeInTheDocument()
		expect(screen.getByText('$4,800')).toBeInTheDocument()
		expect(screen.getByText('Put Short:')).toBeInTheDocument()
		expect(screen.getByText('$4,900')).toBeInTheDocument()
		expect(screen.getByText('Call Short:')).toBeInTheDocument()
		expect(screen.getByText('$5,100')).toBeInTheDocument()
		expect(screen.getByText('Call Long:')).toBeInTheDocument()
		expect(screen.getByText('$5,200')).toBeInTheDocument()
	})

	it('should update when strikes change', () => {
		const { rerender } = render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Initial strikes
		const chart = screen.getByTestId('profit-loss-chart')
		expect(chart).toHaveAttribute('data-put-long', '4800')
		
		// Update strikes
		const newStrikes = { ...mockStrikes, put_long_pct: 95 }
		rerender(
			<StrikeVisualization
				strikes={newStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Should reflect new strike
		expect(chart).toHaveAttribute('data-put-long', '4750') // 95% of 5000 = 4750
		expect(screen.getByText('$4,750')).toBeInTheDocument()
	})

	it('should update when current price changes', () => {
		const { rerender } = render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={5000}
			/>
		)
		
		// Initial price
		expect(screen.getByText('$5,000')).toBeInTheDocument()
		
		// Update price
		rerender(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={5500}
			/>
		)
		
		// Should show updated price and recalculated strikes
		expect(screen.getByText('$5,500')).toBeInTheDocument()
		const chart = screen.getByTestId('profit-loss-chart')
		expect(chart).toHaveAttribute('data-put-long', '5280') // 96% of 5500 = 5280
	})

	it('should apply custom className and height', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
				className="custom-viz-class"
				height={600}
			/>
		)
		
		const container = screen.getByTestId('profit-loss-chart').parentElement
		expect(container).toHaveClass('custom-viz-class')
	})

	it('should show risk zones information', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		expect(screen.getByText('Risk Profile')).toBeInTheDocument()
		expect(screen.getByText(/Profit Zone:/)).toBeInTheDocument()
		expect(screen.getByText('$4,900 - $5,100')).toBeInTheDocument() // Between short strikes
	})

	it('should calculate and display spread widths', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		expect(screen.getByText('Spread Information')).toBeInTheDocument()
		expect(screen.getByText('Put Spread Width:')).toBeInTheDocument()
		expect(screen.getByText('Call Spread Width:')).toBeInTheDocument()
		// Check for calculated values (4900 - 4800 = 100, 5200 - 5100 = 100)
		expect(screen.getAllByText('$100')).toHaveLength(2)
	})

	it('should handle invalid strike configurations gracefully', () => {
		const invalidStrikes: StrikeConfig = {
			put_long_pct: 99, // Higher than put_short_pct
			put_short_pct: 98,
			call_short_pct: 102,
			call_long_pct: 104
		}

		render(
			<StrikeVisualization
				strikes={invalidStrikes}
				currentPrice={mockCurrentPrice}
			/>
		)
		
		// Should still render but show validation warning
		expect(screen.getByTestId('profit-loss-chart')).toBeInTheDocument()
		expect(screen.getByText(/Invalid Strike Configuration/)).toBeInTheDocument()
	})

	it('should show percentage values in strike levels', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
				showPercentages={true}
			/>
		)
		
		// Check for percentage values - they are in the same span as price
		expect(screen.getByText('$4,800 (96%)')).toBeInTheDocument()
		expect(screen.getByText('$4,900 (98%)')).toBeInTheDocument()
		expect(screen.getByText('$5,100 (102%)')).toBeInTheDocument()
		expect(screen.getByText('$5,200 (104%)')).toBeInTheDocument()
	})

	it('should handle zero prices gracefully', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={0}
			/>
		)
		
		// Should handle edge case without crashing
		expect(screen.getByTestId('profit-loss-chart')).toBeInTheDocument()
		// Zero price should appear in the current price display
		expect(screen.getAllByText('$0')).toHaveLength(8) // Multiple $0 values in various fields
	})

	it('should calculate profit zone correctly based on breakevens', () => {
		render(
			<StrikeVisualization
				strikes={mockStrikes}
				currentPrice={mockCurrentPrice}
				credit={25}
			/>
		)
		
		// Check breakeven range calculation
		expect(screen.getByText(/Breakeven Range:/)).toBeInTheDocument()
		// Lower breakeven: 4900 - 25 = 4875, Upper breakeven: 5100 + 25 = 5125
		expect(screen.getByText('$4,875 - $5,125')).toBeInTheDocument()
	})
})