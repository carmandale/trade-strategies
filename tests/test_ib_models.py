"""Tests for Interactive Brokers integration database models."""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import inspect
from database.config import get_db_session, Base, engine
from database.models import (
    IBSettings,
    OptionsDataCache,
    HistoricalOptionsData,
    IBConnectionLog,
    Strategy
)


class TestIBSettings:
	"""Test IBSettings model."""
	
	def test_ib_settings_creation(self, db_session):
		"""Test creating IB settings record."""
		settings = IBSettings(
			host="127.0.0.1",
			port=7497,
			client_id=1,
			account="DU123456",
			market_data_type=1,
			auto_connect=True,
			encrypted_credentials="encrypted_password_here"
		)
		db_session.add(settings)
		db_session.commit()
		
		assert settings.id is not None
		assert settings.host == "127.0.0.1"
		assert settings.port == 7497
		assert settings.account == "DU123456"
		assert settings.auto_connect is True
	
	def test_ib_settings_defaults(self, db_session):
		"""Test IB settings default values."""
		settings = IBSettings(account="TEST123")
		db_session.add(settings)
		db_session.commit()
		
		assert settings.host == "127.0.0.1"
		assert settings.port == 7497
		assert settings.client_id == 1
		assert settings.market_data_type == 1
		assert settings.auto_connect is False
	
	def test_ib_settings_update(self, db_session):
		"""Test updating IB settings."""
		settings = IBSettings(account="TEST123")
		db_session.add(settings)
		db_session.commit()
		
		settings.port = 4001
		settings.auto_connect = True
		db_session.commit()
		
		updated = db_session.query(IBSettings).filter_by(account="TEST123").first()
		assert updated.port == 4001
		assert updated.auto_connect is True
	
	def test_ib_settings_to_dict(self, db_session):
		"""Test converting IB settings to dictionary."""
		settings = IBSettings(
			account="TEST123",
			host="192.168.1.100",
			port=4002
		)
		db_session.add(settings)
		db_session.commit()
		
		data = settings.to_dict()
		assert data['account'] == "TEST123"
		assert data['host'] == "192.168.1.100"
		assert data['port'] == 4002
		assert 'created_at' in data
		assert 'updated_at' in data


class TestOptionsDataCache:
	"""Test OptionsDataCache model."""
	
	def test_options_cache_creation(self, db_session):
		"""Test creating options cache entry."""
		cache = OptionsDataCache(
			symbol="SPY",
			strike=Decimal("450.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			bid=Decimal("5.25"),
			ask=Decimal("5.35"),
			last=Decimal("5.30"),
			volume=1000,
			open_interest=5000,
			implied_volatility=Decimal("0.1850"),
			delta=Decimal("0.5500"),
			gamma=Decimal("0.0125"),
			theta=Decimal("-0.85"),
			vega=Decimal("12.50"),
			rho=Decimal("8.25"),
			timestamp=datetime.now(timezone.utc)
		)
		db_session.add(cache)
		db_session.commit()
		
		assert cache.id is not None
		assert cache.symbol == "SPY"
		assert cache.strike == Decimal("450.00")
		assert cache.delta == Decimal("0.5500")
	
	def test_options_cache_unique_constraint(self, db_session):
		"""Test unique constraint on options cache."""
		timestamp = datetime.now(timezone.utc)
		cache1 = OptionsDataCache(
			symbol="SPY",
			strike=Decimal("450.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			timestamp=timestamp
		)
		db_session.add(cache1)
		db_session.commit()
		
		# Attempt to add duplicate should fail
		cache2 = OptionsDataCache(
			symbol="SPY",
			strike=Decimal("450.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			timestamp=timestamp
		)
		db_session.add(cache2)
		
		with pytest.raises(Exception):  # Should raise IntegrityError
			db_session.commit()
	
	def test_get_cached_data(self, db_session):
		"""Test retrieving cached options data."""
		# Add expired cache entry
		expired_cache = OptionsDataCache(
			symbol="SPY",
			strike=Decimal("450.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			timestamp=datetime.now(timezone.utc) - timedelta(seconds=10),
			ttl_seconds=5  # Already expired
		)
		db_session.add(expired_cache)
		
		# Add valid cache entry
		valid_cache = OptionsDataCache(
			symbol="SPY",
			strike=Decimal("450.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			bid=Decimal("5.25"),
			ask=Decimal("5.35"),
			timestamp=datetime.now(timezone.utc),
			ttl_seconds=300  # 5 minutes
		)
		db_session.add(valid_cache)
		db_session.commit()
		
		# Should return valid entry
		data = OptionsDataCache.get_cached_data(
			db_session, 
			"SPY", 
			Decimal("450.00"),
			datetime(2025, 1, 17).date(),
			"call"
		)
		assert data is not None
		assert data.bid == Decimal("5.25")
	
	def test_cleanup_expired_cache(self, db_session):
		"""Test cleaning up expired cache entries."""
		# Add expired entries
		for i in range(3):
			cache = OptionsDataCache(
				symbol="SPY",
				strike=Decimal(f"450.{i:02d}"),
				expiration=datetime(2025, 1, 17).date(),
				option_type="call",
				timestamp=datetime.now(timezone.utc) - timedelta(seconds=10),
				ttl_seconds=5
			)
			db_session.add(cache)
		
		# Add valid entry
		valid_cache = OptionsDataCache(
			symbol="SPY",
			strike=Decimal("451.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			timestamp=datetime.now(timezone.utc),
			ttl_seconds=300
		)
		db_session.add(valid_cache)
		db_session.commit()
		
		# Cleanup expired
		count = OptionsDataCache.cleanup_expired(db_session)
		db_session.commit()
		
		assert count == 3
		remaining = db_session.query(OptionsDataCache).count()
		assert remaining == 1


class TestHistoricalOptionsData:
	"""Test HistoricalOptionsData model."""
	
	def test_historical_data_creation(self, db_session):
		"""Test creating historical options data."""
		historical = HistoricalOptionsData(
			symbol="SPY",
			strike=Decimal("450.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			date=datetime(2025, 1, 10).date(),
			open=Decimal("5.00"),
			high=Decimal("5.50"),
			low=Decimal("4.95"),
			close=Decimal("5.25"),
			volume=10000,
			open_interest=50000,
			implied_volatility=Decimal("0.1850")
		)
		db_session.add(historical)
		db_session.commit()
		
		assert historical.id is not None
		assert historical.close == Decimal("5.25")
		assert historical.volume == 10000
	
	def test_historical_data_unique_constraint(self, db_session):
		"""Test unique constraint on historical data."""
		historical1 = HistoricalOptionsData(
			symbol="SPY",
			strike=Decimal("450.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			date=datetime(2025, 1, 10).date(),
			close=Decimal("5.25")
		)
		db_session.add(historical1)
		db_session.commit()
		
		# Duplicate should fail
		historical2 = HistoricalOptionsData(
			symbol="SPY",
			strike=Decimal("450.00"),
			expiration=datetime(2025, 1, 17).date(),
			option_type="call",
			date=datetime(2025, 1, 10).date(),
			close=Decimal("5.30")
		)
		db_session.add(historical2)
		
		with pytest.raises(Exception):
			db_session.commit()
	
	def test_get_historical_range(self, db_session):
		"""Test retrieving historical data for date range."""
		# Add data for multiple dates
		for i in range(5):
			historical = HistoricalOptionsData(
				symbol="SPY",
				strike=Decimal("450.00"),
				expiration=datetime(2025, 1, 17).date(),
				option_type="call",
				date=datetime(2025, 1, 10 + i).date(),
				close=Decimal(f"5.{i}0")
			)
			db_session.add(historical)
		db_session.commit()
		
		# Query range
		data = HistoricalOptionsData.get_date_range(
			db_session,
			"SPY",
			datetime(2025, 1, 12).date(),
			datetime(2025, 1, 14).date()
		)
		
		assert len(data) == 3
		assert all(d.symbol == "SPY" for d in data)


class TestIBConnectionLog:
	"""Test IBConnectionLog model."""
	
	def test_connection_log_creation(self, db_session):
		"""Test creating connection log entries."""
		log = IBConnectionLog(
			event_type="connect",
			status="success",
			account="DU123456",
			event_metadata={"server_version": 176, "connection_time": 1.5}
		)
		db_session.add(log)
		db_session.commit()
		
		assert log.id is not None
		assert log.event_type == "connect"
		assert log.status == "success"
		assert log.event_metadata["server_version"] == 176
	
	def test_connection_log_error(self, db_session):
		"""Test logging connection errors."""
		log = IBConnectionLog(
			event_type="connect",
			status="error",
			error_message="Connection refused: IB Gateway not running",
			event_metadata={"attempted_port": 7497}
		)
		db_session.add(log)
		db_session.commit()
		
		assert log.error_message == "Connection refused: IB Gateway not running"
		assert log.event_metadata["attempted_port"] == 7497
	
	def test_get_recent_logs(self, db_session):
		"""Test retrieving recent connection logs."""
		# Add multiple log entries
		for i in range(5):
			log = IBConnectionLog(
				event_type="heartbeat",
				status="success",
				account="DU123456"
			)
			db_session.add(log)
		db_session.commit()
		
		logs = IBConnectionLog.get_recent_logs(db_session, limit=3)
		assert len(logs) == 3
		# Logs should be ordered by created_at DESC
		assert logs[0].created_at >= logs[1].created_at


class TestStrategyModifications:
	"""Test modifications to Strategy model for IB integration."""
	
	def test_strategy_data_source(self, db_session):
		"""Test strategy data_source field."""
		strategy = Strategy(
			name="Test Iron Condor",
			strategy_type="iron_condor",
			symbol="SPY",
			parameters={},
			data_source="ib_realtime"
		)
		db_session.add(strategy)
		db_session.commit()
		
		assert strategy.data_source == "ib_realtime"
	
	def test_strategy_ib_snapshot(self, db_session):
		"""Test strategy ib_snapshot JSONB field."""
		snapshot_data = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"options_data": [
				{
					"strike": 450,
					"type": "call",
					"bid": 5.25,
					"ask": 5.35,
					"greeks": {
						"delta": 0.55,
						"gamma": 0.0125,
						"theta": -0.85,
						"vega": 12.50
					}
				}
			],
			"underlying_price": 450.25
		}
		
		strategy = Strategy(
			name="Test Strategy",
			strategy_type="iron_condor",
			symbol="SPY",
			parameters={},
			data_source="ib_realtime",
			ib_snapshot=snapshot_data
		)
		db_session.add(strategy)
		db_session.commit()
		
		# Retrieve and verify
		saved = db_session.query(Strategy).filter_by(name="Test Strategy").first()
		assert saved.ib_snapshot is not None
		assert saved.ib_snapshot["underlying_price"] == 450.25
		assert saved.ib_snapshot["options_data"][0]["greeks"]["delta"] == 0.55
	
	def test_strategy_data_source_validation(self, db_session):
		"""Test data_source field validation."""
		# Valid values should work
		for source in ['estimated', 'ib_realtime', 'ib_historical']:
			strategy = Strategy(
				name=f"Test {source}",
				strategy_type="iron_condor",
				symbol="SPY",
				parameters={},
				data_source=source
			)
			db_session.add(strategy)
		db_session.commit()
		
		# Invalid value should fail
		strategy = Strategy(
			name="Invalid Source",
			strategy_type="iron_condor",
			symbol="SPY",
			parameters={},
			data_source="invalid_source"
		)
		db_session.add(strategy)
		
		with pytest.raises(Exception):
			db_session.commit()


class TestDatabaseSchema:
	"""Test database schema and table creation."""
	
	def test_ib_tables_exist(self, db_session):
		"""Test that all IB tables are created."""
		inspector = inspect(engine)
		tables = inspector.get_table_names()
		
		required_tables = [
			'ib_settings',
			'options_data_cache',
			'historical_options_data',
			'ib_connection_log'
		]
		
		for table in required_tables:
			assert table in tables, f"Table {table} not found in database"
	
	def test_ib_settings_columns(self, db_session):
		"""Test ib_settings table columns."""
		inspector = inspect(engine)
		columns = {col['name']: col for col in inspector.get_columns('ib_settings')}
		
		expected_columns = [
			'id', 'user_id', 'host', 'port', 'client_id', 'account',
			'market_data_type', 'auto_connect', 'encrypted_credentials',
			'created_at', 'updated_at'
		]
		
		for col_name in expected_columns:
			assert col_name in columns, f"Column {col_name} not found in ib_settings"
	
	def test_options_cache_indexes(self, db_session):
		"""Test indexes on options_data_cache table."""
		inspector = inspect(engine)
		indexes = inspector.get_indexes('options_data_cache')
		
		index_names = [idx['name'] for idx in indexes]
		assert 'idx_options_cache_symbol' in index_names
		assert 'idx_options_cache_timestamp' in index_names
	
	def test_strategy_modifications(self, db_session):
		"""Test modifications to strategies table."""
		inspector = inspect(engine)
		columns = {col['name']: col for col in inspector.get_columns('strategies')}
		
		# Check new columns exist
		assert 'data_source' in columns
		assert 'ib_snapshot' in columns
		
		# Check data_source has proper type
		data_source_col = columns['data_source']
		assert data_source_col['type'].python_type == str