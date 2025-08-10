import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { StrategyDashboard } from '../StrategyDashboard'

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
  return {
    StrategyApiService: {
      getIronCondorAll,
      getIronCondorPerformance,
      getIronCondorByTimeframe,
    }
  }
})

describe('StrategyDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders performance summary and strategies list', async () => {
    render(<StrategyDashboard symbol="SPY" />)

    await waitFor(() => {
      expect(screen.getByLabelText('Total Trades Value')).toBeInTheDocument()
    })

    expect(screen.getByLabelText('Total Trades Value').textContent).toContain('15')
    expect(screen.getByLabelText('Overall Win Rate Value').textContent).toContain('66.7%')
    expect(screen.getByLabelText('Total PnL Value').textContent).toContain('$1,800.00')
    expect(screen.getByLabelText('Best Timeframe Value').textContent).toContain('Daily')

    expect(await screen.findByText('SPY Iron Condor Daily')).toBeInTheDocument()
    expect(await screen.findByText('SPY Iron Condor Weekly')).toBeInTheDocument()
  })

  it('drills down into timeframe and shows trades', async () => {
    const user = userEvent.setup()
    render(<StrategyDashboard symbol="SPY" />)

    const dailyCard = await screen.findByText('SPY Iron Condor Daily')
    await user.click(dailyCard)

    await waitFor(() => {
      expect(screen.getByText(/Iron Condor — Daily/i)).toBeInTheDocument()
    })

    // Target specific aria-labelled values to avoid duplicate label collisions
    expect(screen.getByLabelText('Timeframe Win Rate Value')).toBeInTheDocument()
    expect(screen.getByLabelText('Timeframe Total PnL Value')).toBeInTheDocument()
    expect(screen.getByLabelText('Timeframe Avg Trade Value')).toBeInTheDocument()

    expect(screen.getByText('2024-01-02')).toBeInTheDocument()
    expect(screen.getByText('420/425/430/435')).toBeInTheDocument()
    expect(screen.getByText('+$125.00')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    const { StrategyApiService } = await import('../../services/strategyApi')
    ;(StrategyApiService.getIronCondorAll as any).mockRejectedValueOnce(new Error('Network error'))
    ;(StrategyApiService.getIronCondorPerformance as any).mockResolvedValueOnce(null)

    render(<StrategyDashboard symbol="SPY" />)

    await waitFor(() => {
      expect(screen.getByText(/Error Loading Strategies/i)).toBeInTheDocument()
    })
  })
})


