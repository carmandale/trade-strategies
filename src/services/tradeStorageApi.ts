/**
 * Trade Storage Service - Database Implementation
 * Uses PostgreSQL database via API endpoints for persistent storage
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface StoredTrade {
	id: string
	trade_date: string
	entry_time?: string
	symbol: string
	strategy_type: string
	strikes: number[]
	contracts: number
	entry_price: number
	credit_debit: number
	status: 'open' | 'closed' | 'expired'
	notes?: string
	strategy_id?: string
	exit_price?: number
	exit_time?: string
	realized_pnl?: number
	created_at: string
	updated_at: string
}

export interface TradeCreateRequest {
	trade_date: string
	entry_time?: string
	symbol: string
	strategy_type: string
	strikes: number[]
	contracts: number
	entry_price: number
	credit_debit: number
	status?: 'open' | 'closed' | 'expired'
	notes?: string
	strategy_id?: string
	exit_price?: number
	exit_time?: string
	realized_pnl?: number
}

export interface TradeStats {
	total_trades: number
	open_trades: number
	closed_trades: number
	total_realized_pnl: number
	win_rate: number
	avg_pnl_per_trade: number
}

export class TradeStorageApiService {
	/**
	 * Get all stored trades from database
	 */
	static async getAllTrades(filters?: {
		status?: string
		symbol?: string
		strategy_type?: string
		start_date?: string
		end_date?: string
		limit?: number
		offset?: number
	}): Promise<StoredTrade[]> {
		try {
			const params = new URLSearchParams()
			if (filters) {
				Object.entries(filters).forEach(([key, value]) => {
					if (value !== undefined) params.append(key, String(value))
				})
			}
			
			const response = await fetch(`${API_BASE_URL}/api/trades?${params}`)
			if (!response.ok) {
				throw new Error(`Failed to fetch trades: ${response.statusText}`)
			}
			
			return await response.json()
		} catch (error) {
			console.error('Error fetching trades:', error)
			// Fall back to localStorage if API fails
			return TradeStorageApiService.getLocalStorageTrades()
		}
	}
	
	/**
	 * Get a single trade by ID
	 */
	static async getTrade(id: string): Promise<StoredTrade | null> {
		try {
			const response = await fetch(`${API_BASE_URL}/api/trades/${id}`)
			if (response.status === 404) return null
			if (!response.ok) {
				throw new Error(`Failed to fetch trade: ${response.statusText}`)
			}
			
			return await response.json()
		} catch (error) {
			console.error('Error fetching trade:', error)
			return null
		}
	}
	
	/**
	 * Save a new trade to database
	 */
	static async saveTrade(trade: TradeCreateRequest): Promise<StoredTrade> {
		try {
			const response = await fetch(`${API_BASE_URL}/api/trades/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(trade)
			})
			
			if (!response.ok) {
				throw new Error(`Failed to create trade: ${response.statusText}`)
			}
			
			const createdTrade = await response.json()
			
			// Also save to localStorage as backup
			TradeStorageApiService.saveToLocalStorage(createdTrade)
			
			return createdTrade
		} catch (error) {
			console.error('Error creating trade:', error)
			// Fall back to localStorage if API fails
			const localTrade = {
				...trade,
				id: `local_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			} as StoredTrade
			TradeStorageApiService.saveToLocalStorage(localTrade)
			return localTrade
		}
	}
	
	/**
	 * Update an existing trade
	 */
	static async updateTrade(id: string, updates: Partial<StoredTrade>): Promise<StoredTrade | null> {
		try {
			const response = await fetch(`${API_BASE_URL}/api/trades/${id}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(updates)
			})
			
			if (response.status === 404) return null
			if (!response.ok) {
				throw new Error(`Failed to update trade: ${response.statusText}`)
			}
			
			const updatedTrade = await response.json()
			
			// Update localStorage backup
			TradeStorageApiService.updateLocalStorage(updatedTrade)
			
			return updatedTrade
		} catch (error) {
			console.error('Error updating trade:', error)
			return null
		}
	}
	
	/**
	 * Close a trade
	 */
	static async closeTrade(id: string, exitPrice: number, exitTime?: string, notes?: string): Promise<StoredTrade | null> {
		try {
			const response = await fetch(`${API_BASE_URL}/api/trades/${id}/close`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					exit_price: exitPrice,
					exit_time: exitTime,
					notes: notes
				})
			})
			
			if (response.status === 404) return null
			if (!response.ok) {
				throw new Error(`Failed to close trade: ${response.statusText}`)
			}
			
			const closedTrade = await response.json()
			
			// Update localStorage backup
			TradeStorageApiService.updateLocalStorage(closedTrade)
			
			return closedTrade
		} catch (error) {
			console.error('Error closing trade:', error)
			return null
		}
	}
	
	/**
	 * Delete a trade
	 */
	static async deleteTrade(id: string): Promise<boolean> {
		try {
			const response = await fetch(`${API_BASE_URL}/api/trades/${id}`, {
				method: 'DELETE'
			})
			
			if (response.status === 404) return false
			if (!response.ok) {
				throw new Error(`Failed to delete trade: ${response.statusText}`)
			}
			
			// Remove from localStorage backup
			TradeStorageApiService.removeFromLocalStorage(id)
			
			return true
		} catch (error) {
			console.error('Error deleting trade:', error)
			// Try to remove from localStorage at least
			TradeStorageApiService.removeFromLocalStorage(id)
			return false
		}
	}
	
	/**
	 * Get trade statistics
	 */
	static async getTradeStats(filters?: {
		symbol?: string
		strategy_type?: string
		start_date?: string
		end_date?: string
	}): Promise<TradeStats> {
		try {
			const params = new URLSearchParams()
			if (filters) {
				Object.entries(filters).forEach(([key, value]) => {
					if (value !== undefined) params.append(key, String(value))
				})
			}
			
			const response = await fetch(`${API_BASE_URL}/api/trades/stats/summary?${params}`)
			if (!response.ok) {
				throw new Error(`Failed to fetch stats: ${response.statusText}`)
			}
			
			return await response.json()
		} catch (error) {
			console.error('Error fetching stats:', error)
			// Calculate from local trades if API fails
			const trades = TradeStorageApiService.getLocalStorageTrades()
			return TradeStorageApiService.calculateLocalStats(trades)
		}
	}
	
	// === LocalStorage Backup Methods ===
	
	private static STORAGE_KEY = 'spy_trades_backup'
	
	/**
	 * Get trades from localStorage backup
	 */
	private static getLocalStorageTrades(): StoredTrade[] {
		try {
			const stored = localStorage.getItem(this.STORAGE_KEY)
			return stored ? JSON.parse(stored) : []
		} catch {
			return []
		}
	}
	
	/**
	 * Save trade to localStorage backup
	 */
	private static saveToLocalStorage(trade: StoredTrade): void {
		try {
			const trades = this.getLocalStorageTrades()
			const index = trades.findIndex(t => t.id === trade.id)
			if (index >= 0) {
				trades[index] = trade
			} else {
				trades.unshift(trade)
			}
			localStorage.setItem(this.STORAGE_KEY, JSON.stringify(trades))
		} catch (error) {
			console.error('Error saving to localStorage backup:', error)
		}
	}
	
	/**
	 * Update trade in localStorage backup
	 */
	private static updateLocalStorage(trade: StoredTrade): void {
		this.saveToLocalStorage(trade)
	}
	
	/**
	 * Remove trade from localStorage backup
	 */
	private static removeFromLocalStorage(id: string): void {
		try {
			const trades = this.getLocalStorageTrades()
			const filtered = trades.filter(t => t.id !== id)
			localStorage.setItem(this.STORAGE_KEY, JSON.stringify(filtered))
		} catch (error) {
			console.error('Error removing from localStorage backup:', error)
		}
	}
	
	/**
	 * Calculate stats from local trades
	 */
	private static calculateLocalStats(trades: StoredTrade[]): TradeStats {
		const openTrades = trades.filter(t => t.status === 'open').length
		const closedTrades = trades.filter(t => t.status === 'closed').length
		const realizedTrades = trades.filter(t => t.realized_pnl !== undefined)
		const totalPnl = realizedTrades.reduce((sum, t) => sum + (t.realized_pnl || 0), 0)
		const winningTrades = realizedTrades.filter(t => (t.realized_pnl || 0) > 0).length
		const winRate = realizedTrades.length > 0 ? (winningTrades / realizedTrades.length) * 100 : 0
		const avgPnl = realizedTrades.length > 0 ? totalPnl / realizedTrades.length : 0
		
		return {
			total_trades: trades.length,
			open_trades: openTrades,
			closed_trades: closedTrades,
			total_realized_pnl: totalPnl,
			win_rate: winRate,
			avg_pnl_per_trade: avgPnl
		}
	}
	
	/**
	 * Sync localStorage trades to database (one-time migration)
	 */
	static async syncLocalToDatabase(): Promise<number> {
		const localTrades = this.getLocalStorageTrades()
		let syncedCount = 0
		
		for (const trade of localTrades) {
			// Skip trades that already have non-local IDs (already in DB)
			if (!trade.id.startsWith('local_')) continue
			
			try {
				// Create trade in database
				const dbTrade = await this.saveTrade({
					trade_date: trade.trade_date,
					entry_time: trade.entry_time,
					symbol: trade.symbol,
					strategy_type: trade.strategy_type,
					strikes: trade.strikes,
					contracts: trade.contracts,
					entry_price: trade.entry_price,
					credit_debit: trade.credit_debit,
					status: trade.status,
					notes: trade.notes,
					exit_price: trade.exit_price,
					exit_time: trade.exit_time,
					realized_pnl: trade.realized_pnl
				})
				
				// Remove old local trade and replace with DB version
				this.removeFromLocalStorage(trade.id)
				this.saveToLocalStorage(dbTrade)
				syncedCount++
			} catch (error) {
				console.error(`Failed to sync trade ${trade.id}:`, error)
			}
		}
		
		return syncedCount
	}
}

export default TradeStorageApiService