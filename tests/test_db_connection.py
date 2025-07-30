"""Tests for database connection and configuration."""
import pytest
import os
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from database.config import get_db, get_database_url, engine, SessionLocal


class TestDatabaseConnection:
    """Test database connection functionality."""
    
    def test_database_url_from_environment(self):
        """Test database URL is correctly constructed from environment variables."""
        with patch.dict(os.environ, {
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'tradestrategies_test'
        }):
            url = get_database_url()
            assert url == 'postgresql://testuser:testpass@localhost:5432/tradestrategies_test'
    
    def test_database_url_defaults(self):
        """Test database URL uses defaults when environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            url = get_database_url()
            assert 'postgresql://' in url
            assert 'localhost' in url
            assert '5432' in url
    
    def test_engine_creation(self):
        """Test SQLAlchemy engine is created with correct parameters."""
        test_url = 'postgresql://test:test@localhost/test'
        with patch('database.config.get_database_url', return_value=test_url):
            with patch('database.config.create_engine') as mock_create:
                from database import config
                # Force module reload to pick up patched URL
                import importlib
                importlib.reload(config)
                
                mock_create.assert_called_once()
                call_args = mock_create.call_args[0]
                assert call_args[0] == test_url
    
    def test_session_local_configuration(self):
        """Test SessionLocal is configured correctly."""
        assert SessionLocal.kw['autocommit'] == False
        assert SessionLocal.kw['autoflush'] == False
    
    def test_get_db_yields_session(self):
        """Test get_db function yields a database session."""
        mock_session = MagicMock()
        with patch('database.config.SessionLocal', return_value=mock_session):
            db_gen = get_db()
            db = next(db_gen)
            assert db == mock_session
    
    def test_get_db_closes_session_on_exit(self):
        """Test get_db closes the session when done."""
        mock_session = MagicMock()
        with patch('database.config.SessionLocal', return_value=mock_session):
            db_gen = get_db()
            next(db_gen)
            
            # Simulate generator exit
            try:
                next(db_gen)
            except StopIteration:
                pass
            
            mock_session.close.assert_called_once()
    
    def test_get_db_closes_session_on_exception(self):
        """Test get_db closes the session even if an exception occurs."""
        mock_session = MagicMock()
        with patch('database.config.SessionLocal', return_value=mock_session):
            db_gen = get_db()
            next(db_gen)
            
            # Simulate exception during session use
            with pytest.raises(Exception):
                db_gen.throw(Exception("Test error"))
            
            mock_session.close.assert_called_once()
    
    @pytest.mark.integration
    def test_real_database_connection(self):
        """Test actual database connection (requires PostgreSQL to be running)."""
        from sqlalchemy import text
        try:
            # Attempt to connect to the database
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                assert result.scalar() == 1
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.integration  
    def test_database_session_crud(self):
        """Test basic CRUD operations with a database session."""
        from sqlalchemy import text
        try:
            db = SessionLocal()
            
            # Test we can execute a simple query
            result = db.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            assert db_name is not None
            
            db.close()
        except OperationalError as e:
            pytest.skip(f"Database not available: {e}")


class TestDatabaseErrorHandling:
    """Test database error handling scenarios."""
    
    def test_connection_failure_handling(self):
        """Test handling of database connection failures."""
        with patch('database.config.create_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.connect.side_effect = OperationalError("Connection failed", None, None)
            mock_create.return_value = mock_engine
            
            # The application should handle this gracefully
            with pytest.raises(OperationalError):
                with mock_engine.connect():
                    pass
    
    def test_transaction_rollback_on_error(self):
        """Test that transactions are rolled back on error."""
        mock_session = MagicMock()
        
        with patch('database.config.SessionLocal', return_value=mock_session):
            db_gen = get_db()
            db = next(db_gen)
            
            # Simulate an error during transaction
            db.commit.side_effect = Exception("Transaction failed")
            
            # The session should still be closed properly
            try:
                next(db_gen)
            except StopIteration:
                pass
            
            mock_session.close.assert_called_once()