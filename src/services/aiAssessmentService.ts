/**
 * AI Assessment Service - Frontend client for AI strategy assessment API
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  /**
   * Assess a trading strategy using AI
   */
  static async assessStrategy(strategy: StrategyParams): Promise<AIAssessment> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/assess-strategy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(strategy),
      })

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please try again later.')
        } else if (response.status === 503) {
          throw new Error('AI assessment service temporarily unavailable')
        } else {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || `Assessment failed (HTTP ${response.status})`)
        }
      }

      const assessment = await response.json()
      return assessment
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error('Failed to assess strategy')
    }
  }

  /**
   * Get current market data
   */
  static async getMarketData(useCache: boolean = true): Promise<MarketData> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/market-data?use_cache=${useCache}`)

      if (!response.ok) {
        throw new Error(`Failed to fetch market data (HTTP ${response.status})`)
      }

      const marketData = await response.json()
      return marketData
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error('Failed to fetch market data')
    }
  }

  /**
   * Get AI service status
   */
  static async getServiceStatus(): Promise<AIServiceStatus> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/status`)

      if (!response.ok) {
        throw new Error(`Failed to get service status (HTTP ${response.status})`)
      }

      const status = await response.json()
      return status
    } catch (error) {
      // Return fallback status if service is completely unavailable
      return {
        service_available: false,
        api_key_configured: false,
        model: 'unknown',
        cache_ttl: 0,
        rate_limit: {},
        usage_stats: {},
        message: error instanceof Error ? error.message : 'Service unavailable'
      }
    }
  }

  /**
   * Get cached assessment by strategy hash
   */
  static async getCachedAssessment(strategyHash: string): Promise<AIAssessment | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/assessment/${strategyHash}`)

      if (response.status === 404) {
        return null // No cached assessment found
      }

      if (!response.ok) {
        throw new Error(`Failed to get cached assessment (HTTP ${response.status})`)
      }

      const assessment = await response.json()
      return assessment
    } catch (error) {
      console.warn('Failed to get cached assessment:', error)
      return null
    }
  }

  /**
   * Calculate strategy hash for caching
   */
  static calculateStrategyHash(strategy: StrategyParams): string {
    // Create a deterministic hash from strategy parameters
    const sortedStrategy = JSON.stringify(strategy, Object.keys(strategy).sort())
    
    // Simple hash function (in production, consider using crypto.subtle)
    let hash = 0
    for (let i = 0; i < sortedStrategy.length; i++) {
      const char = sortedStrategy.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(16)
  }

  /**
   * Format assessment for display
   */
  static formatAssessment(assessment: AIAssessment): {
    badgeColor: string
    confidenceColor: string
    icon: string
  } {
    const { recommendation, confidence } = assessment

    // Recommendation badge colors
    const badgeColors = {
      'GO': 'bg-green-100 text-green-800 border-green-200',
      'CAUTION': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'NO-GO': 'bg-red-100 text-red-800 border-red-200'
    }

    // Confidence score colors
    let confidenceColor = 'text-gray-600'
    if (confidence >= 75) {
      confidenceColor = 'text-green-600'
    } else if (confidence >= 50) {
      confidenceColor = 'text-yellow-600'
    } else {
      confidenceColor = 'text-red-600'
    }

    // Icons for recommendations
    const icons = {
      'GO': '✓',
      'CAUTION': '⚠',
      'NO-GO': '✗'
    }

    return {
      badgeColor: badgeColors[recommendation],
      confidenceColor,
      icon: icons[recommendation]
    }
  }

  /**
   * Check if service is healthy
   */
  static async isServiceHealthy(): Promise<boolean> {
    try {
      const status = await this.getServiceStatus()
      return status.service_available
    } catch {
      return false
    }
  }
}