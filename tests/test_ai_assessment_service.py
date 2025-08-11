"""Tests for AI assessment service."""
import pytest
import json
import hashlib
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import asyncio

from services.ai_assessment_service import AIAssessmentService
from services.market_data_service import MarketDataCollector
from database.models import AIAssessment, AIUsageLog, AISettings
from database.config import SessionLocal


class TestAIAssessmentService:
    """Test AIAssessmentService."""
    
    @pytest.fixture
    def service(self):
        """Create AIAssessmentService instance."""
        return AIAssessmentService()
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client."""
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [
            Mock(message=Mock(content=json.dumps({
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
            })))
        ]
        mock_completion.usage = Mock(
            prompt_tokens=350,
            completion_tokens=100,
            total_tokens=450
        )
        mock_client.chat.completions.create = Mock(return_value=mock_completion)
        return mock_client
    
    @pytest.fixture
    def strategy_params(self):
        """Create sample strategy parameters."""
        return {
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
    
    @pytest.fixture
    def market_data(self):
        """Create sample market data."""
        return {
            "spx_price": Decimal("5635.50"),
            "spx_change": Decimal("17.25"),
            "spx_change_percent": Decimal("0.31"),
            "vix_level": Decimal("14.2"),
            "vix_change": Decimal("-0.9"),
            "vix_trend": "declining",
            "volume": 2200000,
            "volume_vs_avg": Decimal("1.09"),
            "technical_indicators": {
                "rsi_14": 72.4,
                "ma_20": 5625.30,
                "ma_50": 5598.75,
                "bollinger_position": "upper_half"
            }
        }
    
    def test_build_prompt(self, service, strategy_params, market_data):
        """Test building structured prompt for OpenAI."""
        prompt = service._build_prompt(strategy_params, market_data)
        
        assert "STRATEGY DETAILS:" in prompt
        assert "iron_condor" in prompt
        assert "SPX" in prompt
        assert "5500" in prompt  # Put short strike
        assert "CURRENT MARKET CONDITIONS:" in prompt
        assert "5635.50" in prompt  # Current SPX price
        assert "VIX: 14.2" in prompt
        assert "ASSESSMENT REQUEST:" in prompt
        assert "JSON" in prompt
    
    def test_calculate_strategy_hash(self, service, strategy_params):
        """Test strategy hash calculation for caching."""
        hash1 = service._calculate_strategy_hash(strategy_params)
        hash2 = service._calculate_strategy_hash(strategy_params)
        
        # Same parameters should produce same hash
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256 hex digest length
        
        # Different parameters should produce different hash
        modified_params = strategy_params.copy()
        modified_params["strikes"]["put_short"] = 5510
        hash3 = service._calculate_strategy_hash(modified_params)
        assert hash1 != hash3
    
    
    def test_assess_strategy_success(self, service, strategy_params, market_data, mock_openai_client):
        """Test successful strategy assessment."""
        # Inject mock client directly into service
        service.client = mock_openai_client
        
        # Mock cache to ensure fresh API call
        with patch.object(service, '_get_cached_assessment', return_value=None):
            with patch.object(service, '_get_market_data', return_value=market_data):
                assessment = service.assess_strategy(strategy_params)
        
        assert assessment is not None
        assert assessment["recommendation"] == "GO"
        assert assessment["confidence"] == 78
        assert len(assessment["reasoning"]["supporting_factors"]) == 2
        assert len(assessment["reasoning"]["risk_factors"]) == 2
        assert assessment["market_regime"] == "Low volatility, neutral sentiment"
        
        # Verify OpenAI was called
        mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_parse_openai_response(self, service):
        """Test parsing OpenAI response."""
        # Valid JSON response
        valid_response = json.dumps({
            "recommendation": "CAUTION",
            "confidence": 65,
            "reasoning": {
                "supporting_factors": ["Factor 1", "Factor 2"],
                "risk_factors": ["Risk 1", "Risk 2"]
            },
            "market_regime": "Moderate volatility"
        })
        
        result = service._parse_openai_response(valid_response)
        assert result["recommendation"] == "CAUTION"
        assert result["confidence"] == 65
        
        # Invalid JSON
        invalid_response = "This is not JSON"
        result = service._parse_openai_response(invalid_response)
        assert result is None
        
        # Missing required fields
        incomplete_response = json.dumps({
            "recommendation": "GO"
            # Missing confidence and other fields
        })
        result = service._parse_openai_response(incomplete_response)
        assert result is None
    
    @pytest.mark.integration
    def test_save_assessment_to_database(self, service):
        """Test saving assessment to database."""
        with SessionLocal() as db:
            assessment_data = {
                "recommendation": "GO",
                "confidence": 78,
                "reasoning": {
                    "supporting_factors": ["Low VIX", "Support level"],
                    "risk_factors": ["Fed meeting", "Earnings"]
                },
                "market_regime": "Low volatility"
            }
            
            strategy_params = {
                "strategy_type": "iron_condor",
                "symbol": "SPX",
                "strikes": {"put_short": 5500},
                "expiration": "2025-08-15"
            }
            
            market_conditions = {
                "spx_price": 5635.50,
                "vix_level": 14.2
            }
            
            saved = service._save_assessment(
                db,
                assessment_data,
                strategy_params,
                market_conditions,
                token_usage=450,
                processing_time_ms=2150
            )
            
            assert saved.id is not None
            assert saved.recommendation == "GO" or saved.recommendation.value == "GO"
            assert saved.confidence == 78
            assert saved.strategy_type == "iron_condor"
            assert saved.token_usage == 450
    
    @pytest.mark.integration
    def test_get_cached_assessment(self, service):
        """Test retrieving cached assessment."""
        with SessionLocal() as db:
            # Create an assessment
            strategy_hash = "test_hash_" + datetime.now().isoformat()
            assessment = AIAssessment(
                assessment_id=f"assess_test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                strategy_hash=strategy_hash,
                strategy_type="iron_condor",
                symbol="SPX",
                strategy_params={"test": "params"},
                recommendation="GO",
                confidence=78,
                reasoning={"supporting_factors": [], "risk_factors": []},
                market_conditions={"test": "conditions"},
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
            )
            db.add(assessment)
            db.commit()
            
            # Try to get cached assessment
            cached = service._get_cached_assessment(db, strategy_hash)
            
            assert cached is not None
            assert cached.strategy_hash == strategy_hash
            assert cached.recommendation == "GO" or cached.recommendation.value == "GO"
    
    def test_rate_limiting(self, service):
        """Test rate limiting functionality."""
        # Reset rate limiter
        service._reset_rate_limiter()
        
        # Should allow first 10 requests
        for i in range(10):
            assert service._check_rate_limit() is True
        
        # 11th request should be rate limited
        assert service._check_rate_limit() is False
        
        # After waiting, should allow again (mocked)
        with patch('time.time', return_value=service._rate_limit_window + 61):
            service._reset_rate_limiter()
            assert service._check_rate_limit() is True
    
    @pytest.mark.integration
    def test_log_usage(self, service):
        """Test usage logging."""
        with SessionLocal() as db:
            service._log_usage(
                db,
                assessment_id="test_assessment_001",
                operation="assess_strategy",
                model="gpt-4",
                tokens_input=350,
                tokens_output=100,
                tokens_total=450,
                cost_usd=Decimal("0.025"),
                response_time_ms=2150,
                success=True,
                error_message=None
            )
            
            # Verify log was created
            log = db.query(AIUsageLog).filter(
                AIUsageLog.assessment_id == "test_assessment_001"
            ).first()
            
            assert log is not None
            assert log.tokens_total == 450
            assert log.cost_usd == Decimal("0.025")
            assert log.success is True
    
    
    def test_error_handling_api_failure(self, service, strategy_params):
        """Test handling of API failures."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        service.client = mock_client
        
        assessment = service.assess_strategy(strategy_params)
        
        # Should return None or error indicator
        assert assessment is None or "error" in assessment
    
    def test_validate_assessment_data(self, service):
        """Test assessment data validation."""
        # Valid data
        valid_data = {
            "recommendation": "GO",
            "confidence": 78,
            "reasoning": {
                "supporting_factors": ["Factor 1"],
                "risk_factors": ["Risk 1"]
            },
            "market_regime": "Test regime"
        }
        assert service._validate_assessment(valid_data) is True
        
        # Invalid recommendation
        invalid_rec = valid_data.copy()
        invalid_rec["recommendation"] = "INVALID"
        assert service._validate_assessment(invalid_rec) is False
        
        # Invalid confidence
        invalid_conf = valid_data.copy()
        invalid_conf["confidence"] = 150
        assert service._validate_assessment(invalid_conf) is False
        
        # Missing required field
        missing_field = valid_data.copy()
        del missing_field["reasoning"]
        assert service._validate_assessment(missing_field) is False
    
    @pytest.mark.integration
    def test_get_or_update_settings(self, service):
        """Test getting or updating AI settings."""
        with SessionLocal() as db:
            settings = service._get_settings(db)
            
            assert settings is not None
            assert settings.model == "gpt-5"  # Default
            assert settings.temperature == Decimal("0.30")
            assert settings.max_tokens == 800
            assert settings.cache_ttl == 300
    
    def test_calculate_cost(self, service):
        """Test cost calculation for API usage."""
        # GPT-4 pricing (example)
        cost = service._calculate_cost(
            model="gpt-4",
            input_tokens=350,
            output_tokens=100
        )
        
        # Should return a reasonable cost
        assert cost > 0
        assert cost < 1  # Less than $1 for a single request
        assert isinstance(cost, Decimal)