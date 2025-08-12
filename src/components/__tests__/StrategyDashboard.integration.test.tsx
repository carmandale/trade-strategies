import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { StrategyDashboard } from '../StrategyDashboard'

// Mock the strategy API
vi.mock('../../services/strategyApi', () => {
  const getIronCondorAll = vi.fn(async () => ({
    strategies: {
      daily: {
        metadata: { timeframe: 'daily', total_trades: 10, date_range: { start: '2024-01-01', end: '2024-02-01' } },
        performance: { win_rate: 0.7, total_pnl: 1000, sharpe_ratio: 1.2, max_drawdown: -200, average_trade: 100 },
        trades: []
      },
      weekly: {
        metadata: { timeframe: 'weekly', total_trades: 5, date_range: { start: '2024-01-01', end: '2024-02-01' } },
        performance: { win_rate: 0.6, total_pnl: 800, sharpe_ratio: 1.0, max_drawdown: -150, average_trade: 160 },
        trades: []
      }
    }
  }))
  
  const getIronCondorPerformance = vi.fn(async () => ({
    summary: {
      total_trades: 15,
      overall_win_rate: 0.6667,
      total_pnl: 1800,
      best_timeframe: 'daily',
      worst_drawdown: -300
    },
    by_timeframe: {
      daily: { win_rate: 0.7, pnl: 1000 },
      weekly: { win_rate: 0.6, pnl: 800 }
    }
  }))
  
  const getIronCondorByTimeframe = vi.fn(async () => ({
    metadata: { timeframe: 'daily', total_trades: 10, date_range: { start: '2024-01-01', end: '2024-02-01' } },
    performance: { win_rate: 0.7, total_pnl: 1000, sharpe_ratio: 1.2, max_drawdown: -200, average_trade: 100 },
    trades: [
      {
        id: 't1',
        entry_date: '2024-01-02',
        expiration_date: '2024-01-02',
        strikes: { put_long: 420, put_short: 425, call_short: 430, call_long: 435 },
        credit_received: 1.25,
        pnl: 125,
        outcome: 'win'
      }
    ]
  }))
  
  // New mock for strike-based calculations
  const calculateIronCondorWithStrikes = vi.fn(async (options: any) => ({
    performance: {
      win_rate: options.strikes ? 0.72 : 0.7, // Slightly different with custom strikes
      total_pnl: options.strikes ? 1100 : 1000,
      sharpe_ratio: 1.25,
      max_drawdown: -180,
      average_trade: 110
    },
    trades: [
      {
        id: 'custom-t1',
        entry_date: '2024-01-02',
        strikes: options.strikes || { put_long: 420, put_short: 425, call_short: 430, call_long: 435 },
        credit_received: 1.30,
        pnl: 130,
        outcome: 'win'
      }
    ]
  }))
  
  return {
    StrategyApiService: {
      getIronCondorAll,
      getIronCondorPerformance,
      getIronCondorByTimeframe,
      calculateIronCondorWithStrikes,
    }
  }
})

// Mock the market data service for current price
vi.mock('../../services/marketApi', () => ({
  MarketApiService: {
    getCurrentPrice: vi.fn(async () => ({ price: 430.50, timestamp: new Date().toISOString() }))
  }
}))

describe('StrategyDashboard Integration with Strike Selection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders strategy dashboard with strike selection when timeframe is selected', async () => {
    const user = userEvent.setup()
    render(<StrategyDashboard symbol="SPY" />)

    // Wait for initial load and select a strategy
    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    await user.click(dailyCard)

    // Should show timeframe details section
    await waitFor(() => {
      expect(screen.getByText(/Iron Condor — Daily/i)).toBeInTheDocument()
    })

    // Should show strike selection controls
    expect(screen.getByText('Strike Selection')).toBeInTheDocument()
    expect(screen.getByText('Put Short Strike (%)')).toBeInTheDocument()
    expect(screen.getByText('Call Short Strike (%)')).toBeInTheDocument()

    // Should show strike visualization
    expect(screen.getByText('Strike Visualization')).toBeInTheDocument()
    expect(screen.getByText('Iron Condor Strategy Analysis')).toBeInTheDocument()
  })

  it('updates strategy calculations when strikes are changed', async () => {
    const user = userEvent.setup()
    const { StrategyApiService } = await import('../../services/strategyApi')
    
    render(<StrategyDashboard symbol="SPY" />)

    // Select daily strategy
    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByText(/Iron Condor — Daily/i)).toBeInTheDocument()
    })

    // Find and modify a strike selector
    const putShortSlider = screen.getByTestId('put-short-slider')
    expect(putShortSlider).toBeInTheDocument()

    // Simulate changing put short strike from default 98% to 97%
    const putShortInput = screen.getByRole('spinbutton', { name: 'Put Short Strike (%)' })
    await user.clear(putShortInput)
    await user.type(putShortInput, '97')

    // Should trigger API call with new strikes after debounce
    await waitFor(() => {
      expect(StrategyApiService.calculateIronCondorWithStrikes).toHaveBeenCalledWith(
        expect.objectContaining({
          timeframe: 'daily',
          strikes: expect.objectContaining({
            put_short_pct: 97
          })
        })
      )
    }, { timeout: 1000 })

    // Should show updated performance metrics
    await waitFor(() => {
      expect(screen.getByLabelText('Timeframe Win Rate Value')).toHaveTextContent('72.0%')
    })
  })

  it('preserves strike selections when switching between strategies', async () => {
    const user = userEvent.setup()
    render(<StrategyDashboard symbol="SPY" />)

    // Select daily strategy
    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByText(/Iron Condor — Daily/i)).toBeInTheDocument()
    })

    // Modify a strike
    const putShortInput = screen.getByLabelText('Put Short Strike (%)')
    await user.clear(putShortInput)
    await user.type(putShortInput, '97')

    // Switch to weekly strategy
    const weeklyCard = screen.getByText('SPY Iron Condor Weekly')
    await user.click(weeklyCard)

    await waitFor(() => {
      expect(screen.getByText(/Iron Condor — Weekly/i)).toBeInTheDocument()
    })

    // Switch back to daily - should preserve the custom strike
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByLabelText('Put Short Strike (%)')).toHaveValue(97)
    })
  })

  it('shows loading states during strike recalculation', async () => {
    const user = userEvent.setup()
    const { StrategyApiService } = await import('../../services/strategyApi')
    
    // Make API call slower to test loading state
    ;(StrategyApiService.calculateIronCondorWithStrikes as any).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        performance: { win_rate: 0.72, total_pnl: 1100, sharpe_ratio: 1.25, max_drawdown: -180, average_trade: 110 },
        trades: []
      }), 500))
    )

    render(<StrategyDashboard symbol="SPY" />)

    // Select strategy
    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByText('Strike Selection')).toBeInTheDocument()
    })

    // Modify strike
    const putShortInput = screen.getByLabelText('Put Short Strike (%)')
    await user.clear(putShortInput)
    await user.type(putShortInput, '96')

    // Should show loading indicator
    expect(screen.getByText('Calculating...')).toBeInTheDocument()

    // Loading should disappear after calculation
    await waitFor(() => {
      expect(screen.queryByText('Calculating...')).not.toBeInTheDocument()
    }, { timeout: 1000 })
  })

  it('handles API errors gracefully during strike recalculation', async () => {
    const user = userEvent.setup()
    const { StrategyApiService } = await import('../../services/strategyApi')
    
    render(<StrategyDashboard symbol="SPY" />)

    // Select strategy
    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByText('Strike Selection')).toBeInTheDocument()
    })

    // Mock API failure
    ;(StrategyApiService.calculateIronCondorWithStrikes as any).mockRejectedValueOnce(
      new Error('Calculation failed')
    )

    // Modify strike
    const putShortInput = screen.getByLabelText('Put Short Strike (%)')
    await user.clear(putShortInput)
    await user.type(putShortInput, '95')

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/calculation failed/i)).toBeInTheDocument()
    })
  })

  it('is responsive on mobile screens', async () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    })
    
    render(<StrategyDashboard symbol="SPY" />)

    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    const user = userEvent.setup()
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByText('Strike Selection')).toBeInTheDocument()
    })

    // Strike controls should be stacked vertically on mobile
    const strikeSelector = screen.getByText('Strike Selection').closest('div')
    expect(strikeSelector).toHaveClass('space-y-6')

    // Visualization should maintain readable layout
    const visualization = screen.getByText('Strike Visualization')
    expect(visualization).toBeInTheDocument()
  })

  it('updates profit/loss chart when strikes change', async () => {
    const user = userEvent.setup()
    render(<StrategyDashboard symbol="SPY" />)

    // Select strategy
    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByText('Strike Visualization')).toBeInTheDocument()
    })

    // Should show profit/loss chart
    expect(screen.getByText('Profit/Loss Chart')).toBeInTheDocument()

    // Modify strike
    const putShortInput = screen.getByLabelText('Put Short Strike (%)')
    await user.clear(putShortInput)
    await user.type(putShortInput, '96')

    // Chart should update with new strike configuration
    await waitFor(() => {
      // Chart component should re-render with new position
      const chartContainer = screen.getByText('Profit/Loss Chart').closest('[data-testid]')
      expect(chartContainer).toBeInTheDocument()
    })
  })

  it('validates strike order and shows errors', async () => {
    const user = userEvent.setup()
    render(<StrategyDashboard symbol="SPY" />)

    // Select strategy  
    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByText('Strike Selection')).toBeInTheDocument()
    })

    // Set invalid strike order (put long >= put short)
    const putLongInput = screen.getByLabelText('Put Long Strike (%)')
    const putShortInput = screen.getByLabelText('Put Short Strike (%)')

    await user.clear(putLongInput)
    await user.type(putLongInput, '99') // Higher than put short (should be 98%)

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText('Put long strike must be lower than put short')).toBeInTheDocument()
    })

    // Should show warning in visualization
    expect(screen.getByText('Invalid Strike Configuration')).toBeInTheDocument()
  })
})