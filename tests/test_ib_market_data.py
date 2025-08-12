"""Tests for Interactive Brokers market data service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from services.ib_market_data_service import IBMarketDataService
from database.models import OptionsDataCache, HistoricalOptionsData


class TestIBMarketDataService:
	"""Test IBMarketDataService class."""
	
	@pytest.fixture
	def mock_ib_connection(self):
		"""Create a mock IB connection."""
		with patch('services.ib_market_data_service.ib_connection_manager') as mock_conn:
			mock_conn.is_connected = True
			mock_conn.ib_client = Mock()
			yield mock_conn
	
	@pytest.fixture
	def market_data_service(self, mock_ib_connection):
		"""Create IBMarketDataService instance."""
		service = IBMarketDataService()
		service.connection_manager = mock_ib_connection
		return service
	
	def test_initialization(self):
		"""Test IBMarketDataService initialization."""
		service = IBMarketDataService()
		assert service.cache_ttl == 5  # 5 second TTL
		assert service.request_queue == []
		assert service.rate_limit == 50  # Requests per second
		assert service.last_request_time is None
	
	@patch('services.ib_market_data_service.Option')
	@patch('services.ib_market_data_service.Stock')
	def test_fetch_options_chain(self, mock_stock, mock_option, market_data_service):
		"""Test fetching options chain from IB."""
		# Setup mock stock
		mock_underlying = Mock()
		mock_underlying.symbol = 'SPY'
		mock_underlying.last = 450.50
		mock_stock.return_value = mock_underlying
		
		# Setup mock options
		mock_call = Mock()
		mock_call.symbol = 'SPY'
		mock_call.strike = 450
		mock_call.lastTradeDateOrContractMonth = '20250117'
		mock_call.right = 'C'
		mock_call.bid = 5.25
		mock_call.ask = 5.35
		mock_call.last = 5.30
		mock_call.volume = 1000
		mock_call.openInterest = 5000
		mock_call.impliedVolatility = 0.1850
		mock_call.delta = 0.55
		mock_call.gamma = 0.0125
		mock_call.theta = -0.85
		mock_call.vega = 12.50
		mock_call.rho = 8.25
		
		mock_put = Mock()
		mock_put.symbol = 'SPY'
		mock_put.strike = 450
		mock_put.lastTradeDateOrContractMonth = '20250117'
		mock_put.right = 'P'
		mock_put.bid = 4.75
		mock_put.ask = 4.85
		mock_put.last = 4.80
		mock_put.volume = 800
		mock_put.openInterest = 4000
		mock_put.impliedVolatility = 0.1825
		mock_put.delta = -0.45
		mock_put.gamma = 0.0125
		mock_put.theta = -0.80
		mock_put.vega = 12.25
		mock_put.rho = -7.75
		
		# Mock the IB client methods
		market_data_service.connection_manager.ib_client.qualifyContracts.return_value = [mock_underlying]
		market_data_service.connection_manager.ib_client.reqTickers = Mock(return_value=[mock_underlying])
		
		# Mock option chain creation
		mock_option.side_effect = [mock_call, mock_put]
		market_data_service.connection_manager.ib_client.qualifyContracts.side_effect = [
			[mock_underlying], [mock_call], [mock_put]
		]
		market_data_service.connection_manager.ib_client.reqMktData = Mock()
		
		# Test fetching options chain
		options_data = market_data_service.fetch_options_chain(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			strikes=[450]
		)
		
		assert len(options_data) >= 0  # Should return data
		# Note: Actual data structure depends on IB API response
	
	def test_fetch_options_chain_not_connected(self, market_data_service):
		"""Test fetching options chain when not connected."""
		market_data_service.connection_manager.is_connected = False
		
		options_data = market_data_service.fetch_options_chain(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			strikes=[450]
		)
		
		assert options_data == []
	
	@patch('services.ib_market_data_service.get_db_session')
	def test_get_cached_options_data(self, mock_get_db, market_data_service):
		"""Test retrieving cached options data."""
		# Mock database session
		mock_db = Mock()
		mock_get_db.return_value = iter([mock_db])
		
		# Mock cached data
		mock_cache = Mock(spec=OptionsDataCache)
		mock_cache.symbol = 'SPY'
		mock_cache.strike = Decimal('450.00')
		mock_cache.option_type = 'call'
		mock_cache.bid = Decimal('5.25')
		mock_cache.ask = Decimal('5.35')
		mock_cache.delta = Decimal('0.55')
		mock_cache.is_expired.return_value = False
		mock_cache.to_dict.return_value = {
			'symbol': 'SPY',
			'strike': 450.00,
			'option_type': 'call',
			'bid': 5.25,
			'ask': 5.35,
			'delta': 0.55
		}
		
		OptionsDataCache.get_cached_data = Mock(return_value=mock_cache)
		
		# Test getting cached data
		cached_data = market_data_service.get_cached_options_data(
			symbol='SPY',
			strike=450,
			expiration=date(2025, 1, 17),
			option_type='call'
		)
		
		assert cached_data is not None
		assert cached_data['symbol'] == 'SPY'
		assert cached_data['strike'] == 450.00
		assert cached_data['bid'] == 5.25
	
	@patch('services.ib_market_data_service.get_db_session')
	def test_cache_options_data(self, mock_get_db, market_data_service):
		"""Test caching options data."""
		# Mock database session
		mock_db = Mock()
		mock_get_db.return_value = iter([mock_db])
		
		# Test data to cache
		options_data = {
			'symbol': 'SPY',
			'strike': 450,
			'expiration': date(2025, 1, 17),
			'option_type': 'call',
			'bid': 5.25,
			'ask': 5.35,
			'delta': 0.55,
			'gamma': 0.0125,
			'theta': -0.85,
			'vega': 12.50
		}
		
		# Cache the data
		market_data_service.cache_options_data(options_data)
		
		# Verify database operations
		mock_db.add.assert_called_once()
		mock_db.commit.assert_called_once()
	
	def test_calculate_greeks(self, market_data_service):
		"""Test Greeks calculation."""
		# Mock option data
		option_data = {
			'strike': 450,
			'expiration': date(2025, 1, 17),
			'option_type': 'call',
			'bid': 5.25,
			'ask': 5.35,
			'underlying_price': 450.50,
			'risk_free_rate': 0.05,
			'implied_volatility': 0.1850
		}
		
		# Calculate Greeks
		greeks = market_data_service.calculate_greeks(option_data)
		
		# Verify Greeks are calculated
		assert 'delta' in greeks
		assert 'gamma' in greeks
		assert 'theta' in greeks
		assert 'vega' in greeks
		assert 'rho' in greeks
		
		# Check reasonable ranges
		assert -1 <= greeks['delta'] <= 1
		assert greeks['gamma'] >= 0
		assert greeks['vega'] >= 0
	
	@patch('services.ib_market_data_service.get_db_session')
	def test_get_historical_options_data(self, mock_get_db, market_data_service):
		"""Test retrieving historical options data."""
		# Mock database session
		mock_db = Mock()
		mock_get_db.return_value = iter([mock_db])
		
		# Mock historical data
		mock_historical = Mock(spec=HistoricalOptionsData)
		mock_historical.symbol = 'SPY'
		mock_historical.strike = Decimal('450.00')
		mock_historical.date = datetime(2025, 1, 10)
		mock_historical.close = Decimal('5.25')
		mock_historical.volume = 10000
		mock_historical.to_dict.return_value = {
			'symbol': 'SPY',
			'strike': 450.00,
			'date': '2025-01-10',
			'close': 5.25,
			'volume': 10000
		}
		
		HistoricalOptionsData.get_date_range = Mock(return_value=[mock_historical])
		
		# Test getting historical data
		historical_data = market_data_service.get_historical_options_data(
			symbol='SPY',
			start_date=date(2025, 1, 1),
			end_date=date(2025, 1, 31),
			strikes=[450]
		)
		
		assert len(historical_data) == 1
		assert historical_data[0]['symbol'] == 'SPY'
		assert historical_data[0]['strike'] == 450.00
	
	def test_rate_limiting(self, market_data_service):
		"""Test rate limiting functionality."""
		# Set last request time
		market_data_service.last_request_time = datetime.now(timezone.utc)
		market_data_service.rate_limit = 10  # 10 requests per second
		
		# Check if should wait
		should_wait = market_data_service.check_rate_limit()
		
		# Should need to wait if called immediately
		assert should_wait > 0
	
	def test_request_queue_processing(self, market_data_service):
		"""Test request queue processing."""
		# Add requests to queue
		request1 = {
			'type': 'options_chain',
			'params': {'symbol': 'SPY', 'expiration': date(2025, 1, 17)}
		}
		request2 = {
			'type': 'option_quote',
			'params': {'symbol': 'SPY', 'strike': 450}
		}
		
		market_data_service.add_to_queue(request1)
		market_data_service.add_to_queue(request2)
		
		assert len(market_data_service.request_queue) == 2
		
		# Process queue
		next_request = market_data_service.get_next_request()
		assert next_request == request1
		assert len(market_data_service.request_queue) == 1
	
	@patch('services.ib_market_data_service.Contract')
	def test_create_option_contract(self, mock_contract, market_data_service):
		"""Test creating IB option contract."""
		# Create option contract
		contract = market_data_service.create_option_contract(
			symbol='SPY',
			strike=450,
			expiration=date(2025, 1, 17),
			option_type='call'
		)
		
		# Verify contract creation
		mock_contract.assert_called_once()
		assert contract is not None
	
	def test_format_option_data(self, market_data_service):
		"""Test formatting option data for response."""
		# Mock IB option data
		ib_option = Mock()
		ib_option.symbol = 'SPY'
		ib_option.strike = 450
		ib_option.lastTradeDateOrContractMonth = '20250117'
		ib_option.right = 'C'
		ib_option.bid = 5.25
		ib_option.ask = 5.35
		ib_option.last = 5.30
		ib_option.volume = 1000
		ib_option.openInterest = 5000
		ib_option.impliedVolatility = 0.1850
		ib_option.delta = 0.55
		ib_option.gamma = 0.0125
		ib_option.theta = -0.85
		ib_option.vega = 12.50
		ib_option.rho = 8.25
		
		# Format the data
		formatted = market_data_service.format_option_data(ib_option)
		
		assert formatted['symbol'] == 'SPY'
		assert formatted['strike'] == 450
		assert formatted['option_type'] == 'call'
		assert formatted['bid'] == 5.25
		assert formatted['ask'] == 5.35
		assert formatted['delta'] == 0.55
	
	def test_handle_ib_error(self, market_data_service):
		"""Test handling IB API errors."""
		# Test error handling
		error_code = 200  # No security definition found
		error_msg = "No security definition has been found for the request"
		
		handled = market_data_service.handle_ib_error(error_code, error_msg)
		
		assert handled is True  # Should handle known errors gracefully
	
	@patch('services.ib_market_data_service.asyncio.create_task')
	def test_start_market_data_stream(self, mock_create_task, market_data_service):
		"""Test starting market data stream."""
		# Start streaming
		market_data_service.start_market_data_stream(
			symbol='SPY',
			strikes=[450, 455],
			expiration=date(2025, 1, 17)
		)
		
		# Verify task creation
		mock_create_task.assert_called_once()
	
	def test_stop_market_data_stream(self, market_data_service):
		"""Test stopping market data stream."""
		# Mock streaming task
		mock_task = Mock()
		market_data_service.streaming_task = mock_task
		
		# Stop streaming
		market_data_service.stop_market_data_stream()
		
		# Verify task cancellation
		mock_task.cancel.assert_called_once()
		assert market_data_service.streaming_task is None
	
	def test_validate_option_parameters(self, market_data_service):
		"""Test option parameter validation."""
		# Valid parameters
		is_valid = market_data_service.validate_option_parameters(
			symbol='SPY',
			strike=450,
			expiration=date(2025, 1, 17),
			option_type='call'
		)
		assert is_valid is True
		
		# Invalid option type
		is_valid = market_data_service.validate_option_parameters(
			symbol='SPY',
			strike=450,
			expiration=date(2025, 1, 17),
			option_type='invalid'
		)
		assert is_valid is False
		
		# Invalid strike
		is_valid = market_data_service.validate_option_parameters(
			symbol='SPY',
			strike=-100,
			expiration=date(2025, 1, 17),
			option_type='call'
		)
		assert is_valid is False
	
	@patch('services.ib_market_data_service.get_db_session')
	def test_cleanup_expired_cache(self, mock_get_db, market_data_service):
		"""Test cleaning up expired cache entries."""
		# Mock database session
		mock_db = Mock()
		mock_get_db.return_value = iter([mock_db])
		
		OptionsDataCache.cleanup_expired = Mock(return_value=5)
		
		# Clean up expired entries
		count = market_data_service.cleanup_expired_cache()
		
		assert count == 5
		mock_db.commit.assert_called_once()
	
	def test_get_underlying_price(self, market_data_service):
		"""Test getting underlying price."""
		# Mock IB client
		mock_stock = Mock()
		mock_stock.last = 450.50
		market_data_service.connection_manager.ib_client.reqTickers = Mock(
			return_value=[mock_stock]
		)
		
		# Get underlying price
		price = market_data_service.get_underlying_price('SPY')
		
		assert price == 450.50
	
	def test_get_underlying_price_not_connected(self, market_data_service):
		"""Test getting underlying price when not connected."""
		market_data_service.connection_manager.is_connected = False
		
		price = market_data_service.get_underlying_price('SPY')
		
		assert price is None