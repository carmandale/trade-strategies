"""Custom exceptions and error handling for the Trade Strategies API."""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import logging
from typing import Any, Dict

# Set up logging
logger = logging.getLogger(__name__)

class TradeStrategiesException(Exception):
    """Base exception class for Trade Strategies API."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class DatabaseConnectionError(TradeStrategiesException):
    """Raised when database connection fails."""
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, "DB_CONNECTION_ERROR")

class ResourceNotFoundError(TradeStrategiesException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        super().__init__(message, "RESOURCE_NOT_FOUND")

class ValidationError(TradeStrategiesException):
    """Raised when data validation fails."""
    def __init__(self, message: str, field: str = None):
        if field:
            message = f"Validation error in field '{field}': {message}"
        super().__init__(message, "VALIDATION_ERROR")

class BusinessLogicError(TradeStrategiesException):
    """Raised when business logic constraints are violated."""
    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_LOGIC_ERROR")

def create_error_response(
    status_code: int, 
    message: str, 
    error_code: str = None,
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    error_response = {
        "error": True,
        "message": message,
        "status_code": status_code
    }
    
    if error_code:
        error_response["error_code"] = error_code
    
    if details:
        error_response["details"] = details
    
    return error_response

async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database exceptions."""
    logger.error(f"Database error on {request.url}: {str(exc)}")
    
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=create_error_response(
                status_code=409,
                message="Data integrity constraint violation",
                error_code="INTEGRITY_ERROR",
                details={"constraint_violation": str(exc.orig)}
            )
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=500,
            message="Database operation failed",
            error_code="DATABASE_ERROR"
        )
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation exceptions."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    
    # Extract field-specific errors
    error_details = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        error_details.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=422,
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": error_details}
        )
    )

async def custom_exception_handler(request: Request, exc: TradeStrategiesException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.warning(f"Application error on {request.url}: {exc.message}")
    
    status_code = 400
    if isinstance(exc, ResourceNotFoundError):
        status_code = 404
    elif isinstance(exc, DatabaseConnectionError):
        status_code = 503
    elif isinstance(exc, BusinessLogicError):
        status_code = 422
    
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(
            status_code=status_code,
            message=exc.message,
            error_code=exc.error_code
        )
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    logger.error(f"Unhandled error on {request.url}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=500,
            message="An unexpected error occurred",
            error_code="INTERNAL_ERROR"
        )
    )

# Error handling middleware
def setup_exception_handlers(app):
    """Set up all exception handlers for the FastAPI app."""
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(TradeStrategiesException, custom_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)