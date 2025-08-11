"""Tests for AI assessment API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from decimal import Decimal
import json

from api.main import app
from database.config import SessionLocal
from database.models import AIAssessment, MarketDataSnapshot

client = TestClient(app)


class TestAIAssessmentEndpoints:
    """Test AI assessment API endpoints."""
    
    def test_assess_strategy_success(self):
        """Test successful strategy assessment."""
        with patch('api.routes.ai_assessment.AIAssessmentService') as mock_service_class:
            # Mock the assessment service
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.assess_strategy.return_value = {
                "recommendation": "GO",
                "confidence": 78,
                "reasoning": {
                    "supporting_factors": [
                        "Low VIX indicates stable conditions",
                        "SPX above key support level"
                    ],
                    "risk_factors": [
                        "Fed meeting tomorrow",
                        "Earnings season approaching"
                    ]
                },
                "market_regime": "Low volatility, neutral sentiment"
            }
            
            # Test data
            strategy_data = {
                "strategy_type": "iron_condor",
                "symbol": "SPX",
                "strikes": {
                    "put_short": 5500,
                    "put_long": 5480,
                    "call_short": 5700,
                    "call_long": 5720
                },
                "expiration": "2025-08-15",
                "quantity": 10,
                "max_profit": 2000,
                "max_loss": 18000,
                "breakeven": [5520, 5680]
            }
            
            response = client.post("/api/ai/assess-strategy", json=strategy_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["recommendation"] == "GO"
            assert data["confidence"] == 78
            assert len(data["reasoning"]["supporting_factors"]) == 2
            assert len(data["reasoning"]["risk_factors"]) == 2
    
    def test_assess_strategy_invalid_data(self):
        """Test assessment with invalid strategy data."""
        # Missing required fields
        invalid_data = {
            "strategy_type": "iron_condor"
            # Missing other required fields
        }
        
        response = client.post("/api/ai/assess-strategy", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_assess_strategy_service_error(self):
        """Test handling of service errors."""
        with patch('api.routes.ai_assessment.AIAssessmentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.assess_strategy.return_value = None
            
            strategy_data = {
                "strategy_type": "iron_condor",
                "symbol": "SPX",
                "strikes": {"put_short": 5500},
                "expiration": "2025-08-15"
            }
            
            response = client.post("/api/ai/assess-strategy", json=strategy_data)
            
            assert response.status_code == 503  # Service unavailable
            assert "unavailable" in response.json()["detail"].lower()
    
    def test_assess_strategy_rate_limit(self):
        """Test rate limiting response."""
        with patch('api.routes.ai_assessment.AIAssessmentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.assess_strategy.return_value = {
                "error": "Rate limit exceeded. Please try again later."
            }
            
            strategy_data = {
                "strategy_type": "iron_condor",
                "symbol": "SPX",
                "strikes": {"put_short": 5500},
                "expiration": "2025-08-15"
            }
            
            response = client.post("/api/ai/assess-strategy", json=strategy_data)
            
            assert response.status_code == 429  # Too many requests
            assert "rate limit" in response.json()["detail"].lower()
    
    def test_get_market_data_success(self):
        """Test fetching current market data."""
        with patch('api.routes.ai_assessment.MarketDataCollector') as mock_collector_class:
            mock_collector = Mock()
            mock_collector_class.return_value = mock_collector
            
            # Mock market data
            mock_snapshot = Mock()
            mock_snapshot.to_dict.return_value = {
                "spx_price": 5635.50,
                "spx_change": 17.25,
                "spx_change_percent": 0.31,
                "vix_level": 14.2,
                "vix_change": -0.9,
                "volume": 2200000,
                "volume_vs_avg": 1.09,
                "technical_indicators": {
                    "rsi_14": 72.4,
                    "ma_20": 5625.30,
                    "ma_50": 5598.75,
                    "bollinger_position": "upper_half"
                }
            }
            
            with patch('api.routes.ai_assessment.SessionLocal') as mock_session:
                mock_db = Mock()
                mock_session.return_value.__enter__.return_value = mock_db
                mock_collector.get_or_create_snapshot.return_value = mock_snapshot
                
                response = client.get("/api/ai/market-data")
                
                assert response.status_code == 200
                data = response.json()
                assert data["spx_price"] == 5635.50
                assert data["vix_level"] == 14.2
                assert "technical_indicators" in data
    
    def test_get_market_data_cached(self):
        """Test returning cached market data."""
        with patch('api.routes.ai_assessment.MarketDataCollector') as mock_collector_class:
            mock_collector = Mock()
            mock_collector_class.return_value = mock_collector
            
            # Mock cached snapshot
            mock_snapshot = Mock()
            mock_snapshot.to_dict.return_value = {
                "spx_price": 5635.50,
                "spx_change": 17.25,
                "spx_change_percent": 0.31,
                "vix_level": 14.2,
                "vix_change": -0.9,
                "volume": 2200000,
                "volume_vs_avg": 1.09,
                "technical_indicators": {"rsi_14": 72.4},
                "cached": True,
                "expires_at": "2025-08-11T10:35:00Z"
            }
            mock_snapshot.is_expired.return_value = False  # Not expired
            
            with patch('api.routes.ai_assessment.SessionLocal') as mock_session:
                mock_db = Mock()
                mock_session.return_value.__enter__.return_value = mock_db
                mock_collector.get_or_create_snapshot.return_value = mock_snapshot
                
                response = client.get("/api/ai/market-data?use_cache=true")
                
                assert response.status_code == 200
                data = response.json()
                assert data["cached"] is True
    
    def test_get_market_data_error(self):
        """Test market data fetch error handling."""
        with patch('api.routes.ai_assessment.MarketDataCollector') as mock_collector_class:
            mock_collector = Mock()
            mock_collector_class.return_value = mock_collector
            mock_collector.get_or_create_snapshot.side_effect = Exception("API Error")
            
            with patch('api.routes.ai_assessment.SessionLocal') as mock_session:
                mock_db = Mock()
                mock_session.return_value.__enter__.return_value = mock_db
                
                response = client.get("/api/ai/market-data")
                
                assert response.status_code == 500
                assert "error" in response.json()["detail"].lower()
    
    def test_get_ai_status(self):
        """Test AI service status endpoint."""
        with patch('api.routes.ai_assessment.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock usage stats
            with patch('database.models.AIUsageLog.get_usage_stats') as mock_stats:
                mock_stats.return_value = {
                    "total_requests": 150,
                    "total_tokens": 45000,
                    "total_cost": 2.35,
                    "avg_response_time": 1850.5,
                    "success_rate": 98.5
                }
                
                # Mock latest assessment
                with patch.object(mock_db, 'query') as mock_query:
                    mock_assessment = Mock()
                    mock_assessment.created_at = datetime.now(timezone.utc)
                    mock_assessment.model_used = "gpt-4"
                    
                    mock_query.return_value.order_by.return_value.first.return_value = mock_assessment
                    
                    response = client.get("/api/ai/status")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["service_available"] is True
                    assert data["usage_stats"]["total_requests"] == 150
                    assert data["usage_stats"]["success_rate"] == 98.5
    
    def test_get_ai_status_no_api_key(self):
        """Test status when OpenAI API key is not configured."""
        with patch('api.routes.ai_assessment.os.getenv') as mock_getenv:
            mock_getenv.return_value = None  # No API key
            
            response = client.get("/api/ai/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["service_available"] is False
            assert "not configured" in data["message"].lower()
    
    def test_get_cached_assessment(self):
        """Test retrieving cached assessment by strategy hash."""
        with patch('api.routes.ai_assessment.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock cached assessment
            mock_assessment = Mock()
            mock_assessment.to_dict.return_value = {
                "assessment_id": "assess_20250811_SPX",
                "recommendation": "GO",
                "confidence": 78,
                "cached": True
            }
            
            with patch.object(mock_db, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = mock_assessment
                
                response = client.get("/api/ai/assessment/abc123def456")
                
                assert response.status_code == 200
                data = response.json()
                assert data["cached"] is True
                assert data["recommendation"] == "GO"
    
    def test_get_cached_assessment_not_found(self):
        """Test when cached assessment is not found."""
        with patch('api.routes.ai_assessment.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            with patch.object(mock_db, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = None
                
                response = client.get("/api/ai/assessment/nonexistent")
                
                assert response.status_code == 404
                assert "not found" in response.json()["detail"].lower()
    
    def test_assess_strategy_with_caching(self):
        """Test that assessment results are properly cached."""
        with patch('api.routes.ai_assessment.AIAssessmentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # First call returns fresh assessment
            mock_service.assess_strategy.return_value = {
                "recommendation": "GO",
                "confidence": 78,
                "reasoning": {
                    "supporting_factors": ["Low VIX"],
                    "risk_factors": ["Fed meeting"]
                },
                "market_regime": "Stable",
                "cached": False
            }
            
            strategy_data = {
                "strategy_type": "iron_condor",
                "symbol": "SPX",
                "strikes": {"put_short": 5500},
                "expiration": "2025-08-15"
            }
            
            # First request
            response1 = client.post("/api/ai/assess-strategy", json=strategy_data)
            assert response1.status_code == 200
            
            # Second call returns cached assessment
            mock_service.assess_strategy.return_value = {
                "recommendation": "GO",
                "confidence": 78,
                "reasoning": {
                    "supporting_factors": ["Low VIX"],
                    "risk_factors": ["Fed meeting"]
                },
                "market_regime": "Stable",
                "cached": True
            }
            
            # Second request with same data
            response2 = client.post("/api/ai/assess-strategy", json=strategy_data)
            assert response2.status_code == 200
            assert response2.json()["cached"] is True