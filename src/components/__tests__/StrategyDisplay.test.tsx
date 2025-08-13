// Comprehensive tests for strategy display components
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StrategyCard } from '../StrategyCard'
import { StrategyList } from '../StrategyList'
import { StrategyData } from '../../types/strategy'

// Mock data for testing
const mockStrategyData: StrategyData = {
	id: '1',
	name: 'SPY Iron Condor Daily',
	strategy_type: 'iron_condor',
	symbol: 'SPY',
	timeframe: 'daily',
	parameters: { put_short: 0.975, call_short: 1.02, credit: 25 },
	performance: {
		total_pnl: 2450.50,
		win_rate: 68.5,
		total_trades: 45,
		avg_pnl_per_trade: 54.45,
		sharpe_ratio: 1.35,
		max_drawdown: -580.25
	},
	is_active: true,
	created_at: '2025-07-30T12:00:00Z',
	updated_at: '2025-07-30T12:00:00Z'
}

const mockNegativePnlStrategy: StrategyData = {
	...mockStrategyData,
	id: '2',
	name: 'Losing Strategy',
	performance: {
		...mockStrategyData.performance,
		total_pnl: -1250.75,
		avg_pnl_per_trade: -27.79,
		win_rate: 35.2
	},
	is_active: false
}

const mockStrategies: StrategyData[] = [mockStrategyData, mockNegativePnlStrategy]

describe('StrategyCard Component', () => {
	it('renders strategy card with all required information', () => {
		render(<StrategyCard strategy={mockStrategyData} />)
		
		// Check header information
		expect(screen.getByText('SPY Iron Condor Daily')).toBeInTheDocument()
		expect(screen.getByText('Iron Condor')).toBeInTheDocument()
		expect(screen.getByText('Daily (0DTE)')).toBeInTheDocument()
		expect(screen.getByText('SPY')).toBeInTheDocument()
		
		// Check performance metrics
		expect(screen.getByText('+$2,450.50')).toBeInTheDocument()
		expect(screen.getByText('68.5%')).toBeInTheDocument()
		expect(screen.getByText('+$54.45')).toBeInTheDocument()
		expect(screen.getByText('45')).toBeInTheDocument()
	})

	it('displays negative P&L correctly with proper styling', () => {
		render(<StrategyCard strategy={mockNegativePnlStrategy} />)
		
		// Check negative values are formatted and styled correctly (they show as positive values but with red styling)
		const totalPnl = screen.getByText('$1,250.75')
		const avgPnl = screen.getByText('$27.79')
		
		expect(totalPnl).toBeInTheDocument()
		expect(totalPnl).toHaveClass('text-red-600')
		expect(avgPnl).toBeInTheDocument()
		expect(avgPnl).toHaveClass('text-red-600')
	})

	it('shows active status indicator for active strategies', () => {
		render(<StrategyCard strategy={mockStrategyData} />)
		
		// Active indicator should be present
		const activeIndicator = document.querySelector('.bg-green-500')
		expect(activeIndicator).toBeInTheDocument()
	})

	it('hides active status indicator for inactive strategies', () => {
		render(<StrategyCard strategy={mockNegativePnlStrategy} />)
		
		// Active indicator should not be present
		const activeIndicator = document.querySelector('.bg-green-500')
		expect(activeIndicator).not.toBeInTheDocument()
	})

	it('displays detailed information when showDetails is true', () => {
		render(<StrategyCard strategy={mockStrategyData} showDetails={true} />)
		
		// Check detailed metrics
		expect(screen.getByText('Sharpe Ratio:')).toBeInTheDocument()
		expect(screen.getByText('1.35')).toBeInTheDocument()
		expect(screen.getByText('Max Drawdown:')).toBeInTheDocument()
		expect(screen.getByText('$580.25')).toBeInTheDocument() // Shows as positive with red styling
		
		// Check parameters section
		expect(screen.getByText('Parameters')).toBeInTheDocument()
	})

	it('handles click events correctly', async () => {
		const user = userEvent.setup()
		const onClickMock = vi.fn()
		
		render(<StrategyCard strategy={mockStrategyData} onClick={onClickMock} />)
		
		// Get the card by its data-testid instead of role since there are multiple buttons now
		const card = screen.getByTestId('strategy-card-1')
		await user.click(card)
		
		expect(onClickMock).toHaveBeenCalledTimes(1)
	})

	it('handles keyboard navigation (Enter key)', async () => {
		const user = userEvent.setup()
		const onClickMock = vi.fn()
		
		render(<StrategyCard strategy={mockStrategyData} onClick={onClickMock} />)
		
		// Get the card by its data-testid instead of role since there are multiple buttons now
		const card = screen.getByTestId('strategy-card-1')
		card.focus()
		await user.keyboard('{Enter}')
		
		expect(onClickMock).toHaveBeenCalledTimes(1)
	})

	it('handles keyboard navigation (Space key)', async () => {
		const user = userEvent.setup()
		const onClickMock = vi.fn()
		
		render(<StrategyCard strategy={mockStrategyData} onClick={onClickMock} />)
		
		// Get the card by its data-testid instead of role since there are multiple buttons now
		const card = screen.getByTestId('strategy-card-1')
		card.focus()
		await user.keyboard(' ')
		
		expect(onClickMock).toHaveBeenCalledTimes(1)
	})

	it('displays different strategy types correctly', () => {
		const bullCallStrategy: StrategyData = {
			...mockStrategyData,
			strategy_type: 'bull_call',
			name: 'SPY Bull Call'
		}
		
		render(<StrategyCard strategy={bullCallStrategy} />)
		
		expect(screen.getByText('Bull Call Spread')).toBeInTheDocument()
	})

	it('displays different timeframes correctly', () => {
		const weeklyStrategy: StrategyData = {
			...mockStrategyData,
			timeframe: 'weekly'
		}
		
		render(<StrategyCard strategy={weeklyStrategy} />)
		
		expect(screen.getByText('Weekly')).toBeInTheDocument()
	})
})

describe('StrategyList Component', () => {
	it('renders loading state correctly', () => {
		render(<StrategyList strategies={[]} loading={true} />)
		
		expect(screen.getByText('Loading strategies...')).toBeInTheDocument()
		// Check that loading spinner is present (Loader2 icon)
		const loader = document.querySelector('.animate-spin')
		expect(loader).toBeInTheDocument()
	})

	it('renders error state correctly', () => {
		const errorMessage = 'Failed to load strategies'
		
		render(<StrategyList strategies={[]} error={errorMessage} />)
		
		expect(screen.getByText('Error Loading Strategies')).toBeInTheDocument()
		expect(screen.getByText(errorMessage)).toBeInTheDocument()
		expect(screen.getByText('Try Again')).toBeInTheDocument()
	})

	it('renders empty state correctly', () => {
		render(<StrategyList strategies={[]} />)
		
		expect(screen.getByText('No Strategies Found')).toBeInTheDocument()
		expect(screen.getByText(/No trading strategies are currently available/)).toBeInTheDocument()
	})

	it('renders strategy list with summary statistics', () => {
		render(<StrategyList strategies={mockStrategies} />)
		
		// Check summary header
		expect(screen.getByText('Strategy Portfolio')).toBeInTheDocument()
		expect(screen.getByText('2')).toBeInTheDocument() // Total strategies
		expect(screen.getByText('1')).toBeInTheDocument() // Active strategies
		
		// Check calculated total P&L (2450.50 - 1250.75 = 1199.75)
		expect(screen.getByText('+$1,199.75')).toBeInTheDocument()
		
		// Check average win rate ((68.5 + 35.2) / 2 = 51.85)
		expect(screen.getByText('51.9%')).toBeInTheDocument()
	})

	it('renders all strategy cards in grid layout', () => {
		render(<StrategyList strategies={mockStrategies} />)
		
		// Check that both strategies are rendered
		expect(screen.getByText('SPY Iron Condor Daily')).toBeInTheDocument()
		expect(screen.getByText('Losing Strategy')).toBeInTheDocument()
		
		// Check cards grid container exists (second grid in the component)
		const grids = document.querySelectorAll('.grid')
		const cardsGrid = grids[1] // Second grid is the cards grid
		expect(cardsGrid).toBeInTheDocument()
		expect(cardsGrid).toHaveClass('grid-cols-1', 'lg:grid-cols-2', 'xl:grid-cols-3')
	})

	it('handles strategy selection correctly', async () => {
		const user = userEvent.setup()
		const onStrategySelectMock = vi.fn()
		
		render(
			<StrategyList 
				strategies={mockStrategies} 
				onStrategySelect={onStrategySelectMock}
			/>
		)
		
		const firstStrategyCard = screen.getByText('SPY Iron Condor Daily').closest('[role="button"]')
		expect(firstStrategyCard).toBeInTheDocument()
		
		await user.click(firstStrategyCard!)
		
		expect(onStrategySelectMock).toHaveBeenCalledTimes(1)
		expect(onStrategySelectMock).toHaveBeenCalledWith(mockStrategyData)
	})

	it('displays footer information correctly', () => {
		render(<StrategyList strategies={mockStrategies} />)
		
		expect(screen.getByText('Showing 2 strategies')).toBeInTheDocument()
		expect(screen.getByText('• 1 active, 1 inactive')).toBeInTheDocument()
	})

	it('handles single strategy count correctly', () => {
		render(<StrategyList strategies={[mockStrategyData]} />)
		
		expect(screen.getByText('Showing 1 strategy')).toBeInTheDocument()
	})

	it('calculates negative total P&L correctly', () => {
		const negativeStrategies = [
			mockNegativePnlStrategy, 
			{ ...mockNegativePnlStrategy, id: '3', name: 'Another Losing Strategy' }
		]
		
		render(<StrategyList strategies={negativeStrategies} />)
		
		// Total should be -2501.50 (2 * -1250.75) - check for negative value text and its styling
		// Use a text matcher function to handle the split text nodes
		const totalPnlContainer = screen.getByText((content, element) => {
			return element?.textContent === '$-2,501.50'
		})
		expect(totalPnlContainer).toBeInTheDocument()
		expect(totalPnlContainer).toHaveClass('text-2xl', 'font-bold', 'text-red-600', 'dark:text-red-400')
	})

	it('handles try again button click in error state', async () => {
		const user = userEvent.setup()
		
		// Mock window.location.reload
		const reloadMock = vi.fn()
		Object.defineProperty(window, 'location', {
			value: { reload: reloadMock },
			writable: true
		})
		
		render(<StrategyList strategies={[]} error="Test error" />)
		
		const tryAgainButton = screen.getByText('Try Again')
		await user.click(tryAgainButton)
		
		expect(reloadMock).toHaveBeenCalledTimes(1)
	})
})

describe('Component Integration Tests', () => {
	it('strategy cards within strategy list maintain proper styling', () => {
		render(<StrategyList strategies={mockStrategies} />)
		
		// Check that strategy cards have proper styling classes
		const cards = document.querySelectorAll('.bg-white.dark\\:bg-gray-800')
		expect(cards.length).toBeGreaterThan(0)
		
		// Check hover effects are present
		const hoverableCard = document.querySelector('.hover\\:shadow-md')
		expect(hoverableCard).toBeInTheDocument()
	})

	it('maintains accessibility standards', () => {
		render(<StrategyList strategies={mockStrategies} onStrategySelect={vi.fn()} />)
		
		// Check that clickable cards have proper roles
		const cards = screen.getAllByTestId(/strategy-card-/)
		expect(cards.length).toBe(2) // Two strategy cards
		
		// Check tabIndex is set for keyboard navigation
		cards.forEach(card => {
			expect(card).toHaveAttribute('tabIndex', '0')
		})
	})

	it('handles empty performance data gracefully', () => {
		const strategyWithMinimalPerformance: StrategyData = {
			...mockStrategyData,
			performance: {
				total_pnl: 0,
				win_rate: 0,
				total_trades: 0,
				avg_pnl_per_trade: 0
			}
		}
		
		render(<StrategyCard strategy={strategyWithMinimalPerformance} />)
		
		// Check for zero values - there might be multiple instances
		const zeroValueElements = screen.getAllByText('+$0.00')
		expect(zeroValueElements.length).toBeGreaterThan(0)
		expect(screen.getByText('0.0%')).toBeInTheDocument()
		expect(screen.getByText('0')).toBeInTheDocument()
	})
})
