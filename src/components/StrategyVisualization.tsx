import React, { useState } from 'react'
import { TradeTicket, type TicketResponse } from './TradeTicket'
import { ApiService } from '../services/api'
import { EquityCurveChart } from './EquityCurveChart'
import { PLHistogramChart } from './PLHistogramChart'
import { PerformanceMetrics } from './PerformanceMetrics'

export type StrategyVisualizationData = {
  equityData: Array<{ date: string; cumulativePL: number; dailyPL: number }>
  histogramData: Array<{ range: string; count: number; midpoint: number }>
  performanceData: {
    totalPL: number
    winRate: number
    totalTrades: number
    avgPLPerTrade: number
    sharpeRatio?: number
    maxDrawdown?: number
    bestTrade?: number
    worstTrade?: number
    consecutiveWins?: number
    consecutiveLosses?: number
  }
}

export type StrategyInfo = {
  name: string
  symbol: string
  timeframe: string
  parameters?: Record<string, unknown>
}

export function StrategyVisualization(props: {
  data: StrategyVisualizationData | null
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  strategyInfo?: StrategyInfo
  enableExport?: boolean
}) {
  const { data, loading, error, onRetry, strategyInfo, enableExport } = props

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin inline-block h-6 w-6 mr-2 rounded-full border-2 border-gray-300 border-t-transparent" />
        <span>Loading strategy analysis...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 border rounded-md border-red-300 bg-red-50">
        <h3 className="font-semibold text-red-700">Visualization Error</h3>
        <p className="text-red-600 mb-2">{error}</p>
        <button aria-label="Retry" className="px-3 py-1 bg-red-600 text-white rounded" onClick={onRetry}>
          Retry
        </button>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-4 text-center text-gray-600">No data available</div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h2 className="text-xl font-semibold">Strategy Analysis</h2>
        {strategyInfo && (
          <div className="text-sm text-gray-600 flex gap-2 items-center">
            <span className="font-medium">{strategyInfo.name}</span>
            <span>•</span>
            <span>{strategyInfo.symbol}</span>
            <span>•</span>
            <span>{strategyInfo.timeframe === 'daily' ? 'Daily (0DTE)' : strategyInfo.timeframe}</span>
          </div>
        )}
      </header>

      <GenerateTicketBar strategyInfo={strategyInfo} />

      {enableExport && (
        <div className="flex gap-2 items-center">
          <span className="font-medium">Export Charts</span>
          <button aria-label="Export as PNG" className="px-2 py-1 text-sm border rounded">PNG</button>
          <button aria-label="Export as CSV" className="px-2 py-1 text-sm border rounded">CSV</button>
        </div>
      )}

      <section aria-label="Toggle Layout">
        <PerformanceMetrics data={data.performanceData} />
      </section>

      <section>
        <h3 className="font-medium mb-2">Equity Curve Overview</h3>
        <EquityCurveChart data={data.equityData} />
      </section>

      <section>
        <PLHistogramChart data={data.histogramData} />
      </section>
    </div>
  )
}


function GenerateTicketBar({ strategyInfo }: { strategyInfo?: StrategyInfo }) {
  const [busy, setBusy] = useState(false)
  const [ticket, setTicket] = useState<TicketResponse | null>(null)

  const generate = async () => {
    if (!strategyInfo) return
    setBusy(true)
    try {
      // Example: generate an at-a-glance iron condor one week out, 10-wide
      const today = new Date()
      const exp = new Date(today.getTime() + 7 * 24 * 3600 * 1000)
      const expiration = exp.toISOString().slice(0, 10)
      const mid = 0 // strike will be interpreted by backend consumer; using placeholders is fine for manual edit
      const payload = {
        symbol: strategyInfo.symbol,
        strategy_type: strategyInfo.timeframe || 'daily',
        contracts: 1,
        pricing: { side: 'CREDIT' as const, net: 1.0, tif: 'GTC' as const },
        legs: [
          { action: 'SELL' as const, type: 'PUT' as const, strike: mid - 5, expiration, quantity: 1 },
          { action: 'BUY' as const, type: 'PUT' as const, strike: mid - 15, expiration, quantity: 1 },
          { action: 'SELL' as const, type: 'CALL' as const, strike: mid + 5, expiration, quantity: 1 },
          { action: 'BUY' as const, type: 'CALL' as const, strike: mid + 15, expiration, quantity: 1 },
        ],
      }
      const res = await ApiService.createOptionsTicket(payload)
      setTicket(res)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="flex items-center gap-2">
        <button onClick={generate} className="px-3 py-1 border rounded" disabled={busy || !strategyInfo}>
          {busy ? 'Generating…' : 'Generate Trade Ticket'}
        </button>
      </div>
      {ticket && <TradeTicket ticket={ticket} onClose={() => setTicket(null)} />}
    </>
  )
}

