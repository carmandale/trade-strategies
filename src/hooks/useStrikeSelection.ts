import { useState, useEffect, useCallback, useMemo } from 'react'
import { StrategyApiService } from '../services/strategyApi'
import type { StrikeConfig } from '../types/strategy'

// Default strike configurations by timeframe
const DEFAULT_STRIKES: Record<'daily' | 'weekly' | 'monthly', StrikeConfig> = {
	daily: {
		put_short_pct: 98.0,
		put_long_pct: 97.5,
		call_short_pct: 102.0,
		call_long_pct: 102.5
	},
	weekly: {
		put_short_pct: 97.0,
		put_long_pct: 96.5,
		call_short_pct: 103.0,
		call_long_pct: 103.5
	},
	monthly: {
		put_short_pct: 95.0,
		put_long_pct: 94.0,
		call_short_pct: 105.0,
		call_long_pct: 106.0
	}
}

interface StrikeCalculationResult {
	performance: {
		win_rate: number
		total_pnl: number
		sharpe_ratio: number
		max_drawdown: number
		average_trade: number
	}
	trades: any[]
}

interface UseStrikeSelectionProps {
	symbol: string
	currentPrice: number
	selectedTimeframe: 'daily' | 'weekly' | 'monthly' | null
}

interface UseStrikeSelectionReturn {
	// Strike configuration
	strikes: StrikeConfig
	setStrikes: (strikes: StrikeConfig) => void
	
	// Calculation results
	calculationResult: StrikeCalculationResult | null
	
	// Loading and error states
	isCalculating: boolean
	calculationError: string | null
	
	// Reset functions
	resetToDefaults: () => void
	resetError: () => void
}

export const useStrikeSelection = ({
	symbol,
	currentPrice,
	selectedTimeframe
}: UseStrikeSelectionProps): UseStrikeSelectionReturn => {
	// Store strike configurations per timeframe
	const [strikesByTimeframe, setStrikesByTimeframe] = useState<
		Record<string, StrikeConfig>
	>({})
	
	// Calculation state
	const [calculationResult, setCalculationResult] = useState<StrikeCalculationResult | null>(null)
	const [isCalculating, setIsCalculating] = useState(false)
	const [calculationError, setCalculationError] = useState<string | null>(null)
	
	// Get current strikes for selected timeframe
	const strikes = useMemo(() => {
		if (!selectedTimeframe) return DEFAULT_STRIKES.daily
		
		return strikesByTimeframe[selectedTimeframe] || DEFAULT_STRIKES[selectedTimeframe]
	}, [selectedTimeframe, strikesByTimeframe])
	
	// Update strikes for current timeframe
	const setStrikes = useCallback((newStrikes: StrikeConfig) => {
		if (!selectedTimeframe) return
		
		setStrikesByTimeframe(prev => ({
			...prev,
			[selectedTimeframe]: newStrikes
		}))
	}, [selectedTimeframe])
	
	// Reset to default strikes for current timeframe
	const resetToDefaults = useCallback(() => {
		if (!selectedTimeframe) return
		
		setStrikesByTimeframe(prev => {
			const newState = { ...prev }
			delete newState[selectedTimeframe]
			return newState
		})
		setCalculationResult(null)
		setCalculationError(null)
	}, [selectedTimeframe])
	
	// Clear error state
	const resetError = useCallback(() => {
		setCalculationError(null)
	}, [])
	
	// Calculate strategy with current strikes
	const calculateStrategy = useCallback(async (strikesToCalculate: StrikeConfig) => {
		if (!selectedTimeframe) return
		
		setIsCalculating(true)
		setCalculationError(null)
		
		try {
			// Check if we need to add the API method to StrategyApiService
			const result = await StrategyApiService.calculateIronCondorWithStrikes({
				symbol,
				timeframe: selectedTimeframe,
				strikes: strikesToCalculate,
				current_price: currentPrice,
				days_back: 30 // Default lookback period
			})
			
			setCalculationResult(result)
		} catch (error) {
			console.error('Strike calculation failed:', error)
			setCalculationError(error instanceof Error ? error.message : 'Calculation failed')
			setCalculationResult(null)
		} finally {
			setIsCalculating(false)
		}
	}, [symbol, selectedTimeframe, currentPrice])
	
	// Trigger calculation when strikes change
	useEffect(() => {
		if (!selectedTimeframe) return
		
		// Use a debounce effect to avoid too many API calls
		const debounceTimer = setTimeout(() => {
			calculateStrategy(strikes)
		}, 300)
		
		return () => clearTimeout(debounceTimer)
	}, [strikes, calculateStrategy, selectedTimeframe])
	
	// Reset calculation when timeframe changes
	useEffect(() => {
		if (selectedTimeframe) {
			setCalculationResult(null)
			setCalculationError(null)
		}
	}, [selectedTimeframe])
	
	return {
		strikes,
		setStrikes,
		calculationResult,
		isCalculating,
		calculationError,
		resetToDefaults,
		resetError
	}
}