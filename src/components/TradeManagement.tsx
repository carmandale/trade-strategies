import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
	Trash2, 
	Download, 
	Upload, 
	Archive, 
	TrendingUp, 
	TrendingDown,
	Clock,
	Filter,
	X
} from 'lucide-react';
import TradeStorageApiService, { StoredTrade } from '../services/tradeStorageApi';

interface TradeManagementProps {
	trades: StoredTrade[]
	onDeleteTrade: (id: string) => void
	onCloseTrade?: (id: string, closePrice: number) => void
	onRefresh: () => void
}

export const TradeManagement: React.FC<TradeManagementProps> = ({
	trades,
	onDeleteTrade,
	onCloseTrade,
	onRefresh
}) => {
	const [filterStrategy, setFilterStrategy] = useState<string>('all')
	const [filterStatus, setFilterStatus] = useState<string>('all')
	const [showExportModal, setShowExportModal] = useState(false)
	const [showImportModal, setShowImportModal] = useState(false)
	const [importData, setImportData] = useState('')
	
	// Get storage stats (calculated from provided trades)
	const stats = {
		totalTrades: trades.length,
		activeTrades: trades.filter(t => t.status === 'open').length,
		closedTrades: trades.filter(t => t.status === 'closed').length,
		expiredTrades: trades.filter(t => t.status === 'expired').length,
		storageUsedBytes: 0,
		storageUsedKB: '0'
	}
	
	// Filter trades
	const filteredTrades = trades.filter(trade => {
		if (filterStrategy !== 'all' && trade.strategy_type !== filterStrategy) return false
		if (filterStatus !== 'all' && trade.status !== filterStatus) return false
		return true
	})
	
	// Calculate summary statistics
	const totalPnL = filteredTrades.reduce((sum, trade) => sum + (trade.realized_pnl || 0), 0)
	const winningTrades = filteredTrades.filter(trade => (trade.realized_pnl || 0) > 0).length
	const losingTrades = filteredTrades.filter(trade => (trade.realized_pnl || 0) < 0).length
	const winRate = filteredTrades.length > 0 ? (winningTrades / filteredTrades.length) * 100 : 0
	
	const handleExport = () => {
		const json = JSON.stringify(trades, null, 2)
		const blob = new Blob([json], { type: 'application/json' })
		const url = URL.createObjectURL(blob)
		const a = document.createElement('a')
		a.href = url
		a.download = `spy-trades-${new Date().toISOString().split('T')[0]}.json`
		a.click()
		URL.revokeObjectURL(url)
		setShowExportModal(false)
	}
	
	const handleImport = async () => {
		try {
			const tradesToImport = JSON.parse(importData) as StoredTrade[]
			let importCount = 0
			
			for (const trade of tradesToImport) {
				try {
					await TradeStorageApiService.saveTrade({
						trade_date: trade.trade_date || new Date().toISOString().split('T')[0],
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
					importCount++
				} catch (error) {
					console.error(`Failed to import trade:`, error)
				}
			}
			
			alert(`Successfully imported ${importCount} trades`)
			onRefresh()
			setShowImportModal(false)
			setImportData('')
		} catch (error) {
			alert('Error importing trades: ' + error)
		}
	}
	
	const handleClearAll = async () => {
		if (confirm('Are you sure you want to delete ALL trades? This cannot be undone.')) {
			// Delete all trades from database
			for (const trade of trades) {
				await TradeStorageApiService.deleteTrade(trade.id)
			}
			onRefresh()
		}
	}
	
	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		})
	}
	
	const formatStrikes = (trade: StoredTrade): string => {
		if (Array.isArray(trade.strikes)) {
			return trade.strikes.join('/')
		}
		return ''
	}
	
	const formatStrategyName = (strategyType: string): string => {
		switch(strategyType.toLowerCase()) {
			case 'bull_call':
			case 'bullcall':
				return 'Bull Call'
			case 'iron_condor':
			case 'ironcondor':
				return 'Iron Condor'
			case 'butterfly':
				return 'Butterfly'
			default:
				return strategyType
		}
	}
	
	return (
		<div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
			{/* Header */}
			<div className="flex items-center justify-between mb-6">
				<div>
					<h2 className="text-2xl font-bold text-slate-100 mb-2">Trade History</h2>
					<div className="flex items-center gap-4 text-sm text-slate-400">
						<span>Total: {stats.totalTrades} trades</span>
						<span>Active: {stats.activeTrades}</span>
						<span>Closed: {stats.closedTrades}</span>
						<span>Storage: {stats.storageUsedKB} KB</span>
					</div>
				</div>
				
				<div className="flex items-center gap-2">
					<button
						onClick={() => setShowImportModal(true)}
						className="p-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-slate-100 transition-colors"
						title="Import trades"
					>
						<Upload className="w-5 h-5" />
					</button>
					<button
						onClick={() => setShowExportModal(true)}
						className="p-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-slate-100 transition-colors"
						title="Export trades"
					>
						<Download className="w-5 h-5" />
					</button>
					<button
						onClick={handleClearAll}
						className="p-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-400 hover:text-red-300 transition-colors"
						title="Clear all trades"
					>
						<Archive className="w-5 h-5" />
					</button>
				</div>
			</div>
			
			{/* Summary Stats */}
			<div className="grid grid-cols-4 gap-4 mb-6">
				<div className="bg-slate-700/30 rounded-xl p-4">
					<div className="text-slate-400 text-sm mb-1">Total P&L</div>
					<div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
						${totalPnL.toFixed(2)}
					</div>
				</div>
				<div className="bg-slate-700/30 rounded-xl p-4">
					<div className="text-slate-400 text-sm mb-1">Win Rate</div>
					<div className="text-2xl font-bold text-slate-100">
						{winRate.toFixed(1)}%
					</div>
				</div>
				<div className="bg-slate-700/30 rounded-xl p-4">
					<div className="text-slate-400 text-sm mb-1">Winning</div>
					<div className="text-2xl font-bold text-green-400">
						{winningTrades}
					</div>
				</div>
				<div className="bg-slate-700/30 rounded-xl p-4">
					<div className="text-slate-400 text-sm mb-1">Losing</div>
					<div className="text-2xl font-bold text-red-400">
						{losingTrades}
					</div>
				</div>
			</div>
			
			{/* Filters */}
			<div className="flex items-center gap-4 mb-6">
				<div className="flex items-center gap-2">
					<Filter className="w-4 h-4 text-slate-400" />
					<span className="text-slate-400 text-sm">Filter:</span>
				</div>
				
				<select
					value={filterStrategy}
					onChange={(e) => setFilterStrategy(e.target.value)}
					className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-1 text-sm text-slate-200"
				>
					<option value="all">All Strategies</option>
					<option value="bull_call">Bull Call</option>
					<option value="iron_condor">Iron Condor</option>
					<option value="butterfly">Butterfly</option>
				</select>
				
				<select
					value={filterStatus}
					onChange={(e) => setFilterStatus(e.target.value)}
					className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-1 text-sm text-slate-200"
				>
					<option value="all">All Status</option>
					<option value="active">Active</option>
					<option value="closed">Closed</option>
					<option value="expired">Expired</option>
				</select>
			</div>
			
			{/* Trade List */}
			<div className="space-y-2 max-h-96 overflow-y-auto">
				<AnimatePresence>
					{filteredTrades.length === 0 ? (
						<div className="text-center py-8 text-slate-500">
							No trades found. Execute a strategy to see it here.
						</div>
					) : (
						filteredTrades.map(trade => (
							<motion.div
								key={trade.id}
								initial={{ opacity: 0, y: 20 }}
								animate={{ opacity: 1, y: 0 }}
								exit={{ opacity: 0, x: -100 }}
								className="bg-slate-700/30 rounded-lg p-4 flex items-center justify-between hover:bg-slate-700/50 transition-colors"
							>
								<div className="flex items-center gap-4">
									{/* Status Indicator */}
									<div className={`w-2 h-2 rounded-full ${
										trade.status === 'active' ? 'bg-green-400' : 
										trade.status === 'closed' ? 'bg-slate-400' : 'bg-orange-400'
									}`} />
									
									{/* Trade Info */}
									<div>
										<div className="flex items-center gap-3">
											<span className="font-semibold text-slate-100">
												{formatStrategyName(trade.strategy_type)}
											</span>
											<span className="text-slate-400 text-sm">
												{formatStrikes(trade)}
											</span>
											<span className="text-slate-500 text-xs">
												{trade.contracts} contracts
											</span>
										</div>
										<div className="flex items-center gap-3 mt-1">
											<span className="text-slate-500 text-xs flex items-center gap-1">
												<Clock className="w-3 h-3" />
												{formatDate(trade.created_at || trade.trade_date)}
											</span>
											{trade.notes && (
												<span className="text-slate-500 text-xs">
													{trade.notes}
												</span>
											)}
										</div>
									</div>
								</div>
								
								{/* Actions and P&L */}
								<div className="flex items-center gap-4">
									{/* P&L Display */}
									{trade.realized_pnl !== undefined && trade.realized_pnl !== null && (
										<div className={`flex items-center gap-1 font-semibold ${
											trade.realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
										}`}>
											{trade.realized_pnl >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
											${Math.abs(trade.realized_pnl).toFixed(2)}
										</div>
									)}
									
									{/* Close Trade Button (for active trades) */}
									{trade.status === 'active' && onCloseTrade && (
										<button
											onClick={() => {
												const closePrice = prompt('Enter closing price:')
												if (closePrice) {
													onCloseTrade(trade.id, parseFloat(closePrice))
												}
											}}
											className="p-2 bg-blue-500/20 hover:bg-blue-500/30 rounded-lg text-blue-400 hover:text-blue-300 transition-colors"
											title="Close trade"
										>
											<X className="w-4 h-4" />
										</button>
									)}
									
									{/* Delete Button */}
									<button
										onClick={() => {
											if (confirm('Delete this trade?')) {
												onDeleteTrade(trade.id)
											}
										}}
										className="p-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-400 hover:text-red-300 transition-colors"
										title="Delete trade"
									>
										<Trash2 className="w-4 h-4" />
									</button>
								</div>
							</motion.div>
						))
					)}
				</AnimatePresence>
			</div>
			
			{/* Export Modal */}
			{showExportModal && (
				<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
					<div className="bg-slate-800 rounded-xl p-6 max-w-md w-full">
						<h3 className="text-xl font-bold text-slate-100 mb-4">Export Trades</h3>
						<p className="text-slate-400 mb-4">
							Export all {stats.totalTrades} trades as a JSON file for backup or analysis.
						</p>
						<div className="flex justify-end gap-3">
							<button
								onClick={() => setShowExportModal(false)}
								className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 transition-colors"
							>
								Cancel
							</button>
							<button
								onClick={handleExport}
								className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white transition-colors"
							>
								Export
							</button>
						</div>
					</div>
				</div>
			)}
			
			{/* Import Modal */}
			{showImportModal && (
				<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
					<div className="bg-slate-800 rounded-xl p-6 max-w-md w-full">
						<h3 className="text-xl font-bold text-slate-100 mb-4">Import Trades</h3>
						<p className="text-slate-400 mb-4">
							Paste JSON data to import trades:
						</p>
						<textarea
							value={importData}
							onChange={(e) => setImportData(e.target.value)}
							className="w-full h-32 bg-slate-700 border border-slate-600 rounded-lg p-3 text-slate-200 mb-4"
							placeholder="Paste JSON data here..."
						/>
						<div className="flex justify-end gap-3">
							<button
								onClick={() => {
									setShowImportModal(false)
									setImportData('')
								}}
								className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 transition-colors"
							>
								Cancel
							</button>
							<button
								onClick={handleImport}
								className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white transition-colors"
							>
								Import
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	)
}