"""Tests for market data collection service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pandas as pd
import numpy as np

from services.market_data_service import MarketDataCollector
from database.models import MarketDataSnapshot
from database.config import SessionLocal


class TestMarketDataCollector:
    """Test MarketDataCollector service."""
    
    @pytest.fixture
    def collector(self):
        """Create MarketDataCollector instance."""
        return MarketDataCollector()
    
    def test_get_current_spx_price(self, collector):
        """Test fetching current SPX price and movement."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock yfinance response
            mock_instance = Mock()
            mock_ticker.return_value = mock_instance
            mock_instance.info = {
                'regularMarketPrice': 5635.50,
                'regularMarketPreviousClose': 5618.25,
                'regularMarketChangePercent': 0.31
            }
            mock_instance.history.return_value = pd.DataFrame({
                'Close': [5618.25, 5635.50],
                'Volume': [2150000, 2200000]
            })
            
            result = collector.get_current_spx()
            
            assert result['price'] == Decimal('5635.50')
            assert result['change'] == Decimal('17.25')
            assert result['change_percent'] == Decimal('0.31')
            assert result['symbol'] == 'SPX'
    
    def test_get_vix_level_and_trend(self, collector):
        """Test fetching VIX level and calculating trend."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock VIX data
            mock_instance = Mock()
            mock_ticker.return_value = mock_instance
            mock_instance.info = {
                'regularMarketPrice': 14.2,
                'regularMarketPreviousClose': 15.1
            }
            # Mock 5-day history for trend
            mock_instance.history.return_value = pd.DataFrame({
                'Close': [16.5, 15.8, 15.3, 15.1, 14.2]
            })
            
            result = collector.get_vix_level()
            
            assert result['level'] == Decimal('14.2')
            assert result['change'] == Decimal('-0.9')
            assert result['trend'] == 'declining'  # VIX decreasing over 5 days
            assert result['percentile_rank'] < 50  # Low VIX level
    
    def test_get_volume_data(self, collector):
        """Test fetching and analyzing volume data."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock SPY volume data (proxy for SPX)
            mock_instance = Mock()
            mock_ticker.return_value = mock_instance
            
            # Mock 20-day volume history for average
            volumes = [2000000] * 19 + [2200000]  # 20 days
            mock_instance.history.return_value = pd.DataFrame({
                'Volume': volumes
            })
            
            result = collector.get_volume_data()
            
            assert result['current_volume'] == 2200000
            assert result['avg_volume_20d'] == 2010000  # Average of 20 days
            assert result['volume_vs_avg'] == Decimal('1.09')  # 109% of average
            assert result['volume_trend'] == 'above_average'
    
    def test_calculate_technical_indicators(self, collector):
        """Test calculation of technical indicators."""
        with patch('yfinance.download') as mock_download:
            # Create 50 days of price data for indicators
            prices = np.random.uniform(5600, 5700, 50)
            prices[-1] = 5635.50  # Current price
            
            mock_download.return_value = pd.DataFrame({
                'Close': prices
            })
            
            result = collector.get_technical_indicators('SPX')
            
            assert 'rsi_14' in result
            assert 0 <= result['rsi_14'] <= 100
            assert 'ma_20' in result
            assert 'ma_50' in result
            assert 'bollinger_upper' in result
            assert 'bollinger_lower' in result
            assert 'bollinger_position' in result
    
    def test_calculate_rsi(self, collector):
        """Test RSI calculation."""
        # Create price series with strong upward trend
        prices = pd.Series([100, 102, 101, 103, 104, 102, 105, 106, 104, 107, 108, 106, 109, 110, 112, 115])
        
        rsi = collector._calculate_rsi(prices, period=14)
        
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100
        # With mostly upward movement, RSI should be >= 50
        assert rsi >= 50
    
    def test_collect_market_snapshot(self, collector):
        """Test collecting complete market snapshot."""
        with patch.object(collector, 'get_current_spx') as mock_spx, \
             patch.object(collector, 'get_vix_level') as mock_vix, \
             patch.object(collector, 'get_volume_data') as mock_volume, \
             patch.object(collector, 'get_technical_indicators') as mock_tech:
            
            # Mock individual data methods
            mock_spx.return_value = {
                'price': Decimal('5635.50'),
                'change': Decimal('17.25'),
                'change_percent': Decimal('0.31'),
                'symbol': 'SPX'
            }
            mock_vix.return_value = {
                'level': Decimal('14.2'),
                'change': Decimal('-0.9'),
                'trend': 'declining',
                'percentile_rank': 25
            }
            mock_volume.return_value = {
                'current_volume': 2200000,
                'avg_volume_20d': 2010000,
                'volume_vs_avg': Decimal('1.09'),
                'volume_trend': 'above_average'
            }
            mock_tech.return_value = {
                'rsi_14': 72.4,
                'ma_20': 5625.30,
                'ma_50': 5598.75,
                'bollinger_upper': 5680.20,
                'bollinger_lower': 5570.40,
                'bollinger_position': 'upper_half'
            }
            
            snapshot = collector.collect_market_snapshot()
            
            assert snapshot['spx_price'] == Decimal('5635.50')
            assert snapshot['vix_level'] == Decimal('14.2')
            assert snapshot['volume'] == 2200000
            assert snapshot['technical_indicators']['rsi_14'] == 72.4
    
    @pytest.mark.integration
    def test_save_market_snapshot_to_database(self, collector):
        """Test saving market snapshot to database."""
        with SessionLocal() as db:
            # Collect snapshot data
            snapshot_data = {
                'spx_price': Decimal('5635.50'),
                'spx_change': Decimal('17.25'),
                'spx_change_percent': Decimal('0.31'),
                'vix_level': Decimal('14.2'),
                'vix_change': Decimal('-0.9'),
                'volume': 2200000,
                'volume_vs_avg': Decimal('1.09'),
                'technical_indicators': {
                    'rsi_14': 72.4,
                    'ma_20': 5625.30
                }
            }
            
            # Save to database
            saved_snapshot = collector.save_snapshot(db, snapshot_data)
            
            assert saved_snapshot.id is not None
            assert saved_snapshot.spx_price == Decimal('5635.50')
            assert saved_snapshot.vix_level == Decimal('14.2')
            assert saved_snapshot.expires_at > datetime.now(timezone.utc)
    
    @pytest.mark.integration
    def test_get_cached_snapshot(self, collector):
        """Test retrieving cached market snapshot."""
        import uuid
        with SessionLocal() as db:
            # Create a snapshot with unique ID to avoid conflicts
            unique_id = f"market_test_{uuid.uuid4().hex[:8]}"
            snapshot = MarketDataSnapshot(
                snapshot_id=unique_id,
                spx_price=Decimal('5635.50'),
                spx_change=Decimal('17.25'),
                spx_change_percent=Decimal('0.31'),
                vix_level=Decimal('14.2'),
                vix_change=Decimal('-0.9'),
                volume=2200000,
                volume_vs_avg=Decimal('1.09'),
                technical_indicators={'rsi_14': 72.4},
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
            )
            db.add(snapshot)
            db.commit()
            
            # Try to get cached snapshot
            cached = collector.get_or_create_snapshot(db, use_cache=True)
            
            assert cached is not None
            assert cached.spx_price == Decimal('5635.50')
            assert cached.snapshot_id == snapshot.snapshot_id
    
    def test_error_handling_with_api_failure(self, collector):
        """Test graceful handling of API failures."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Simulate API failure
            mock_ticker.side_effect = Exception("API connection failed")
            
            result = collector.get_current_spx()
            
            # Should return None or default values on failure
            assert result is None or 'error' in result
    
    def test_data_validation(self, collector):
        """Test data validation for market values."""
        # Test invalid price
        assert not collector._validate_price(-100)
        assert not collector._validate_price(0)
        assert collector._validate_price(5635.50)
        
        # Test invalid percentage
        assert not collector._validate_percentage(150)
        assert not collector._validate_percentage(-150)
        assert collector._validate_percentage(2.5)
        
        # Test invalid volume
        assert not collector._validate_volume(-1000)
        assert collector._validate_volume(2200000)