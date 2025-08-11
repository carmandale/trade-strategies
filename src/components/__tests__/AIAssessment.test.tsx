/**
 * @vitest-environment jsdom
 */
import React from 'react'
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AIAssessmentButton } from '../AIAssessmentButton'
import { AIAssessmentResult } from '../AIAssessmentResult'
import { AIAssessmentService } from '../../services/aiAssessmentService'

// Mock the AI assessment service
vi.mock('../../services/aiAssessmentService', () => ({
  AIAssessmentService: {
    assessStrategy: vi.fn(),
    isServiceHealthy: vi.fn(),
    formatAssessment: vi.fn(() => ({
      badgeColor: 'bg-green-100 text-green-800 border-green-200',
      confidenceColor: 'text-green-600',
      icon: '✓'
    }))
  }
}))

describe('AIAssessmentButton', () => {
  const mockOnAssessmentComplete = vi.fn()
  const mockStrategy = {
    strategy_type: 'iron_condor',
    symbol: 'SPX',
    strikes: {
      put_short: 5500,
      put_long: 5480,
      call_short: 5700,
      call_long: 5720
    },
    expiration: '2025-08-15',
    quantity: 10,
    max_profit: 2000,
    max_loss: 18000,
    breakeven: [5520, 5680]
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Default mock implementation - service is healthy
    ;(AIAssessmentService.isServiceHealthy as Mock).mockResolvedValue(true)
  })

  it('renders AI assessment button', () => {
    render(
      <AIAssessmentButton 
        strategy={mockStrategy}
        onAssessmentComplete={mockOnAssessmentComplete}
      />
    )
    
    expect(screen.getByRole('button', { name: /analyze with ai/i })).toBeInTheDocument()
  })

  it('shows loading state when assessment is in progress', async () => {
    const mockAssessment = new Promise(resolve => 
      setTimeout(() => resolve({
        recommendation: 'GO',
        confidence: 78,
        reasoning: {
          supporting_factors: ['Low VIX'],
          risk_factors: ['Fed meeting']
        },
        market_regime: 'Stable'
      }), 100)
    );
    
    (AIAssessmentService.assessStrategy as Mock).mockReturnValue(mockAssessment)

    render(
      <AIAssessmentButton 
        strategy={mockStrategy}
        onAssessmentComplete={mockOnAssessmentComplete}
      />
    )
    
    const button = screen.getByRole('button', { name: /analyze with ai/i })
    fireEvent.click(button)
    
    expect(screen.getByText(/analyzing/i)).toBeInTheDocument()
    expect(button).toBeDisabled()
    
    await waitFor(() => {
      expect(mockOnAssessmentComplete).toHaveBeenCalled()
    })
  })

  it('handles assessment success', async () => {
    const mockResult = {
      recommendation: 'GO',
      confidence: 78,
      reasoning: {
        supporting_factors: ['Low VIX', 'Support level'],
        risk_factors: ['Fed meeting']
      },
      market_regime: 'Low volatility environment'
    };

    (AIAssessmentService.assessStrategy as Mock).mockResolvedValue(mockResult)

    render(
      <AIAssessmentButton 
        strategy={mockStrategy}
        onAssessmentComplete={mockOnAssessmentComplete}
      />
    )
    
    const button = screen.getByRole('button', { name: /analyze with ai/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(mockOnAssessmentComplete).toHaveBeenCalledWith(mockResult)
    })
  })

  it('handles assessment failure', async () => {
    (AIAssessmentService.assessStrategy as Mock).mockRejectedValue(
      new Error('Rate limit exceeded')
    )

    render(
      <AIAssessmentButton 
        strategy={mockStrategy}
        onAssessmentComplete={mockOnAssessmentComplete}
      />
    )
    
    const button = screen.getByRole('button', { name: /analyze with ai/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText(/rate limit exceeded/i)).toBeInTheDocument()
    })
  })

  it('disables button when disabled prop is true', () => {
    render(
      <AIAssessmentButton 
        strategy={mockStrategy}
        onAssessmentComplete={mockOnAssessmentComplete}
        disabled={true}
      />
    )
    
    expect(screen.getByRole('button', { name: /analyze with ai/i })).toBeDisabled()
  })
})

describe('AIAssessmentResult', () => {
  const mockAssessment = {
    recommendation: 'GO',
    confidence: 78,
    reasoning: {
      supporting_factors: [
        'Low VIX indicates stable market conditions',
        'SPX trading above key support level'
      ],
      risk_factors: [
        'Federal Reserve meeting scheduled for next week',
        'Earnings season could increase volatility'
      ]
    },
    market_regime: 'Low volatility environment with neutral sentiment',
    timestamp: '2025-08-11T10:30:00Z',
    cached: false
  }

  it('renders assessment result with GO recommendation', () => {
    render(<AIAssessmentResult assessment={mockAssessment} />)
    
    expect(screen.getByText(/✓ GO/)).toBeInTheDocument()
    expect(screen.getByText('78% confident')).toBeInTheDocument()
    expect(screen.getByText('Low volatility environment with neutral sentiment')).toBeInTheDocument()
  })

  it('displays supporting factors', () => {
    render(<AIAssessmentResult assessment={mockAssessment} />)
    
    expect(screen.getByText('Low VIX indicates stable market conditions')).toBeInTheDocument()
    expect(screen.getByText('SPX trading above key support level')).toBeInTheDocument()
  })

  it('displays risk factors', () => {
    render(<AIAssessmentResult assessment={mockAssessment} />)
    
    expect(screen.getByText('Federal Reserve meeting scheduled for next week')).toBeInTheDocument()
    expect(screen.getByText('Earnings season could increase volatility')).toBeInTheDocument()
  })

  it('renders CAUTION recommendation with appropriate styling', () => {
    const cautionAssessment = {
      ...mockAssessment,
      recommendation: 'CAUTION',
      confidence: 65
    }
    
    render(<AIAssessmentResult assessment={cautionAssessment} />)
    
    const badge = screen.getByText('CAUTION')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800')
  })

  it('renders NO-GO recommendation with appropriate styling', () => {
    const noGoAssessment = {
      ...mockAssessment,
      recommendation: 'NO-GO',
      confidence: 45
    }
    
    render(<AIAssessmentResult assessment={noGoAssessment} />)
    
    const badge = screen.getByText('NO-GO')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('bg-red-100', 'text-red-800')
  })

  it('shows cached indicator when assessment is cached', () => {
    const cachedAssessment = {
      ...mockAssessment,
      cached: true
    }
    
    render(<AIAssessmentResult assessment={cachedAssessment} />)
    
    expect(screen.getByText(/cached/i)).toBeInTheDocument()
  })

  it('displays confidence score with appropriate color coding', () => {
    // High confidence (>75) - green
    render(<AIAssessmentResult assessment={{...mockAssessment, confidence: 85}} />)
    expect(screen.getByText('85% confident')).toHaveClass('text-green-600')
    
    // Medium confidence (50-75) - yellow
    render(<AIAssessmentResult assessment={{...mockAssessment, confidence: 65}} />)
    expect(screen.getByText('65% confident')).toHaveClass('text-yellow-600')
    
    // Low confidence (<50) - red  
    render(<AIAssessmentResult assessment={{...mockAssessment, confidence: 35}} />)
    expect(screen.getByText('35% confident')).toHaveClass('text-red-600')
  })
})

describe('AI Assessment Integration', () => {
  it('integrates AI assessment into strategy card workflow', async () => {
    const mockResult = {
      recommendation: 'GO',
      confidence: 78,
      reasoning: {
        supporting_factors: ['Market conditions favorable'],
        risk_factors: ['Minor volatility expected']
      },
      market_regime: 'Stable'
    };

    (AIAssessmentService.assessStrategy as Mock).mockResolvedValue(mockResult)

    const TestComponent = () => {
      const [assessment, setAssessment] = React.useState(null)
      return (
        <div>
          <AIAssessmentButton 
            strategy={{
              strategy_type: 'iron_condor',
              symbol: 'SPX',
              strikes: { put_short: 5500 },
              expiration: '2025-08-15'
            }}
            onAssessmentComplete={setAssessment}
          />
          {assessment && <AIAssessmentResult assessment={assessment} />}
        </div>
      )
    }

    render(<TestComponent />)
    
    const button = screen.getByRole('button', { name: /analyze with ai/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText('GO')).toBeInTheDocument()
      expect(screen.getByText('78% confident')).toBeInTheDocument()
    })
  })
})