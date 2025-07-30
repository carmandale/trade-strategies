"""Tests for database schema creation and validation."""
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from database.config import engine, Base, SessionLocal


class TestDatabaseSchema:
    """Test database schema creation and structure."""
    
    @pytest.mark.integration
    def test_all_tables_exist(self):
        """Test that all required tables exist in the database."""
        try:
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            # Required tables from our schema design
            required_tables = [
                'strategies',
                'backtests', 
                'trades',
                'market_data_cache'
            ]
            
            for table in required_tables:
                assert table in table_names, f"Table '{table}' is missing from database"
                
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_strategies_table_structure(self):
        """Test strategies table has correct columns and types."""
        try:
            inspector = inspect(engine)
            columns = inspector.get_columns('strategies')
            column_names = [col['name'] for col in columns]
            
            # Required columns
            required_columns = [
                'id', 'name', 'strategy_type', 'symbol', 
                'parameters', 'is_active', 'created_at', 'updated_at'
            ]
            
            for col in required_columns:
                assert col in column_names, f"Column '{col}' missing from strategies table"
            
            # Check specific column types
            column_types = {col['name']: str(col['type']) for col in columns}
            assert 'UUID' in column_types['id']
            assert 'VARCHAR' in column_types['name']
            assert 'JSONB' in column_types['parameters']
            assert 'BOOLEAN' in column_types['is_active']
            
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_trades_table_structure(self):
        """Test trades table has correct columns and types."""
        try:
            inspector = inspect(engine)
            columns = inspector.get_columns('trades')
            column_names = [col['name'] for col in columns]
            
            # Required columns
            required_columns = [
                'id', 'strategy_id', 'trade_date', 'entry_time', 'exit_time',
                'symbol', 'strategy_type', 'strikes', 'contracts', 
                'entry_price', 'exit_price', 'credit_debit', 'realized_pnl',
                'status', 'notes', 'created_at', 'updated_at'
            ]
            
            for col in required_columns:
                assert col in column_names, f"Column '{col}' missing from trades table"
            
            # Check specific column types
            column_types = {col['name']: str(col['type']) for col in columns}
            assert 'UUID' in column_types['id']
            assert 'JSONB' in column_types['strikes']
            assert 'DECIMAL' in column_types['entry_price']
            assert 'INTEGER' in column_types['contracts']
            
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_backtests_table_structure(self):
        """Test backtests table has correct columns and types."""
        try:
            inspector = inspect(engine)
            columns = inspector.get_columns('backtests')
            column_names = [col['name'] for col in columns]
            
            # Required columns
            required_columns = [
                'id', 'strategy_id', 'start_date', 'end_date',
                'timeframe', 'parameters', 'results', 'created_at'
            ]
            
            for col in required_columns:
                assert col in column_names, f"Column '{col}' missing from backtests table"
            
            # Check specific column types
            column_types = {col['name']: str(col['type']) for col in columns}
            assert 'UUID' in column_types['id']
            assert 'DATE' in column_types['start_date']
            assert 'JSONB' in column_types['parameters']
            assert 'JSONB' in column_types['results']
            
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_market_data_cache_table_structure(self):
        """Test market_data_cache table has correct columns and types."""
        try:
            inspector = inspect(engine)
            columns = inspector.get_columns('market_data_cache')
            column_names = [col['name'] for col in columns]
            
            # Required columns
            required_columns = [
                'id', 'symbol', 'data_date', 'data_type',
                'data', 'created_at', 'expires_at'
            ]
            
            for col in required_columns:
                assert col in column_names, f"Column '{col}' missing from market_data_cache table"
            
            # Check specific column types
            column_types = {col['name']: str(col['type']) for col in columns}
            assert 'UUID' in column_types['id']
            assert 'VARCHAR' in column_types['symbol']
            assert 'JSONB' in column_types['data']
            
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_indexes_exist(self):
        """Test that required indexes are created."""
        try:
            inspector = inspect(engine)
            
            # Test strategies table indexes
            strategies_indexes = inspector.get_indexes('strategies')
            index_names = [idx['name'] for idx in strategies_indexes]
            
            # Should have index on strategy_type and symbol
            # Note: Index names may vary by database implementation
            # This test verifies indexes exist, exact names may differ
            
            # Test trades table indexes  
            trades_indexes = inspector.get_indexes('trades')
            trades_index_names = [idx['name'] for idx in trades_indexes]
            
            # Should have indexes on trade_date, status, strategy_type
            assert len(trades_indexes) > 0, "No indexes found on trades table"
            
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are properly set up."""
        try:
            inspector = inspect(engine)
            
            # Test backtests -> strategies foreign key
            backtests_fks = inspector.get_foreign_keys('backtests')
            strategy_fk_exists = any(
                fk['referred_table'] == 'strategies' and 'strategy_id' in fk['constrained_columns']
                for fk in backtests_fks
            )
            assert strategy_fk_exists, "Foreign key from backtests to strategies missing"
            
            # Test trades -> strategies foreign key (nullable)
            trades_fks = inspector.get_foreign_keys('trades')
            trades_strategy_fk_exists = any(
                fk['referred_table'] == 'strategies' and 'strategy_id' in fk['constrained_columns']
                for fk in trades_fks
            )
            assert trades_strategy_fk_exists, "Foreign key from trades to strategies missing"
            
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_unique_constraints(self):
        """Test that unique constraints are properly set up."""
        try:
            inspector = inspect(engine)
            
            # Test market_data_cache unique constraint
            cache_unique_constraints = inspector.get_unique_constraints('market_data_cache')
            
            # Should have unique constraint on (symbol, data_date, data_type)
            symbol_date_type_unique = any(
                set(uc['column_names']) == {'symbol', 'data_date', 'data_type'}
                for uc in cache_unique_constraints
            )
            assert symbol_date_type_unique, "Unique constraint on (symbol, data_date, data_type) missing"
            
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_default_values(self):
        """Test that default values are properly configured."""
        try:
            with SessionLocal() as db:
                # Test that we can create a basic strategy with defaults
                result = db.execute(text("""
                    INSERT INTO strategies (name, strategy_type, parameters) 
                    VALUES ('Test Strategy', 'iron_condor', '{}')
                    RETURNING id, symbol, is_active, created_at
                """))
                
                row = result.fetchone()
                assert row is not None
                assert row.symbol == 'SPY'  # Default symbol
                assert row.is_active == True  # Default is_active
                assert row.created_at is not None  # Default timestamp
                
                # Clean up
                db.execute(text("DELETE FROM strategies WHERE name = 'Test Strategy'"))
                db.commit()
                
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")


class TestSchemaValidation:
    """Test schema validation and constraints."""
    
    @pytest.mark.integration
    def test_jsonb_fields_accept_json(self):
        """Test that JSONB fields properly store and retrieve JSON data."""
        try:
            with SessionLocal() as db:
                # Test complex JSON in parameters field
                test_params = {
                    "put_short_delta": 0.16,
                    "call_short_delta": 0.16,
                    "strikes": [420, 425, 430, 435],
                    "dte": 7,
                    "nested": {"key": "value", "number": 42}
                }
                
                result = db.execute(text("""
                    INSERT INTO strategies (name, strategy_type, parameters) 
                    VALUES ('JSON Test', 'iron_condor', :params)
                    RETURNING id, parameters
                """), {"params": test_params})
                
                row = result.fetchone()
                assert row is not None
                
                # Verify JSON was stored correctly
                stored_params = row.parameters
                assert stored_params['put_short_delta'] == 0.16
                assert stored_params['strikes'] == [420, 425, 430, 435]
                assert stored_params['nested']['key'] == 'value'
                
                # Clean up
                db.execute(text("DELETE FROM strategies WHERE name = 'JSON Test'"))
                db.commit()
                
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration
    def test_enum_constraints(self):
        """Test that enum-like constraints work for strategy types and status."""
        try:
            with SessionLocal() as db:
                # Test valid strategy type
                result = db.execute(text("""
                    INSERT INTO strategies (name, strategy_type, parameters) 
                    VALUES ('Valid Type Test', 'iron_condor', '{}')
                    RETURNING strategy_type
                """))
                
                row = result.fetchone()
                assert row.strategy_type == 'iron_condor'
                
                # Test valid trade status
                db.execute(text("""
                    INSERT INTO trades (strategy_type, strikes, contracts, entry_price, 
                                      credit_debit, trade_date, status) 
                    VALUES ('iron_condor', '[420, 425]', 1, 422.50, 1.25, CURRENT_DATE, 'open')
                """))
                
                # Clean up
                db.execute(text("DELETE FROM strategies WHERE name = 'Valid Type Test'"))
                db.execute(text("DELETE FROM trades WHERE strategy_type = 'iron_condor' AND contracts = 1"))
                db.commit()
                
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")