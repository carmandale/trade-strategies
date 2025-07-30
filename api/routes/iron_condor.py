"""Iron Condor strategy API routes."""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from database.config import get_db
from services.iron_condor_service import IronCondorService
from api.models.strategy_models import (
    IronCondorStrategyResponse,
    TimeframeStrategyResponse, 
    PerformanceSummaryResponse
)
from api.exceptions import ResourceNotFoundError, BusinessLogicError

router = APIRouter(prefix="/api/strategies/iron-condor", tags=["iron-condor"])

@router.get("/", response_model=IronCondorStrategyResponse)
async def get_iron_condor_strategies(
    limit: int = Query(100, ge=1, le=1000, description="Number of trades to return per timeframe"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive Iron Condor strategy data for all timeframes.
    
    Returns strategy data, performance metrics, and trade details for daily, 
    weekly, and monthly Iron Condor strategies.
    """
    try:
        service = IronCondorService(db)
        
        # Validate parameters
        validated_params = service.validate_parameters(limit=limit, offset=offset)
        
        # Get strategy data for all timeframes
        strategy_data = service.get_all_timeframes_data(
            limit=validated_params["limit"],
            offset=validated_params["offset"]
        )
        
        return strategy_data
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No data found",
                "code": "NO_DATA",
                "message": "No Iron Condor strategies found for the specified criteria"
            }
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid parameters",
                "code": "INVALID_PARAMETER", 
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database connection failed",
                "code": "DB_CONNECTION_ERROR",
                "message": "Unable to retrieve strategy data. Please try again later."
            }
        )

@router.get("/{timeframe}", response_model=TimeframeStrategyResponse)
async def get_iron_condor_by_timeframe(
    timeframe: str,
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of trades to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Retrieve Iron Condor strategy data for a specific timeframe.
    
    Returns strategy data, performance metrics, and trade details for the 
    specified timeframe (daily, weekly, or monthly) with optional date filtering.
    """
    try:
        service = IronCondorService(db)
        
        # Validate parameters
        validated_params = service.validate_parameters(
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # Get strategy data for specific timeframe
        strategy_data = service.get_timeframe_data(
            timeframe=validated_params["timeframe"],
            start_date=validated_params.get("start_date"),
            end_date=validated_params.get("end_date"),
            limit=validated_params["limit"],
            offset=validated_params["offset"]
        )
        
        return strategy_data
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No data found",
                "code": "NO_DATA",
                "message": f"No Iron Condor strategies found for timeframe: {timeframe}"
            }
        )
    except BusinessLogicError as e:
        # Handle both validation errors and invalid timeframe
        if "Invalid timeframe" in str(e):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid timeframe",
                    "code": "INVALID_PARAMETER",
                    "message": "Timeframe must be one of: daily, weekly, monthly"
                }
            )
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Validation error",
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database connection failed",
                "code": "DB_CONNECTION_ERROR",
                "message": "Unable to retrieve strategy data. Please try again later."
            }
        )

@router.get("/performance", response_model=PerformanceSummaryResponse)
async def get_iron_condor_performance(db: Session = Depends(get_db)):
    """
    Get aggregated performance metrics across all Iron Condor timeframes.
    
    Returns summary statistics including total trades, overall win rate, 
    total P&L, best performing timeframe, and performance breakdown by timeframe.
    """
    try:
        service = IronCondorService(db)
        
        # Get performance summary
        performance_data = service.get_performance_summary()
        
        return performance_data
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No data found",
                "code": "NO_DATA",
                "message": "No Iron Condor performance data available"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Calculation error",
                "code": "CALCULATION_ERROR",
                "message": "Unable to calculate performance metrics. Please try again later."
            }
        )

# Additional utility endpoints for Iron Condor analysis

@router.get("/timeframes", response_model=dict)
async def get_available_timeframes():
    """
    Get list of available timeframes for Iron Condor strategies.
    
    Returns the supported timeframes and their descriptions.
    """
    return {
        "timeframes": [
            {
                "name": "daily",
                "description": "0DTE (zero days to expiration) strategies",
                "typical_duration": "Same day"
            },
            {
                "name": "weekly", 
                "description": "Weekly expiration strategies",
                "typical_duration": "1 week"
            },
            {
                "name": "monthly",
                "description": "Monthly expiration strategies", 
                "typical_duration": "1 month"
            }
        ]
    }

@router.get("/health", response_model=dict)
async def iron_condor_health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for Iron Condor strategy service.
    
    Verifies database connectivity and basic service functionality.
    """
    try:
        service = IronCondorService(db)
        
        # Simple health check - try to validate basic parameters
        service.validate_parameters(timeframe="daily", limit=1, offset=0)
        
        return {
            "status": "healthy",
            "service": "iron_condor",
            "database": "connected",
            "timestamp": "2025-07-30T00:00:00Z"  # Will be dynamic in real implementation
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unavailable",
                "code": "SERVICE_ERROR",
                "message": "Iron Condor service is currently unavailable"
            }
        )