"""Tests for AI assessment SQLAlchemy models."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from database.config import SessionLocal
from database.models import AIAssessment, AISettings, AIUsageLog, MarketDataSnapshot


class TestAIAssessmentModel:
    """Test AIAssessment model CRUD operations."""
    
    @pytest.mark.integration
    def test_create_ai_assessment(self):
        """Test creating a new AI assessment record."""
        with SessionLocal() as db:
            assessment = AIAssessment(
                assessment_id="assess_2025-08-11_14:30:00",
                strategy_hash="bull_call_spx_5635_5655_20250816",
                strategy_type="bull_call",
                symbol="SPX",
                strategy_params={
                    "legs": [
                        {"strike": 5635, "type": "call", "action": "buy"},
                        {"strike": 5655, "type": "call", "action": "sell"}
                    ],
                    "quantity": 10,
                    "expiration": "2025-08-16",
                    "max_profit": 13000,
                    "max_loss": 7000,
                    "breakeven": 5642
                },
                recommendation="GO",
                confidence=78,
                reasoning={
                    "supporting_factors": [
                        "Low VIX indicates stable conditions",
                        "SPX above support at 5630"
                    ],
                    "risk_factors": [
                        "Fed meeting tomorrow",
                        "Earnings season begins"
                    ]
                },
                market_conditions={
                    "regime": "Low volatility, mild bullish bias",
                    "spx_price": 5635.50,
                    "spx_change": 0.3,
                    "vix_level": 14.2,
                    "volume_vs_avg": 0.85
                },
                model_used="gpt-5",
                token_usage=450,
                cost_usd=Decimal("0.025"),
                processing_time_ms=2150,
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            
            db.add(assessment)
            db.commit()
            
            # Verify record was created
            assert assessment.id is not None
            assert assessment.assessment_id == "assess_2025-08-11_14:30:00"
            assert assessment.strategy_type == "bull_call"
            assert assessment.recommendation == "GO"
            assert assessment.confidence == 78
            assert assessment.model_used == "gpt-5"
            
    @pytest.mark.integration
    def test_ai_assessment_unique_constraint(self):
        """Test that assessment_id must be unique."""
        with SessionLocal() as db:
            assessment_id = "assess_duplicate_test"
            
            # Create first assessment
            assessment1 = AIAssessment(
                assessment_id=assessment_id,
                strategy_hash="test_hash_1",
                strategy_type="iron_condor",
                symbol="SPX",
                strategy_params={"test": "data1"},
                recommendation="GO",
                confidence=75,
                reasoning={"supporting_factors": [], "risk_factors": []},
                market_conditions={"test": "conditions"},
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            db.add(assessment1)
            db.commit()
            
            # Try to create duplicate assessment_id
            assessment2 = AIAssessment(
                assessment_id=assessment_id,  # Same ID
                strategy_hash="test_hash_2",
                strategy_type="bull_call",
                symbol="SPY",
                strategy_params={"test": "data2"},
                recommendation="CAUTION",
                confidence=65,
                reasoning={"supporting_factors": [], "risk_factors": []},
                market_conditions={"test": "conditions"},
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            
            with pytest.raises(IntegrityError):
                db.add(assessment2)
                db.commit()
                
    @pytest.mark.integration
    def test_ai_assessment_recommendation_constraint(self):
        """Test that recommendation must be valid value."""
        with SessionLocal() as db:
            assessment = AIAssessment(
                assessment_id="assess_test_invalid_recommendation",
                strategy_hash="test_hash",
                strategy_type="bull_call",
                symbol="SPX",
                strategy_params={"test": "data"},
                recommendation="INVALID",  # Invalid value
                confidence=50,
                reasoning={"supporting_factors": [], "risk_factors": []},
                market_conditions={"test": "conditions"},
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            
            with pytest.raises(IntegrityError):
                db.add(assessment)
                db.commit()
                
    @pytest.mark.integration 
    def test_ai_assessment_confidence_constraint(self):
        """Test that confidence must be between 0 and 100."""
        with SessionLocal() as db:
            # Test confidence > 100
            assessment = AIAssessment(
                assessment_id="assess_test_confidence_high",
                strategy_hash="test_hash",
                strategy_type="bull_call",
                symbol="SPX",
                strategy_params={"test": "data"},
                recommendation="GO",
                confidence=150,  # Invalid - too high
                reasoning={"supporting_factors": [], "risk_factors": []},
                market_conditions={"test": "conditions"},
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            
            with pytest.raises(IntegrityError):
                db.add(assessment)
                db.commit()


class TestAISettingsModel:
    """Test AISettings model CRUD operations."""
    
    @pytest.mark.integration
    def test_create_ai_settings(self):
        """Test creating AI settings record."""
        with SessionLocal() as db:
            settings = AISettings(
                user_id=1,  # Will be None for single-user app
                model="gpt-5",
                temperature=Decimal("0.30"),
                max_tokens=800,
                cache_ttl=300,
                reasoning_effort="medium",
                auto_assess=False
            )
            
            db.add(settings)
            db.commit()
            
            # Verify record was created
            assert settings.id is not None
            assert settings.model == "gpt-5"
            assert settings.temperature == Decimal("0.30")
            assert settings.max_tokens == 800
            assert settings.cache_ttl == 300
            assert settings.reasoning_effort == "medium"
            assert settings.auto_assess is False
            
    @pytest.mark.integration
    def test_ai_settings_defaults(self):
        """Test that AI settings have correct default values."""
        with SessionLocal() as db:
            settings = AISettings(user_id=None)  # Single-user app
            
            db.add(settings)
            db.commit()
            
            # Check defaults
            assert settings.model == "gpt-5"
            assert settings.temperature == Decimal("0.30")
            assert settings.max_tokens == 800
            assert settings.cache_ttl == 300
            assert settings.reasoning_effort == "medium"
            assert settings.auto_assess is False


class TestAIUsageLogModel:
    """Test AIUsageLog model CRUD operations."""
    
    @pytest.mark.integration
    def test_create_ai_usage_log(self):
        """Test creating AI usage log record."""
        with SessionLocal() as db:
            usage_log = AIUsageLog(
                assessment_id="assess_2025-08-11_14:30:00",
                operation="assess_strategy",
                model="gpt-5",
                tokens_input=350,
                tokens_output=100,
                tokens_total=450,
                cost_usd=Decimal("0.025"),
                response_time_ms=2150,
                success=True,
                error_message=None
            )
            
            db.add(usage_log)
            db.commit()
            
            # Verify record was created
            assert usage_log.id is not None
            assert usage_log.assessment_id == "assess_2025-08-11_14:30:00"
            assert usage_log.operation == "assess_strategy"
            assert usage_log.model == "gpt-5"
            assert usage_log.tokens_total == 450
            assert usage_log.cost_usd == Decimal("0.025")
            assert usage_log.success is True
            
    @pytest.mark.integration
    def test_ai_usage_log_with_error(self):
        """Test creating AI usage log with error."""
        with SessionLocal() as db:
            usage_log = AIUsageLog(
                assessment_id="assess_error_test",
                operation="assess_strategy",
                model="gpt-5",
                tokens_input=0,
                tokens_output=0,
                tokens_total=0,
                cost_usd=Decimal("0.00"),
                response_time_ms=5000,
                success=False,
                error_message="OpenAI API timeout"
            )
            
            db.add(usage_log)
            db.commit()
            
            assert usage_log.success is False
            assert usage_log.error_message == "OpenAI API timeout"


class TestMarketDataSnapshotModel:
    """Test MarketDataSnapshot model CRUD operations."""
    
    @pytest.mark.integration
    def test_create_market_data_snapshot(self):
        """Test creating market data snapshot record."""
        with SessionLocal() as db:
            snapshot = MarketDataSnapshot(
                snapshot_id="market_2025-08-11_14:30",
                spx_price=Decimal("5635.50"),
                spx_change=Decimal("17.25"),
                spx_change_percent=Decimal("0.31"),
                vix_level=Decimal("14.2"),
                vix_change=Decimal("-0.9"),
                volume=2150000,
                volume_vs_avg=Decimal("0.85"),
                technical_indicators={
                    "rsi_14": 72.4,
                    "ma_20": 5625.30,
                    "ma_50": 5598.75,
                    "bollinger_position": "upper_half"
                },
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            )
            
            db.add(snapshot)
            db.commit()
            
            # Verify record was created
            assert snapshot.id is not None
            assert snapshot.snapshot_id == "market_2025-08-11_14:30"
            assert snapshot.spx_price == Decimal("5635.50")
            assert snapshot.vix_level == Decimal("14.2")
            assert snapshot.volume == 2150000
            assert "rsi_14" in snapshot.technical_indicators
            
    @pytest.mark.integration
    def test_market_data_snapshot_unique_constraint(self):
        """Test that snapshot_id must be unique."""
        with SessionLocal() as db:
            snapshot_id = "market_duplicate_test"
            
            # Create first snapshot
            snapshot1 = MarketDataSnapshot(
                snapshot_id=snapshot_id,
                spx_price=Decimal("5600.00"),
                spx_change=Decimal("10.00"),
                spx_change_percent=Decimal("0.18"),
                vix_level=Decimal("15.0"),
                vix_change=Decimal("0.5"),
                volume=2000000,
                volume_vs_avg=Decimal("0.90"),
                technical_indicators={"test": "data1"},
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            )
            db.add(snapshot1)
            db.commit()
            
            # Try to create duplicate snapshot_id
            snapshot2 = MarketDataSnapshot(
                snapshot_id=snapshot_id,  # Same ID
                spx_price=Decimal("5650.00"),
                spx_change=Decimal("20.00"),
                spx_change_percent=Decimal("0.36"),
                vix_level=Decimal("13.5"),
                vix_change=Decimal("-1.0"),
                volume=2200000,
                volume_vs_avg=Decimal("0.80"),
                technical_indicators={"test": "data2"},
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            )
            
            with pytest.raises(IntegrityError):
                db.add(snapshot2)
                db.commit()