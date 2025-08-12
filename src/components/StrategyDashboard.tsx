import React, { useEffect, useState } from 'react'
import { StrategyList } from './StrategyList'
import { StrikeSelector } from './StrikeSelector'
import { StrikeVisualization } from './StrikeVisualization'
import { useStrikeSelection } from '../hooks/useStrikeSelection'
import type { StrategyData, StrategyPerformance } from '../types/strategy'
import { StrategyApiService } from '../services/strategyApi'
import { MarketApiService } from '../services/marketApi'

export const StrategyDashboard: React.FC<{ symbol?: string }> = ({ symbol = 'SPY' }) => {
  const [strategies, setStrategies] = useState<StrategyData[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<{
    total_trades: number
    overall_win_rate: number
    total_pnl: number
    best_timeframe: string | null
  } | null>(null)
  const [selectedTimeframe, setSelectedTimeframe] = useState<'daily' | 'weekly' | 'monthly' | null>(null)
  const [timeframeLoading, setTimeframeLoading] = useState<boolean>(false)
  const [timeframeError, setTimeframeError] = useState<string | null>(null)
  const [timeframeData, setTimeframeData] = useState<any | null>(null)
  const [currentPrice, setCurrentPrice] = useState<number>(430.50) // Default SPY price

  // Strike selection hook
  const {
    strikes,
    setStrikes,
    calculationResult,
    isCalculating,
    calculationError,
    resetToDefaults,
    resetError
  } = useStrikeSelection({
    symbol,
    currentPrice,
    selectedTimeframe
  })

  // Fetch current price when symbol changes
  useEffect(() => {
    const fetchCurrentPrice = async () => {
      try {
        const priceData = await MarketApiService.getCurrentPrice(symbol)
        setCurrentPrice(priceData.price)
      } catch (err) {
        console.error('Failed to fetch current price:', err)
        // Keep default price if fetch fails
      }
    }
    
    fetchCurrentPrice()
  }, [symbol])

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await StrategyApiService.getIronCondorAll({ limit: 100, offset: 0 })
        const mapped: StrategyData[] = Object.entries<any>(data?.strategies || {}).map(([timeframe, tf]) => {
          const perf = tf?.performance || {}
          const performance: StrategyPerformance = {
            total_pnl: Number(perf.total_pnl ?? 0),
            win_rate: Number(((perf.win_rate ?? 0) * 100).toFixed(2)),
            total_trades: Number(tf?.metadata?.total_trades ?? 0),
            avg_pnl_per_trade: Number(perf.average_trade ?? 0),
            sharpe_ratio: typeof perf.sharpe_ratio === 'number' ? perf.sharpe_ratio : undefined,
            max_drawdown: typeof perf.max_drawdown === 'number' ? perf.max_drawdown : undefined,
          }

        const id = `iron-condor-${timeframe}`
        const name = `${symbol} Iron Condor ${timeframe.charAt(0).toUpperCase()}${timeframe.slice(1)}`
        const createdAt = new Date().toISOString()

          return {
            id,
            name,
            strategy_type: 'iron_condor',
            symbol,
            timeframe: timeframe as 'daily' | 'weekly' | 'monthly',
            parameters: { timeframe },
            performance,
            is_active: true,
            created_at: createdAt,
            updated_at: createdAt,
          }
        })

        setStrategies(mapped)

        // Fetch performance summary (best timeframe, totals)
        const perf = await StrategyApiService.getIronCondorPerformance()
        if (perf?.summary) {
          setSummary({
            total_trades: Number(perf.summary.total_trades ?? 0),
            overall_win_rate: Number(((perf.summary.overall_win_rate ?? 0) * 100).toFixed(1)),
            total_pnl: Number(perf.summary.total_pnl ?? 0),
            best_timeframe: perf.summary.best_timeframe ?? null,
          })
        }
      } catch (err: any) {
        setError(err?.message || 'Failed to load strategies')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [symbol])

  const handleSelect = async (strategy: StrategyData) => {
    setSelectedTimeframe(strategy.timeframe)
    setTimeframeLoading(true)
    setTimeframeError(null)
    setTimeframeData(null)
    try {
      const data = await StrategyApiService.getIronCondorByTimeframe(strategy.timeframe)
      setTimeframeData(data)
    } catch (e: any) {
      setTimeframeError(e?.message || 'Failed to load timeframe data')
    } finally {
      setTimeframeLoading(false)
    }
  }

  const isSelected = (tf: 'daily' | 'weekly' | 'monthly') => selectedTimeframe === tf

  return (
    <div className="mt-8 space-y-6 flex flex-col" data-testid="strategy-dashboard">
      {summary && (
        <div className="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-lg p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400" aria-label="Total Trades Value">
                {summary.total_trades.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Trades</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400" aria-label="Overall Win Rate Value">
                {summary.overall_win_rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Overall Win Rate</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${summary.total_pnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`} aria-label="Total PnL Value">
                {summary.total_pnl >= 0 ? '+' : ''}${Math.abs(summary.total_pnl).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total P&L</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400" aria-label="Best Timeframe Value">
                {summary.best_timeframe ? summary.best_timeframe.charAt(0).toUpperCase() + summary.best_timeframe.slice(1) : '—'}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Best Timeframe</div>
            </div>
          </div>
        </div>
      )}

      {/* Display strategies using StrategyList */}
      <StrategyList 
        strategies={strategies} 
        loading={loading} 
        error={error} 
        onStrategySelect={handleSelect}
      />

      {/* Timeframe details */}
      {selectedTimeframe && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {symbol} Iron Condor — {selectedTimeframe.charAt(0).toUpperCase() + selectedTimeframe.slice(1)}
            </h3>
            {timeframeLoading && <span className="text-sm text-gray-500">Loading…</span>}
          </div>
          {timeframeError && (
            <div className="text-red-600 dark:text-red-400 text-sm">{timeframeError}</div>
          )}
          {timeframeData && (
            <div className="space-y-4" id={`panel-${selectedTimeframe}`} role="tabpanel" aria-labelledby={`tab-${selectedTimeframe}`}>
              {/* Metrics row - prioritize custom calculation results */}
              {(() => {
                // Use custom calculation results if available, otherwise fall back to original timeframe data
                const displayData = calculationResult?.performance || timeframeData.performance || {}
                
                return (
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        Win Rate {calculationResult && <span className="text-blue-500">*</span>}
                      </div>
                      <div aria-label="Timeframe Win Rate Value" className="text-lg font-bold text-blue-600 dark:text-blue-400">
                        {((displayData.win_rate ?? 0) * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        Total P&L {calculationResult && <span className="text-blue-500">*</span>}
                      </div>
                      <div aria-label="Timeframe Total PnL Value" className={`text-lg font-bold ${Number(displayData.total_pnl ?? 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {Number(displayData.total_pnl ?? 0) >= 0 ? '+' : ''}${Math.abs(Number(displayData.total_pnl ?? 0)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        Avg Trade {calculationResult && <span className="text-blue-500">*</span>}
                      </div>
                      <div aria-label="Timeframe Avg Trade Value" className={`text-lg font-bold ${Number(displayData.average_trade ?? 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                        {Number(displayData.average_trade ?? 0) >= 0 ? '+' : ''}${Math.abs(Number(displayData.average_trade ?? 0)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        Sharpe {calculationResult && <span className="text-blue-500">*</span>}
                      </div>
                      <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
                        {Number(displayData.sharpe_ratio ?? 0).toFixed(2)}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        Max DD {calculationResult && <span className="text-blue-500">*</span>}
                      </div>
                      <div className="text-lg font-bold text-red-600 dark:text-red-400">
                        ${Math.abs(Number(displayData.max_drawdown ?? 0)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>
                )
              })()}
              
              {calculationResult && (
                <div className="text-center">
                  <p className="text-xs text-blue-600 dark:text-blue-400">
                    <span className="text-blue-500">*</span> Updated with custom strike configuration
                  </p>
                </div>
              )}

              {/* Strike Selection and Visualization */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Strike Selection Controls */}
                <div>
                  <StrikeSelector
                    strikes={strikes}
                    currentPrice={currentPrice}
                    onStrikesChange={setStrikes}
                    loading={isCalculating}
                  />
                  
                  {calculationError && (
                    <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                      <div className="flex items-center">
                        <div className="text-red-800 dark:text-red-200 text-sm">
                          <strong>Calculation Error:</strong> {calculationError}
                        </div>
                        <button
                          onClick={resetError}
                          className="ml-auto text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 text-sm underline"
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  )}
                  
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      onClick={resetToDefaults}
                      className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      Reset to Defaults
                    </button>
                  </div>
                </div>

                {/* Strike Visualization */}
                <div>
                  <StrikeVisualization
                    strikes={strikes}
                    currentPrice={currentPrice}
                    loading={isCalculating}
                    height={350}
                    showPercentages={true}
                  />
                </div>
              </div>

              {/* Trades table */}
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                      <th className="py-2 pr-4">Entry Date</th>
                      <th className="py-2 pr-4">Strikes</th>
                      <th className="py-2 pr-4">Credit</th>
                      <th className="py-2 pr-4">P/L</th>
                      <th className="py-2 pr-4">Outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(timeframeData.trades || []).slice(0, 50).map((t: any) => (
                      <tr key={t.id} className="border-b border-gray-100 dark:border-gray-800">
                        <td className="py-2 pr-4 text-gray-900 dark:text-gray-100">{t.entry_date || '—'}</td>
                        <td className="py-2 pr-4 text-gray-900 dark:text-gray-100">
                          {t.strikes ? `${t.strikes.put_long ?? ''}/${t.strikes.put_short ?? ''}/${t.strikes.call_short ?? ''}/${t.strikes.call_long ?? ''}` : '—'}
                        </td>
                        <td className="py-2 pr-4">${Number(t.credit_received ?? 0).toFixed(2)}</td>
                        <td className={`py-2 pr-4 ${Number(t.pnl ?? 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                          {Number(t.pnl ?? 0) >= 0 ? '+' : ''}${Math.abs(Number(t.pnl ?? 0)).toFixed(2)}
                        </td>
                        <td className="py-2 pr-4">{t.outcome || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default StrategyDashboard


