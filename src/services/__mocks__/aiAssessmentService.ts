/**
 * Mock AI Assessment Service for testing
 */

import { vi } from 'vitest'

export interface StrategyParams {
  strategy_type: string
  symbol: string
  strikes: Record<string, number>
  expiration: string
  quantity?: number
  max_profit?: number
  max_loss?: number
  breakeven?: number[]
}

export interface AssessmentReasoning {
  supporting_factors: string[]
  risk_factors: string[]
}

export interface AIAssessment {
  recommendation: 'GO' | 'CAUTION' | 'NO-GO'
  confidence: number
  reasoning: AssessmentReasoning
  market_regime: string
  cached?: boolean
  timestamp?: string
}

export interface MarketData {
  spx_price: number
  spx_change: number
  spx_change_percent: number
  vix_level: number
  vix_change: number
  volume: number
  volume_vs_avg: number
  technical_indicators: Record<string, any>
  cached?: boolean
  expires_at?: string
}

export interface AIServiceStatus {
  service_available: boolean
  api_key_configured: boolean
  model: string
  cache_ttl: number
  rate_limit: Record<string, any>
  usage_stats: Record<string, any>
  last_assessment?: string
  message: string
}

export class AIAssessmentService {
  static assessStrategy = vi.fn(async (strategy: StrategyParams): Promise<AIAssessment> => {
    return {
      recommendation: 'GO',
      confidence: 85,
      reasoning: {
        supporting_factors: ['Positive market trend', 'Low volatility'],
        risk_factors: ['Upcoming earnings report']
      },
      market_regime: 'Bullish trend with moderate volatility',
      cached: false,
      timestamp: new Date().toISOString()
    }
  })

  static getMarketData = vi.fn(async (useCache: boolean = true): Promise<MarketData> => {
    return {
      spx_price: 4500,
      spx_change: 15.5,
      spx_change_percent: 0.35,
      vix_level: 16.2,
      vix_change: -0.5,
      volume: 2500000000,
      volume_vs_avg: 0.95,
      technical_indicators: {
        rsi: 55,
        macd: 0.5
      }
    }
  })

  static getServiceStatus = vi.fn(async (): Promise<AIServiceStatus> => {
    return {
      service_available: true,
      api_key_configured: true,
      model: 'gpt-4',
      cache_ttl: 3600,
      rate_limit: {
        requests_per_minute: 10
      },
      usage_stats: {
        total_requests: 100
      },
      message: 'Service is operational'
    }
  })

  static getCachedAssessment = vi.fn(async (strategyHash: string): Promise<AIAssessment | null> => {
    return null
  })

  static calculateStrategyHash = vi.fn((strategy: StrategyParams): string => {
    return 'mock-hash-123456'
  })

  static formatAssessment = vi.fn((assessment: AIAssessment) => {
    return {
      badgeColor: 'bg-green-100 text-green-800 border-green-200',
      confidenceColor: 'text-green-600',
      icon: '✓'
    }
  })

  static isServiceHealthy = vi.fn(async (): Promise<boolean> => {
    return true
  })
}

