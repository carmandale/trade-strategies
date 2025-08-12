"""Tests for IB-powered strategy calculations."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timezone
from decimal import Decimal
from services.ib_strategy_calculator import IBStrategyCalculator
from services.ib_market_data_service import ib_market_data_service
from database.models import Strategy


class TestIBStrategyCalculator:
	"""Test IBStrategyCalculator class."""
	
	@pytest.fixture
	def mock_market_data_service(self):
		"""Create a mock IB market data service."""
		with patch('services.ib_strategy_calculator.ib_market_data_service') as mock_service:
			mock_service.connection_manager.is_connected = True
			yield mock_service
	
	@pytest.fixture
	def calculator(self, mock_market_data_service):
		"""Create IBStrategyCalculator instance."""
		calculator = IBStrategyCalculator()
		calculator.market_data_service = mock_market_data_service
		return calculator
	
	@pytest.fixture
	def sample_ib_options_data(self):
		"""Sample IB options data for testing."""
		return [
			{
				'symbol': 'SPY',
				'strike': 440,
				'expiration': date(2025, 1, 17),
				'option_type': 'put',
				'bid': 2.15,
				'ask': 2.25,
				'mid_price': 2.20,
				'delta': -0.25,
				'gamma': 0.015,
				'theta': -0.45,
				'vega': 8.5,
				'underlying_price': 450.50
			},
			{
				'symbol': 'SPY',
				'strike': 445,
				'expiration': date(2025, 1, 17),
				'option_type': 'put',
				'bid': 3.45,
				'ask': 3.55,
				'mid_price': 3.50,
				'delta': -0.35,
				'gamma': 0.018,
				'theta': -0.55,
				'vega': 9.2,
				'underlying_price': 450.50
			},
			{
				'symbol': 'SPY',
				'strike': 455,
				'expiration': date(2025, 1, 17),
				'option_type': 'call',
				'bid': 3.25,
				'ask': 3.35,
				'mid_price': 3.30,
				'delta': 0.35,
				'gamma': 0.018,
				'theta': -0.52,
				'vega': 9.1,
				'underlying_price': 450.50
			},
			{
				'symbol': 'SPY',
				'strike': 460,
				'expiration': date(2025, 1, 17),
				'option_type': 'call',
				'bid': 2.05,
				'ask': 2.15,
				'mid_price': 2.10,
				'delta': 0.25,
				'gamma': 0.015,
				'theta': -0.42,
				'vega': 8.3,
				'underlying_price': 450.50
			}
		]
	
	def test_initialization(self):
		"""Test IBStrategyCalculator initialization."""
		calculator = IBStrategyCalculator()
		assert calculator.market_data_service is not None
		assert calculator.fallback_enabled is True
		assert calculator.cache_duration == 5  # seconds
	
	def test_calculate_iron_condor_with_ib_data(self, calculator, sample_ib_options_data):
		"""Test calculating Iron Condor with real IB data."""
		# Mock the market data service to return our sample data
		calculator.market_data_service.fetch_options_chain.return_value = sample_ib_options_data
		
		# Calculate Iron Condor strategy
		result = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10
		)
		
		# Verify calculation results
		assert result is not None
		assert result['strategy_type'] == 'iron_condor'
		assert result['data_source'] == 'ib_realtime'
		assert 'legs' in result
		assert len(result['legs']) == 4
		assert 'max_profit' in result
		assert 'max_loss' in result
		assert 'breakeven_points' in result
		assert 'total_credit' in result
		assert 'greeks' in result
		
		# Verify Greeks are calculated from IB data
		assert result['greeks']['delta'] is not None
		assert result['greeks']['gamma'] is not None
		assert result['greeks']['theta'] is not None
		assert result['greeks']['vega'] is not None
	
	def test_calculate_iron_condor_fallback_to_estimates(self, calculator):
		"""Test Iron Condor calculation with fallback to estimates."""
		# Mock IB service as disconnected
		calculator.market_data_service.connection_manager.is_connected = False
		
		# Calculate Iron Condor with fallback
		result = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10,
			underlying_price=450.50  # Provided for fallback
		)
		
		# Verify fallback calculation
		assert result is not None
		assert result['strategy_type'] == 'iron_condor'
		assert result['data_source'] == 'estimated'
		assert 'legs' in result
		assert len(result['legs']) == 4
		assert 'max_profit' in result
		assert 'max_loss' in result
		assert 'breakeven_points' in result
	
	def test_calculate_iron_condor_mixed_data_sources(self, calculator, sample_ib_options_data):
		"""Test Iron Condor calculation with partial IB data availability."""
		# Mock partial data - only some strikes available from IB
		partial_data = sample_ib_options_data[:2]  # Only put options
		calculator.market_data_service.fetch_options_chain.return_value = partial_data
		
		result = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10,
			underlying_price=450.50
		)
		
		# Should use mixed data sources
		assert result is not None
		assert result['data_source'] == 'mixed'  # IB + estimates
		assert 'data_source_details' in result
	
	def test_calculate_bull_call_spread_with_ib_data(self, calculator, sample_ib_options_data):
		"""Test calculating Bull Call Spread with IB data."""
		# Filter for call options only
		call_options = [opt for opt in sample_ib_options_data if opt['option_type'] == 'call']
		calculator.market_data_service.fetch_options_chain.return_value = call_options
		
		result = calculator.calculate_bull_call_spread(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			long_strike=455,
			short_strike=460,
			contracts=10
		)
		
		assert result is not None
		assert result['strategy_type'] == 'bull_call_spread'
		assert result['data_source'] == 'ib_realtime'
		assert len(result['legs']) == 2
		assert result['legs'][0]['action'] == 'buy'  # Long call
		assert result['legs'][1]['action'] == 'sell'  # Short call
	
	def test_get_option_data_by_strike(self, calculator, sample_ib_options_data):
		"""Test retrieving specific option data by strike."""
		calculator.market_data_service.fetch_options_chain.return_value = sample_ib_options_data
		
		# Get specific option data
		put_445 = calculator.get_option_data_by_strike(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			strike=445,
			option_type='put'
		)
		
		assert put_445 is not None
		assert put_445['strike'] == 445
		assert put_445['option_type'] == 'put'
		assert put_445['mid_price'] == 3.50
		assert put_445['delta'] == -0.35
	
	def test_calculate_strategy_greeks(self, calculator, sample_ib_options_data):
		"""Test calculating combined strategy Greeks."""
		# Mock strategy with multiple legs
		strategy_legs = [
			{'option_data': sample_ib_options_data[1], 'quantity': -10, 'action': 'sell'},  # Short put 445
			{'option_data': sample_ib_options_data[0], 'quantity': 10, 'action': 'buy'},   # Long put 440
			{'option_data': sample_ib_options_data[2], 'quantity': -10, 'action': 'sell'}, # Short call 455
			{'option_data': sample_ib_options_data[3], 'quantity': 10, 'action': 'buy'}    # Long call 460
		]
		
		greeks = calculator.calculate_strategy_greeks(strategy_legs)
		
		assert greeks is not None
		assert 'delta' in greeks
		assert 'gamma' in greeks
		assert 'theta' in greeks
		assert 'vega' in greeks
		assert 'rho' in greeks
		
		# Iron Condor should be approximately delta neutral
		assert abs(greeks['delta']) < 1.0  # Should be close to 0
	
	def test_calculate_profit_loss_scenarios(self, calculator, sample_ib_options_data):
		"""Test calculating P&L scenarios at different underlying prices."""
		calculator.market_data_service.fetch_options_chain.return_value = sample_ib_options_data
		
		result = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10
		)
		
		# Calculate P&L at different price levels
		scenarios = calculator.calculate_profit_loss_scenarios(result, price_range=(430, 470, 5))
		
		assert scenarios is not None
		assert len(scenarios) > 0
		assert all('price' in scenario for scenario in scenarios)
		assert all('pnl' in scenario for scenario in scenarios)
		
		# Verify max profit occurs between short strikes
		max_profit_scenario = max(scenarios, key=lambda x: x['pnl'])
		assert 445 <= max_profit_scenario['price'] <= 455
	
	def test_estimate_option_price_fallback(self, calculator):
		"""Test option price estimation fallback method."""
		estimated_price = calculator.estimate_option_price(
			underlying_price=450.50,
			strike=455,
			expiration=date(2025, 1, 17),
			option_type='call',
			implied_volatility=0.20
		)
		
		assert estimated_price > 0
		assert isinstance(estimated_price, float)
	
	def test_validate_strategy_parameters(self, calculator):
		"""Test strategy parameter validation."""
		# Valid parameters
		is_valid = calculator.validate_iron_condor_parameters(
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460
		)
		assert is_valid is True
		
		# Invalid parameters (inverted spreads)
		is_valid = calculator.validate_iron_condor_parameters(
			put_short_strike=440,  # Should be higher than long
			put_long_strike=445,
			call_short_strike=460,  # Should be lower than long  
			call_long_strike=455
		)
		assert is_valid is False
	
	def test_cache_strategy_calculation(self, calculator, sample_ib_options_data):
		"""Test caching of strategy calculations."""
		calculator.market_data_service.fetch_options_chain.return_value = sample_ib_options_data
		
		# First calculation - should hit IB
		result1 = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10
		)
		
		# Second calculation with same parameters - should use cache
		result2 = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10
		)
		
		# Results should be identical
		assert result1['total_credit'] == result2['total_credit']
		assert result1['max_profit'] == result2['max_profit']
		
		# Market data service should only be called once due to caching
		calculator.market_data_service.fetch_options_chain.assert_called_once()
	
	@patch('services.ib_strategy_calculator.get_db_session')
	def test_save_strategy_with_ib_data(self, mock_get_db, calculator, sample_ib_options_data):
		"""Test saving strategy calculation with IB data tracking."""
		# Mock database session
		mock_db = Mock()
		mock_get_db.return_value = iter([mock_db])
		
		calculator.market_data_service.fetch_options_chain.return_value = sample_ib_options_data
		
		result = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10,
			save_to_db=True
		)
		
		# Verify database operations
		mock_db.add.assert_called_once()
		mock_db.commit.assert_called_once()
		
		# Verify strategy was created with IB data source
		saved_strategy = mock_db.add.call_args[0][0]
		assert isinstance(saved_strategy, Strategy)
		assert saved_strategy.data_source == 'ib_realtime'
		assert saved_strategy.ib_snapshot is not None
	
	def test_error_handling_ib_connection_lost(self, calculator):
		"""Test error handling when IB connection is lost during calculation."""
		# Mock connection loss during calculation
		calculator.market_data_service.fetch_options_chain.side_effect = Exception("Connection lost")
		calculator.fallback_enabled = True
		
		result = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10,
			underlying_price=450.50  # Required for fallback
		)
		
		# Should fallback to estimates
		assert result is not None
		assert result['data_source'] == 'estimated'
		assert 'error_details' in result
	
	def test_real_time_updates_websocket_ready(self, calculator, sample_ib_options_data):
		"""Test that calculations are structured for WebSocket updates."""
		calculator.market_data_service.fetch_options_chain.return_value = sample_ib_options_data
		
		result = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10,
			include_live_updates=True
		)
		
		# Verify result includes fields needed for real-time updates
		assert 'subscription_id' in result
		assert 'update_frequency' in result
		assert 'last_updated' in result
		assert result['update_frequency'] <= 5  # Should update every 5 seconds or less
	
	def test_compare_ib_vs_estimates(self, calculator, sample_ib_options_data):
		"""Test comparison between IB data and estimated calculations."""
		calculator.market_data_service.fetch_options_chain.return_value = sample_ib_options_data
		
		# Calculate with IB data
		ib_result = calculator.calculate_iron_condor(
			symbol='SPY',
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10
		)
		
		# Calculate with estimates
		estimated_result = calculator.calculate_iron_condor_estimated(
			symbol='SPY',
			underlying_price=450.50,
			expiration=date(2025, 1, 17),
			put_short_strike=445,
			put_long_strike=440,
			call_short_strike=455,
			call_long_strike=460,
			contracts=10,
			implied_volatility=0.20
		)
		
		# Compare results
		comparison = calculator.compare_data_sources(ib_result, estimated_result)
		
		assert 'ib_result' in comparison
		assert 'estimated_result' in comparison
		assert 'differences' in comparison
		assert 'accuracy_metrics' in comparison