/**
 * Mock Market API Service for testing
 */

import { vi } from 'vitest'

export const MarketApiService = {
  getCurrentPrice: vi.fn(async (symbol: string) => {
    return {
      price: 430.50,
      timestamp: new Date().toISOString()
    }
  }),
  
  getHistoricalPrices: vi.fn(async (symbol: string, period: string) => {
    return {
      prices: [
        { date: '2024-01-01', close: 425.00 },
        { date: '2024-01-02', close: 428.50 },
        { date: '2024-01-03', close: 430.50 }
      ],
      period
    }
  }),
  
  getMarketStatus: vi.fn(async () => {
    return {
      status: 'open',
      next_open: '2024-01-04T09:30:00Z',
      next_close: '2024-01-04T16:00:00Z'
    }
  })
}

