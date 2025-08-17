"""Interactive Brokers market data service with SPX focus and Phase 1 integration.

This service implements Phase 2 of Issue #12: Market Data Integration
- Uses repaired IBConnectionManager from Phase 1
- Focuses on SPX (S&P 500 Index) options
- Implements rate limiting (45 req/sec) and connection pooling
- Provides yfinance fallback for resilience
"""
import logging
import asyncio
import time
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import math
from scipy.stats import norm
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Semaphore
import yfinance as yf

try:
	from ib_insync import Stock, Option, Contract, Index
except ImportError:
	logger.warning("ib_insync not available, fallback mode only")
	Stock = Option = Contract = Index = None

from services.ib_connection_manager import IBConnectionManager
from database.config import get_db_session
from database.models import OptionsDataCache, HistoricalOptionsData

logger = logging.getLogger(__name__)


class IBMarketDataServiceSPX:
	"""Service for fetching real-time SPX options data from Interactive Brokers."""
	
	def __init__(self):
		"""Initialize the market data service with SPX defaults."""
		# Use Phase 1 repaired connection manager
		self.connection_manager = IBConnectionManager()
		
		# SPX-specific configuration
		self.default_symbol = 'SPX'
		self.cache_ttl = 30  # 30-second cache TTL for SPX
		self.rate_limit = 45  # 45 requests per second (buffer under IB's 50/sec)
		self.strike_increment = 5  # SPX uses 5-point strike increments
		
		# Connection pooling
		self.connection_pool_size = 5
		self.connection_pool = []
		self.available_connections = []
		self.pool_lock = Lock()
		self.pool_semaphore = Semaphore(self.connection_pool_size)
		
		# Request management
		self.request_queue: List[Dict[str, Any]] = []
		self.last_request_time: Optional[datetime] = None
		self.request_counter = 0
		self.request_window_start = datetime.now(timezone.utc)
		
		# Streaming and subscriptions
		self.streaming_task: Optional[asyncio.Task] = None
		self.active_subscriptions: Dict[str, Any] = {}
		
		# Fallback configuration
		self.use_fallback = False
		self.fallback_reason = None
		
		# Initialize connection pool
		self.create_connection_pool(self.connection_pool_size)
	
	def create_connection_pool(self, size: int) -> List[Any]:
		"""Create connection pool for concurrent requests.
		
		Args:
			size: Number of connections in pool
		
		Returns:
			List of connection objects
		"""
		with self.pool_lock:
			self.connection_pool = []
			self.available_connections = []
			
			for i in range(size):
				# Each connection uses the same manager but tracks its own state
				conn = {
					'id': i,
					'manager': self.connection_manager,
					'in_use': False,
					'last_used': None
				}
				self.connection_pool.append(conn)
				self.available_connections.append(conn)
			
			logger.info(f"Created connection pool with {size} connections")
			return self.connection_pool
	
	def acquire_connection(self) -> Optional[Dict[str, Any]]:
		"""Acquire a connection from the pool.
		
		Returns:
			Connection object or None if none available
		"""
		self.pool_semaphore.acquire()
		with self.pool_lock:
			if self.available_connections:
				conn = self.available_connections.pop(0)
				conn['in_use'] = True
				conn['last_used'] = datetime.now(timezone.utc)
				return conn
			return None
	
	def release_connection(self, conn: Dict[str, Any]) -> None:
		"""Release a connection back to the pool.
		
		Args:
			conn: Connection to release
		"""
		with self.pool_lock:
			conn['in_use'] = False
			if conn not in self.available_connections:
				self.available_connections.append(conn)
		self.pool_semaphore.release()
	
	def round_to_strike_increment(self, price: float, increment: int = 5) -> int:
		"""Round price to nearest strike increment.
		
		Args:
			price: Price to round
			increment: Strike increment (5 for SPX)
		
		Returns:
			Rounded strike price
		"""
		return int(round(price / increment) * increment)
	
	def generate_strike_range(self, 
							 symbol: str,
							 current_price: float,
							 percentage_range: float = 0.025,
							 strike_increment: int = None) -> List[int]:
		"""Generate strike range for options.
		
		Args:
			symbol: Underlying symbol (SPX)
			current_price: Current underlying price
			percentage_range: Percentage up/down from current
			strike_increment: Strike increment (defaults to 5 for SPX)
		
		Returns:
			List of strike prices
		"""
		if strike_increment is None:
			strike_increment = self.strike_increment if symbol == 'SPX' else 1
		
		lower_bound = current_price * (1 - percentage_range)
		upper_bound = current_price * (1 + percentage_range)
		
		lower_strike = self.round_to_strike_increment(lower_bound, strike_increment)
		upper_strike = self.round_to_strike_increment(upper_bound, strike_increment)
		
		strikes = []
		current_strike = lower_strike
		while current_strike <= upper_strike:
			strikes.append(current_strike)
			current_strike += strike_increment
		
		return strikes
	
	def check_rate_limit(self) -> float:
		"""Check if rate limit allows immediate request.
		
		Returns:
			Time to wait in seconds (0 if can proceed)
		"""
		now = datetime.now(timezone.utc)
		
		# Reset counter if window has passed
		if (now - self.request_window_start).total_seconds() >= 1.0:
			self.request_counter = 0
			self.request_window_start = now
		
		# Check if we've hit the limit
		if self.request_counter >= self.rate_limit:
			# Calculate wait time until next window
			time_into_window = (now - self.request_window_start).total_seconds()
			wait_time = 1.0 - time_into_window
			return max(0, wait_time)
		
		# Can proceed
		self.request_counter += 1
		self.last_request_time = now
		return 0
	
	def should_use_fallback(self) -> bool:
		"""Determine if fallback to yfinance should be used.
		
		Returns:
			True if fallback should be used
		"""
		if not self.connection_manager.is_connected():
			self.use_fallback = True
			self.fallback_reason = "IB not connected"
			return True
		
		if self.connection_manager.health_monitor_active is False:
			self.use_fallback = True
			self.fallback_reason = "Health monitor inactive"
			return True
		
		return False
	
	def fetch_with_fallback(self, 
						   symbol: str,
						   expiration: date,
						   strikes: Optional[List[int]] = None) -> List[Dict[str, Any]]:
		"""Fetch options data with yfinance fallback.
		
		Args:
			symbol: Underlying symbol (SPX)
			expiration: Option expiration date
			strikes: Optional list of strikes
		
		Returns:
			Options data from yfinance
		"""
		try:
			# SPX is ^GSPC in yfinance
			yf_symbol = '^GSPC' if symbol == 'SPX' else symbol
			
			ticker = yf.Ticker(yf_symbol)
			
			# Get current price
			info = ticker.info
			current_price = info.get('regularMarketPrice', info.get('price', 0))
			
			if not current_price:
				# Try getting from history
				hist = ticker.history(period='1d')
				if not hist.empty:
					current_price = hist['Close'].iloc[-1]
			
			# Get options chain
			exp_str = expiration.strftime('%Y-%m-%d')
			try:
				opt_chain = ticker.option_chain(exp_str)
			except:
				# If exact date not available, get available dates
				expirations = ticker.options
				if not expirations:
					logger.error(f"No options available for {symbol}")
					return []
				
				# Find closest expiration
				target = expiration
				closest = min(expirations, 
							 key=lambda x: abs(datetime.strptime(x, '%Y-%m-%d').date() - target))
				opt_chain = ticker.option_chain(closest)
			
			options_data = []
			
			# Process calls
			for _, row in opt_chain.calls.iterrows():
				if strikes and row['strike'] not in strikes:
					continue
				
				options_data.append({
					'symbol': symbol,
					'strike': float(row['strike']),
					'expiration': expiration,
					'option_type': 'call',
					'bid': float(row.get('bid', 0)),
					'ask': float(row.get('ask', 0)),
					'last': float(row.get('lastPrice', 0)),
					'volume': int(row.get('volume', 0)),
					'open_interest': int(row.get('openInterest', 0)),
					'implied_volatility': float(row.get('impliedVolatility', 0.20)),
					'underlying_price': current_price,
					'timestamp': datetime.now(timezone.utc),
					'source': 'yfinance'
				})
			
			# Process puts
			for _, row in opt_chain.puts.iterrows():
				if strikes and row['strike'] not in strikes:
					continue
				
				options_data.append({
					'symbol': symbol,
					'strike': float(row['strike']),
					'expiration': expiration,
					'option_type': 'put',
					'bid': float(row.get('bid', 0)),
					'ask': float(row.get('ask', 0)),
					'last': float(row.get('lastPrice', 0)),
					'volume': int(row.get('volume', 0)),
					'open_interest': int(row.get('openInterest', 0)),
					'implied_volatility': float(row.get('impliedVolatility', 0.20)),
					'underlying_price': current_price,
					'timestamp': datetime.now(timezone.utc),
					'source': 'yfinance'
				})
			
			# Calculate Greeks for fallback data
			for option in options_data:
				greeks = self.calculate_greeks(option)
				option.update(greeks)
			
			logger.info(f"Fetched {len(options_data)} options via yfinance fallback")
			return options_data
			
		except Exception as e:
			logger.error(f"Error in yfinance fallback: {str(e)}")
			return []
	
	def fetch_options_chain(self, 
							symbol: str = None,
							expiration: date = None,
							strikes: Optional[List[int]] = None) -> List[Dict[str, Any]]:
		"""Fetch options chain data with SPX focus.
		
		Args:
			symbol: Underlying symbol (defaults to SPX)
			expiration: Option expiration date
			strikes: Optional list of specific strikes to fetch
		
		Returns:
			List of option contract data
		"""
		# Default to SPX
		if symbol is None:
			symbol = self.default_symbol
		
		# Check if we should use fallback
		if self.should_use_fallback():
			logger.info(f"Using yfinance fallback: {self.fallback_reason}")
			return self.fetch_with_fallback(symbol, expiration, strikes)
		
		# Acquire connection from pool
		conn = self.acquire_connection()
		if not conn:
			logger.warning("No available connections in pool")
			return self.fetch_with_fallback(symbol, expiration, strikes)
		
		try:
			# Check rate limiting
			wait_time = self.check_rate_limit()
			if wait_time > 0:
				time.sleep(wait_time)
			
			# Get IB client from connection
			ib_client = conn['manager'].get_connection()
			if not ib_client:
				raise Exception("Could not get IB client")
			
			# For SPX, use Index contract
			if symbol == 'SPX':
				underlying = Index('SPX', 'CBOE')
			else:
				underlying = Stock(symbol, 'SMART', 'USD')
			
			ib_client.qualifyContracts(underlying)
			
			# Get underlying price
			underlying_price = self.get_underlying_price(symbol, ib_client)
			if not underlying_price:
				logger.error(f"Could not get underlying price for {symbol}")
				raise Exception("No underlying price")
			
			options_data = []
			
			# Generate strikes if not provided
			if not strikes:
				if symbol == 'SPX':
					# Generate SPX strikes around current price (±2.5%)
					strikes = self.generate_strike_range(
						symbol, underlying_price, 0.025, self.strike_increment
					)
				else:
					# Generate strikes for other symbols
					atm_strike = round(underlying_price)
					strikes = [atm_strike + i for i in range(-10, 11)]
			
			# Format expiration for IB
			exp_str = expiration.strftime('%Y%m%d')
			
			# Fetch both calls and puts for each strike
			for strike in strikes:
				for right in ['C', 'P']:  # Call and Put
					try:
						# Check rate limit for each request
						wait_time = self.check_rate_limit()
						if wait_time > 0:
							time.sleep(wait_time)
						
						# Create option contract
						if symbol == 'SPX':
							option = Option('SPX', exp_str, strike, right, 'SMART', 'CBOE')
						else:
							option = Option(symbol, exp_str, strike, right, 'SMART')
						
						qualified = ib_client.qualifyContracts(option)
						
						if qualified:
							# Request market data
							ticker = ib_client.reqMktData(qualified[0])
							ib_client.sleep(0.1)  # Small delay for data
							
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
			# Try fallback
			return self.fetch_with_fallback(symbol, expiration, strikes)
		
		finally:
			# Release connection back to pool
			if conn:
				self.release_connection(conn)
	
	def get_underlying_price(self, symbol: str, ib_client=None) -> Optional[float]:
		"""Get current underlying price for SPX or other symbols.
		
		Args:
			symbol: Stock/index symbol
			ib_client: Optional IB client to use
		
		Returns:
			Current price or None if not available
		"""
		if not ib_client:
			if not self.connection_manager.is_connected():
				# Use yfinance fallback
				try:
					yf_symbol = '^GSPC' if symbol == 'SPX' else symbol
					ticker = yf.Ticker(yf_symbol)
					info = ticker.info
					return info.get('regularMarketPrice', info.get('price'))
				except:
					return None
			
			ib_client = self.connection_manager.get_connection()
			if not ib_client:
				return None
		
		try:
			# Create contract
			if symbol == 'SPX':
				contract = Index('SPX', 'CBOE')
			else:
				contract = Stock(symbol, 'SMART', 'USD')
			
			qualified = ib_client.qualifyContracts(contract)
			
			if qualified:
				ticker = ib_client.reqMktData(qualified[0])
				ib_client.sleep(0.1)
				
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
			
			# Get market data (scale appropriately for SPX)
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
					'risk_free_rate': 0.05,  # Current approximate rate
					'implied_volatility': iv or 0.185  # SPX typical IV
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
				'timestamp': datetime.now(timezone.utc),
				'source': 'IB'
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
			S = option_data.get('underlying_price', 0)  # Underlying price
			K = option_data.get('strike', 0)  # Strike price
			
			# Handle expiration date properly
			exp = option_data.get('expiration')
			if isinstance(exp, date):
				T = (exp - date.today()).days / 365.0
			else:
				T = 0
			
			r = option_data.get('risk_free_rate', 0.05)  # Risk-free rate
			sigma = option_data.get('implied_volatility', 0.185)  # SPX typical volatility
			option_type = option_data.get('option_type', 'call')
			
			# Avoid division by zero
			if T <= 0 or S <= 0 or K <= 0 or sigma <= 0:
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
			
			# Theta (per day)
			if option_type == 'call':
				theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) 
						- r * K * math.exp(-r * T) * norm.cdf(d2)) / 365
			else:
				theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) 
						+ r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365
			
			vega = S * norm.pdf(d1) * math.sqrt(T) / 100
			
			# Scale Greeks for SPX (larger notional value)
			if option_data.get('symbol') == 'SPX':
				# SPX has 100 multiplier, scale Greeks appropriately
				vega *= 10  # SPX vega is larger
				theta *= 10  # SPX theta is larger
			
			return {
				'delta': round(delta, 4),
				'gamma': round(gamma, 6),
				'theta': round(theta, 2),
				'vega': round(vega, 2),
				'rho': round(rho, 2)
			}
		
		except Exception as e:
			logger.error(f"Error calculating Greeks: {str(e)}")
			return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
	
	def fetch_option_quote(self, 
						  symbol: str,
						  strike: int,
						  expiration: date,
						  option_type: str) -> Optional[Dict[str, Any]]:
		"""Fetch single option quote.
		
		Args:
			symbol: Underlying symbol
			strike: Strike price
			expiration: Expiration date
			option_type: 'call' or 'put'
		
		Returns:
			Option quote data
		"""
		# Check cache first
		cached = self.get_cached_options_data(symbol, strike, expiration, option_type)
		if cached:
			return cached
		
		# Fetch fresh data
		options = self.fetch_options_chain(symbol, expiration, [strike])
		
		for option in options:
			if (option['strike'] == strike and 
				option['option_type'] == option_type):
				return option
		
		return None
	
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
					data = cached.to_dict()
					data['ttl'] = self.cache_ttl  # Add TTL info
					return data
				
				return None
		except Exception as e:
			logger.error(f"Error getting cached data: {str(e)}")
			return None
	
	def cache_options_data(self, option_data: Dict[str, Any]) -> None:
		"""Cache options data with SPX-specific TTL.
		
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
	
	def handle_ib_error(self, error_code: int, error_msg: str) -> bool:
		"""Handle IB API errors with fallback logic.
		
		Args:
			error_code: IB error code
			error_msg: Error message
		
		Returns:
			True if error was handled, False if critical
		"""
		# Connection errors - trigger fallback
		connection_errors = [502, 504, 1100, 1101, 1102]
		if error_code in connection_errors:
			logger.error(f"IB Connection Error {error_code}: {error_msg}")
			self.use_fallback = True
			self.fallback_reason = f"IB Error {error_code}"
			return True
		
		# Market data errors
		market_data_errors = [354, 10167]  # Not subscribed
		if error_code in market_data_errors:
			logger.warning(f"IB Market Data Warning {error_code}: {error_msg}")
			return True
		
		# Known non-critical errors
		non_critical_codes = [200, 2104, 2106, 2158]
		if error_code in non_critical_codes:
			logger.warning(f"IB Warning {error_code}: {error_msg}")
			return True
		
		logger.error(f"IB Error {error_code}: {error_msg}")
		return False
	
	async def start_market_data_stream(self, 
									   symbol: str = None,
									   strikes: List[int] = None,
									   expiration: date = None) -> None:
		"""Start streaming market data for SPX options.
		
		Args:
			symbol: Underlying symbol (defaults to SPX)
			strikes: List of strikes to stream
			expiration: Expiration date
		"""
		if symbol is None:
			symbol = self.default_symbol
		
		if self.streaming_task:
			self.streaming_task.cancel()
		
		self.streaming_task = asyncio.create_task(
			self._market_data_stream_loop(symbol, strikes, expiration)
		)
		logger.info(f"Started market data stream for {symbol}")
	
	async def _market_data_stream_loop(self, 
									   symbol: str,
									   strikes: List[int],
									   expiration: date) -> None:
		"""Background task for streaming market data.
		
		Args:
			symbol: Underlying symbol
			strikes: List of strikes
			expiration: Expiration date
		"""
		try:
			while True:
				try:
					# Fetch fresh options data
					options_data = self.fetch_options_chain(symbol, expiration, strikes)
					
					# Update active subscriptions
					for option in options_data:
						key = f"{option['symbol']}_{option['strike']}_{option['option_type']}"
						self.active_subscriptions[key] = option
					
					logger.debug(f"Updated {len(options_data)} option subscriptions")
				
				except Exception as e:
					logger.error(f"Error in stream update: {str(e)}")
				
				# Wait before next update (use cache TTL)
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
		logger.info("Stopped market data stream")
	
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
ib_market_data_service_spx = IBMarketDataServiceSPX()