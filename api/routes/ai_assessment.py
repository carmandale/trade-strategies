"""AI assessment API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import os
import logging

from services.ai_assessment_service import AIAssessmentService
from services.market_data_service import MarketDataCollector
from database.config import SessionLocal
from database.models import AIAssessment, AIUsageLog

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ai",
    tags=["AI Assessment"]
)


class StrategyAssessmentRequest(BaseModel):
    """Request model for strategy assessment."""
    strategy_type: str = Field(..., description="Type of strategy (iron_condor, bull_call, etc.)")
    symbol: str = Field(default="SPX", description="Trading symbol")
    strikes: Dict[str, float] = Field(..., description="Strike prices for the strategy")
    expiration: str = Field(..., description="Expiration date (YYYY-MM-DD)")
    quantity: int = Field(default=1, description="Number of contracts")
    max_profit: Optional[float] = Field(None, description="Maximum profit potential")
    max_loss: Optional[float] = Field(None, description="Maximum loss potential")
    breakeven: Optional[List[float]] = Field(None, description="Breakeven points")


class AssessmentResponse(BaseModel):
    """Response model for strategy assessment."""
    recommendation: str = Field(..., description="GO, CAUTION, or NO-GO")
    confidence: int = Field(..., description="Confidence score 0-100")
    reasoning: Dict[str, List[str]] = Field(..., description="Supporting and risk factors")
    market_regime: str = Field(..., description="Current market conditions summary")
    cached: bool = Field(default=False, description="Whether this is a cached response")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MarketDataResponse(BaseModel):
    """Response model for market data."""
    spx_price: float
    spx_change: float
    spx_change_percent: float
    vix_level: float
    vix_change: float
    volume: int
    volume_vs_avg: float
    technical_indicators: Dict[str, Any]
    cached: bool = Field(default=False)
    expires_at: Optional[str] = None


class ServiceStatusResponse(BaseModel):
    """Response model for service status."""
    service_available: bool
    api_key_configured: bool
    model: str
    cache_ttl: int
    rate_limit: Dict[str, Any]
    usage_stats: Dict[str, Any]
    last_assessment: Optional[str] = None
    message: str


@router.post("/assess-strategy", response_model=AssessmentResponse)
async def assess_strategy(request: StrategyAssessmentRequest):
    """
    Assess a trading strategy using AI.
    
    Returns recommendation (GO/CAUTION/NO-GO), confidence score,
    and detailed reasoning based on current market conditions.
    """
    try:
        service = AIAssessmentService()
        
        # Convert request to dict for service
        strategy_params = request.model_dump()
        
        # Get assessment
        result = service.assess_strategy(strategy_params)
        
        if result is None:
            raise HTTPException(
                status_code=503,
                detail="AI assessment service temporarily unavailable"
            )
        
        # Check for rate limit error
        if isinstance(result, dict) and "error" in result:
            if "rate limit" in result["error"].lower():
                raise HTTPException(
                    status_code=429,
                    detail=result["error"]
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=result["error"]
                )
        
        # Add cached flag if present
        if "cached" not in result:
            result["cached"] = False
        
        return AssessmentResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assessment failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Assessment failed: {str(e)}"
        )


@router.get("/market-data", response_model=MarketDataResponse)
async def get_market_data(use_cache: bool = Query(True, description="Use cached data if available")):
    """
    Get current market data snapshot.
    
    Returns SPX price, VIX level, volume, and technical indicators.
    Cached for 30 minutes by default.
    """
    try:
        collector = MarketDataCollector()
        
        with SessionLocal() as db:
            snapshot = collector.get_or_create_snapshot(db, use_cache=use_cache)
            
            if snapshot:
                data = snapshot.to_dict()
                data["cached"] = use_cache and not snapshot.is_expired()
                return MarketDataResponse(**data)
            else:
                # Fallback to direct collection
                data = collector.collect_market_snapshot()
                if data:
                    data["cached"] = False
                    return MarketDataResponse(**data)
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to fetch market data"
                    )
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market data fetch failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Market data error: {str(e)}"
        )


@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status():
    """
    Get AI service status and usage statistics.
    
    Returns service availability, configuration, and usage metrics.
    """
    try:
        # Check API key configuration
        api_key = os.getenv('OPENAI_API_KEY')
        api_key_configured = bool(api_key and api_key != 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        
        # Get configuration
        model = os.getenv('OPENAI_MODEL', 'gpt-4')
        cache_ttl = int(os.getenv('AI_ASSESSMENT_CACHE_TTL', '300'))
        
        # Get usage statistics
        with SessionLocal() as db:
            # Get usage stats for last 24 hours
            from datetime import timedelta
            start_date = datetime.now(timezone.utc) - timedelta(days=1)
            usage_stats = AIUsageLog.get_usage_stats(db, start_date=start_date)
            
            # Get last assessment time
            last_assessment = db.query(AIAssessment).order_by(
                AIAssessment.created_at.desc()
            ).first()
            
            last_assessment_time = None
            if last_assessment:
                last_assessment_time = last_assessment.created_at.isoformat()
        
        return ServiceStatusResponse(
            service_available=api_key_configured,
            api_key_configured=api_key_configured,
            model=model,
            cache_ttl=cache_ttl,
            rate_limit={
                "requests_per_minute": 10,
                "current_usage": "Available via assessment endpoint"
            },
            usage_stats=usage_stats,
            last_assessment=last_assessment_time,
            message="AI assessment service is operational" if api_key_configured else "OpenAI API key not configured"
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return ServiceStatusResponse(
            service_available=False,
            api_key_configured=False,
            model="unknown",
            cache_ttl=0,
            rate_limit={},
            usage_stats={},
            last_assessment=None,
            message=f"Service status check failed: {str(e)}"
        )


@router.get("/assessment/{strategy_hash}")
async def get_cached_assessment(strategy_hash: str):
    """
    Get cached assessment by strategy hash.
    
    Returns cached assessment if available and not expired.
    """
    try:
        with SessionLocal() as db:
            assessment = db.query(AIAssessment).filter(
                AIAssessment.strategy_hash == strategy_hash,
                AIAssessment.expires_at > datetime.now(timezone.utc)
            ).first()
            
            if assessment:
                result = assessment.to_dict()
                result["cached"] = True
                return result
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Assessment not found or expired"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache retrieval error: {str(e)}"
        )