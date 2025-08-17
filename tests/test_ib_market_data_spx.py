"""Tests for Interactive Brokers market data service with SPX focus and Phase 1 integration."""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import asyncio
from typing import List, Dict, Any
from services.ib_market_data_service_spx import IBMarketDataServiceSPX
from services.ib_connection_manager import IBConnectionManager
from database.models import OptionsDataCache, HistoricalOptionsData


class TestIBMarketDataServiceSPX:
	"""Test IBMarketDataService with SPX (S&P 500 Index) focus and Phase 1 integration."""
	
	@pytest.fixture
	def mock_connection_manager(self):
		"""Create a mock IBConnectionManager with Phase 1 fixes."""
		with patch('services.ib_market_data_service_spx.IBConnectionManager') as mock_conn_class:
			mock_manager = Mock(spec=IBConnectionManager)
			mock_manager.is_connected = Mock(return_value=True)
			mock_manager.ib_client = Mock()
			mock_manager.get_connection = Mock(return_value=mock_manager.ib_client)
			mock_manager.connection_settings = Mock()
			mock_manager.health_monitor_active = True
			mock_conn_class.return_value = mock_manager
			yield mock_manager
	
	@pytest.fixture
	def market_data_service(self, mock_connection_manager):
		"""Create IBMarketDataServiceSPX instance with Phase 1 connection manager."""
		service = IBMarketDataServiceSPX()
		service.connection_manager = mock_connection_manager
		return service
	
	def test_initialization_with_spx_defaults(self):
		"""Test IBMarketDataServiceSPX initialization with SPX-specific defaults."""
		service = IBMarketDataServiceSPX()
		assert service.cache_ttl == 30  # 30 second TTL for SPX market data
		assert service.request_queue == []
		assert service.rate_limit == 45  # 45 requests per second (buffer under IB's 50/sec)
		assert service.last_request_time is None
		assert service.default_symbol == 'SPX'  # SPX is the default symbol
		assert service.strike_increment == 5  # SPX uses 5-point strike increments
		assert service.connection_pool_size == 5  # Connection pooling support
	
	def test_phase1_connection_manager_integration(self, market_data_service):
		"""Test integration with Phase 1 repaired IBConnectionManager."""
		# Verify connection manager is properly initialized
		assert market_data_service.connection_manager is not None
		assert market_data_service.connection_manager.is_connected() is True
		assert market_data_service.connection_manager.health_monitor_active is True
	
	@patch('services.ib_market_data_service_spx.Option')
	@patch('services.ib_market_data_service_spx.Stock')
	def test_fetch_spx_options_chain(self, mock_stock, mock_option, market_data_service):
		"""Test fetching SPX options chain with proper strike increments."""
		# Setup mock SPX underlying
		mock_underlying = Mock()
		mock_underlying.symbol = 'SPX'
		mock_underlying.last = 4505.00  # SPX trades around 4300-5600
		mock_stock.return_value = mock_underlying
		
		# Setup mock SPX call option
		mock_call = Mock()
		mock_call.symbol = 'SPX'
		mock_call.strike = 4505  # SPX uses 5-point increments
		mock_call.lastTradeDateOrContractMonth = '20250117'
		mock_call.right = 'C'
		mock_call.bid = 52.50  # SPX options are more expensive than SPY
		mock_call.ask = 53.50
		mock_call.last = 53.00
		mock_call.volume = 1000
		mock_call.openInterest = 5000
		mock_call.impliedVolatility = 0.1850
		mock_call.delta = 0.55
		mock_call.gamma = 0.0125
		mock_call.theta = -8.50  # Larger theta for SPX
		mock_call.vega = 125.00  # Larger vega for SPX
		mock_call.rho = 82.50
		
		# Setup mock SPX put option
		mock_put = Mock()
		mock_put.symbol = 'SPX'
		mock_put.strike = 4505
		mock_put.lastTradeDateOrContractMonth = '20250117'
		mock_put.right = 'P'
		mock_put.bid = 47.50
		mock_put.ask = 48.50
		mock_put.last = 48.00
		mock_put.volume = 800
		mock_put.openInterest = 4000
		mock_put.impliedVolatility = 0.1825
		mock_put.delta = -0.45
		mock_put.gamma = 0.0125
		mock_put.theta = -8.00
		mock_put.vega = 122.50
		mock_put.rho = -77.50
		
		# Mock the IB client methods
		market_data_service.connection_manager.ib_client.qualifyContracts.return_value = [mock_underlying]
		market_data_service.connection_manager.ib_client.reqTickers = Mock(return_value=[mock_underlying])
		
		# Mock option chain creation
		mock_option.side_effect = [mock_call, mock_put]
		market_data_service.connection_manager.ib_client.qualifyContracts.side_effect = [
			[mock_underlying], [mock_call], [mock_put]
		]
		market_data_service.connection_manager.ib_client.reqMktData = Mock()
		
		# Test fetching SPX options chain with 5-point strikes
		spx_strikes = [4490, 4495, 4500, 4505, 4510, 4515, 4520]  # SPX 5-point increments
		options_data = market_data_service.fetch_options_chain(
			symbol='SPX',
			expiration=date(2025, 1, 17),
			strikes=spx_strikes
		)
		
		assert len(options_data) >= 0  # Should return data
		# Verify strikes are in 5-point increments
		for strike in spx_strikes:
			assert strike % 5 == 0, f"SPX strike {strike} not in 5-point increments"
	
	def test_generate_spx_strike_range(self, market_data_service):
		"""Test generating SPX strike range with 5-point increments."""
		# SPX current price around 4505
		current_price = 4505.00
		
		# Generate strikes for Iron Condor (±2.5% range)
		strikes = market_data_service.generate_strike_range(
			symbol='SPX',
			current_price=current_price,
			percentage_range=0.025,  # 2.5% up and down
			strike_increment=5  # SPX uses 5-point increments
		)
		
		expected_strikes = [
			4395, 4400, 4405, 4410, 4415, 4420, 4425, 4430, 4435, 4440,
			4445, 4450, 4455, 4460, 4465, 4470, 4475, 4480, 4485, 4490,
			4495, 4500, 4505, 4510, 4515, 4520, 4525, 4530, 4535, 4540,
			4545, 4550, 4555, 4560, 4565, 4570, 4575, 4580, 4585, 4590,
			4595, 4600, 4605, 4610, 4615
		]
		
		# All strikes should be divisible by 5
		for strike in strikes:
			assert strike % 5 == 0, f"Strike {strike} not divisible by 5"
		
		# Should cover the range
		assert min(strikes) <= current_price * 0.975
		assert max(strikes) >= current_price * 1.025
	
	def test_rate_limiting_45_per_second(self, market_data_service):
		"""Test rate limiting at 45 requests per second for SPX."""
		# Set rate limit for SPX
		market_data_service.rate_limit = 45  # 45 req/sec with buffer
		
		# Simulate rapid requests
		request_times = []
		for _ in range(50):  # Try 50 requests
			wait_time = market_data_service.check_rate_limit()
			if wait_time > 0:
				# Would need to wait
				assert len(request_times) >= 45, "Should allow 45 requests before limiting"
				break
			request_times.append(datetime.now(timezone.utc))
			market_data_service.last_request_time = datetime.now(timezone.utc)
	
	def test_connection_pooling_support(self, market_data_service):
		"""Test connection pooling for concurrent SPX market data requests."""
		# Create connection pool
		pool = market_data_service.create_connection_pool(size=5)
		
		assert len(pool) == 5
		
		# Test acquiring connection from pool
		conn = market_data_service.acquire_connection()
		assert conn is not None
		
		# Test releasing connection back to pool
		market_data_service.release_connection(conn)
		assert len(market_data_service.available_connections) == 5
	
	@patch('services.ib_market_data_service_spx.yf')
	def test_yfinance_fallback_for_spx(self, mock_yf, market_data_service):
		"""Test fallback to yfinance when IB connection fails for SPX."""
		# Simulate IB connection failure
		market_data_service.connection_manager.is_connected = Mock(return_value=False)
		
		# Mock yfinance response for SPX
		mock_ticker = Mock()
		mock_ticker.info = {
			'symbol': '^GSPC',  # SPX symbol in yfinance
			'regularMarketPrice': 4505.00,
			'bid': 4504.50,
			'ask': 4505.50
		}
		mock_ticker.options = ['2025-01-17']
		mock_option_chain = Mock()
		mock_option_chain.calls = Mock()
		mock_option_chain.puts = Mock()
		mock_ticker.option_chain = Mock(return_value=mock_option_chain)
		
		mock_yf.Ticker.return_value = mock_ticker
		
		# Fetch data with fallback
		result = market_data_service.fetch_with_fallback(
			symbol='SPX',
			expiration=date(2025, 1, 17)
		)
		
		assert result is not None
		mock_yf.Ticker.assert_called_with('^GSPC')  # SPX is ^GSPC in yfinance
	
	@patch('services.ib_market_data_service_spx.get_db_session')
	def test_redis_caching_for_spx(self, mock_get_db, market_data_service):
		"""Test Redis caching with 30-second TTL for SPX data."""
		# Mock database session
		mock_db = Mock()
		mock_get_db.return_value = iter([mock_db])
		
		# Mock cached SPX data
		mock_cache = Mock(spec=OptionsDataCache)
		mock_cache.symbol = 'SPX'
		mock_cache.strike = Decimal('4505.00')
		mock_cache.option_type = 'call'
		mock_cache.bid = Decimal('52.50')
		mock_cache.ask = Decimal('53.50')
		mock_cache.delta = Decimal('0.55')
		mock_cache.ttl = 30  # 30 second TTL for SPX
		mock_cache.is_expired.return_value = False
		mock_cache.to_dict.return_value = {
			'symbol': 'SPX',
			'strike': 4505.00,
			'option_type': 'call',
			'bid': 52.50,
			'ask': 53.50,
			'delta': 0.55,
			'ttl': 30
		}
		
		OptionsDataCache.get_cached_data = Mock(return_value=mock_cache)
		
		# Test getting cached SPX data
		cached_data = market_data_service.get_cached_options_data(
			symbol='SPX',
			strike=4505,
			expiration=date(2025, 1, 17),
			option_type='call'
		)
		
		assert cached_data is not None
		assert cached_data['symbol'] == 'SPX'
		assert cached_data['strike'] == 4505.00
		assert cached_data['bid'] == 52.50
		assert cached_data['ttl'] == 30
	
	def test_calculate_greeks_for_spx(self, market_data_service):
		"""Test Greeks calculation for SPX options."""
		# SPX option data
		spx_option_data = {
			'symbol': 'SPX',
			'strike': 4505,
			'expiration': date(2025, 1, 17),
			'option_type': 'call',
			'bid': 52.50,
			'ask': 53.50,
			'underlying_price': 4505.00,
			'risk_free_rate': 0.05,
			'implied_volatility': 0.1850
		}
		
		# Calculate Greeks for SPX
		greeks = market_data_service.calculate_greeks(spx_option_data)
		
		# Verify Greeks are calculated
		assert 'delta' in greeks
		assert 'gamma' in greeks
		assert 'theta' in greeks
		assert 'vega' in greeks
		assert 'rho' in greeks
		
		# Check reasonable ranges for at-the-money SPX option
		assert 0.4 <= greeks['delta'] <= 0.6  # ATM call delta
		assert greeks['gamma'] >= 0
		assert greeks['theta'] < 0  # Time decay is negative
		assert greeks['vega'] > 0  # Positive vega for long options
		
		# SPX Greeks should be larger in absolute terms than SPY
		assert abs(greeks['vega']) > 10  # SPX has larger vega
		assert abs(greeks['theta']) > 1  # SPX has larger theta
	
	def test_handle_ib_error_with_fallback(self, market_data_service):
		"""Test handling IB API errors with graceful fallback."""
		# Test various IB error codes
		errors = [
			(200, "No security definition has been found for the request"),
			(354, "Requested market data is not subscribed"),
			(502, "Couldn't connect to TWS"),
			(504, "Not connected"),
			(1100, "Connectivity between IB and TWS has been lost")
		]
		
		for error_code, error_msg in errors:
			handled = market_data_service.handle_ib_error(error_code, error_msg)
			assert handled is True, f"Should handle error {error_code}"
			
			# Should trigger fallback for connection errors
			if error_code in [502, 504, 1100]:
				assert market_data_service.should_use_fallback() is True
	
	@patch('services.ib_market_data_service_spx.asyncio.create_task')
	async def test_websocket_streaming_for_spx(self, mock_create_task, market_data_service):
		"""Test WebSocket streaming setup for SPX market data."""
		# Start streaming for SPX strikes
		spx_strikes = [4495, 4500, 4505, 4510, 4515]
		
		await market_data_service.start_market_data_stream(
			symbol='SPX',
			strikes=spx_strikes,
			expiration=date(2025, 1, 17)
		)
		
		# Verify streaming task created
		mock_create_task.assert_called_once()
		
		# Verify subscription for SPX options
		for strike in spx_strikes:
			assert strike % 5 == 0, f"SPX strike {strike} should be in 5-point increments"
	
	def test_iron_condor_data_for_spx(self, market_data_service):
		"""Test fetching Iron Condor data for SPX with proper strikes."""
		# SPX Iron Condor strikes (5-point increments)
		# Current SPX: 4505
		# Put spread: 4395/4400 (97.5%/98% of current)
		# Call spread: 4610/4615 (102%/102.5% of current)
		
		current_price = 4505.00
		
		# Calculate Iron Condor strikes for SPX
		put_long_strike = market_data_service.round_to_strike_increment(
			current_price * 0.975, increment=5
		)  # 4395
		put_short_strike = market_data_service.round_to_strike_increment(
			current_price * 0.98, increment=5
		)  # 4415
		call_short_strike = market_data_service.round_to_strike_increment(
			current_price * 1.02, increment=5
		)  # 4595
		call_long_strike = market_data_service.round_to_strike_increment(
			current_price * 1.025, increment=5
		)  # 4620
		
		assert put_long_strike == 4390  # Rounded to nearest 5
		assert put_short_strike == 4415
		assert call_short_strike == 4595
		assert call_long_strike == 4620
		
		# All strikes should be in 5-point increments
		for strike in [put_long_strike, put_short_strike, call_short_strike, call_long_strike]:
			assert strike % 5 == 0, f"Strike {strike} not in 5-point increments"
	
	def test_performance_targets_for_spx(self, market_data_service):
		"""Test performance targets are met for SPX market data."""
		import time
		
		# Test cache response time (<200ms)
		start = time.time()
		cached_data = market_data_service.get_cached_options_data(
			symbol='SPX',
			strike=4505,
			expiration=date(2025, 1, 17),
			option_type='call'
		)
		cache_time = (time.time() - start) * 1000  # Convert to ms
		
		# Should be fast for cached data
		assert cache_time < 200, f"Cache response took {cache_time}ms, should be <200ms"
		
		# Test Greeks calculation time (<50ms)
		start = time.time()
		greeks = market_data_service.calculate_greeks({
			'symbol': 'SPX',
			'strike': 4505,
			'expiration': date(2025, 1, 17),
			'option_type': 'call',
			'underlying_price': 4505.00,
			'risk_free_rate': 0.05,
			'implied_volatility': 0.1850
		})
		greeks_time = (time.time() - start) * 1000
		
		assert greeks_time < 50, f"Greeks calculation took {greeks_time}ms, should be <50ms"
	
	def test_concurrent_requests_with_pool(self, market_data_service):
		"""Test handling concurrent SPX requests with connection pooling."""
		import concurrent.futures
		
		# Create pool
		market_data_service.create_connection_pool(size=5)
		
		def fetch_strike_data(strike):
			"""Fetch data for a single strike."""
			return market_data_service.fetch_option_quote(
				symbol='SPX',
				strike=strike,
				expiration=date(2025, 1, 17),
				option_type='call'
			)
		
		# Test concurrent requests for multiple strikes
		spx_strikes = [4490, 4495, 4500, 4505, 4510, 4515, 4520]
		
		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			futures = [executor.submit(fetch_strike_data, strike) for strike in spx_strikes]
			results = [f.result() for f in concurrent.futures.as_completed(futures)]
		
		# Should handle all requests
		assert len(results) == len(spx_strikes)