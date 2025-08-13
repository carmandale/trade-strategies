import { vi } from 'vitest';

export interface StrategyParams {
  strategy_type: string;
  symbol: string;
  timeframe: string;
  strikes?: {
    put_long?: number;
    put_short?: number;
    call_short?: number;
    call_long?: number;
    body?: number;
    lower?: number;
    upper?: number;
  };
  current_price?: number;
}

export interface AIAssessment {
  score: number;
  recommendation: string;
  analysis: string;
  risk_level: 'low' | 'medium' | 'high';
  confidence: number;
  key_factors: string[];
}

export const getStrategyAssessment = vi.fn(async (params: StrategyParams): Promise<AIAssessment> => {
  return {
    score: 72,
    recommendation: 'Consider Entry',
    analysis: 'This strategy has a favorable risk/reward profile in the current market conditions.',
    risk_level: 'medium',
    confidence: 0.85,
    key_factors: [
      'Implied volatility is elevated',
      'Support and resistance levels are well-defined',
      'Market sentiment is neutral to slightly bullish'
    ]
  };
});

export const AIAssessmentService = {
  getStrategyAssessment
};

