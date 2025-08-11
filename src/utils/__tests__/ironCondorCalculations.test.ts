import { describe, it, expect } from 'vitest'
import {
	calculateIronCondorPnL,
	calculateBreakevenPoints,
	getMaxProfitLoss,
	generatePriceRange,
	validateStrikeOrder,
	type IronCondorPosition,
	type PnLDataPoint
} from '../ironCondorCalculations'

describe('ironCondorCalculations', () => {
	const mockPosition: IronCondorPosition = {
		putLongStrike: 4900,
		putShortStrike: 4950,
		callShortStrike: 5050,
		callLongStrike: 5100,
		credit: 25, // Net credit received
		contracts: 1
	}

	describe('calculateIronCondorPnL', () => {
		it('should calculate maximum profit when price is between short strikes', () => {
			const pnl = calculateIronCondorPnL(5000, mockPosition)
			expect(pnl).toBe(25) // Full credit received
		})

		it('should calculate maximum loss when price is below put long strike', () => {
			const pnl = calculateIronCondorPnL(4850, mockPosition)
			expect(pnl).toBe(-25) // Max loss = width - credit = 50 - 25 = -25
		})

		it('should calculate maximum loss when price is above call long strike', () => {
			const pnl = calculateIronCondorPnL(5150, mockPosition)
			expect(pnl).toBe(-25) // Same max loss
		})

		it('should calculate partial loss on put side', () => {
			const pnl = calculateIronCondorPnL(4920, mockPosition)
			// Put spread loses value: (4950 - 4920) = 30
			// P&L = credit - put loss = 25 - 30 = -5
			expect(pnl).toBe(-5)
		})

		it('should calculate partial loss on call side', () => {
			const pnl = calculateIronCondorPnL(5080, mockPosition)
			// Call spread loses value: (5080 - 5050) = 30
			// P&L = credit - call loss = 25 - 30 = -5
			expect(pnl).toBe(-5)
		})

		it('should handle multiple contracts', () => {
			const multiContractPosition = { ...mockPosition, contracts: 2 }
			const pnl = calculateIronCondorPnL(5000, multiContractPosition)
			expect(pnl).toBe(50) // 25 * 2 contracts
		})

		it('should handle zero credit (debug case)', () => {
			const zeroCreditPosition = { ...mockPosition, credit: 0 }
			const pnl = calculateIronCondorPnL(5000, zeroCreditPosition)
			expect(pnl).toBe(0)
		})
	})

	describe('calculateBreakevenPoints', () => {
		it('should calculate correct breakeven points', () => {
			const breakevens = calculateBreakevenPoints(mockPosition)
			expect(breakevens).toEqual({
				lowerBreakeven: 4925, // putShortStrike - credit = 4950 - 25
				upperBreakeven: 5075  // callShortStrike + credit = 5050 + 25
			})
		})

		it('should handle different credit amounts', () => {
			const highCreditPosition = { ...mockPosition, credit: 40 }
			const breakevens = calculateBreakevenPoints(highCreditPosition)
			expect(breakevens).toEqual({
				lowerBreakeven: 4910, // 4950 - 40
				upperBreakeven: 5090  // 5050 + 40
			})
		})

		it('should handle zero credit', () => {
			const zeroCreditPosition = { ...mockPosition, credit: 0 }
			const breakevens = calculateBreakevenPoints(zeroCreditPosition)
			expect(breakevens).toEqual({
				lowerBreakeven: 4950, // Same as short strikes
				upperBreakeven: 5050
			})
		})
	})

	describe('getMaxProfitLoss', () => {
		it('should calculate correct maximum profit and loss', () => {
			const maxPnL = getMaxProfitLoss(mockPosition)
			expect(maxPnL).toEqual({
				maxProfit: 25,  // Credit received
				maxLoss: -25    // Spread width - credit = 50 - 25 = -25
			})
		})

		it('should handle wide spreads', () => {
			const widePosition = {
				...mockPosition,
				putLongStrike: 4800,
				callLongStrike: 5200,
				credit: 30
			}
			const maxPnL = getMaxProfitLoss(widePosition)
			expect(maxPnL).toEqual({
				maxProfit: 30,  // Credit
				maxLoss: -70    // 100 - 30 = -70
			})
		})

		it('should handle multiple contracts', () => {
			const multiPosition = { ...mockPosition, contracts: 3 }
			const maxPnL = getMaxProfitLoss(multiPosition)
			expect(maxPnL).toEqual({
				maxProfit: 75,  // 25 * 3
				maxLoss: -75    // -25 * 3
			})
		})
	})

	describe('generatePriceRange', () => {
		it('should generate price range around current price', () => {
			const range = generatePriceRange(5000, 0.1, 10) // 10% range, 10 points
			expect(range.length).toBe(10)
			expect(range[0]).toBe(4500) // 5000 * 0.9
			expect(range[range.length - 1]).toBe(5500) // 5000 * 1.1
		})

		it('should handle custom step sizes', () => {
			const range = generatePriceRange(5000, 0.05, 5) // 5% range, 5 points
			expect(range.length).toBe(5)
			expect(range[0]).toBe(4750) // 5000 * 0.95
			expect(range[range.length - 1]).toBe(5250) // 5000 * 1.05
		})

		it('should round to nearest integer', () => {
			const range = generatePriceRange(5000.7, 0.01, 3)
			expect(range.every(price => Number.isInteger(price))).toBe(true)
		})

		it('should handle edge case of single point', () => {
			const range = generatePriceRange(5000, 0.1, 1)
			expect(range).toEqual([5000])
		})
	})

	describe('validateStrikeOrder', () => {
		it('should validate correct strike order', () => {
			const result = validateStrikeOrder(mockPosition)
			expect(result.isValid).toBe(true)
			expect(result.errors).toEqual([])
		})

		it('should catch put strikes in wrong order', () => {
			const invalidPosition = {
				...mockPosition,
				putLongStrike: 4960, // Higher than putShortStrike
				putShortStrike: 4950
			}
			const result = validateStrikeOrder(invalidPosition)
			expect(result.isValid).toBe(false)
			expect(result.errors).toContain('Put long strike must be lower than put short strike')
		})

		it('should catch call strikes in wrong order', () => {
			const invalidPosition = {
				...mockPosition,
				callShortStrike: 5100, // Higher than callLongStrike
				callLongStrike: 5090
			}
			const result = validateStrikeOrder(invalidPosition)
			expect(result.isValid).toBe(false)
			expect(result.errors).toContain('Call short strike must be lower than call long strike')
		})

		it('should catch overlapping put and call strikes', () => {
			const invalidPosition = {
				...mockPosition,
				putShortStrike: 5060, // Higher than callShortStrike
				callShortStrike: 5050
			}
			const result = validateStrikeOrder(invalidPosition)
			expect(result.isValid).toBe(false)
			expect(result.errors).toContain('Put short strike must be lower than call short strike')
		})

		it('should catch multiple validation errors', () => {
			const invalidPosition = {
				putLongStrike: 4960,
				putShortStrike: 4950,
				callShortStrike: 5100,
				callLongStrike: 5090,
				credit: 25,
				contracts: 1
			}
			const result = validateStrikeOrder(invalidPosition)
			expect(result.isValid).toBe(false)
			expect(result.errors.length).toBeGreaterThan(1)
		})

		it('should validate equal strikes as invalid', () => {
			const invalidPosition = {
				...mockPosition,
				putLongStrike: 4950, // Equal to putShortStrike
				putShortStrike: 4950
			}
			const result = validateStrikeOrder(invalidPosition)
			expect(result.isValid).toBe(false)
		})
	})
})