"""Interactive Brokers market data service."""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from database.config import get_db_session
from database.models import (
	OptionsDataCache,
	HistoricalOptionsData,
	Strategy
)

logger = logging.getLogger(__name__)


class IBDataService:
	"""Service for managing IB market data."""
	
	def __init__(self):
		"""Initialize the IB data service."""
		self.cache_ttl_seconds = 5  # Default cache TTL
	
	def get_options_chain(self, 
						  symbol: str,
						  expiration: date,
						  strikes: Optional[List[float]] = None) -> List[Dict[str, Any]]:
		"""Get options chain data from IB.
		
		Args:
			symbol: Underlying symbol (e.g., 'SPY')
			expiration: Option expiration date
			strikes: Optional list of specific strikes to fetch
		
		Returns:
			List of option contract data dictionaries
		"""
		options_data = []
		
		# Check cache first
		with next(get_db_session()) as db:
			for option_type in ['call', 'put']:
				if strikes:
					for strike in strikes:
						cached = OptionsDataCache.get_cached_data(
							db, symbol, Decimal(str(strike)), 
							datetime.combine(expiration, datetime.min.time()),
							option_type
						)
						if cached and not cached.is_expired():
							options_data.append(cached.to_dict())
		
		# If no cached data or expired, fetch from IB (placeholder)
		if not options_data:
			# This will be replaced with actual IB API calls
			logger.info(f"Fetching options chain for {symbol} exp {expiration}")
			# Placeholder data for now
			if strikes:
				for strike in strikes:
					for option_type in ['call', 'put']:
						options_data.append(self._create_placeholder_option(
							symbol, strike, expiration, option_type
						))
		
		return options_data
	
	def get_option_quote(self,
						symbol: str,
						strike: float,
						expiration: date,
						option_type: str) -> Optional[Dict[str, Any]]:
		"""Get real-time quote for a specific option.
		
		Args:
			symbol: Underlying symbol
			strike: Strike price
			expiration: Expiration date
			option_type: 'call' or 'put'
		
		Returns:
			Option quote data or None if not available
		"""
		with next(get_db_session()) as db:
			# Check cache
			cached = OptionsDataCache.get_cached_data(
				db, symbol, Decimal(str(strike)),
				datetime.combine(expiration, datetime.min.time()),
				option_type
			)
			
			if cached and not cached.is_expired():
				return cached.to_dict()
			
			# Fetch from IB (placeholder)
			logger.info(f"Fetching quote for {symbol} {strike} {option_type} exp {expiration}")
			option_data = self._create_placeholder_option(
				symbol, strike, expiration, option_type
			)
			
			# Cache the data
			self._cache_option_data(db, option_data)
			
			return option_data
	
	def get_option_greeks(self,
						 symbol: str,
						 strike: float,
						 expiration: date,
						 option_type: str) -> Optional[Dict[str, float]]:
		"""Get Greeks for a specific option.
		
		Args:
			symbol: Underlying symbol
			strike: Strike price
			expiration: Expiration date
			option_type: 'call' or 'put'
		
		Returns:
			Dictionary of Greeks or None
		"""
		quote = self.get_option_quote(symbol, strike, expiration, option_type)
		if quote:
			return {
				'delta': quote.get('delta'),
				'gamma': quote.get('gamma'),
				'theta': quote.get('theta'),
				'vega': quote.get('vega'),
				'rho': quote.get('rho')
			}
		return None
	
	def get_historical_options_data(self,
									symbol: str,
									start_date: date,
									end_date: date,
									strikes: Optional[List[float]] = None) -> List[Dict[str, Any]]:
		"""Get historical options data from IB.
		
		Args:
			symbol: Underlying symbol
			start_date: Start date for historical data
			end_date: End date for historical data
			strikes: Optional list of specific strikes
		
		Returns:
			List of historical options data
		"""
		with next(get_db_session()) as db:
			# Check database for existing historical data
			historical_data = HistoricalOptionsData.get_date_range(
				db, symbol,
				datetime.combine(start_date, datetime.min.time()),
				datetime.combine(end_date, datetime.max.time())
			)
			
			if historical_data:
				return [data.to_dict() for data in historical_data]
			
			# Fetch from IB (placeholder)
			logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
			# Placeholder implementation
			return []
	
	def cache_option_data(self, option_data: Dict[str, Any]) -> None:
		"""Cache option data in the database.
		
		Args:
			option_data: Option data to cache
		"""
		with next(get_db_session()) as db:
			self._cache_option_data(db, option_data)
	
	def _cache_option_data(self, db_session, option_data: Dict[str, Any]) -> None:
		"""Internal method to cache option data.
		
		Args:
			db_session: Database session
			option_data: Option data to cache
		"""
		try:
			cache_entry = OptionsDataCache(
				symbol=option_data['symbol'],
				strike=Decimal(str(option_data['strike'])),
				expiration=option_data['expiration'] if isinstance(option_data['expiration'], datetime) 
						  else datetime.combine(option_data['expiration'], datetime.min.time()),
				option_type=option_data['option_type'],
				bid=Decimal(str(option_data.get('bid', 0))) if option_data.get('bid') else None,
				ask=Decimal(str(option_data.get('ask', 0))) if option_data.get('ask') else None,
				last=Decimal(str(option_data.get('last', 0))) if option_data.get('last') else None,
				volume=option_data.get('volume'),
				open_interest=option_data.get('open_interest'),
				implied_volatility=Decimal(str(option_data.get('implied_volatility', 0))) if option_data.get('implied_volatility') else None,
				delta=Decimal(str(option_data.get('delta', 0))) if option_data.get('delta') else None,
				gamma=Decimal(str(option_data.get('gamma', 0))) if option_data.get('gamma') else None,
				theta=Decimal(str(option_data.get('theta', 0))) if option_data.get('theta') else None,
				vega=Decimal(str(option_data.get('vega', 0))) if option_data.get('vega') else None,
				rho=Decimal(str(option_data.get('rho', 0))) if option_data.get('rho') else None,
				timestamp=datetime.now(timezone.utc),
				ttl_seconds=self.cache_ttl_seconds
			)
			db_session.add(cache_entry)
			db_session.commit()
			logger.debug(f"Cached option data for {option_data['symbol']} {option_data['strike']} {option_data['option_type']}")
		except Exception as e:
			logger.error(f"Failed to cache option data: {str(e)}")
			db_session.rollback()
	
	def cleanup_expired_cache(self) -> int:
		"""Clean up expired cache entries.
		
		Returns:
			Number of entries cleaned up
		"""
		with next(get_db_session()) as db:
			count = OptionsDataCache.cleanup_expired(db)
			db.commit()
			logger.info(f"Cleaned up {count} expired cache entries")
			return count
	
	def update_strategy_with_ib_data(self, 
									 strategy_id: str,
									 ib_data: Dict[str, Any]) -> None:
		"""Update a strategy with IB market data snapshot.
		
		Args:
			strategy_id: Strategy ID to update
			ib_data: IB market data to store
		"""
		with next(get_db_session()) as db:
			strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
			if strategy:
				strategy.data_source = 'ib_realtime'
				strategy.ib_snapshot = ib_data
				db.commit()
				logger.info(f"Updated strategy {strategy_id} with IB data")
			else:
				logger.warning(f"Strategy {strategy_id} not found")
	
	def _create_placeholder_option(self, 
								   symbol: str,
								   strike: float,
								   expiration: date,
								   option_type: str) -> Dict[str, Any]:
		"""Create placeholder option data for testing.
		
		This will be replaced with actual IB data fetching.
		
		Args:
			symbol: Underlying symbol
			strike: Strike price
			expiration: Expiration date
			option_type: 'call' or 'put'
		
		Returns:
			Placeholder option data dictionary
		"""
		# Simple placeholder pricing based on moneyness
		# This is just for testing and will be replaced
		base_price = 450  # Assume SPY at 450
		moneyness = (strike - base_price) / base_price
		
		if option_type == 'call':
			if moneyness < 0:  # ITM
				bid = abs(moneyness) * base_price * 0.02
			else:  # OTM
				bid = max(0.05, 2.0 - moneyness * 10)
		else:  # put
			if moneyness > 0:  # ITM
				bid = moneyness * base_price * 0.02
			else:  # OTM
				bid = max(0.05, 2.0 + moneyness * 10)
		
		ask = bid + 0.05
		
		return {
			'symbol': symbol,
			'strike': strike,
			'expiration': expiration,
			'option_type': option_type,
			'bid': round(bid, 2),
			'ask': round(ask, 2),
			'last': round((bid + ask) / 2, 2),
			'volume': 1000,
			'open_interest': 5000,
			'implied_volatility': 0.20,
			'delta': 0.50 if option_type == 'call' else -0.50,
			'gamma': 0.01,
			'theta': -0.50,
			'vega': 10.0,
			'rho': 5.0,
			'timestamp': datetime.now(timezone.utc).isoformat()
		}


# Singleton instance
ib_data_service = IBDataService()