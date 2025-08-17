"""Tests for SQLAlchemy model CRUD operations."""
import pytest
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from database.config import SessionLocal
from database.models import Strategy, Backtest, Trade, MarketDataCache


class TestStrategyModel:
    """Test Strategy model CRUD operations."""
    
    @pytest.mark.integration
    def test_create_strategy(self):
        """Test creating a new strategy."""
        with SessionLocal() as db:
            import uuid
            from datetime import datetime
            strategy = Strategy(
                id=uuid.uuid4(),  # Explicitly set ID for mock testing
                name="Test Iron Condor",
                strategy_type="iron_condor",
                symbol="SPY",
                parameters={
                    "put_short_delta": 0.16,
                    "call_short_delta": 0.16,
                    "strikes": [420, 425, 430, 435],
                    "dte": 7
                },
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            
            db.add(strategy)
            db.commit()
            db.refresh(strategy)
            
            # Verify creation
            assert strategy.id is not None
            assert strategy.name == "Test Iron Condor"
            assert strategy.strategy_type == "iron_condor"
            assert strategy.symbol == "SPY"
            assert strategy.is_active is True
            assert strategy.parameters["strikes"] == [420, 425, 430, 435]
            assert strategy.created_at is not None
            
            # Clean up
            db.delete(strategy)
            db.commit()
    
    @pytest.mark.integration
    def test_read_strategy(self):
        """Test reading an existing strategy."""
        with SessionLocal() as db:
            # Create strategy
            strategy = Strategy(
                name="Read Test Strategy",
                strategy_type="bull_call",
                parameters={"strikes": [400, 410]}
            )
            db.add(strategy)
            db.commit()
            strategy_id = strategy.id
            
            # Read strategy
            found_strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            assert found_strategy is not None
            assert found_strategy.name == "Read Test Strategy"
            assert found_strategy.strategy_type == "bull_call"
            
            # Clean up
            db.delete(found_strategy)
            db.commit()
    
    @pytest.mark.integration
    def test_update_strategy(self):
        """Test updating an existing strategy."""
        with SessionLocal() as db:
            # Create strategy
            strategy = Strategy(
                name="Update Test",
                strategy_type="iron_condor",
                parameters={"strikes": [420, 425, 430, 435]}
            )
            db.add(strategy)
            db.commit()
            
            # Update strategy
            strategy.name = "Updated Strategy Name"
            strategy.parameters = {"strikes": [415, 420, 425, 430]}
            strategy.is_active = False
            db.commit()
            
            # Verify update
            db.refresh(strategy)
            assert strategy.name == "Updated Strategy Name"
            assert strategy.parameters["strikes"] == [415, 420, 425, 430]
            assert strategy.is_active is False
            assert strategy.updated_at is not None
            
            # Clean up
            db.delete(strategy)
            db.commit()
    
    @pytest.mark.integration
    def test_delete_strategy(self):
        """Test deleting a strategy."""
        with SessionLocal() as db:
            # Create strategy
            strategy = Strategy(
                name="Delete Test",
                strategy_type="butterfly",
                parameters={"strikes": [420, 425, 430]}
            )
            db.add(strategy)
            db.commit()
            strategy_id = strategy.id
            
            # Delete strategy
            db.delete(strategy)
            db.commit()
            
            # Verify deletion
            found_strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            assert found_strategy is None


class TestBacktestModel:
    """Test Backtest model CRUD operations."""
    
    @pytest.mark.integration
    def test_create_backtest(self):
        """Test creating a new backtest."""
        with SessionLocal() as db:
            # Create parent strategy first
            strategy = Strategy(
                name="Backtest Parent Strategy",
                strategy_type="iron_condor",
                parameters={"strikes": [420, 425, 430, 435]}
            )
            db.add(strategy)
            db.commit()
            
            # Create backtest
            backtest = Backtest(
                strategy_id=strategy.id,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
                timeframe="daily",
                parameters={
                    "capital": 10000,
                    "max_positions": 5
                },
                results={
                    "total_pnl": 1250.75,
                    "win_rate": 0.67,
                    "sharpe_ratio": 1.35,
                    "trades_count": 15
                }
            )
            
            db.add(backtest)
            db.commit()
            db.refresh(backtest)
            
            # Verify creation
            assert backtest.id is not None
            assert backtest.strategy_id == strategy.id
            assert backtest.timeframe == "daily"
            assert backtest.results["total_pnl"] == 1250.75
            assert backtest.results["win_rate"] == 0.67
            assert backtest.created_at is not None
            
            # Clean up
            db.delete(backtest)
            db.delete(strategy)
            db.commit()
    
    @pytest.mark.integration
    def test_backtest_strategy_relationship(self):
        """Test backtest to strategy relationship."""
        with SessionLocal() as db:
            # Create strategy
            strategy = Strategy(
                name="Relationship Test Strategy",
                strategy_type="iron_condor",
                parameters={"strikes": [420, 425, 430, 435]}
            )
            db.add(strategy)
            db.commit()
            
            # Create backtest
            backtest = Backtest(
                strategy_id=strategy.id,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
                timeframe="weekly",
                parameters={"capital": 5000},
                results={"total_pnl": 500}
            )
            db.add(backtest)
            db.commit()
            
            # Test relationship
            assert backtest.strategy is not None
            assert backtest.strategy.name == "Relationship Test Strategy"
            assert len(strategy.backtests) == 1
            assert strategy.backtests[0].timeframe == "weekly"
            
            # Clean up
            db.delete(backtest)
            db.delete(strategy)
            db.commit()


class TestTradeModel:
    """Test Trade model CRUD operations."""
    
    @pytest.mark.integration
    def test_create_trade(self):
        """Test creating a new trade."""
        with SessionLocal() as db:
            trade = Trade(
                trade_date=datetime(2025, 1, 15),
                entry_time=datetime(2025, 1, 15, 9, 30),
                symbol="SPY",
                strategy_type="iron_condor",
                strikes=[420, 425, 430, 435],
                contracts=10,
                entry_price=Decimal("426.50"),
                credit_debit=Decimal("1.25"),
                status="open",
                notes="Morning entry at market open"
            )
            
            db.add(trade)
            db.commit()
            db.refresh(trade)
            
            # Verify creation
            assert trade.id is not None
            assert trade.symbol == "SPY"
            assert trade.strategy_type == "iron_condor"
            assert trade.strikes == [420, 425, 430, 435]
            assert trade.contracts == 10
            assert trade.entry_price == Decimal("426.50")
            assert trade.credit_debit == Decimal("1.25")
            assert trade.status == "open"
            assert trade.notes == "Morning entry at market open"
            assert trade.created_at is not None
            
            # Clean up
            db.delete(trade)
            db.commit()
    
    @pytest.mark.integration
    def test_complete_trade_cycle(self):
        """Test complete trade lifecycle from open to closed."""
        with SessionLocal() as db:
            # Create open trade
            trade = Trade(
                trade_date=datetime(2025, 1, 15),
                entry_time=datetime(2025, 1, 15, 9, 30),
                symbol="SPY",
                strategy_type="bull_call",
                strikes=[420, 430],
                contracts=5,
                entry_price=Decimal("425.00"),
                credit_debit=Decimal("2.50"),
                status="open"
            )
            
            db.add(trade)
            db.commit()
            
            # Close the trade
            trade.exit_time = datetime(2025, 1, 15, 15, 30)
            trade.exit_price = Decimal("427.75")
            trade.realized_pnl = Decimal("137.50")  # (427.75 - 425.00) * 5 * 10 - fees
            trade.status = "closed"
            trade.notes = "Closed at 3:30 PM with profit"
            
            db.commit()
            db.refresh(trade)
            
            # Verify closure
            assert trade.status == "closed"
            assert trade.exit_price == Decimal("427.75")
            assert trade.realized_pnl == Decimal("137.50")
            assert trade.exit_time is not None
            
            # Clean up
            db.delete(trade)
            db.commit()
    
    @pytest.mark.integration
    def test_trade_with_strategy_relationship(self):
        """Test trade linked to a strategy."""
        with SessionLocal() as db:
            # Create strategy
            strategy = Strategy(
                name="Trade Strategy Link",
                strategy_type="iron_condor",
                parameters={"strikes": [420, 425, 430, 435]}
            )
            db.add(strategy)
            db.commit()
            
            # Create trade linked to strategy
            trade = Trade(
                strategy_id=strategy.id,
                trade_date=datetime(2025, 1, 15),
                entry_time=datetime(2025, 1, 15, 10, 0),
                symbol="SPY",
                strategy_type="iron_condor",
                strikes=[420, 425, 430, 435],
                contracts=3,
                entry_price=Decimal("426.25"),
                credit_debit=Decimal("1.15")
            )
            
            db.add(trade)
            db.commit()
            
            # Test relationship
            assert trade.strategy is not None
            assert trade.strategy.name == "Trade Strategy Link"
            assert len(strategy.trades) == 1
            assert strategy.trades[0].contracts == 3
            
            # Clean up
            db.delete(trade)
            db.delete(strategy)
            db.commit()


class TestMarketDataCacheModel:
    """Test MarketDataCache model CRUD operations."""
    
    @pytest.mark.integration
    def test_create_market_data_cache(self):
        """Test creating market data cache entry."""
        with SessionLocal() as db:
            cache_entry = MarketDataCache(
                symbol="SPY",
                data_date=datetime(2025, 1, 15),
                data_type="intraday",
                data={
                    "open": 425.50,
                    "high": 428.75,
                    "low": 424.25,
                    "close": 427.80,
                    "volume": 45678900,
                    "bars": [
                        {"time": "09:30", "price": 425.50, "volume": 156789},
                        {"time": "09:31", "price": 425.65, "volume": 134567}
                    ]
                },
                expires_at=datetime(2025, 1, 16, 0, 0)
            )
            
            db.add(cache_entry)
            db.commit()
            db.refresh(cache_entry)
            
            # Verify creation
            assert cache_entry.id is not None
            assert cache_entry.symbol == "SPY"
            assert cache_entry.data_type == "intraday"
            assert cache_entry.data["close"] == 427.80
            assert cache_entry.data["volume"] == 45678900
            assert len(cache_entry.data["bars"]) == 2
            assert cache_entry.expires_at is not None
            
            # Clean up
            db.delete(cache_entry)
            db.commit()
    
    @pytest.mark.integration
    def test_unique_constraint_market_data(self):
        """Test unique constraint on symbol, data_date, data_type."""
        with SessionLocal() as db:
            # Create first entry
            cache1 = MarketDataCache(
                symbol="SPY",
                data_date=datetime(2025, 1, 15),
                data_type="daily",
                data={"close": 427.80},
                expires_at=datetime(2025, 1, 16)
            )
            db.add(cache1)
            db.commit()
            
            # Try to create duplicate entry (should fail)
            cache2 = MarketDataCache(
                symbol="SPY",
                data_date=datetime(2025, 1, 15),
                data_type="daily",
                data={"close": 428.00},
                expires_at=datetime(2025, 1, 16)
            )
            db.add(cache2)
            
            with pytest.raises(IntegrityError):
                db.commit()
            
            # Clean up
            db.rollback()
            db.delete(cache1)
            db.commit()


class TestModelConstraints:
    """Test model constraints and validation."""
    
    @pytest.mark.integration
    def test_strategy_required_fields(self):
        """Test that strategy required fields are enforced."""
        with SessionLocal() as db:
            # Missing name (should fail)
            strategy = Strategy(
                strategy_type="iron_condor",
                parameters={"strikes": [420, 425]}
            )
            db.add(strategy)
            
            with pytest.raises(IntegrityError):
                db.commit()
            
            db.rollback()
    
    @pytest.mark.integration
    def test_trade_required_fields(self):
        """Test that trade required fields are enforced."""
        with SessionLocal() as db:
            # Missing entry_time (should fail)
            trade = Trade(
                trade_date=datetime(2025, 1, 15),
                symbol="SPY",
                strategy_type="iron_condor",
                strikes=[420, 425],
                contracts=5,
                entry_price=Decimal("425.00"),
                credit_debit=Decimal("1.25")
            )
            db.add(trade)
            
            with pytest.raises(IntegrityError):
                db.commit()
            
            db.rollback()
    
    @pytest.mark.integration
    def test_foreign_key_constraints(self):
        """Test foreign key constraint enforcement."""
        with SessionLocal() as db:
            # Try to create backtest with non-existent strategy_id
            import uuid
            fake_strategy_id = uuid.uuid4()
            
            backtest = Backtest(
                strategy_id=fake_strategy_id,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
                timeframe="daily",
                parameters={"capital": 1000},
                results={"pnl": 100}
            )
            db.add(backtest)
            
            with pytest.raises(IntegrityError):
                db.commit()
            
            db.rollback()