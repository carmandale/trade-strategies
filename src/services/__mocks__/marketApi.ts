// Mock implementation of MarketApiService for testing
export interface MarketPrice {
	symbol: string
	price: number
	timestamp: string
	change?: number
	change_percent?: number
}

export class MarketApiService {
	// Mock current market price
	static async getCurrentPrice(symbol: string): Promise<MarketPrice> {
		return {
			symbol,
			price: 430.50, // Fixed price for testing
			timestamp: new Date().toISOString(),
			change: 0.5,
			change_percent: 0.12
		}
	}

	// Mock historical price data
	static async getHistoricalPrices(
		symbol: string, 
		days: number = 30
	): Promise<{ date: string; price: number }[]> {
		// Generate mock historical data
		const result = []
		const baseDate = new Date()
		const basePrice = 430.50
		
		for (let i = 0; i < days; i++) {
			const date = new Date(baseDate)
			date.setDate(date.getDate() - i)
			
			result.push({
				date: date.toISOString().split('T')[0],
				price: basePrice + (Math.random() - 0.5) * 10
			})
		}
		
		return result
	}

	// Mock multiple prices
	static async getMultiplePrices(symbols: string[]): Promise<MarketPrice[]> {
		return symbols.map(symbol => ({
			symbol,
			price: 430.50, // Fixed price for testing
			timestamp: new Date().toISOString(),
			change: 0.5,
			change_percent: 0.12
		}))
	}
}

export default MarketApiService

