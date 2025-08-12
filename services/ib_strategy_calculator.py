"""Interactive Brokers-powered strategy calculator with fallback to estimates."""
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import math
from scipy.stats import norm
from services.ib_market_data_service import ib_market_data_service
from database.config import get_db_session
from database.models import Strategy

logger = logging.getLogger(__name__)


class IBStrategyCalculator:
	"""Calculator for options strategies using IB real-time data with fallback to estimates."""
	
	def __init__(self):
		"""Initialize the strategy calculator."""
		self.market_data_service = ib_market_data_service
		self.fallback_enabled = True
		self.cache_duration = 5  # seconds
		self._calculation_cache = {}
		self._cache_timestamps = {}
	
	def calculate_iron_condor(self,
							  symbol: str,
							  expiration: date,
							  put_short_strike: float,
							  put_long_strike: float,
							  call_short_strike: float,
							  call_long_strike: float,
							  contracts: int = 1,
							  underlying_price: Optional[float] = None,
							  save_to_db: bool = False,
							  include_live_updates: bool = False) -> Dict[str, Any]:
		"""Calculate Iron Condor strategy using IB data with fallback.
		
		Args:
			symbol: Underlying symbol
			expiration: Option expiration date
			put_short_strike: Short put strike price
			put_long_strike: Long put strike price  
			call_short_strike: Short call strike price
			call_long_strike: Long call strike price
			contracts: Number of contracts
			underlying_price: Current underlying price (for fallback)
			save_to_db: Whether to save strategy to database
			include_live_updates: Whether to include live update info
		
		Returns:
			Dictionary with strategy calculation results
		"""
		try:
			# Validate parameters
			if not self.validate_iron_condor_parameters(
				put_short_strike, put_long_strike,
				call_short_strike, call_long_strike
			):
				raise ValueError("Invalid Iron Condor strike parameters")
			
			# Check cache first
			cache_key = f"iron_condor_{symbol}_{expiration}_{put_short_strike}_{put_long_strike}_{call_short_strike}_{call_long_strike}_{contracts}"
			cached_result = self._get_cached_calculation(cache_key)
			if cached_result:
				return cached_result
			
			# Try to get IB data first
			ib_data = None
			data_source = 'estimated'
			error_details = None
			
			if self.market_data_service.connection_manager.is_connected:
				try:
					strikes = [put_long_strike, put_short_strike, call_short_strike, call_long_strike]
					ib_data = self.market_data_service.fetch_options_chain(
						symbol=symbol,
						expiration=expiration,
						strikes=strikes
					)
					
					if ib_data and len(ib_data) >= 4:
						data_source = 'ib_realtime'
					elif ib_data and len(ib_data) > 0:
						data_source = 'mixed'  # Partial IB data
				
				except Exception as e:
					logger.warning(f"IB data fetch failed, using fallback: {str(e)}")
					error_details = str(e)
			
			# Get underlying price from IB or use provided
			if not underlying_price:
				underlying_price = self.market_data_service.get_underlying_price(symbol)
				if not underlying_price:
					raise ValueError("No underlying price available")
			
			# Build strategy legs
			legs = []
			total_credit = 0.0
			data_source_details = {}
			
			# Define the Iron Condor legs
			leg_definitions = [
				{'strike': put_long_strike, 'type': 'put', 'action': 'buy', 'quantity': contracts},
				{'strike': put_short_strike, 'type': 'put', 'action': 'sell', 'quantity': contracts},
				{'strike': call_short_strike, 'type': 'call', 'action': 'sell', 'quantity': contracts},
				{'strike': call_long_strike, 'type': 'call', 'action': 'buy', 'quantity': contracts}
			]
			
			for leg_def in leg_definitions:
				option_data = self.get_option_data_by_strike(
					symbol=symbol,
					expiration=expiration,
					strike=leg_def['strike'],
					option_type=leg_def['type'],
					ib_data=ib_data,
					underlying_price=underlying_price
				)
				
				if option_data:
					price = option_data.get('mid_price') or option_data.get('last') or \
							(option_data.get('bid', 0) + option_data.get('ask', 0)) / 2
					
					if not price:
						# Fallback to estimation
						price = self.estimate_option_price(
							underlying_price=underlying_price,
							strike=leg_def['strike'],
							expiration=expiration,
							option_type=leg_def['type']
						)
						data_source_details[f"{leg_def['type']}_{leg_def['strike']}"] = 'estimated'
					else:
						data_source_details[f"{leg_def['type']}_{leg_def['strike']}"] = 'ib'
					
					# Calculate leg value (credit received for sells, debit paid for buys)
					leg_value = price * leg_def['quantity'] * 100  # Options are per 100 shares
					if leg_def['action'] == 'sell':
						total_credit += leg_value
					else:
						total_credit -= leg_value
					
					legs.append({
						'strike': leg_def['strike'],
						'option_type': leg_def['type'],
						'action': leg_def['action'],
						'quantity': leg_def['quantity'],
						'price': price,
						'value': leg_value,
						'option_data': option_data
					})
			
			# Calculate strategy metrics
			put_spread_width = put_short_strike - put_long_strike
			call_spread_width = call_long_strike - call_short_strike
			max_profit = total_credit
			max_loss = (max(put_spread_width, call_spread_width) * contracts * 100) - total_credit
			
			# Calculate breakeven points
			breakeven_lower = put_short_strike - (total_credit / (contracts * 100))
			breakeven_upper = call_short_strike + (total_credit / (contracts * 100))
			
			# Calculate combined Greeks
			strategy_greeks = self.calculate_strategy_greeks(legs)
			
			# Build result
			result = {
				'strategy_id': str(uuid.uuid4()),
				'strategy_type': 'iron_condor',
				'symbol': symbol,
				'expiration': expiration.isoformat(),
				'underlying_price': underlying_price,
				'data_source': data_source,
				'legs': legs,
				'total_credit': round(total_credit, 2),
				'max_profit': round(max_profit, 2),
				'max_loss': round(max_loss, 2),
				'breakeven_points': [round(breakeven_lower, 2), round(breakeven_upper, 2)],
				'profit_range': [round(breakeven_lower, 2), round(breakeven_upper, 2)],
				'greeks': strategy_greeks,
				'risk_reward_ratio': round(max_profit / abs(max_loss), 2) if max_loss != 0 else 0,
				'probability_of_profit': self.estimate_probability_of_profit(
					underlying_price, breakeven_lower, breakeven_upper, expiration
				),
				'contracts': contracts,
				'calculated_at': datetime.now(timezone.utc).isoformat(),
				'data_source_details': data_source_details
			}
			
			if error_details:
				result['error_details'] = error_details
			
			# Add live update information if requested
			if include_live_updates:
				result.update({
					'subscription_id': str(uuid.uuid4()),
					'update_frequency': 5,  # seconds
					'last_updated': datetime.now(timezone.utc).isoformat(),
					'live_updates_enabled': True
				})
			
			# Cache the result
			self._cache_calculation(cache_key, result)
			
			# Save to database if requested
			if save_to_db:
				self._save_strategy_to_db(result, ib_data)
			
			return result
		
		except Exception as e:
			logger.error(f"Error calculating Iron Condor: {str(e)}")
			
			if self.fallback_enabled and underlying_price:
				# Return basic estimated calculation
				return self.calculate_iron_condor_estimated(
					symbol=symbol,
					underlying_price=underlying_price,
					expiration=expiration,
					put_short_strike=put_short_strike,
					put_long_strike=put_long_strike,
					call_short_strike=call_short_strike,
					call_long_strike=call_long_strike,
					contracts=contracts,
					error_details=str(e)
				)
			else:
				raise
	
	def calculate_bull_call_spread(self,
								   symbol: str,
								   expiration: date,
								   long_strike: float,
								   short_strike: float,
								   contracts: int = 1,
								   underlying_price: Optional[float] = None,
								   save_to_db: bool = False) -> Dict[str, Any]:
		"""Calculate Bull Call Spread using IB data with fallback.
		
		Args:
			symbol: Underlying symbol
			expiration: Option expiration date
			long_strike: Long call strike (lower)
			short_strike: Short call strike (higher)
			contracts: Number of contracts
			underlying_price: Current underlying price
			save_to_db: Whether to save to database
		
		Returns:
			Dictionary with strategy calculation results
		"""
		try:
			if long_strike >= short_strike:
				raise ValueError("Long strike must be lower than short strike for Bull Call Spread")
			
			# Get IB data
			strikes = [long_strike, short_strike]
			ib_data = self.market_data_service.fetch_options_chain(
				symbol=symbol,
				expiration=expiration,
				strikes=strikes
			)
			
			data_source = 'ib_realtime' if ib_data else 'estimated'
			
			if not underlying_price:
				underlying_price = self.market_data_service.get_underlying_price(symbol)
			
			# Build legs
			legs = []
			net_debit = 0.0
			
			for strike in [long_strike, short_strike]:
				option_data = self.get_option_data_by_strike(
					symbol=symbol,
					expiration=expiration,
					strike=strike,
					option_type='call',
					ib_data=ib_data,
					underlying_price=underlying_price
				)
				
				price = option_data.get('mid_price', 0) if option_data else \
						self.estimate_option_price(underlying_price, strike, expiration, 'call')
				
				action = 'buy' if strike == long_strike else 'sell'
				leg_value = price * contracts * 100
				
				if action == 'buy':
					net_debit += leg_value
				else:
					net_debit -= leg_value
				
				legs.append({
					'strike': strike,
					'option_type': 'call',
					'action': action,
					'quantity': contracts,
					'price': price,
					'value': leg_value,
					'option_data': option_data
				})
			
			# Calculate metrics
			spread_width = short_strike - long_strike
			max_profit = (spread_width * contracts * 100) - net_debit
			max_loss = net_debit
			breakeven = long_strike + (net_debit / (contracts * 100))
			
			return {
				'strategy_id': str(uuid.uuid4()),
				'strategy_type': 'bull_call_spread',
				'symbol': symbol,
				'expiration': expiration.isoformat(),
				'underlying_price': underlying_price,
				'data_source': data_source,
				'legs': legs,
				'net_debit': round(net_debit, 2),
				'max_profit': round(max_profit, 2),
				'max_loss': round(max_loss, 2),
				'breakeven_point': round(breakeven, 2),
				'greeks': self.calculate_strategy_greeks(legs),
				'contracts': contracts,
				'calculated_at': datetime.now(timezone.utc).isoformat()
			}
		
		except Exception as e:
			logger.error(f"Error calculating Bull Call Spread: {str(e)}")
			raise
	
	def get_option_data_by_strike(self,
								  symbol: str,
								  expiration: date,
								  strike: float,
								  option_type: str,
								  ib_data: Optional[List[Dict]] = None,
								  underlying_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
		"""Get option data for specific strike, preferring IB data.
		
		Args:
			symbol: Option symbol
			expiration: Expiration date
			strike: Strike price
			option_type: 'call' or 'put'
			ib_data: Pre-fetched IB data
			underlying_price: Underlying price for fallback
		
		Returns:
			Option data dictionary or None
		"""
		# Search in provided IB data first
		if ib_data:
			for option in ib_data:
				if (option['strike'] == strike and 
					option['option_type'] == option_type and
					option['expiration'] == expiration):
					return option
		
		# Try to get from cache
		cached = self.market_data_service.get_cached_options_data(
			symbol, strike, expiration, option_type
		)
		if cached:
			return cached
		
		# Fallback to individual fetch if connected
		if self.market_data_service.connection_manager.is_connected:
			try:
				chain_data = self.market_data_service.fetch_options_chain(
					symbol, expiration, [strike]
				)
				for option in chain_data:
					if (option['strike'] == strike and 
						option['option_type'] == option_type):
						return option
			except Exception as e:
				logger.warning(f"Failed to fetch individual option data: {str(e)}")
		
		# Return None if no data available
		return None
	
	def calculate_strategy_greeks(self, legs: List[Dict[str, Any]]) -> Dict[str, float]:
		"""Calculate combined Greeks for the strategy.
		
		Args:
			legs: List of strategy legs with option data
		
		Returns:
			Dictionary of combined Greeks
		"""
		total_delta = 0.0
		total_gamma = 0.0
		total_theta = 0.0
		total_vega = 0.0
		total_rho = 0.0
		
		for leg in legs:
			option_data = leg.get('option_data', {})
			multiplier = leg['quantity'] * (1 if leg['action'] == 'buy' else -1)
			
			total_delta += (option_data.get('delta', 0) or 0) * multiplier
			total_gamma += (option_data.get('gamma', 0) or 0) * multiplier
			total_theta += (option_data.get('theta', 0) or 0) * multiplier
			total_vega += (option_data.get('vega', 0) or 0) * multiplier
			total_rho += (option_data.get('rho', 0) or 0) * multiplier
		
		return {
			'delta': round(total_delta, 4),
			'gamma': round(total_gamma, 6),
			'theta': round(total_theta, 4),
			'vega': round(total_vega, 4),
			'rho': round(total_rho, 4)
		}
	
	def calculate_profit_loss_scenarios(self, 
										strategy_result: Dict[str, Any],
										price_range: Tuple[float, float, float] = None) -> List[Dict[str, Any]]:
		"""Calculate P&L scenarios at different underlying prices.
		
		Args:
			strategy_result: Strategy calculation result
			price_range: (start, end, step) for price scenarios
		
		Returns:
			List of P&L scenarios
		"""
		if not price_range:
			underlying = strategy_result['underlying_price']
			price_range = (underlying * 0.9, underlying * 1.1, underlying * 0.01)
		
		scenarios = []
		start_price, end_price, step = price_range
		
		current_price = start_price
		while current_price <= end_price:
			pnl = self._calculate_pnl_at_price(strategy_result, current_price)
			scenarios.append({
				'price': round(current_price, 2),
				'pnl': round(pnl, 2),
				'pnl_percentage': round((pnl / abs(strategy_result.get('max_loss', 1))) * 100, 2)
			})
			current_price += step
		
		return scenarios
	
	def _calculate_pnl_at_price(self, strategy_result: Dict[str, Any], price_at_expiration: float) -> float:
		"""Calculate P&L at a specific price at expiration.
		
		Args:
			strategy_result: Strategy data
			price_at_expiration: Underlying price at expiration
		
		Returns:
			Profit/Loss amount
		"""
		total_pnl = 0.0
		
		for leg in strategy_result.get('legs', []):
			strike = leg['strike']
			option_type = leg['option_type']
			action = leg['action']
			quantity = leg['quantity']
			premium_paid_received = leg.get('value', 0)
			
			# Calculate intrinsic value at expiration
			if option_type == 'call':
				intrinsic_value = max(0, price_at_expiration - strike) * quantity * 100
			else:  # put
				intrinsic_value = max(0, strike - price_at_expiration) * quantity * 100
			
			if action == 'buy':
				# For bought options: intrinsic value - premium paid
				leg_pnl = intrinsic_value - abs(premium_paid_received)
			else:
				# For sold options: premium received - intrinsic value owed
				leg_pnl = abs(premium_paid_received) - intrinsic_value
			
			total_pnl += leg_pnl
		
		return total_pnl
	
	def estimate_option_price(self,
							  underlying_price: float,
							  strike: float,
							  expiration: date,
							  option_type: str,
							  implied_volatility: float = 0.20,
							  risk_free_rate: float = 0.05) -> float:
		"""Estimate option price using Black-Scholes model.
		
		Args:
			underlying_price: Current underlying price
			strike: Option strike price
			expiration: Expiration date
			option_type: 'call' or 'put'
			implied_volatility: Implied volatility
			risk_free_rate: Risk-free interest rate
		
		Returns:
			Estimated option price
		"""
		try:
			# Calculate time to expiration in years
			days_to_expiration = (expiration - date.today()).days
			T = max(days_to_expiration / 365.0, 1/365)  # Minimum 1 day
			
			# Black-Scholes calculation
			d1 = (math.log(underlying_price / strike) + (risk_free_rate + 0.5 * implied_volatility**2) * T) / (implied_volatility * math.sqrt(T))
			d2 = d1 - implied_volatility * math.sqrt(T)
			
			if option_type == 'call':
				price = (underlying_price * norm.cdf(d1) - 
						strike * math.exp(-risk_free_rate * T) * norm.cdf(d2))
			else:  # put
				price = (strike * math.exp(-risk_free_rate * T) * norm.cdf(-d2) - 
						underlying_price * norm.cdf(-d1))
			
			return max(0.01, price)  # Minimum price of $0.01
		
		except Exception as e:
			logger.error(f"Error estimating option price: {str(e)}")
			# Simple intrinsic value fallback
			if option_type == 'call':
				return max(0.01, underlying_price - strike) if underlying_price > strike else 0.01
			else:
				return max(0.01, strike - underlying_price) if strike > underlying_price else 0.01
	
	def estimate_probability_of_profit(self,
									   current_price: float,
									   lower_breakeven: float,
									   upper_breakeven: float,
									   expiration: date,
									   implied_volatility: float = 0.20) -> float:
		"""Estimate probability that the strategy will be profitable.
		
		Args:
			current_price: Current underlying price
			lower_breakeven: Lower breakeven point
			upper_breakeven: Upper breakeven point
			expiration: Expiration date
			implied_volatility: Implied volatility
		
		Returns:
			Probability of profit (0-1)
		"""
		try:
			days_to_expiration = (expiration - date.today()).days
			T = max(days_to_expiration / 365.0, 1/365)
			
			# Standard deviation of price movement
			std_dev = current_price * implied_volatility * math.sqrt(T)
			
			# Z-scores for breakeven points
			z1 = (lower_breakeven - current_price) / std_dev
			z2 = (upper_breakeven - current_price) / std_dev
			
			# Probability of being between breakeven points
			prob = norm.cdf(z2) - norm.cdf(z1)
			
			return round(min(max(prob, 0), 1), 4)
		
		except Exception as e:
			logger.error(f"Error calculating probability of profit: {str(e)}")
			return 0.5  # Default to 50%
	
	def validate_iron_condor_parameters(self,
										put_short_strike: float,
										put_long_strike: float,
										call_short_strike: float,
										call_long_strike: float) -> bool:
		"""Validate Iron Condor strike parameters.
		
		Args:
			put_short_strike: Short put strike
			put_long_strike: Long put strike
			call_short_strike: Short call strike
			call_long_strike: Long call strike
		
		Returns:
			True if valid, False otherwise
		"""
		# Put spread: long < short
		if put_long_strike >= put_short_strike:
			return False
		
		# Call spread: short < long
		if call_short_strike >= call_long_strike:
			return False
		
		# Put strikes should be below call strikes
		if put_short_strike >= call_short_strike:
			return False
		
		return True
	
	def calculate_iron_condor_estimated(self,
										symbol: str,
										underlying_price: float,
										expiration: date,
										put_short_strike: float,
										put_long_strike: float,
										call_short_strike: float,
										call_long_strike: float,
										contracts: int = 1,
										implied_volatility: float = 0.20,
										error_details: Optional[str] = None) -> Dict[str, Any]:
		"""Calculate Iron Condor using estimated option prices.
		
		Args:
			symbol: Underlying symbol
			underlying_price: Current underlying price
			expiration: Option expiration date
			put_short_strike: Short put strike
			put_long_strike: Long put strike
			call_short_strike: Short call strike
			call_long_strike: Long call strike
			contracts: Number of contracts
			implied_volatility: Implied volatility for estimates
			error_details: Error message if this is a fallback
		
		Returns:
			Dictionary with estimated strategy results
		"""
		legs = []
		total_credit = 0.0
		
		strikes_and_types = [
			(put_long_strike, 'put', 'buy'),
			(put_short_strike, 'put', 'sell'),
			(call_short_strike, 'call', 'sell'),
			(call_long_strike, 'call', 'buy')
		]
		
		for strike, option_type, action in strikes_and_types:
			estimated_price = self.estimate_option_price(
				underlying_price, strike, expiration, option_type, implied_volatility
			)
			
			leg_value = estimated_price * contracts * 100
			if action == 'sell':
				total_credit += leg_value
			else:
				total_credit -= leg_value
			
			legs.append({
				'strike': strike,
				'option_type': option_type,
				'action': action,
				'quantity': contracts,
				'price': estimated_price,
				'value': leg_value,
				'option_data': {
					'estimated': True,
					'implied_volatility': implied_volatility
				}
			})
		
		put_spread_width = put_short_strike - put_long_strike
		call_spread_width = call_long_strike - call_short_strike
		max_profit = total_credit
		max_loss = (max(put_spread_width, call_spread_width) * contracts * 100) - total_credit
		
		breakeven_lower = put_short_strike - (total_credit / (contracts * 100))
		breakeven_upper = call_short_strike + (total_credit / (contracts * 100))
		
		result = {
			'strategy_id': str(uuid.uuid4()),
			'strategy_type': 'iron_condor',
			'symbol': symbol,
			'expiration': expiration.isoformat(),
			'underlying_price': underlying_price,
			'data_source': 'estimated',
			'legs': legs,
			'total_credit': round(total_credit, 2),
			'max_profit': round(max_profit, 2),
			'max_loss': round(max_loss, 2),
			'breakeven_points': [round(breakeven_lower, 2), round(breakeven_upper, 2)],
			'greeks': {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0},  # Estimated
			'contracts': contracts,
			'calculated_at': datetime.now(timezone.utc).isoformat(),
			'estimated_parameters': {
				'implied_volatility': implied_volatility,
				'risk_free_rate': 0.05
			}
		}
		
		if error_details:
			result['error_details'] = error_details
		
		return result
	
	def compare_data_sources(self, 
							 ib_result: Dict[str, Any],
							 estimated_result: Dict[str, Any]) -> Dict[str, Any]:
		"""Compare results from IB data vs estimates.
		
		Args:
			ib_result: Result calculated with IB data
			estimated_result: Result calculated with estimates
		
		Returns:
			Comparison analysis
		"""
		return {
			'ib_result': ib_result,
			'estimated_result': estimated_result,
			'differences': {
				'total_credit_diff': abs(ib_result.get('total_credit', 0) - estimated_result.get('total_credit', 0)),
				'max_profit_diff': abs(ib_result.get('max_profit', 0) - estimated_result.get('max_profit', 0)),
				'max_loss_diff': abs(ib_result.get('max_loss', 0) - estimated_result.get('max_loss', 0))
			},
			'accuracy_metrics': {
				'data_source_quality': ib_result.get('data_source', 'unknown'),
				'comparison_timestamp': datetime.now(timezone.utc).isoformat()
			}
		}
	
	def _get_cached_calculation(self, cache_key: str) -> Optional[Dict[str, Any]]:
		"""Get cached calculation if not expired."""
		if cache_key in self._calculation_cache:
			timestamp = self._cache_timestamps.get(cache_key)
			if timestamp and (datetime.now(timezone.utc) - timestamp).total_seconds() < self.cache_duration:
				return self._calculation_cache[cache_key]
		return None
	
	def _cache_calculation(self, cache_key: str, result: Dict[str, Any]) -> None:
		"""Cache calculation result."""
		self._calculation_cache[cache_key] = result
		self._cache_timestamps[cache_key] = datetime.now(timezone.utc)
	
	def _save_strategy_to_db(self, result: Dict[str, Any], ib_data: Optional[List[Dict]] = None) -> None:
		"""Save strategy calculation to database.
		
		Args:
			result: Strategy calculation result
			ib_data: Original IB data if available
		"""
		try:
			with next(get_db_session()) as db:
				strategy = Strategy(
					name=f"{result['strategy_type'].title()} - {result['symbol']}",
					strategy_type=result['strategy_type'],
					symbol=result['symbol'],
					parameters={
						'expiration': result['expiration'],
						'legs': result['legs'],
						'contracts': result['contracts']
					},
					data_source=result['data_source'],
					ib_snapshot={
						'calculation_result': result,
						'raw_ib_data': ib_data,
						'snapshot_time': datetime.now(timezone.utc).isoformat()
					}
				)
				
				db.add(strategy)
				db.commit()
				logger.info(f"Saved strategy {result['strategy_id']} to database")
		
		except Exception as e:
			logger.error(f"Error saving strategy to database: {str(e)}")


# Singleton instance
ib_strategy_calculator = IBStrategyCalculator()