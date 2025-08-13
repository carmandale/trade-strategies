import { vi } from 'vitest';

export const MarketApiService = {
  getCurrentPrice: vi.fn(async (symbol: string) => ({
    price: 430.50,
    timestamp: new Date().toISOString()
  })),
  
  getHistoricalPrices: vi.fn(async (symbol: string, timeframe: string) => ({
    prices: [
      { date: '2025-01-01', open: 425.10, high: 432.50, low: 424.80, close: 430.25 },
      { date: '2025-01-02', open: 430.25, high: 435.75, low: 429.90, close: 433.50 },
      { date: '2025-01-03', open: 433.50, high: 436.25, low: 431.00, close: 435.75 }
    ],
    timeframe: timeframe
  })),
  
  getMarketStatus: vi.fn(async () => ({
    is_market_open: true,
    next_market_open: '2025-01-04T09:30:00Z',
    next_market_close: '2025-01-03T16:00:00Z'
  }))
};

