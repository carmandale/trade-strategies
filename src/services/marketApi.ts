// Market data API service for current prices and market information
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface MarketPrice {
	symbol: string
	price: number
	timestamp: string
	change?: number
	change_percent?: number
}

export class MarketApiService {
	// Get current market price for a symbol
	static async getCurrentPrice(symbol: string): Promise<MarketPrice> {
		try {
			const response = await fetch(`${API_BASE_URL}/api/market/price/${symbol}`)
			
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`)
			}

			const data = await response.json()
			
			return {
				symbol: data.symbol || symbol,
				price: data.price || 0,
				timestamp: data.timestamp || new Date().toISOString(),
				change: data.change,
				change_percent: data.change_percent
			}
		} catch (error) {
			console.error(`Error fetching price for ${symbol}:`, error)
			
			// Return fallback mock data for development
			return this.getMockPrice(symbol)
		}
	}

	// Get historical price data
	static async getHistoricalPrices(
		symbol: string, 
		days: number = 30
	): Promise<{ date: string; price: number }[]> {
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/market/history/${symbol}?days=${days}`
			)
			
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`)
			}

			return await response.json()
		} catch (error) {
			console.error(`Error fetching historical prices for ${symbol}:`, error)
			return []
		}
	}

	// Get multiple prices at once
	static async getMultiplePrices(symbols: string[]): Promise<MarketPrice[]> {
		try {
			const response = await fetch(`${API_BASE_URL}/api/market/prices`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ symbols })
			})
			
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`)
			}

			const data = await response.json()
			return data.prices || symbols.map(symbol => this.getMockPrice(symbol))
		} catch (error) {
			console.error(`Error fetching multiple prices:`, error)
			return symbols.map(symbol => this.getMockPrice(symbol))
		}
	}

	// Mock price data for development/fallback
	private static getMockPrice(symbol: string): MarketPrice {
		const basePrices: Record<string, number> = {
			'SPY': 430.50,
			'QQQ': 365.20,
			'IWM': 195.80,
			'SPX': 4305.20,
			'AAPL': 175.40,
			'MSFT': 380.90,
			'TSLA': 245.60
		}

		const basePrice = basePrices[symbol] || 100.00
		
		// Add some random variation to simulate real market movement
		const variation = (Math.random() - 0.5) * 0.02 // ±1% variation
		const mockPrice = basePrice * (1 + variation)
		
		return {
			symbol,
			price: Math.round(mockPrice * 100) / 100, // Round to 2 decimal places
			timestamp: new Date().toISOString(),
			change: Math.round((mockPrice - basePrice) * 100) / 100,
			change_percent: Math.round(variation * 10000) / 100 // Convert to percentage
		}
	}
}

export default MarketApiService