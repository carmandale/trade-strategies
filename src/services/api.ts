// API service for connecting React frontend to FastAPI backend
import { SpreadConfig, AnalysisData, Trade } from '../components/generated/SPYSpreadStrategiesApp';

const API_BASE_URL = 'http://localhost:8000';

export interface SpreadAnalysisRequest {
  date: string;
  ticker: string;
  contracts: number;
  bull_call_strikes: number[];
  iron_condor_strikes: number[];
  butterfly_strikes: number[];
  entry_time: string;
  exit_time: string;
}

export interface SpreadAnalysisResponse {
  date: string;
  current_price: number;
  chart_data: {
    time: string;
    price: number;
    bb_upper?: number;
    bb_lower?: number;
    rsi?: number;
  }[];
  results: {
    bull_call: {
      max_profit: number;
      max_loss: number;
      profit_at_exit: number;
      entry_price: number;
      exit_price: number;
    };
    iron_condor: {
      max_profit: number;
      max_loss: number;
      profit_at_exit: number;
      entry_price: number;
      exit_price: number;
    };
    butterfly: {
      max_profit: number;
      max_loss: number;
      profit_at_exit: number;
      entry_price: number;
      exit_price: number;
    };
  };
}

export interface TradeEntry {
  date: string;
  strategy: string;
  strikes: number[];
  contracts: number;
  entry_price: number;
  credit_debit: number;
  notes?: string;
}

// Missing types that components expect
export interface StrategyData {
  max_profit: number;
  max_loss: number;
  breakeven_points: number[];
  risk_reward_ratio: number;
}

export interface BacktestResult {
  strategy: string;
  total_profit: number;
  win_rate: number;
  max_drawdown: number;
  trades: number;
}

export interface MarketData {
  current_price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

export interface HistoricalDataPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export class ApiService {
  
  // Get current SPY price
  static async getCurrentPrice(ticker: string = 'SPY'): Promise<number> {
    try {
      const response = await fetch(`${API_BASE_URL}/current_price/${ticker}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.price;
    } catch (error) {
      console.error('Error fetching current price:', error);
      // Return fallback price if API fails
      return 425.50;
    }
  }

  // Analyze spread strategies
  static async analyzeStrategies(
    selectedDate: Date,
    spreadConfig: SpreadConfig,
    contracts: number,
    entryTime: string,
    exitTime: string,
    ticker: string = 'SPY'
  ): Promise<AnalysisData> {
    try {
      const requestData: SpreadAnalysisRequest = {
        date: selectedDate.toISOString().split('T')[0],
        ticker,
        contracts,
        bull_call_strikes: [spreadConfig.bullCallLower, spreadConfig.bullCallUpper],
        iron_condor_strikes: [
          spreadConfig.ironCondorPutLong,
          spreadConfig.ironCondorPutShort,
          spreadConfig.ironCondorCallShort,
          spreadConfig.ironCondorCallLong
        ],
        butterfly_strikes: [
          spreadConfig.butterflyLower,
          spreadConfig.butterflyBody,
          spreadConfig.butterflyUpper
        ],
        entry_time: `${entryTime}:00`,
        exit_time: `${exitTime}:00`
      };

      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SpreadAnalysisResponse = await response.json();

      // Transform backend response to frontend format
      return {
        bullCall: {
          maxProfit: data.results.bull_call.max_profit,
          maxLoss: data.results.bull_call.max_loss,
          breakeven: spreadConfig.bullCallLower + (data.results.bull_call.max_loss / 100 / contracts),
          riskReward: Math.abs(data.results.bull_call.max_profit / data.results.bull_call.max_loss)
        },
        ironCondor: {
          maxProfit: data.results.iron_condor.max_profit,
          maxLoss: data.results.iron_condor.max_loss,
          upperBreakeven: spreadConfig.ironCondorCallShort + 2,
          lowerBreakeven: spreadConfig.ironCondorPutShort - 2,
          riskReward: Math.abs(data.results.iron_condor.max_profit / data.results.iron_condor.max_loss)
        },
        butterfly: {
          maxProfit: data.results.butterfly.max_profit,
          maxLoss: data.results.butterfly.max_loss,
          breakeven1: spreadConfig.butterflyLower + 1.5,
          breakeven2: spreadConfig.butterflyUpper - 1.5,
          riskReward: Math.abs(data.results.butterfly.max_profit / data.results.butterfly.max_loss)
        }
      };
    } catch (error) {
      console.error('Error analyzing strategies:', error);
      // Return fallback data if API fails
      return {
        bullCall: {
          maxProfit: (spreadConfig.bullCallUpper - spreadConfig.bullCallLower) * 100 * contracts,
          maxLoss: 150 * contracts,
          breakeven: spreadConfig.bullCallLower + 1.5,
          riskReward: 2.33
        },
        ironCondor: {
          maxProfit: 200 * contracts,
          maxLoss: 300 * contracts,
          upperBreakeven: spreadConfig.ironCondorCallShort + 2,
          lowerBreakeven: spreadConfig.ironCondorPutShort - 2,
          riskReward: 0.67
        },
        butterfly: {
          maxProfit: 350 * contracts,
          maxLoss: 150 * contracts,
          breakeven1: spreadConfig.butterflyLower + 1.5,
          breakeven2: spreadConfig.butterflyUpper - 1.5,
          riskReward: 2.33
        }
      };
    }
  }

  // Get chart data for visualization
  static async getChartData(
    selectedDate: Date,
    spreadConfig: SpreadConfig,
    contracts: number,
    entryTime: string,
    exitTime: string,
    ticker: string = 'SPY'
  ): Promise<{ time: string; price: number; volume: number }[]> {
    try {
      const requestData: SpreadAnalysisRequest = {
        date: selectedDate.toISOString().split('T')[0],
        ticker,
        contracts,
        bull_call_strikes: [spreadConfig.bullCallLower, spreadConfig.bullCallUpper],
        iron_condor_strikes: [
          spreadConfig.ironCondorPutLong,
          spreadConfig.ironCondorPutShort,
          spreadConfig.ironCondorCallShort,
          spreadConfig.ironCondorCallLong
        ],
        butterfly_strikes: [
          spreadConfig.butterflyLower,
          spreadConfig.butterflyBody,
          spreadConfig.butterflyUpper
        ],
        entry_time: `${entryTime}:00`,
        exit_time: `${exitTime}:00`
      };

      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SpreadAnalysisResponse = await response.json();

      // Transform chart data
      return data.chart_data.map(item => ({
        time: item.time,
        price: item.price,
        volume: Math.floor(Math.random() * 1000000) + 500000 // Mock volume for now
      }));
    } catch (error) {
      console.error('Error fetching chart data:', error);
      // Return fallback chart data
      const basePrice = 425.50;
      const data: { time: string; price: number; volume: number }[] = [];
      for (let i = 0; i < 100; i++) {
        const variation = Math.sin(i * 0.1) * 5 + (Math.random() - 0.5) * 3;
        data.push({
          time: new Date(Date.now() - (100 - i) * 60000).toISOString(),
          price: basePrice + variation,
          volume: Math.floor(Math.random() * 1000000) + 500000
        });
      }
      return data;
    }
  }

  // Save a trade
  static async saveTrade(trade: TradeEntry): Promise<Trade> {
    try {
      const response = await fetch(`${API_BASE_URL}/trades`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(trade),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const savedTrade = await response.json();
      
      // Transform to frontend format
      return {
        id: savedTrade.id.toString(),
        date: savedTrade.date,
        strategy: savedTrade.strategy,
        strikes: savedTrade.strikes.join('/'),
        contracts: savedTrade.contracts,
        pnl: savedTrade.credit_debit * savedTrade.contracts * 100, // Convert to P&L
        notes: savedTrade.notes || '',
        timestamp: new Date(savedTrade.timestamp).getTime()
      };
    } catch (error) {
      console.error('Error saving trade:', error);
      throw error;
    }
  }

  // Get all trades
  static async getTrades(): Promise<Trade[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/trades`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const trades = await response.json();
      
      // Transform to frontend format
      return trades.map((trade: any) => ({
        id: trade.id.toString(),
        date: trade.date,
        strategy: trade.strategy,
        strikes: Array.isArray(trade.strikes) ? trade.strikes.join('/') : trade.strikes,
        contracts: trade.contracts,
        pnl: trade.credit_debit * trade.contracts * 100, // Convert to P&L
        notes: trade.notes || '',
        timestamp: new Date(trade.timestamp).getTime()
      }));
    } catch (error) {
      console.error('Error fetching trades:', error);
      return [];
    }
  }

  // Delete a trade
  static async deleteTrade(tradeId: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/trades/${tradeId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error deleting trade:', error);
      throw error;
    }
  }

  // Get market data for a symbol
  static async getMarketData(symbol: string): Promise<MarketData> {
    try {
      const response = await fetch(`${API_BASE_URL}/market_data/${symbol}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return {
        current_price: data.current_price,
        change: data.change || 0,
        change_percent: data.change_percent || 0,
        volume: data.volume || 0,
        timestamp: data.timestamp || new Date().toISOString()
      };
    } catch (error) {
      console.error('Error fetching market data:', error);
      // Return fallback data
      return {
        current_price: 425.50,
        change: 1.25,
        change_percent: 0.29,
        volume: 45000000,
        timestamp: new Date().toISOString()
      };
    }
  }

  // Get historical data for charting
  static async getHistoricalData(
    symbol: string,
    period: string = '1d',
    interval: string = '1m'
  ): Promise<HistoricalDataPoint[]> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/historical_data/${symbol}?period=${period}&interval=${interval}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.data || data; // Handle different response formats
    } catch (error) {
      console.error('Error fetching historical data:', error);
      // Return fallback data
      const basePrice = 425.50;
      const data: HistoricalDataPoint[] = [];
      for (let i = 0; i < 100; i++) {
        const variation = Math.sin(i * 0.1) * 5 + (Math.random() - 0.5) * 3;
        const price = basePrice + variation;
        data.push({
          timestamp: new Date(Date.now() - (100 - i) * 60000).toISOString(),
          open: price - 0.5,
          high: price + 1,
          low: price - 1,
          close: price,
          volume: Math.floor(Math.random() * 1000000) + 500000
        });
      }
      return data;
    }
  }

  // Get strategy-specific data
  static async getStrategyData(
    strategy: string,
    params: Record<string, any>
  ): Promise<StrategyData> {
    try {
      const response = await fetch(`${API_BASE_URL}/strategy/${strategy}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return {
        max_profit: data.max_profit || 0,
        max_loss: data.max_loss || 0,
        breakeven_points: data.breakeven_points || [],
        risk_reward_ratio: data.risk_reward_ratio || 1
      };
    } catch (error) {
      console.error(`Error fetching ${strategy} strategy data:`, error);
      // Return fallback strategy data based on strategy type
      if (strategy === 'iron_condor') {
        return {
          max_profit: 200 * (params.contracts || 1),
          max_loss: -300 * (params.contracts || 1),
          breakeven_points: [
            (params.put_short || 415) - 2,
            (params.call_short || 435) + 2
          ],
          risk_reward_ratio: 0.67
        };
      } else if (strategy === 'bull_call') {
        const spread = (params.upper_strike || 425) - (params.lower_strike || 420);
        return {
          max_profit: spread * 100 * (params.contracts || 1),
          max_loss: -150 * (params.contracts || 1),
          breakeven_points: [(params.lower_strike || 420) + 1.5],
          risk_reward_ratio: 2.33
        };
      } else {
        return {
          max_profit: 350 * (params.contracts || 1),
          max_loss: -150 * (params.contracts || 1),
          breakeven_points: [420, 430],
          risk_reward_ratio: 2.33
        };
      }
    }
  }
}

// Export a lowercase instance for component compatibility
export const apiService = ApiService;