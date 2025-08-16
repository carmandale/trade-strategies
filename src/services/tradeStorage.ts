/**
 * Trade Storage Service
 * Manages persistent storage of trades using localStorage
 */

export interface StoredTrade {
	id: string
	strategy: 'bullCall' | 'ironCondor' | 'butterfly'
	symbol: string
	executedAt: string
	expirationDate: string
	contracts: number
	strikes: {
		bullCallLower?: number
		bullCallUpper?: number
		ironCondorPutLong?: number
		ironCondorPutShort?: number
		ironCondorCallShort?: number
		ironCondorCallLong?: number
		butterflyLower?: number
		butterflyBody?: number
		butterflyUpper?: number
	}
	entryPrice: number
	analysis?: {
		maxProfit?: number
		maxLoss?: number
		breakeven?: number | number[]
		riskReward?: number
	}
	notes?: string
	status: 'active' | 'closed' | 'expired'
	closePrice?: number
	closedAt?: string
	pnl?: number
}

const STORAGE_KEY = 'spy_trades_history'
const MAX_TRADES = 1000 // Maximum number of trades to store

export class TradeStorageService {
	/**
	 * Get all stored trades
	 */
	static getAllTrades(): StoredTrade[] {
		try {
			const stored = localStorage.getItem(STORAGE_KEY)
			if (!stored) return []
			
			const trades = JSON.parse(stored) as StoredTrade[]
			// Sort by execution date, newest first
			return trades.sort((a, b) => 
				new Date(b.executedAt).getTime() - new Date(a.executedAt).getTime()
			)
		} catch (error) {
			console.error('Error loading trades from storage:', error)
			return []
		}
	}
	
	/**
	 * Get active trades only
	 */
	static getActiveTrades(): StoredTrade[] {
		return this.getAllTrades().filter(trade => trade.status === 'active')
	}
	
	/**
	 * Get trades by strategy type
	 */
	static getTradesByStrategy(strategy: StoredTrade['strategy']): StoredTrade[] {
		return this.getAllTrades().filter(trade => trade.strategy === strategy)
	}
	
	/**
	 * Get a single trade by ID
	 */
	static getTrade(id: string): StoredTrade | null {
		const trades = this.getAllTrades()
		return trades.find(trade => trade.id === id) || null
	}
	
	/**
	 * Save a new trade
	 */
	static saveTrade(trade: Omit<StoredTrade, 'id'>): StoredTrade {
		const trades = this.getAllTrades()
		
		// Generate unique ID
		const newTrade: StoredTrade = {
			...trade,
			id: `trade_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
		}
		
		// Add to beginning of array (newest first)
		trades.unshift(newTrade)
		
		// Limit total stored trades
		if (trades.length > MAX_TRADES) {
			trades.splice(MAX_TRADES)
		}
		
		// Save to localStorage
		try {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(trades))
			console.log('Trade saved:', newTrade.id)
			return newTrade
		} catch (error) {
			console.error('Error saving trade:', error)
			// If localStorage is full, try removing oldest trades
			if (trades.length > 100) {
				const reducedTrades = trades.slice(0, 100)
				localStorage.setItem(STORAGE_KEY, JSON.stringify(reducedTrades))
				return newTrade
			}
			throw error
		}
	}
	
	/**
	 * Update an existing trade
	 */
	static updateTrade(id: string, updates: Partial<StoredTrade>): StoredTrade | null {
		const trades = this.getAllTrades()
		const index = trades.findIndex(trade => trade.id === id)
		
		if (index === -1) {
			console.error('Trade not found:', id)
			return null
		}
		
		// Update the trade
		trades[index] = {
			...trades[index],
			...updates,
			id: trades[index].id // Ensure ID doesn't change
		}
		
		// Save back to localStorage
		try {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(trades))
			console.log('Trade updated:', id)
			return trades[index]
		} catch (error) {
			console.error('Error updating trade:', error)
			throw error
		}
	}
	
	/**
	 * Close a trade
	 */
	static closeTrade(id: string, closePrice: number, pnl?: number): StoredTrade | null {
		return this.updateTrade(id, {
			status: 'closed',
			closePrice,
			closedAt: new Date().toISOString(),
			pnl
		})
	}
	
	/**
	 * Delete a trade
	 */
	static deleteTrade(id: string): boolean {
		const trades = this.getAllTrades()
		const filteredTrades = trades.filter(trade => trade.id !== id)
		
		if (filteredTrades.length === trades.length) {
			console.error('Trade not found for deletion:', id)
			return false
		}
		
		try {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(filteredTrades))
			console.log('Trade deleted:', id)
			return true
		} catch (error) {
			console.error('Error deleting trade:', error)
			return false
		}
	}
	
	/**
	 * Delete all trades
	 */
	static clearAllTrades(): void {
		try {
			localStorage.removeItem(STORAGE_KEY)
			console.log('All trades cleared')
		} catch (error) {
			console.error('Error clearing trades:', error)
		}
	}
	
	/**
	 * Export trades as JSON
	 */
	static exportTrades(): string {
		const trades = this.getAllTrades()
		return JSON.stringify(trades, null, 2)
	}
	
	/**
	 * Import trades from JSON
	 */
	static importTrades(jsonString: string, merge = false): number {
		try {
			const importedTrades = JSON.parse(jsonString) as StoredTrade[]
			
			if (!Array.isArray(importedTrades)) {
				throw new Error('Invalid trade data format')
			}
			
			let trades = merge ? this.getAllTrades() : []
			
			// Add imported trades, avoiding duplicates by ID
			const existingIds = new Set(trades.map(t => t.id))
			let importCount = 0
			
			for (const trade of importedTrades) {
				if (!existingIds.has(trade.id)) {
					trades.push(trade)
					importCount++
				}
			}
			
			// Sort and limit
			trades.sort((a, b) => 
				new Date(b.executedAt).getTime() - new Date(a.executedAt).getTime()
			)
			
			if (trades.length > MAX_TRADES) {
				trades = trades.slice(0, MAX_TRADES)
			}
			
			localStorage.setItem(STORAGE_KEY, JSON.stringify(trades))
			console.log(`Imported ${importCount} trades`)
			return importCount
		} catch (error) {
			console.error('Error importing trades:', error)
			throw error
		}
	}
	
	/**
	 * Get storage statistics
	 */
	static getStorageStats() {
		const trades = this.getAllTrades()
		const storageUsed = JSON.stringify(trades).length
		
		return {
			totalTrades: trades.length,
			activeTrades: trades.filter(t => t.status === 'active').length,
			closedTrades: trades.filter(t => t.status === 'closed').length,
			expiredTrades: trades.filter(t => t.status === 'expired').length,
			storageUsedBytes: storageUsed,
			storageUsedKB: (storageUsed / 1024).toFixed(2)
		}
	}
}

export default TradeStorageService