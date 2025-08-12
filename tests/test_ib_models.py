"""Tests for Interactive Brokers integration database models."""
import pytest
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from database.config import SessionLocal, engine
from database.models import (
	IBSettings,
	OptionsDataCache,
	HistoricalOptionsData,
	IBConnectionLog,
	Strategy
)


class TestIBSettings:
	"""Test IBSettings model."""
	
	@pytest.mark.integration
	def test_ib_settings_creation(self):
		"""Test creating IB settings record."""
		with SessionLocal() as db:
			settings = IBSettings(
				host="127.0.0.1",
				port=7497,
				client_id=1,
				account="DU123456",
				market_data_type=1,
				auto_connect=True,
				encrypted_credentials="encrypted_password_here"
			)
			db.add(settings)
			db.commit()
			
			assert settings.id is not None
			assert settings.host == "127.0.0.1"
			assert settings.port == 7497
			assert settings.account == "DU123456"
			assert settings.auto_connect is True
			
			# Clean up
			db.delete(settings)
			db.commit()
	
	@pytest.mark.integration
	def test_ib_settings_defaults(self):
		"""Test IB settings default values."""
		with SessionLocal() as db:
			settings = IBSettings(account="TEST123")
			db.add(settings)
			db.commit()
			
			assert settings.host == "127.0.0.1"
			assert settings.port == 7497
			assert settings.client_id == 1
			assert settings.market_data_type == 1
			assert settings.auto_connect is False
			
			# Clean up
			db.delete(settings)
			db.commit()
	
	@pytest.mark.integration
	def test_ib_settings_update(self):
		"""Test updating IB settings."""
		with SessionLocal() as db:
			settings = IBSettings(account="TEST123")
			db.add(settings)
			db.commit()
			
			settings.port = 4001
			settings.auto_connect = True
			db.commit()
			
			updated = db.query(IBSettings).filter_by(account="TEST123").first()
			assert updated.port == 4001
			assert updated.auto_connect is True
			
			# Clean up
			db.delete(settings)
			db.commit()
	
	@pytest.mark.integration
	def test_ib_settings_to_dict(self):
		"""Test converting IB settings to dictionary."""
		with SessionLocal() as db:
			settings = IBSettings(
				account="TEST123",
				host="192.168.1.100",
				port=4002
			)
			db.add(settings)
			db.commit()
			
			data = settings.to_dict()
			assert data['account'] == "TEST123"
			assert data['host'] == "192.168.1.100"
			assert data['port'] == 4002
			assert 'created_at' in data
			assert 'updated_at' in data
			
			# Clean up
			db.delete(settings)
			db.commit()


class TestOptionsDataCache:
	"""Test OptionsDataCache model."""
	
	@pytest.mark.integration
	def test_options_cache_creation(self):
		"""Test creating options cache entry."""
		with SessionLocal() as db:
			cache = OptionsDataCache(
				symbol="SPY",
				strike=Decimal("450.00"),
				expiration=datetime(2025, 1, 17),
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
			db.add(cache)
			db.commit()
			
			assert cache.id is not None
			assert cache.symbol == "SPY"
			assert cache.strike == Decimal("450.00")
			assert cache.delta == Decimal("0.5500")
			
			# Clean up
			db.delete(cache)
			db.commit()
	
	@pytest.mark.integration
	def test_options_cache_unique_constraint(self):
		"""Test unique constraint on options cache."""
		with SessionLocal() as db:
			timestamp = datetime.now(timezone.utc)
			cache1 = OptionsDataCache(
				symbol="SPY",
				strike=Decimal("450.00"),
				expiration=datetime(2025, 1, 17),
				option_type="call",
				timestamp=timestamp
			)
			db.add(cache1)
			db.commit()
			
			# Attempt to add duplicate should fail
			cache2 = OptionsDataCache(
				symbol="SPY",
				strike=Decimal("450.00"),
				expiration=datetime(2025, 1, 17),
				option_type="call",
				timestamp=timestamp
			)
			db.add(cache2)
			
			with pytest.raises(IntegrityError):
				db.commit()
			
			db.rollback()
			
			# Clean up
			db.delete(cache1)
			db.commit()
	
	@pytest.mark.integration
	def test_get_cached_data(self):
		"""Test retrieving cached options data."""
		with SessionLocal() as db:
			# Add valid cache entry
			valid_cache = OptionsDataCache(
				symbol="SPY",
				strike=Decimal("450.00"),
				expiration=datetime(2025, 1, 17),
				option_type="call",
				bid=Decimal("5.25"),
				ask=Decimal("5.35"),
				timestamp=datetime.now(timezone.utc),
				ttl_seconds=300  # 5 minutes
			)
			db.add(valid_cache)
			db.commit()
			
			# Should return valid entry
			data = OptionsDataCache.get_cached_data(
				db, 
				"SPY", 
				Decimal("450.00"),
				datetime(2025, 1, 17),
				"call"
			)
			assert data is not None
			assert data.bid == Decimal("5.25")
			
			# Clean up
			db.delete(valid_cache)
			db.commit()
	
	@pytest.mark.integration
	def test_cleanup_expired_cache(self):
		"""Test cleaning up expired cache entries."""
		with SessionLocal() as db:
			# Clean up any existing data first
			db.query(OptionsDataCache).delete()
			db.commit()
			
			# Add expired entries
			for i in range(3):
				cache = OptionsDataCache(
					symbol="SPY",
					strike=Decimal(f"450.{i:02d}"),
					expiration=datetime(2025, 1, 17),
					option_type="call",
					timestamp=datetime.now(timezone.utc) - timedelta(seconds=400),
					ttl_seconds=5
				)
				db.add(cache)
			
			# Add valid entry
			valid_cache = OptionsDataCache(
				symbol="SPY",
				strike=Decimal("451.00"),
				expiration=datetime(2025, 1, 17),
				option_type="call",
				timestamp=datetime.now(timezone.utc),
				ttl_seconds=300
			)
			db.add(valid_cache)
			db.commit()
			
			# Cleanup expired
			count = OptionsDataCache.cleanup_expired(db)
			db.commit()
			
			assert count == 3
			remaining = db.query(OptionsDataCache).count()
			assert remaining == 1
			
			# Clean up
			db.query(OptionsDataCache).delete()
			db.commit()


class TestHistoricalOptionsData:
	"""Test HistoricalOptionsData model."""
	
	@pytest.mark.integration
	def test_historical_data_creation(self):
		"""Test creating historical options data."""
		with SessionLocal() as db:
			historical = HistoricalOptionsData(
				symbol="SPY",
				strike=Decimal("450.00"),
				expiration=datetime(2025, 1, 17),
				option_type="call",
				date=datetime(2025, 1, 10),
				open=Decimal("5.00"),
				high=Decimal("5.50"),
				low=Decimal("4.95"),
				close=Decimal("5.25"),
				volume=10000,
				open_interest=50000,
				implied_volatility=Decimal("0.1850")
			)
			db.add(historical)
			db.commit()
			
			assert historical.id is not None
			assert historical.close == Decimal("5.25")
			assert historical.volume == 10000
			
			# Clean up
			db.delete(historical)
			db.commit()
	
	@pytest.mark.integration
	def test_historical_data_unique_constraint(self):
		"""Test unique constraint on historical data."""
		with SessionLocal() as db:
			historical1 = HistoricalOptionsData(
				symbol="SPY",
				strike=Decimal("450.00"),
				expiration=datetime(2025, 1, 17),
				option_type="call",
				date=datetime(2025, 1, 10),
				close=Decimal("5.25")
			)
			db.add(historical1)
			db.commit()
			
			# Duplicate should fail
			historical2 = HistoricalOptionsData(
				symbol="SPY",
				strike=Decimal("450.00"),
				expiration=datetime(2025, 1, 17),
				option_type="call",
				date=datetime(2025, 1, 10),
				close=Decimal("5.30")
			)
			db.add(historical2)
			
			with pytest.raises(IntegrityError):
				db.commit()
			
			db.rollback()
			
			# Clean up
			db.delete(historical1)
			db.commit()
	
	@pytest.mark.integration
	def test_get_historical_range(self):
		"""Test retrieving historical data for date range."""
		with SessionLocal() as db:
			# Add data for multiple dates
			for i in range(5):
				historical = HistoricalOptionsData(
					symbol="SPY",
					strike=Decimal("450.00"),
					expiration=datetime(2025, 1, 17),
					option_type="call",
					date=datetime(2025, 1, 10 + i),
					close=Decimal(f"5.{i}0")
				)
				db.add(historical)
			db.commit()
			
			# Query range
			data = HistoricalOptionsData.get_date_range(
				db,
				"SPY",
				datetime(2025, 1, 12),
				datetime(2025, 1, 14)
			)
			
			assert len(data) == 3
			assert all(d.symbol == "SPY" for d in data)
			
			# Clean up
			db.query(HistoricalOptionsData).filter_by(symbol="SPY").delete()
			db.commit()


class TestIBConnectionLog:
	"""Test IBConnectionLog model."""
	
	@pytest.mark.integration
	def test_connection_log_creation(self):
		"""Test creating connection log entries."""
		with SessionLocal() as db:
			log = IBConnectionLog(
				event_type="connect",
				status="success",
				account="DU123456",
				event_metadata={"server_version": 176, "connection_time": 1.5}
			)
			db.add(log)
			db.commit()
			
			assert log.id is not None
			assert log.event_type == "connect"
			assert log.status == "success"
			assert log.event_metadata["server_version"] == 176
			
			# Clean up
			db.delete(log)
			db.commit()
	
	@pytest.mark.integration
	def test_connection_log_error(self):
		"""Test logging connection errors."""
		with SessionLocal() as db:
			log = IBConnectionLog(
				event_type="connect",
				status="error",
				error_message="Connection refused: IB Gateway not running",
				event_metadata={"attempted_port": 7497}
			)
			db.add(log)
			db.commit()
			
			assert log.error_message == "Connection refused: IB Gateway not running"
			assert log.event_metadata["attempted_port"] == 7497
			
			# Clean up
			db.delete(log)
			db.commit()
	
	@pytest.mark.integration
	def test_get_recent_logs(self):
		"""Test retrieving recent connection logs."""
		with SessionLocal() as db:
			# Add multiple log entries
			for i in range(5):
				log = IBConnectionLog(
					event_type="heartbeat",
					status="success",
					account="DU123456"
				)
				db.add(log)
			db.commit()
			
			logs = IBConnectionLog.get_recent_logs(db, limit=3)
			assert len(logs) == 3
			# Logs should be ordered by created_at DESC
			assert logs[0].created_at >= logs[1].created_at
			
			# Clean up
			db.query(IBConnectionLog).delete()
			db.commit()


class TestStrategyModifications:
	"""Test modifications to Strategy model for IB integration."""
	
	@pytest.mark.integration
	def test_strategy_data_source(self):
		"""Test strategy data_source field."""
		with SessionLocal() as db:
			strategy = Strategy(
				name="Test Iron Condor",
				strategy_type="iron_condor",
				symbol="SPY",
				parameters={},
				data_source="ib_realtime"
			)
			db.add(strategy)
			db.commit()
			
			assert strategy.data_source == "ib_realtime"
			
			# Clean up
			db.delete(strategy)
			db.commit()
	
	@pytest.mark.integration
	def test_strategy_ib_snapshot(self):
		"""Test strategy ib_snapshot JSONB field."""
		with SessionLocal() as db:
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
			db.add(strategy)
			db.commit()
			
			# Retrieve and verify
			saved = db.query(Strategy).filter_by(name="Test Strategy").first()
			assert saved.ib_snapshot is not None
			assert saved.ib_snapshot["underlying_price"] == 450.25
			assert saved.ib_snapshot["options_data"][0]["greeks"]["delta"] == 0.55
			
			# Clean up
			db.delete(strategy)
			db.commit()


class TestDatabaseSchema:
	"""Test database schema and table creation."""
	
	@pytest.mark.integration
	def test_ib_tables_exist(self):
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
	
	@pytest.mark.integration
	def test_ib_settings_columns(self):
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
	
	@pytest.mark.integration
	def test_options_cache_indexes(self):
		"""Test indexes on options_data_cache table."""
		inspector = inspect(engine)
		indexes = inspector.get_indexes('options_data_cache')
		
		index_names = [idx['name'] for idx in indexes]
		assert 'idx_options_cache_symbol' in index_names
		assert 'idx_options_cache_timestamp' in index_names
	
	@pytest.mark.integration
	def test_strategy_modifications(self):
		"""Test modifications to strategies table."""
		inspector = inspect(engine)
		columns = {col['name']: col for col in inspector.get_columns('strategies')}
		
		# Check new columns exist
		assert 'data_source' in columns
		assert 'ib_snapshot' in columns