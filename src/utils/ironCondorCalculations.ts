/**
 * Iron Condor Calculations Utility
 * 
 * Provides utilities for calculating profit/loss, breakeven points, and validation
 * for Iron Condor options strategies.
 */

export interface IronCondorPosition {
	putLongStrike: number
	putShortStrike: number
	callShortStrike: number
	callLongStrike: number
	credit: number // Net credit received for the position
	contracts: number
}

export interface PnLDataPoint {
	price: number
	pnl: number
}

export interface BreakevenPoints {
	lowerBreakeven: number
	upperBreakeven: number
}

export interface MaxProfitLoss {
	maxProfit: number
	maxLoss: number
}

export interface ValidationResult {
	isValid: boolean
	errors: string[]
}

/**
 * Calculate profit/loss for an Iron Condor at a given underlying price
 */
export function calculateIronCondorPnL(price: number, position: IronCondorPosition): number {
	const { putLongStrike, putShortStrike, callShortStrike, callLongStrike, credit, contracts } = position

	// Calculate intrinsic values at expiration
	const putLongValue = Math.max(0, putLongStrike - price)
	const putShortValue = Math.max(0, putShortStrike - price)
	const callShortValue = Math.max(0, price - callShortStrike)
	const callLongValue = Math.max(0, price - callLongStrike)

	// Net value of spreads
	// Put spread: we sold putShortStrike and bought putLongStrike
	// Call spread: we sold callShortStrike and bought callLongStrike
	const putSpreadValue = putShortValue - putLongValue
	const callSpreadValue = callShortValue - callLongValue

	// Total P/L = credit received - cost to close spreads
	const totalPnL = credit - putSpreadValue - callSpreadValue

	return totalPnL * contracts
}

/**
 * Calculate the breakeven points for an Iron Condor
 */
export function calculateBreakevenPoints(position: IronCondorPosition): BreakevenPoints {
	const { putShortStrike, callShortStrike, credit } = position

	return {
		lowerBreakeven: putShortStrike - credit,
		upperBreakeven: callShortStrike + credit
	}
}

/**
 * Calculate maximum profit and loss for an Iron Condor
 */
export function getMaxProfitLoss(position: IronCondorPosition): MaxProfitLoss {
	const { putLongStrike, putShortStrike, callShortStrike, callLongStrike, credit, contracts } = position

	// Maximum profit occurs when price is between short strikes
	const maxProfit = credit * contracts

	// Maximum loss occurs when one of the spreads reaches maximum width
	const putSpreadWidth = putShortStrike - putLongStrike
	const callSpreadWidth = callLongStrike - callShortStrike
	
	// Both spreads should have the same width for a balanced Iron Condor
	const spreadWidth = Math.max(putSpreadWidth, callSpreadWidth)
	const maxLoss = (credit - spreadWidth) * contracts

	return {
		maxProfit,
		maxLoss
	}
}

/**
 * Generate a range of prices for P/L calculation
 */
export function generatePriceRange(
	centerPrice: number, 
	rangePercent: number = 0.2, 
	numPoints: number = 50
): number[] {
	if (numPoints <= 1) {
		return [Math.round(centerPrice)]
	}

	const minPrice = centerPrice * (1 - rangePercent)
	const maxPrice = centerPrice * (1 + rangePercent)
	const step = (maxPrice - minPrice) / (numPoints - 1)

	const prices: number[] = []
	for (let i = 0; i < numPoints; i++) {
		const price = minPrice + (step * i)
		prices.push(Math.round(price))
	}

	return prices
}

/**
 * Generate P/L curve data for charting
 */
export function generatePnLCurve(
	position: IronCondorPosition, 
	priceRange?: number[]
): PnLDataPoint[] {
	// Use provided range or generate default range
	const centerPrice = (position.putShortStrike + position.callShortStrike) / 2
	const prices = priceRange || generatePriceRange(centerPrice, 0.15, 100)

	return prices.map(price => ({
		price,
		pnl: calculateIronCondorPnL(price, position)
	}))
}

/**
 * Validate strike order for Iron Condor
 */
export function validateStrikeOrder(position: IronCondorPosition): ValidationResult {
	const errors: string[] = []
	const { putLongStrike, putShortStrike, callShortStrike, callLongStrike } = position

	// Put strikes validation
	if (putLongStrike >= putShortStrike) {
		errors.push('Put long strike must be lower than put short strike')
	}

	// Call strikes validation  
	if (callShortStrike >= callLongStrike) {
		errors.push('Call short strike must be lower than call long strike')
	}

	// No overlap between put and call strikes
	if (putShortStrike >= callShortStrike) {
		errors.push('Put short strike must be lower than call short strike')
	}

	return {
		isValid: errors.length === 0,
		errors
	}
}

/**
 * Helper function to convert StrikeConfig percentages to IronCondorPosition
 */
export function strikeConfigToPosition(
	strikePercentages: {
		put_long_pct: number
		put_short_pct: number
		call_short_pct: number
		call_long_pct: number
	},
	currentPrice: number,
	credit: number = 25,
	contracts: number = 1
): IronCondorPosition {
	const roundToFive = (value: number) => Math.round(value / 5) * 5

	return {
		putLongStrike: roundToFive(currentPrice * (strikePercentages.put_long_pct / 100)),
		putShortStrike: roundToFive(currentPrice * (strikePercentages.put_short_pct / 100)),
		callShortStrike: roundToFive(currentPrice * (strikePercentages.call_short_pct / 100)),
		callLongStrike: roundToFive(currentPrice * (strikePercentages.call_long_pct / 100)),
		credit,
		contracts
	}
}