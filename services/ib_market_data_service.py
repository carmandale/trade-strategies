"""Interactive Brokers market data service with real-time options data."""
import logging
import asyncio
import time
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import math
from scipy.stats import norm
from ib_insync import Stock, Option, Contract
from services.ib_connection_manager import ib_connection_manager
from database.config import get_db_session
from database.models import OptionsDataCache, HistoricalOptionsData

logger = logging.getLogger(__name__)


class IBMarketDataService:
	"""Service for fetching real-time options data from Interactive Brokers."""
	
	def __init__(self):
		"""Initialize the market data service."""
		self.connection_manager = ib_connection_manager
		self.cache_ttl = 5  # 5-second cache TTL for real-time data
		self.rate_limit = 50  # Max requests per second
		self.request_queue: List[Dict[str, Any]] = []
		self.last_request_time: Optional[datetime] = None
		self.streaming_task: Optional[asyncio.Task] = None
		self.active_subscriptions: Dict[str, Any] = {}
	
	def fetch_options_chain(self, 
							symbol: str,
							expiration: date,
							strikes: Optional[List[float]] = None) -> List[Dict[str, Any]]:
		"""Fetch options chain data from Interactive Brokers.
		
		Args:
			symbol: Underlying symbol (e.g., 'SPY')
			expiration: Option expiration date
			strikes: Optional list of specific strikes to fetch
		
		Returns:
			List of option contract data
		"""
		if not self.connection_manager.is_connected:
			logger.warning("Not connected to IB, cannot fetch options chain")
			return []
		
		try:
			# Check rate limiting
			wait_time = self.check_rate_limit()
			if wait_time > 0:
				time.sleep(wait_time)
			
			# Update last request time
			self.last_request_time = datetime.now(timezone.utc)
			
			# Create underlying stock contract
			stock = Stock(symbol, 'SMART', 'USD')
			self.connection_manager.ib_client.qualifyContracts(stock)
			
			# Get underlying price
			underlying_price = self.get_underlying_price(symbol)
			if not underlying_price:
				logger.error(f"Could not get underlying price for {symbol}")
				return []
			
			options_data = []
			
			# Determine strikes to fetch
			if not strikes:
				# Generate ATM strikes around current price
				atm_strike = round(underlying_price / 5) * 5  # Round to nearest 5
				strikes = [atm_strike + i * 5 for i in range(-10, 11)]  # 21 strikes
			
			# Format expiration for IB
			exp_str = expiration.strftime('%Y%m%d')
			
			# Fetch both calls and puts for each strike
			for strike in strikes:
				for right in ['C', 'P']:  # Call and Put
					try:
						option = Option(symbol, exp_str, strike, right, 'SMART')
						qualified = self.connection_manager.ib_client.qualifyContracts(option)
						
						if qualified:
							# Request market data
							ticker = self.connection_manager.ib_client.reqMktData(qualified[0])
							self.connection_manager.ib_client.sleep(0.1)  # Small delay
							
							# Format option data
							option_data = self.format_option_data(ticker, underlying_price)
							if option_data:
								options_data.append(option_data)
								
								# Cache the data
								self.cache_options_data(option_data)
					
					except Exception as e:
						logger.warning(f"Error fetching {symbol} {strike} {right}: {str(e)}")
						continue
			
			logger.info(f"Fetched {len(options_data)} option contracts for {symbol}")
			return options_data
			
		except Exception as e:
			logger.error(f"Error fetching options chain for {symbol}: {str(e)}")
			return []
	
	def get_underlying_price(self, symbol: str) -> Optional[float]:
		"""Get current underlying price.
		
		Args:
			symbol: Stock symbol
		
		Returns:
			Current price or None if not available
		"""
		if not self.connection_manager.is_connected:
			return None
		
		try:
			stock = Stock(symbol, 'SMART', 'USD')
			qualified = self.connection_manager.ib_client.qualifyContracts(stock)
			
			if qualified:
				ticker = self.connection_manager.ib_client.reqMktData(qualified[0])
				self.connection_manager.ib_client.sleep(0.1)
				
				if hasattr(ticker, 'last') and ticker.last:
					return float(ticker.last)
				elif hasattr(ticker, 'marketPrice') and ticker.marketPrice:
					return float(ticker.marketPrice)
				elif hasattr(ticker, 'bid') and hasattr(ticker, 'ask'):
					if ticker.bid and ticker.ask:
						return float((ticker.bid + ticker.ask) / 2)
			
			return None
		except Exception as e:
			logger.error(f"Error getting underlying price for {symbol}: {str(e)}")
			return None
	
	def format_option_data(self, ticker, underlying_price: float) -> Optional[Dict[str, Any]]:
		"""Format IB ticker data into standardized option data.
		
		Args:
			ticker: IB ticker object
			underlying_price: Current underlying price
		
		Returns:
			Formatted option data dictionary
		"""
		try:
			contract = ticker.contract
			
			# Parse expiration
			exp_str = contract.lastTradeDateOrContractMonth
			expiration = datetime.strptime(exp_str, '%Y%m%d').date()
			
			# Get option type
			option_type = 'call' if contract.right == 'C' else 'put'
			
			# Get market data
			bid = float(ticker.bid) if ticker.bid and ticker.bid > 0 else None
			ask = float(ticker.ask) if ticker.ask and ticker.ask > 0 else None
			last = float(ticker.last) if ticker.last and ticker.last > 0 else None
			
			# Calculate mid price
			mid_price = None
			if bid and ask:
				mid_price = (bid + ask) / 2
			elif last:
				mid_price = last
			
			# Get Greeks if available
			delta = float(ticker.modelGreeks.delta) if hasattr(ticker, 'modelGreeks') and ticker.modelGreeks and ticker.modelGreeks.delta else None
			gamma = float(ticker.modelGreeks.gamma) if hasattr(ticker, 'modelGreeks') and ticker.modelGreeks and ticker.modelGreeks.gamma else None
			theta = float(ticker.modelGreeks.theta) if hasattr(ticker, 'modelGreeks') and ticker.modelGreeks and ticker.modelGreeks.theta else None
			vega = float(ticker.modelGreeks.vega) if hasattr(ticker, 'modelGreeks') and ticker.modelGreeks and ticker.modelGreeks.vega else None
			rho = float(ticker.modelGreeks.rho) if hasattr(ticker, 'modelGreeks') and ticker.modelGreeks and ticker.modelGreeks.rho else None
			
			# Get implied volatility
			iv = float(ticker.modelGreeks.impliedVol) if hasattr(ticker, 'modelGreeks') and ticker.modelGreeks and ticker.modelGreeks.impliedVol else None
			
			# If Greeks not available from IB, calculate them
			if not delta and mid_price:
				greeks = self.calculate_greeks({
					'strike': float(contract.strike),
					'expiration': expiration,
					'option_type': option_type,
					'option_price': mid_price,
					'underlying_price': underlying_price,
					'risk_free_rate': 0.05,  # Approximate
					'implied_volatility': iv or 0.20  # Default if not available
				})
				delta = greeks.get('delta')
				gamma = greeks.get('gamma')
				theta = greeks.get('theta')
				vega = greeks.get('vega')
				rho = greeks.get('rho')
			
			return {
				'symbol': contract.symbol,
				'strike': float(contract.strike),
				'expiration': expiration,
				'option_type': option_type,
				'bid': bid,
				'ask': ask,
				'last': last,
				'mid_price': mid_price,
				'volume': int(ticker.volume) if ticker.volume else None,
				'open_interest': int(ticker.openInterest) if ticker.openInterest else None,
				'implied_volatility': iv,
				'delta': delta,
				'gamma': gamma,
				'theta': theta,
				'vega': vega,
				'rho': rho,
				'underlying_price': underlying_price,
				'timestamp': datetime.now(timezone.utc)
			}
		
		except Exception as e:
			logger.error(f"Error formatting option data: {str(e)}")
			return None
	
	def calculate_greeks(self, option_data: Dict[str, Any]) -> Dict[str, float]:
		"""Calculate option Greeks using Black-Scholes model.
		
		Args:
			option_data: Option parameters for calculation
		
		Returns:
			Dictionary of calculated Greeks
		"""
		try:
			S = option_data['underlying_price']  # Underlying price
			K = option_data['strike']  # Strike price
			T = (option_data['expiration'] - date.today()).days / 365.0  # Time to expiration
			r = option_data.get('risk_free_rate', 0.05)  # Risk-free rate
			sigma = option_data.get('implied_volatility', 0.20)  # Volatility
			option_type = option_data['option_type']
			
			# Avoid division by zero
			if T <= 0:
				return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
			
			# Calculate d1 and d2
			d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
			d2 = d1 - sigma * math.sqrt(T)
			
			# Calculate Greeks
			if option_type == 'call':
				delta = norm.cdf(d1)
				rho = K * T * math.exp(-r * T) * norm.cdf(d2) / 100
			else:  # put
				delta = -norm.cdf(-d1)
				rho = -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100
			
			gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
			theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) 
					- r * K * math.exp(-r * T) * norm.cdf(d2 if option_type == 'call' else -d2)) / 365
			vega = S * norm.pdf(d1) * math.sqrt(T) / 100
			
			return {
				'delta': round(delta, 4),
				'gamma': round(gamma, 6),
				'theta': round(theta, 4),
				'vega': round(vega, 4),
				'rho': round(rho, 4)
			}
		
		except Exception as e:
			logger.error(f"Error calculating Greeks: {str(e)}")
			return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
	
	def get_cached_options_data(self, 
								symbol: str,
								strike: float,
								expiration: date,
								option_type: str) -> Optional[Dict[str, Any]]:
		"""Get cached options data if not expired.
		
		Args:
			symbol: Option symbol
			strike: Strike price
			expiration: Expiration date
			option_type: 'call' or 'put'
		
		Returns:
			Cached data or None if not available/expired
		"""
		try:
			with next(get_db_session()) as db:
				cached = OptionsDataCache.get_cached_data(
					db, symbol, Decimal(str(strike)), 
					datetime.combine(expiration, datetime.min.time()),
					option_type
				)
				
				if cached and not cached.is_expired():
					return cached.to_dict()
				
				return None
		except Exception as e:
			logger.error(f"Error getting cached data: {str(e)}")
			return None
	
	def cache_options_data(self, option_data: Dict[str, Any]) -> None:
		"""Cache options data with TTL.
		
		Args:
			option_data: Option data to cache
		"""
		try:
			with next(get_db_session()) as db:
				cache_entry = OptionsDataCache(
					symbol=option_data['symbol'],
					strike=Decimal(str(option_data['strike'])),
					expiration=datetime.combine(option_data['expiration'], datetime.min.time()),
					option_type=option_data['option_type'],
					bid=Decimal(str(option_data['bid'])) if option_data.get('bid') else None,
					ask=Decimal(str(option_data['ask'])) if option_data.get('ask') else None,
					last=Decimal(str(option_data['last'])) if option_data.get('last') else None,
					volume=option_data.get('volume'),
					open_interest=option_data.get('open_interest'),
					implied_volatility=Decimal(str(option_data['implied_volatility'])) if option_data.get('implied_volatility') else None,
					delta=Decimal(str(option_data['delta'])) if option_data.get('delta') else None,
					gamma=Decimal(str(option_data['gamma'])) if option_data.get('gamma') else None,
					theta=Decimal(str(option_data['theta'])) if option_data.get('theta') else None,
					vega=Decimal(str(option_data['vega'])) if option_data.get('vega') else None,
					rho=Decimal(str(option_data['rho'])) if option_data.get('rho') else None,
					timestamp=option_data.get('timestamp', datetime.now(timezone.utc)),
					ttl_seconds=self.cache_ttl
				)
				
				db.add(cache_entry)
				db.commit()
				logger.debug(f"Cached option data for {option_data['symbol']} {option_data['strike']} {option_data['option_type']}")
		
		except Exception as e:
			logger.error(f"Error caching option data: {str(e)}")
	
	def get_historical_options_data(self, 
									symbol: str,
									start_date: date,
									end_date: date,
									strikes: Optional[List[float]] = None) -> List[Dict[str, Any]]:
		"""Get historical options data.
		
		Args:
			symbol: Option symbol
			start_date: Start date for data
			end_date: End date for data
			strikes: Optional list of strikes to filter
		
		Returns:
			List of historical data points
		"""
		try:
			with next(get_db_session()) as db:
				historical_data = HistoricalOptionsData.get_date_range(
					db, symbol,
					datetime.combine(start_date, datetime.min.time()),
					datetime.combine(end_date, datetime.max.time())
				)
				
				# Filter by strikes if provided
				if strikes and historical_data:
					strike_set = set(Decimal(str(s)) for s in strikes)
					historical_data = [h for h in historical_data if h.strike in strike_set]
				
				return [data.to_dict() for data in historical_data]
		
		except Exception as e:
			logger.error(f"Error getting historical data: {str(e)}")
			return []
	
	def check_rate_limit(self) -> float:
		"""Check if rate limit allows immediate request.
		
		Returns:
			Time to wait in seconds (0 if can proceed)
		"""
		if not self.last_request_time:
			return 0
		
		time_since_last = (datetime.now(timezone.utc) - self.last_request_time).total_seconds()
		min_interval = 1.0 / self.rate_limit
		
		if time_since_last < min_interval:
			return min_interval - time_since_last
		
		return 0
	
	def add_to_queue(self, request: Dict[str, Any]) -> None:
		"""Add request to processing queue.
		
		Args:
			request: Request details
		"""
		self.request_queue.append(request)
	
	def get_next_request(self) -> Optional[Dict[str, Any]]:
		"""Get next request from queue.
		
		Returns:
			Next request or None if queue empty
		"""
		if self.request_queue:
			return self.request_queue.pop(0)
		return None
	
	def create_option_contract(self, 
							   symbol: str,
							   strike: float,
							   expiration: date,
							   option_type: str) -> Contract:
		"""Create IB option contract.
		
		Args:
			symbol: Underlying symbol
			strike: Strike price
			expiration: Expiration date
			option_type: 'call' or 'put'
		
		Returns:
			IB Contract object
		"""
		right = 'C' if option_type == 'call' else 'P'
		exp_str = expiration.strftime('%Y%m%d')
		
		return Option(symbol, exp_str, strike, right, 'SMART')
	
	def validate_option_parameters(self, 
								   symbol: str,
								   strike: float,
								   expiration: date,
								   option_type: str) -> bool:
		"""Validate option parameters.
		
		Args:
			symbol: Option symbol
			strike: Strike price
			expiration: Expiration date
			option_type: Option type
		
		Returns:
			True if valid, False otherwise
		"""
		if not symbol or len(symbol) == 0:
			return False
		
		if strike <= 0:
			return False
		
		if expiration <= date.today():
			return False
		
		if option_type not in ['call', 'put']:
			return False
		
		return True
	
	def handle_ib_error(self, error_code: int, error_msg: str) -> bool:
		"""Handle IB API errors.
		
		Args:
			error_code: IB error code
			error_msg: Error message
		
		Returns:
			True if error was handled, False if critical
		"""
		# Known non-critical error codes
		non_critical_codes = [200, 354, 10167]  # No security definition, etc.
		
		if error_code in non_critical_codes:
			logger.warning(f"IB Warning {error_code}: {error_msg}")
			return True
		
		logger.error(f"IB Error {error_code}: {error_msg}")
		return False
	
	async def start_market_data_stream(self, 
									   symbol: str,
									   strikes: List[float],
									   expiration: date) -> None:
		"""Start streaming market data for options.
		
		Args:
			symbol: Underlying symbol
			strikes: List of strikes to stream
			expiration: Expiration date
		"""
		if self.streaming_task:
			self.streaming_task.cancel()
		
		self.streaming_task = asyncio.create_task(
			self._market_data_stream_loop(symbol, strikes, expiration)
		)
	
	async def _market_data_stream_loop(self, 
									   symbol: str,
									   strikes: List[float],
									   expiration: date) -> None:
		"""Background task for streaming market data.
		
		Args:
			symbol: Underlying symbol
			strikes: List of strikes
			expiration: Expiration date
		"""
		try:
			while True:
				if self.connection_manager.is_connected:
					# Fetch fresh options data
					options_data = self.fetch_options_chain(symbol, expiration, strikes)
					
					# Update active subscriptions
					for option in options_data:
						key = f"{option['symbol']}_{option['strike']}_{option['option_type']}"
						self.active_subscriptions[key] = option
				
				# Wait before next update
				await asyncio.sleep(self.cache_ttl)
		
		except asyncio.CancelledError:
			logger.info("Market data stream cancelled")
		except Exception as e:
			logger.error(f"Error in market data stream: {str(e)}")
	
	def stop_market_data_stream(self) -> None:
		"""Stop streaming market data."""
		if self.streaming_task:
			self.streaming_task.cancel()
			self.streaming_task = None
		
		self.active_subscriptions.clear()
	
	def cleanup_expired_cache(self) -> int:
		"""Clean up expired cache entries.
		
		Returns:
			Number of entries cleaned up
		"""
		try:
			with next(get_db_session()) as db:
				count = OptionsDataCache.cleanup_expired(db)
				db.commit()
				logger.info(f"Cleaned up {count} expired cache entries")
				return count
		except Exception as e:
			logger.error(f"Error cleaning up cache: {str(e)}")
			return 0


# Singleton instance
ib_market_data_service = IBMarketDataService()