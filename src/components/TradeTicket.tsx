import React from 'react'

export type TicketLeg = {
  Action: 'BUY' | 'SELL'
  Qty: number
  Symbol: string
  Expiration: string
  Strike: string
  Type: 'CALL' | 'PUT'
}

export type TicketPricing = {
  side: 'DEBIT' | 'CREDIT'
  net: number
  limit?: number
  tif: 'DAY' | 'GTC'
}

export type TicketResponse = {
  symbol: string
  strategy_type?: string
  contracts: number
  legs: Array<{
    action: 'BUY' | 'SELL'
    type: 'CALL' | 'PUT'
    strike: number
    expiration: string
    quantity: number
  }>
  pricing: TicketPricing
  underlying_price?: number
  timestamp: string
  fidelity_fields: TicketLeg[]
  copy_text: string
}

export function TradeTicket({
  ticket,
  onClose,
}: {
  ticket: TicketResponse
  onClose: () => void
}) {
  const downloadCSV = () => {
    const header = ['Action', 'Qty', 'Symbol', 'Expiration', 'Strike', 'Type']
    const rows = ticket.fidelity_fields.map((r) => [r.Action, String(r.Qty), r.Symbol, r.Expiration, r.Strike, r.Type])
    const csv = [header, ...rows].map((r) => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${ticket.symbol}-ticket.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const copyText = async () => {
    try {
      await navigator.clipboard.writeText(ticket.copy_text)
    } catch {
      /* no-op */
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-3xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Trade Ticket — {ticket.symbol}</h3>
          <button onClick={onClose} className="px-2 py-1 border rounded">Close</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <div><span className="text-gray-500">Strategy:</span> {ticket.strategy_type || 'N/A'}</div>
            <div><span className="text-gray-500">Contracts:</span> {ticket.contracts}</div>
            <div><span className="text-gray-500">Underlying:</span> {ticket.underlying_price ?? '—'}</div>
          </div>
          <div>
            <div><span className="text-gray-500">Side:</span> {ticket.pricing.side}</div>
            <div><span className="text-gray-500">Net:</span> {ticket.pricing.net}</div>
            <div><span className="text-gray-500">TIF:</span> {ticket.pricing.tif}{ticket.pricing.limit ? ` • Limit ${ticket.pricing.limit}` : ''}</div>
          </div>
        </div>

        <div className="overflow-auto border rounded">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="text-left p-2">Action</th>
                <th className="text-left p-2">Qty</th>
                <th className="text-left p-2">Symbol</th>
                <th className="text-left p-2">Expiration</th>
                <th className="text-left p-2">Strike</th>
                <th className="text-left p-2">Type</th>
              </tr>
            </thead>
            <tbody>
              {ticket.fidelity_fields.map((r, idx) => (
                <tr key={idx} className="border-t">
                  <td className="p-2">{r.Action}</td>
                  <td className="p-2">{r.Qty}</td>
                  <td className="p-2">{r.Symbol}</td>
                  <td className="p-2">{r.Expiration}</td>
                  <td className="p-2">{r.Strike}</td>
                  <td className="p-2">{r.Type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex gap-2 mt-4">
          <button onClick={copyText} className="px-3 py-1 bg-blue-600 text-white rounded">Copy</button>
          <button onClick={downloadCSV} className="px-3 py-1 border rounded">Download CSV</button>
        </div>
      </div>
    </div>
  )
}



