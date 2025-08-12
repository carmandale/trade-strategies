// Strategy data types for the display components

export interface StrikeConfig {
	put_short_pct: number
	put_long_pct: number
	call_short_pct: number
	call_long_pct: number
}

export interface StrategyPerformance {
	total_pnl: number
	win_rate: number
	total_trades: number
	avg_pnl_per_trade: number
	sharpe_ratio?: number
	max_drawdown?: number
}

export interface StrategyData {
	id: string
	name: string
	strategy_type: 'iron_condor' | 'bull_call'
	symbol: string
	timeframe: 'daily' | 'weekly' | 'monthly'
	parameters: Record<string, any>
	performance: StrategyPerformance
	is_active: boolean
	data_source?: 'ib_realtime' | 'estimate' | 'mixed'
	ib_snapshot?: Record<string, any>
	created_at: string
	updated_at: string
}

export interface Trade {
	id: string
	strategy_id: string
	entry_date: string
	exit_date?: string
	strikes: number[]
	contracts: number
	entry_price: number
	exit_price?: number
	realized_pnl?: number
	status: 'open' | 'closed'
	notes?: string
}

export interface ApiResponse<T> {
	data: T
	message?: string
	error?: string
}

export interface LoadingState {
	isLoading: boolean
	error: string | null
}

export interface StrategyListProps {
	strategies: StrategyData[]
	loading?: boolean
	error?: string | null
	onStrategySelect?: (strategy: StrategyData) => void
}

export interface StrategyCardProps {
	strategy: StrategyData
	onClick?: () => void
	showDetails?: boolean
}

export interface PerformanceMetricsProps {
	performance: StrategyPerformance
	timeframe: string
}