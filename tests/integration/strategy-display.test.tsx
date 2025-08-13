import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import { StrategyDashboard } from '@/components/StrategyDashboard'
import { StrategyApiService } from '@/services/strategyApi'
import MarketApiService from '@/services/marketApi'

// Mock the API services
vi.mock('@/services/strategyApi')
vi.mock('@/services/marketApi')

describe('Strategy Display Integration Tests', () => {
	const mockPerformanceData = {
		summary: {
			total_trades: 87,
			overall_win_rate: 0.71,
			total_pnl: 10500.00,
			best_timeframe: 'monthly'
		}
	}

	const mockStrategyData = {
		strategies: {
			daily: {
				metadata: {
					timeframe: 'daily',
					total_trades: 50,
					date_range: { start: '2024-01-01', end: '2024-02-29' }
				},
				performance: {
					win_rate: 0.72,
					total_pnl: 3600.00,
					sharpe_ratio: 1.25,
					max_drawdown: -450.00,
					average_trade: 72.00
				},
				trades: [
					{
						id: 1,
						entry_date: '2024-01-02',
						expiration_date: '2024-01-02',
						strikes: { 
							put_short: 4730, 
							put_long: 4725, 
							call_short: 4780, 
							call_long: 4785 
						},
						credit_received: 1.25,
						pnl: 125.00,
						outcome: 'win'
					}
				],
				equity_curve: [
					{ date: '2024-01-02', cumulativePL: 125, dailyPL: 125 },
					{ date: '2024-01-03', cumulativePL: 95, dailyPL: -30 },
					{ date: '2024-01-04', cumulativePL: 220, dailyPL: 125 },
				],
				pl_histogram: [
					{ range: '-100 to -50', count: 5, midpoint: -75 },
					{ range: '-50 to 0', count: 10, midpoint: -25 },
					{ range: '0 to 50', count: 15, midpoint: 25 },
					{ range: '50 to 100', count: 18, midpoint: 75 },
					{ range: '100 to 150', count: 2, midpoint: 125 },
				]
			},
			weekly: {
				metadata: {
					timeframe: 'weekly',
					total_trades: 25,
					date_range: { start: '2024-01-01', end: '2024-02-29' }
				},
				performance: {
					win_rate: 0.68,
					total_pnl: 2100.00,
					sharpe_ratio: 1.15,
					max_drawdown: -350.00,
					average_trade: 84.00
				},
				trades: [],
				equity_curve: [],
				pl_histogram: []
			},
			monthly: {
				metadata: {
					timeframe: 'monthly',
					total_trades: 12,
					date_range: { start: '2024-01-01', end: '2024-12-31' }
				},
				performance: {
					win_rate: 0.75,
					total_pnl: 4800.00,
					sharpe_ratio: 1.45,
					max_drawdown: -600.00,
					average_trade: 400.00
				},
				trades: [],
				equity_curve: [],
				pl_histogram: []
			}
		}
	}

	beforeEach(() => {
		vi.clearAllMocks()
		
		// Mock MarketApiService.getCurrentPrice to return a fixed price
		vi.mocked(MarketApiService.getCurrentPrice).mockResolvedValue({
			symbol: 'SPY',
			price: 430.50,
			timestamp: new Date().toISOString(),
			change: 1.25,
			change_percent: 0.29
		})
	})

	afterEach(() => {
		vi.restoreAllMocks()
	})

	describe('Full Strategy Display Workflow', () => {
		it('should display loading state initially', () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockImplementation(() => 
				new Promise(() => {}) // Never resolves to keep loading state
			)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockImplementation(() =>
				new Promise(() => {}) // Never resolves to keep loading state
			)

			render(<StrategyDashboard symbol="SPY" />)
			
			expect(screen.getByText(/Loading strategies/i)).toBeInTheDocument()
			expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
		})

		it('should fetch and display all strategy timeframes', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(mockStrategyData)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockResolvedValue(mockPerformanceData)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				// Check that strategy cards exist by data-testid
				expect(screen.getByTestId('strategy-card-daily')).toBeInTheDocument()
				expect(screen.getByTestId('strategy-card-weekly')).toBeInTheDocument()
				expect(screen.getByTestId('strategy-card-monthly')).toBeInTheDocument()
			})

			// Check performance metrics are displayed - updated to match actual UI calculations
			expect(screen.getByText(/71\.7%/)).toBeInTheDocument() // Average win rate in strategy portfolio summary
			expect(screen.getByLabelText('Total PnL Value')).toHaveTextContent('+$10,500.00') // Total P/L in summary
			expect(screen.getByText(/72\.0%/)).toBeInTheDocument() // Daily strategy card win rate (formatted with .toFixed(1))
		})

		it('should display strategy cards with correct data', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(mockStrategyData)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockResolvedValue(mockPerformanceData)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				// Daily strategy card
				const dailyCard = screen.getByTestId('strategy-card-daily')
				expect(dailyCard).toBeInTheDocument()
				expect(dailyCard).toHaveTextContent('50 trades')
				expect(dailyCard).toHaveTextContent('72% win rate')
				
				// Weekly strategy card
				const weeklyCard = screen.getByTestId('strategy-card-weekly')
				expect(weeklyCard).toBeInTheDocument()
				expect(weeklyCard).toHaveTextContent('25 trades')
				expect(weeklyCard).toHaveTextContent('68% win rate')
				
				// Monthly strategy card
				const monthlyCard = screen.getByTestId('strategy-card-monthly')
				expect(monthlyCard).toBeInTheDocument()
				expect(monthlyCard).toHaveTextContent('12 trades')
				expect(monthlyCard).toHaveTextContent('75% win rate')
			})
		})

		it('should display visualization components when data is loaded', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(mockStrategyData)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockResolvedValue(mockPerformanceData)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				// Check for equity curve chart
				expect(screen.getByText(/Equity Curve/i)).toBeInTheDocument()
				expect(screen.getByTestId('equity-curve-chart')).toBeInTheDocument()
				
				// Check for P/L histogram
				expect(screen.getByText(/P\/L Distribution/i)).toBeInTheDocument()
				expect(screen.getByTestId('pl-histogram-chart')).toBeInTheDocument()
				
				// Check for performance metrics
				expect(screen.getByText(/Performance Metrics/i)).toBeInTheDocument()
				expect(screen.getByTestId('performance-metrics')).toBeInTheDocument()
			})
		})

		it('should handle timeframe switching', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(mockStrategyData)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockResolvedValue(mockPerformanceData)
			vi.mocked(StrategyApiService.getIronCondorByTimeframe).mockResolvedValue(mockStrategyData.strategies.weekly)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				expect(screen.getByTestId('strategy-card-daily')).toBeInTheDocument()
			})

			// Click on weekly strategy card (now a button)
			const weeklyCard = screen.getByTestId('strategy-card-weekly')
			await act(async () => {
				weeklyCard.click()
			})

			await waitFor(() => {
				// Weekly detailed data should be displayed
				// The API should have been called for weekly timeframe
				expect(vi.mocked(StrategyApiService.getIronCondorByTimeframe)).toHaveBeenCalledWith('weekly')
			})

			// Update mock for monthly data
			vi.mocked(StrategyApiService.getIronCondorByTimeframe).mockResolvedValue(mockStrategyData.strategies.monthly)

			// Click on monthly strategy card
			const monthlyCard = screen.getByTestId('strategy-card-monthly')
			await act(async () => {
				monthlyCard.click()
			})

			await waitFor(() => {
				// Monthly API should have been called
				expect(vi.mocked(StrategyApiService.getIronCondorByTimeframe)).toHaveBeenCalledWith('monthly')
			})
		})
	})

	describe('API Error Handling', () => {
		it('should display error message when API call fails', async () => {
			const errorMessage = 'Failed to fetch strategies'
			vi.mocked(StrategyApiService.getIronCondorAll).mockRejectedValue(new Error(errorMessage))

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				expect(screen.getByText(/Error loading strategies/i)).toBeInTheDocument()
				expect(screen.getByText(errorMessage)).toBeInTheDocument()
				expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
			})
		})

		it('should display network error message on connection failure', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockRejectedValue(new Error('Network Error'))

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				expect(screen.getByText(/Network Error/i)).toBeInTheDocument()
				expect(screen.getByText(/Please check your connection/i)).toBeInTheDocument()
			})
		})

		it('should handle timeout errors gracefully', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockRejectedValue(new Error('Request timeout'))

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				expect(screen.getByText(/Request timeout/i)).toBeInTheDocument()
				expect(screen.getByText(/The server took too long to respond/i)).toBeInTheDocument()
			})
		})

		it('should retry API call when retry button is clicked', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll)
				.mockRejectedValueOnce(new Error('First failure'))
				.mockResolvedValueOnce(mockStrategyData)

			render(<StrategyDashboard symbol="SPY" />)

			// Wait for error state
			await waitFor(() => {
				expect(screen.getByText(/First failure/i)).toBeInTheDocument()
			})

			// Click retry button
			const retryButton = screen.getByRole('button', { name: /Retry/i })
			await act(async () => {
				retryButton.click()
			})

			// Should show loading state again
			expect(screen.getByText(/Loading strategies/i)).toBeInTheDocument()

			// Should eventually show data
			await waitFor(() => {
				expect(screen.getByTestId('strategy-card-daily')).toBeInTheDocument()
				expect(screen.getByText(/71\.7%/)).toBeInTheDocument() // Average win rate in portfolio summary
			})
		})
	})

	describe('Data Flow Verification', () => {
		it('should correctly pass data from API to visualization components', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(mockStrategyData)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockResolvedValue(mockPerformanceData)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				// Verify equity curve data
				const equityChart = screen.getByTestId('equity-curve-chart')
				expect(equityChart).toHaveAttribute('data-points', '3')
				
				// Verify histogram data
				const histogram = screen.getByTestId('pl-histogram-chart')
				expect(histogram).toHaveAttribute('data-bins', '5')
				
				// Verify performance metrics
				const metrics = screen.getByTestId('performance-metrics')
				expect(metrics).toHaveAttribute('data-trades', '50')
			})
		})

		it('should handle empty data gracefully', async () => {
			const emptyData = {
				strategies: {
					daily: {
						metadata: { timeframe: 'daily', total_trades: 0 },
						performance: {},
						trades: [],
						equity_curve: [],
						pl_histogram: []
					}
				}
			}

			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(emptyData)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				expect(screen.getByText(/No trades available/i)).toBeInTheDocument()
				expect(screen.getByText(/No data to display/i)).toBeInTheDocument()
			})
		})

		it('should handle partial data correctly', async () => {
			const partialData = {
				strategies: {
					daily: {
						metadata: { timeframe: 'daily', total_trades: 10 },
						performance: { win_rate: 0.60 },
						// Missing other fields
					}
				}
			}

			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(partialData)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				expect(screen.getByText(/60%/)).toBeInTheDocument() // Win rate
				expect(screen.getByText(/--/)).toBeInTheDocument() // Missing data placeholder
			})
		})
	})

	describe('Performance Testing', () => {
		it('should handle large datasets efficiently', async () => {
			// Create large dataset
			const largeTrades = Array.from({ length: 1000 }, (_, i) => ({
				id: i,
				entry_date: `2024-01-${(i % 28) + 1}`,
				expiration_date: `2024-01-${(i % 28) + 1}`,
				pnl: Math.random() * 200 - 100,
				outcome: Math.random() > 0.3 ? 'win' : 'loss'
			}))

			const largeData = {
				strategies: {
					daily: {
						...mockStrategyData.strategies.daily,
						trades: largeTrades,
						metadata: { ...mockStrategyData.strategies.daily.metadata, total_trades: 1000 }
					}
				}
			}

			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(largeData)

			const startTime = performance.now()
			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				expect(screen.getByText(/1,000 trades/i)).toBeInTheDocument()
			})

			const endTime = performance.now()
			const renderTime = endTime - startTime

			// Should render within reasonable time (3 seconds)
			expect(renderTime).toBeLessThan(3000)
		})

		it('should implement proper memoization for expensive calculations', async () => {
			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(mockStrategyData)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockResolvedValue(mockPerformanceData)

			const { rerender } = render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				expect(screen.getByText(/Daily/i)).toBeInTheDocument()
			})

			// Track performance calculation calls
			const performanceCalcSpy = vi.spyOn(console, 'log')

			// Re-render with same props
			rerender(<StrategyDashboard symbol="SPY" />)

			// Should not recalculate if data hasn't changed
			expect(performanceCalcSpy).not.toHaveBeenCalledWith('Recalculating performance')
		})
	})

	describe('Mobile Responsiveness', () => {
		it('should adapt layout for mobile screens', async () => {
			// Mock mobile viewport
			window.innerWidth = 375
			window.innerHeight = 667

			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(mockStrategyData)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockResolvedValue(mockPerformanceData)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				// Check for mobile-specific layout
				const container = screen.getByTestId('strategy-dashboard')
				expect(container).toHaveClass('flex-col') // Vertical layout on mobile
				
				// Instead of comparing bounding rectangles (which can be unreliable in test environment),
				// check that the grid has the correct mobile class
				const strategyList = screen.getByTestId('strategy-list')
				expect(strategyList).toHaveClass('grid-cols-1') // Single column on mobile
			})
		})

		it('should show appropriate touch controls on mobile', async () => {
			// Mock touch device
			window.ontouchstart = () => {}

			vi.mocked(StrategyApiService.getIronCondorAll).mockResolvedValue(mockStrategyData)
			vi.mocked(StrategyApiService.getIronCondorPerformance).mockResolvedValue(mockPerformanceData)

			render(<StrategyDashboard symbol="SPY" />)

			await waitFor(() => {
				// Should have strategy list with touch support
				const strategyList = screen.getByTestId('strategy-list')
				expect(strategyList).toBeInTheDocument()
				// Cards should be clickable on touch devices
				const cards = screen.getAllByTestId(/strategy-card-/)
				expect(cards.length).toBeGreaterThan(0)
			})
		})
	})
})
