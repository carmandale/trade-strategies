"""Test configuration and fixtures for pytest."""
import os
import pytest
import tempfile
import subprocess
import time
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Configure test environment with PostgreSQL database."""
    # Check if we're in CI environment (DATABASE_URL already set)
    if 'DATABASE_URL' in os.environ and 'CI' in os.environ:
        # CI environment - use existing DATABASE_URL
        yield
    else:
        # Local environment - use Docker PostgreSQL for tests
        test_env = {
            'DATABASE_URL': 'postgresql://testuser:testpass@localhost:5433/test_trade_strategies',
            'DB_NAME': 'test_trade_strategies',
            'DATABASE_ECHO': 'false',
            'AUTO_CREATE_TABLES': 'true',
            'OPENAI_API_KEY': 'test-key-12345',  # Provide test API key
            'OPENAI_MODEL': 'gpt-4'
        }
        
        with patch.dict(os.environ, test_env):
            yield


@pytest.fixture(scope="session")
def ensure_test_db_running():
    """Ensure PostgreSQL test database is running via Docker."""
    # Skip in CI environment
    if 'CI' in os.environ:
        return
    
    # Check if test database is already running
    try:
        test_engine = create_engine(
            'postgresql://testuser:testpass@localhost:5433/test_trade_strategies',
            poolclass=NullPool
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        return  # Database already running
    except:
        pass  # Database not running, start it
    
    # Start PostgreSQL test database
    print("Starting PostgreSQL test database...")
    subprocess.run(
        ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
        check=True,
        capture_output=True
    )
    
    # Wait for database to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            test_engine = create_engine(
                'postgresql://testuser:testpass@localhost:5433/test_trade_strategies',
                poolclass=NullPool
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            test_engine.dispose()
            print("PostgreSQL test database ready!")
            break
        except:
            if i == max_retries - 1:
                raise RuntimeError("PostgreSQL test database failed to start")
            time.sleep(1)


@pytest.fixture(scope="function")
def test_db_engine(ensure_test_db_running):
    """Create a test database engine using PostgreSQL."""
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL', 'postgresql://testuser:testpass@localhost:5433/test_trade_strategies')
    
    # Create PostgreSQL test database connection
    engine = create_engine(
        database_url,
        poolclass=NullPool,
        echo=False
    )
    
    # Import models to create tables
    try:
        from database.models import Base
        # Drop all tables first to ensure clean state
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    except ImportError:
        # If models don't exist yet, that's okay
        pass
    
    yield engine
    
    # Cleanup
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def mock_db_session():
    """Create a mock database session for tests that don't need real DB."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session.query.return_value.all.return_value = []
    mock_session.execute.return_value.scalar.return_value = 1
    mock_session.execute.return_value.fetchall.return_value = []
    mock_session.execute.return_value.fetchone.return_value = None
    
    yield mock_session


@pytest.fixture(autouse=True)
def patch_database_config():
    """Patch database configuration to use test settings."""
    # Create mock objects
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session.query.return_value.all.return_value = []
    mock_session.execute.return_value.scalar.return_value = 1
    mock_session.execute.return_value.fetchall.return_value = []
    mock_session.execute.return_value.fetchone.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.close.return_value = None
    
    mock_connection = MagicMock()
    mock_connection.execute.return_value.scalar.return_value = 1
    mock_connection.execute.return_value.fetchall.return_value = []
    mock_connection.execute.return_value.fetchone.return_value = None
    
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mock_engine.begin.return_value.__enter__.return_value = mock_connection
    
    def mock_get_db_func():
        yield mock_session
    
    # Basic patching of database configuration
    patches = [
        patch('database.config.engine', mock_engine),
        patch('database.config.SessionLocal', return_value=mock_session),
        patch('database.config.get_db', side_effect=mock_get_db_func),
        # Patch model methods that access the database
        patch('database.models.AIUsageLog.get_usage_stats', return_value={
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_response_time": 0.0,
            "success_rate": 100.0
        }),
    ]
    
    # Start all patches
    for p in patches:
        p.start()
    
    yield {
        'engine': mock_engine,
        'session': mock_session,
        'connection': mock_connection
    }
    
    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture
def sample_strategy_data():
    """Sample strategy data for testing."""
    return {
        "id": "test-strategy-1",
        "name": "Test Iron Condor",
        "strategy_type": "iron_condor",
        "timeframe": "daily",
        "underlying": "SPX",
        "parameters": {
            "put_strike_pct": 0.98,
            "put_protection_pct": 0.975,
            "call_strike_pct": 1.02,
            "call_protection_pct": 1.025,
            "target_credit": 1.50
        },
        "is_active": True
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "symbol": "SPX",
        "price": 4500.00,
        "timestamp": "2024-01-01T12:00:00Z",
        "volume": 1000000,
        "open": 4495.00,
        "high": 4510.00,
        "low": 4490.00,
        "change": 5.00,
        "change_percent": 0.11
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "id": "test-trade-1",
        "strategy_id": "test-strategy-1",
        "entry_date": "2024-01-01",
        "expiration_date": "2024-01-01",
        "underlying_price_at_entry": 4500.00,
        "status": "closed",
        "put_strike": 4410.00,
        "put_protection": 4387.50,
        "call_strike": 4590.00,
        "call_protection": 4612.50,
        "credit_received": 1.50,
        "closing_cost": 0.25,
        "profit_loss": 1.25
    }