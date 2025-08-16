"""Strategy backtesting API routes with database integration."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from decimal import Decimal
from datetime import datetime, timedelta, date
import yfinance as yf
import pandas as pd
import numpy as np

from database.config import get_db
from database.models import Strategy, Backtest, Trade
from services.options_pricing_service import OptionsPricingService

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

class TimeFrame(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class StrategyType(str, Enum):
    IRON_CONDOR = "iron_condor"
    BULL_CALL = "bull_call"

# Database-backed strategy models
class StrategyCreate(BaseModel):
    """Request model for creating a new strategy."""
    name: str = Field(..., min_length=1, max_length=100)
    strategy_type: StrategyType
    symbol: str = Field(default="SPY", min_length=1, max_length=10)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)

class StrategyUpdate(BaseModel):
    """Request model for updating a strategy."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class StrategyResponse(BaseModel):
    """Response model for strategy data."""
    id: str
    name: str
    strategy_type: str
    symbol: str
    parameters: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BacktestRequest(BaseModel):
    symbol: str = "SPY"
    strategy_type: StrategyType
    timeframe: TimeFrame
    days_back: int = 30
    strategy_id: Optional[str] = None
    volatility: Optional[float] = None  # If not provided, will be calculated from historical data
    risk_free_rate: Optional[float] = None  # If not provided, will use default (5%)
    dividend_yield: Optional[float] = None  # If not provided, will use actual dividend yield
    contracts: Optional[int] = 1  # Number of contracts
    custom_strikes: Optional[List[float]] = None  # Custom strike prices (if not using default percentages)

class BacktestResult(BaseModel):
    symbol: str
    strategy_type: str
    timeframe: str
    total_pnl: float
    win_rate: float
    total_trades: int
    avg_pnl_per_trade: float
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    probability_of_profit: float = 0.0
    risk_reward_ratio: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    breakeven_points: List[float] = []
    avg_days_held: float = 0.0
    volatility_used: float = 0.0
    strategy_details: Dict[str, Any] = {}

class CalculateRequest(BaseModel):
    """Request model for real-time strategy calculations with custom strikes."""
    symbol: str = "SPY"
    strategy_type: StrategyType
    timeframe: TimeFrame
    current_price: float
    strike_percentages: Dict[str, float] = Field(
        description="Strike percentages as decimals. For iron_condor: put_long_pct, put_short_pct, call_short_pct, call_long_pct"
    )
    volatility: Optional[float] = None
    risk_free_rate: Optional[float] = None
    dividend_yield: Optional[float] = None
    contracts: Optional[int] = 1

class CalculateResult(BaseModel):
    """Response model for real-time strategy calculations."""
    symbol: str
    strategy_type: str
    timeframe: str
    current_price: float
    strikes: Dict[str, float]
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    probability_of_profit: float
    risk_reward_ratio: float
    greeks: Optional[Dict[str, float]] = None
    entry_cost: float
    volatility_used: float

@router.post("/backtest", response_model=BacktestResult)
async def backtest_strategy(request: BacktestRequest):
    """Run backtest for specified strategy and timeframe using Black-Scholes options pricing."""
    try:
        # Get market data
        ticker = yf.Ticker(request.symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days_back)
        
        hist_data = ticker.history(start=start_date, end=end_date)
        
        if hist_data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.symbol}")
        
        # Initialize options pricing service
        options_pricing = OptionsPricingService(
            risk_free_rate=request.risk_free_rate if request.risk_free_rate is not None else 0.05
        )
        
        # Calculate historical volatility if not provided
        volatility = request.volatility
        if volatility is None:
            # Calculate historical volatility (annualized)
            returns = np.log(hist_data['Close'] / hist_data['Close'].shift(1)).dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        
        # Get dividend yield if not provided
        dividend_yield = request.dividend_yield
        if dividend_yield is None:
            try:
                dividend_yield = ticker.info.get('dividendYield', 0.0)
                if dividend_yield is None:
                    dividend_yield = 0.0
            except:
                dividend_yield = 0.0
        
        # Run backtesting with enhanced options pricing
        if request.strategy_type == StrategyType.IRON_CONDOR:
            result = _backtest_iron_condor_enhanced(
                hist_data, 
                request.timeframe, 
                options_pricing, 
                volatility, 
                dividend_yield,
                request.contracts,
                request.custom_strikes
            )
        else:  # Bull Call
            result = _backtest_bull_call_enhanced(
                hist_data, 
                request.timeframe, 
                options_pricing, 
                volatility, 
                dividend_yield,
                request.contracts,
                request.custom_strikes
            )
        
        # Add volatility used to the result
        result['volatility_used'] = volatility
        
        return BacktestResult(
            symbol=request.symbol,
            strategy_type=request.strategy_type.value,
            timeframe=request.timeframe.value,
            **result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate", response_model=CalculateResult)
async def calculate_strategy(request: CalculateRequest):
    """Calculate strategy metrics in real-time with custom strike percentages."""
    try:
        # Initialize options pricing service
        options_pricing = OptionsPricingService(
            risk_free_rate=request.risk_free_rate if request.risk_free_rate is not None else 0.05
        )
        
        # Get volatility if not provided
        volatility = request.volatility
        if volatility is None:
            # Get historical volatility for the symbol
            try:
                ticker = yf.Ticker(request.symbol)
                hist_data = ticker.history(period="30d")
                if not hist_data.empty:
                    returns = np.log(hist_data['Close'] / hist_data['Close'].shift(1)).dropna()
                    volatility = float(returns.std() * np.sqrt(252))  # Annualized volatility
                else:
                    volatility = 0.2  # Default 20% volatility
            except:
                volatility = 0.2  # Default 20% volatility
        
        # Get dividend yield if not provided
        dividend_yield = request.dividend_yield
        if dividend_yield is None:
            try:
                ticker = yf.Ticker(request.symbol)
                dividend_yield = ticker.info.get('dividendYield', 0.0)
                if dividend_yield is None:
                    dividend_yield = 0.0
            except:
                dividend_yield = 0.0
        
        # Calculate days to expiration
        days_to_expiration = _calculate_days_to_expiration(request.timeframe)
        
        # Calculate strikes from percentages
        current_price = request.current_price
        
        if request.strategy_type == StrategyType.IRON_CONDOR:
            # Validate required strike percentages for iron condor
            required_strikes = ['put_long_pct', 'put_short_pct', 'call_short_pct', 'call_long_pct']
            for strike_key in required_strikes:
                if strike_key not in request.strike_percentages:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Missing required strike percentage: {strike_key}"
                    )
            
            # Calculate strike prices
            put_long = round(current_price * (request.strike_percentages['put_long_pct'] / 100), 2)
            put_short = round(current_price * (request.strike_percentages['put_short_pct'] / 100), 2)
            call_short = round(current_price * (request.strike_percentages['call_short_pct'] / 100), 2)
            call_long = round(current_price * (request.strike_percentages['call_long_pct'] / 100), 2)
            
            strikes = [put_long, put_short, call_short, call_long]
            
            # Validate strike order
            if not (put_long < put_short < call_short < call_long):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid strike order. Must be: put_long < put_short < call_short < call_long"
                )
            
            # Calculate spread prices
            spread_prices = options_pricing.calculate_spread_prices(
                spread_type='iron_condor',
                underlying_price=current_price,
                strikes=strikes,
                days_to_expiration=days_to_expiration,
                volatility=volatility,
                dividend_yield=dividend_yield
            )
            
            # Calculate metrics
            entry_credit = spread_prices['net_credit']
            max_profit = entry_credit * 100 * request.contracts
            
            # Calculate max loss (width of the wider spread minus credit)
            put_width = put_short - put_long
            call_width = call_long - call_short
            max_loss = (max(put_width, call_width) - entry_credit) * 100 * request.contracts
            
            # Calculate breakeven points
            lower_breakeven = put_short - entry_credit
            upper_breakeven = call_short + entry_credit
            breakeven_points = [round(lower_breakeven, 2), round(upper_breakeven, 2)]
            
            # Return strikes dict
            strikes_dict = {
                'put_long': put_long,
                'put_short': put_short,
                'call_short': call_short,
                'call_long': call_long
            }
            
            entry_cost = entry_credit * 100 * request.contracts  # Credit is positive
            
        else:  # Bull Call
            # Validate required strike percentages for bull call
            required_strikes = ['lower_pct', 'upper_pct']
            for strike_key in required_strikes:
                if strike_key not in request.strike_percentages:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required strike percentage: {strike_key}"
                    )
            
            # Calculate strike prices
            lower_strike = round(current_price * (request.strike_percentages['lower_pct'] / 100), 2)
            upper_strike = round(current_price * (request.strike_percentages['upper_pct'] / 100), 2)
            
            strikes = [lower_strike, upper_strike]
            
            # Validate strike order
            if lower_strike >= upper_strike:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid strike order. Lower strike must be less than upper strike"
                )
            
            # Calculate spread prices
            spread_prices = options_pricing.calculate_spread_prices(
                spread_type='bull_call',
                underlying_price=current_price,
                strikes=strikes,
                days_to_expiration=days_to_expiration,
                volatility=volatility,
                dividend_yield=dividend_yield
            )
            
            # Calculate metrics
            entry_debit = spread_prices['net_debit']
            max_loss = entry_debit * 100 * request.contracts
            max_profit = (upper_strike - lower_strike - entry_debit) * 100 * request.contracts
            
            # Calculate breakeven point
            breakeven = lower_strike + entry_debit
            breakeven_points = [round(breakeven, 2)]
            
            # Return strikes dict
            strikes_dict = {
                'lower_strike': lower_strike,
                'upper_strike': upper_strike
            }
            
            entry_cost = entry_debit * 100 * request.contracts  # Debit is negative (cost)
        
        # Calculate probability of profit
        probability_of_profit = options_pricing.calculate_probability_of_profit(
            spread_type=request.strategy_type.value,
            underlying_price=current_price,
            strikes=strikes,
            days_to_expiration=days_to_expiration,
            volatility=volatility,
            dividend_yield=dividend_yield
        )
        
        # Calculate risk-reward ratio
        risk_reward_ratio = abs(max_profit) / abs(max_loss) if max_loss != 0 else 0
        
        return CalculateResult(
            symbol=request.symbol,
            strategy_type=request.strategy_type.value,
            timeframe=request.timeframe.value,
            current_price=current_price,
            strikes=strikes_dict,
            max_profit=round(max_profit, 2),
            max_loss=round(max_loss, 2),
            breakeven_points=breakeven_points,
            probability_of_profit=round(probability_of_profit * 100, 2),
            risk_reward_ratio=round(risk_reward_ratio, 2),
            entry_cost=round(entry_cost, 2),
            volatility_used=round(volatility, 4)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating strategy: {str(e)}")

# Database-backed strategy endpoints
@router.post("/", response_model=StrategyResponse, status_code=201)
async def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """Create a new strategy."""
    try:
        db_strategy = Strategy(
            name=strategy.name,
            strategy_type=strategy.strategy_type.value,
            symbol=strategy.symbol.upper(),
            parameters=strategy.parameters,
            is_active=strategy.is_active
        )
        
        db.add(db_strategy)
        db.commit()
        db.refresh(db_strategy)
        
        return db_strategy
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating strategy: {str(e)}")

@router.get("/", response_model=List[StrategyResponse])
async def get_strategies(
    db: Session = Depends(get_db),
    active: Optional[bool] = Query(None),
    strategy_type: Optional[StrategyType] = Query(None),
    symbol: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get strategies with optional filtering."""
    try:
        query = db.query(Strategy)
        
        # Apply filters
        if active is not None:
            query = query.filter(Strategy.is_active == active)
        if strategy_type:
            query = query.filter(Strategy.strategy_type == strategy_type.value)
        if symbol:
            query = query.filter(Strategy.symbol == symbol.upper())
        
        # Apply pagination and ordering
        strategies = query.order_by(Strategy.created_at.desc()).offset(offset).limit(limit).all()
        
        return strategies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving strategies: {str(e)}")

@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Get a specific strategy by ID."""
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return strategy
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving strategy: {str(e)}")

@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(strategy_id: str, strategy_update: StrategyUpdate, db: Session = Depends(get_db)):
    """Update an existing strategy."""
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Update only provided fields
        update_data = strategy_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(strategy, field, value)
        
        db.commit()
        db.refresh(strategy)
        
        return strategy
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating strategy: {str(e)}")

@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Delete a strategy."""
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        db.delete(strategy)
        db.commit()
        
        return {"message": "Strategy deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting strategy: {str(e)}")

@router.get("/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: str, db: Session = Depends(get_db)):
    """Get performance metrics for a strategy."""
    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Get strategy trades
        trades = db.query(Trade).filter(Trade.strategy_id == strategy_id).all()
        
        if not trades:
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "total_trades": 0,
                "open_trades": 0,
                "closed_trades": 0,
                "total_realized_pnl": 0,
                "win_rate": 0,
                "avg_pnl_per_trade": 0
            }
        
        # Calculate performance metrics using model method
        total_pnl = strategy.calculate_total_pnl(db)
        
        # Calculate other metrics
        total_trades = len(trades)
        open_trades = len([t for t in trades if t.status == "open"])
        closed_trades = len([t for t in trades if t.status == "closed"])
        
        realized_trades = [t for t in trades if t.realized_pnl is not None]
        winning_trades = len([t for t in realized_trades if t.realized_pnl > 0])
        win_rate = (winning_trades / len(realized_trades) * 100) if realized_trades else 0
        
        avg_pnl_per_trade = total_pnl / len(realized_trades) if realized_trades else Decimal('0')
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "total_trades": total_trades,
            "open_trades": open_trades,
            "closed_trades": closed_trades,
            "total_realized_pnl": float(total_pnl),
            "win_rate": round(win_rate, 2),
            "avg_pnl_per_trade": float(avg_pnl_per_trade)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating strategy performance: {str(e)}")

def _backtest_iron_condor(data: pd.DataFrame, timeframe: TimeFrame) -> dict:
    """Basic Iron Condor backtesting logic."""
    # Simplified logic based on existing scripts
    strikes = _get_strikes_for_timeframe(timeframe)
    
    total_trades = len(data) - 1
    wins = 0
    total_pnl = 0.0
    
    for i in range(len(data) - 1):
        current_price = data.iloc[i]['Close']
        next_price = data.iloc[i + 1]['Close']
        
        # Calculate strikes based on current price
        put_strike_short = current_price * strikes['put_short']
        call_strike_short = current_price * strikes['call_short']
        
        # Determine if trade was profitable (price stayed between strikes)
        if put_strike_short <= next_price <= call_strike_short:
            wins += 1
            pnl = strikes['credit']
        else:
            pnl = -strikes['max_loss']
        
        total_pnl += pnl
    
    win_rate = wins / total_trades if total_trades > 0 else 0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate * 100, 2),
        "total_trades": total_trades,
        "avg_pnl_per_trade": round(avg_pnl, 2)
    }

def _backtest_bull_call(data: pd.DataFrame, timeframe: TimeFrame) -> dict:
    """Basic Bull Call backtesting logic."""
    # Simplified bull call logic
    total_trades = len(data) - 1
    wins = 0
    total_pnl = 0.0
    
    for i in range(len(data) - 1):
        current_price = data.iloc[i]['Close']
        next_price = data.iloc[i + 1]['Close']
        
        # Bull call profits when price goes up
        if next_price > current_price:
            wins += 1
            pnl = 50  # Simplified profit
        else:
            pnl = -25  # Simplified loss
        
        total_pnl += pnl
    
    win_rate = wins / total_trades if total_trades > 0 else 0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate * 100, 2),
        "total_trades": total_trades,
        "avg_pnl_per_trade": round(avg_pnl, 2)
    }

def _get_strikes_for_timeframe(timeframe: TimeFrame) -> dict:
    """Get strike configuration based on timeframe."""
    if timeframe == TimeFrame.DAILY:
        return {
            "put_short": 0.975,
            "call_short": 1.02,
            "credit": 25,
            "max_loss": 475
        }
    elif timeframe == TimeFrame.WEEKLY:
        return {
            "put_short": 0.965,
            "call_short": 1.03,
            "credit": 75,
            "max_loss": 425
        }
    else:  # MONTHLY
        return {
            "put_short": 0.94,
            "call_short": 1.05,
            "credit": 150,
            "max_loss": 350
        }

def _get_strike_percentages_for_timeframe(timeframe: TimeFrame) -> dict:
    """Get strike percentages for different strategies based on timeframe."""
    if timeframe == TimeFrame.DAILY:
        return {
            "iron_condor": {
                "put_long": 0.97,    # 3% OTM
                "put_short": 0.975,   # 2.5% OTM
                "call_short": 1.02,   # 2% OTM
                "call_long": 1.025    # 2.5% OTM
            },
            "bull_call": {
                "lower": 0.995,       # 0.5% OTM
                "upper": 1.02         # 2% OTM
            },
            "butterfly": {
                "lower": 0.98,        # 2% OTM
                "middle": 1.0,        # ATM
                "upper": 1.02         # 2% OTM
            }
        }
    elif timeframe == TimeFrame.WEEKLY:
        return {
            "iron_condor": {
                "put_long": 0.96,     # 4% OTM
                "put_short": 0.965,    # 3.5% OTM
                "call_short": 1.03,    # 3% OTM
                "call_long": 1.035     # 3.5% OTM
            },
            "bull_call": {
                "lower": 0.99,        # 1% OTM
                "upper": 1.03         # 3% OTM
            },
            "butterfly": {
                "lower": 0.97,        # 3% OTM
                "middle": 1.0,        # ATM
                "upper": 1.03         # 3% OTM
            }
        }
    else:  # MONTHLY
        return {
            "iron_condor": {
                "put_long": 0.93,     # 7% OTM
                "put_short": 0.94,     # 6% OTM
                "call_short": 1.05,    # 5% OTM
                "call_long": 1.06      # 6% OTM
            },
            "bull_call": {
                "lower": 0.98,        # 2% OTM
                "upper": 1.05         # 5% OTM
            },
            "butterfly": {
                "lower": 0.95,        # 5% OTM
                "middle": 1.0,        # ATM
                "upper": 1.05         # 5% OTM
            }
        }

def _calculate_days_to_expiration(timeframe: TimeFrame) -> int:
    """Calculate days to expiration based on timeframe."""
    if timeframe == TimeFrame.DAILY:
        return 1  # 0DTE
    elif timeframe == TimeFrame.WEEKLY:
        return 7  # 7 days
    else:  # MONTHLY
        return 30  # 30 days

def _calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.05) -> float:
    """Calculate Sharpe ratio from a list of returns."""
    if not returns or len(returns) < 2:
        return 0.0
    
    # Annualize based on trading days (252)
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    
    if std_return == 0:
        return 0.0
    
    # Daily risk-free rate
    daily_rf = risk_free_rate / 252
    
    # Sharpe ratio
    sharpe = (mean_return - daily_rf) / std_return
    
    # Annualize
    sharpe_annualized = sharpe * np.sqrt(252)
    
    return round(sharpe_annualized, 2)

def _calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calculate maximum drawdown from equity curve."""
    if not equity_curve or len(equity_curve) < 2:
        return 0.0
    
    # Calculate running maximum
    running_max = np.maximum.accumulate(equity_curve)
    
    # Calculate drawdown
    drawdown = (equity_curve - running_max) / running_max
    
    # Get maximum drawdown
    max_drawdown = np.min(drawdown)
    
    return round(max_drawdown * 100, 2)  # Convert to percentage

def _backtest_iron_condor_enhanced(
    data: pd.DataFrame, 
    timeframe: TimeFrame, 
    options_pricing: OptionsPricingService,
    volatility: float,
    dividend_yield: float,
    contracts: int = 1,
    custom_strikes: Optional[List[float]] = None
) -> dict:
    """
    Enhanced Iron Condor backtesting using Black-Scholes options pricing.
    
    Args:
        data: Historical price data
        timeframe: Daily, weekly, or monthly
        options_pricing: Options pricing service
        volatility: Implied volatility
        dividend_yield: Dividend yield
        contracts: Number of contracts
        custom_strikes: Optional custom strike prices
        
    Returns:
        Backtest results
    """
    # Get days to expiration
    days_to_expiration = _calculate_days_to_expiration(timeframe)
    
    # Get strike percentages
    strike_percentages = _get_strike_percentages_for_timeframe(timeframe)["iron_condor"]
    
    # Initialize tracking variables
    total_trades = 0
    wins = 0
    total_pnl = 0.0
    pnl_list = []
    equity_curve = [1000.0]  # Start with $1000
    
    # Track max profit/loss
    max_profit_seen = 0.0
    max_loss_seen = 0.0
    
    # For each day in the data
    for i in range(len(data) - days_to_expiration):
        # Skip if not enough data for the full period
        if i + days_to_expiration >= len(data):
            continue
        
        # Entry price
        entry_price = data.iloc[i]['Close']
        
        # Exit price (at expiration)
        exit_price = data.iloc[i + days_to_expiration]['Close']
        
        # Calculate strikes
        if custom_strikes and len(custom_strikes) == 4:
            # Use custom strikes if provided
            put_long, put_short, call_short, call_long = custom_strikes
        else:
            # Calculate strikes based on percentages
            put_long = round(entry_price * strike_percentages["put_long"], 2)
            put_short = round(entry_price * strike_percentages["put_short"], 2)
            call_short = round(entry_price * strike_percentages["call_short"], 2)
            call_long = round(entry_price * strike_percentages["call_long"], 2)
        
        # Calculate spread prices at entry
        entry_prices = options_pricing.calculate_spread_prices(
            spread_type='iron_condor',
            underlying_price=entry_price,
            strikes=[put_long, put_short, call_short, call_long],
            days_to_expiration=days_to_expiration,
            volatility=volatility,
            dividend_yield=dividend_yield
        )
        
        # Calculate spread prices at exit (expiration)
        exit_prices = options_pricing.calculate_spread_prices(
            spread_type='iron_condor',
            underlying_price=exit_price,
            strikes=[put_long, put_short, call_short, call_long],
            days_to_expiration=0.01,  # Almost expired
            volatility=volatility,
            dividend_yield=dividend_yield
        )
        
        # Calculate P&L
        entry_credit = entry_prices['net_credit']
        max_profit = entry_credit * 100 * contracts
        
        # Determine width of the spreads
        put_width = put_short - put_long
        call_width = call_long - call_short
        max_loss = (max(put_width, call_width) - entry_credit) * 100 * contracts
        
        # Calculate P&L at expiration
        if exit_price < put_long:
            # Maximum loss on put side
            pnl = -max_loss
        elif put_long <= exit_price < put_short:
            # Partial loss on put side
            pnl = ((exit_price - put_long) / (put_short - put_long) * entry_credit - 
                  (put_short - exit_price)) * 100 * contracts
        elif put_short <= exit_price <= call_short:
            # Maximum profit (price between short strikes)
            pnl = max_profit
            wins += 1
        elif call_short < exit_price <= call_long:
            # Partial loss on call side
            pnl = ((call_long - exit_price) / (call_long - call_short) * entry_credit - 
                  (exit_price - call_short)) * 100 * contracts
        else:
            # Maximum loss on call side
            pnl = -max_loss
        
        # Update tracking variables
        total_trades += 1
        total_pnl += pnl
        pnl_list.append(pnl)
        equity_curve.append(equity_curve[-1] + pnl)
        
        # Update max profit/loss seen
        max_profit_seen = max(max_profit_seen, max_profit)
        max_loss_seen = max(max_loss_seen, max_loss)
    
    # Calculate metrics
    win_rate = wins / total_trades if total_trades > 0 else 0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    # Calculate Sharpe ratio
    returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] 
              for i in range(1, len(equity_curve))]
    sharpe_ratio = _calculate_sharpe_ratio(returns)
    
    # Calculate max drawdown
    max_drawdown = _calculate_max_drawdown(equity_curve)
    
    # Calculate probability of profit
    probability_of_profit = options_pricing.calculate_probability_of_profit(
        spread_type='iron_condor',
        underlying_price=data.iloc[-1]['Close'],
        strikes=[put_long, put_short, call_short, call_long],
        days_to_expiration=days_to_expiration,
        volatility=volatility,
        dividend_yield=dividend_yield
    )
    
    # Calculate risk-reward ratio
    risk_reward_ratio = max_profit_seen / max_loss_seen if max_loss_seen > 0 else 0
    
    # Calculate breakeven points
    lower_breakeven = put_short - entry_credit
    upper_breakeven = call_short + entry_credit
    
    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate * 100, 2),
        "total_trades": total_trades,
        "avg_pnl_per_trade": round(avg_pnl, 2),
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "probability_of_profit": round(probability_of_profit * 100, 2),
        "risk_reward_ratio": round(risk_reward_ratio, 2),
        "max_profit": round(max_profit_seen, 2),
        "max_loss": round(max_loss_seen, 2),
        "breakeven_points": [round(lower_breakeven, 2), round(upper_breakeven, 2)],
        "avg_days_held": days_to_expiration,
        "strategy_details": {
            "put_long": put_long,
            "put_short": put_short,
            "call_short": call_short,
            "call_long": call_long,
            "entry_credit": round(entry_credit * 100, 2),
            "put_width": round(put_width, 2),
            "call_width": round(call_width, 2)
        }
    }

def _backtest_bull_call_enhanced(
    data: pd.DataFrame, 
    timeframe: TimeFrame, 
    options_pricing: OptionsPricingService,
    volatility: float,
    dividend_yield: float,
    contracts: int = 1,
    custom_strikes: Optional[List[float]] = None
) -> dict:
    """
    Enhanced Bull Call Spread backtesting using Black-Scholes options pricing.
    
    Args:
        data: Historical price data
        timeframe: Daily, weekly, or monthly
        options_pricing: Options pricing service
        volatility: Implied volatility
        dividend_yield: Dividend yield
        contracts: Number of contracts
        custom_strikes: Optional custom strike prices
        
    Returns:
        Backtest results
    """
    # Get days to expiration
    days_to_expiration = _calculate_days_to_expiration(timeframe)
    
    # Get strike percentages
    strike_percentages = _get_strike_percentages_for_timeframe(timeframe)["bull_call"]
    
    # Initialize tracking variables
    total_trades = 0
    wins = 0
    total_pnl = 0.0
    pnl_list = []
    equity_curve = [1000.0]  # Start with $1000
    
    # Track max profit/loss
    max_profit_seen = 0.0
    max_loss_seen = 0.0
    
    # For each day in the data
    for i in range(len(data) - days_to_expiration):
        # Skip if not enough data for the full period
        if i + days_to_expiration >= len(data):
            continue
        
        # Entry price
        entry_price = data.iloc[i]['Close']
        
        # Exit price (at expiration)
        exit_price = data.iloc[i + days_to_expiration]['Close']
        
        # Calculate strikes
        if custom_strikes and len(custom_strikes) == 2:
            # Use custom strikes if provided
            lower_strike, upper_strike = custom_strikes
        else:
            # Calculate strikes based on percentages
            lower_strike = round(entry_price * strike_percentages["lower"], 2)
            upper_strike = round(entry_price * strike_percentages["upper"], 2)
        
        # Calculate spread prices at entry
        entry_prices = options_pricing.calculate_spread_prices(
            spread_type='bull_call',
            underlying_price=entry_price,
            strikes=[lower_strike, upper_strike],
            days_to_expiration=days_to_expiration,
            volatility=volatility,
            dividend_yield=dividend_yield
        )
        
        # Calculate spread prices at exit (expiration)
        exit_prices = options_pricing.calculate_spread_prices(
            spread_type='bull_call',
            underlying_price=exit_price,
            strikes=[lower_strike, upper_strike],
            days_to_expiration=0.01,  # Almost expired
            volatility=volatility,
            dividend_yield=dividend_yield
        )
        
        # Calculate P&L
        entry_debit = entry_prices['net_debit']
        max_loss = entry_debit * 100 * contracts
        max_profit = (upper_strike - lower_strike - entry_debit) * 100 * contracts
        
        # Calculate P&L at expiration
        if exit_price <= lower_strike:
            # Maximum loss
            pnl = -max_loss
        elif lower_strike < exit_price < upper_strike:
            # Partial profit
            pnl = ((exit_price - lower_strike) / (upper_strike - lower_strike) * max_profit) - max_loss
        else:
            # Maximum profit
            pnl = max_profit
            wins += 1
        
        # Update tracking variables
        total_trades += 1
        total_pnl += pnl
        pnl_list.append(pnl)
        equity_curve.append(equity_curve[-1] + pnl)
        
        # Update max profit/loss seen
        max_profit_seen = max(max_profit_seen, max_profit)
        max_loss_seen = max(max_loss_seen, max_loss)
    
    # Calculate metrics
    win_rate = wins / total_trades if total_trades > 0 else 0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    # Calculate Sharpe ratio
    returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] 
              for i in range(1, len(equity_curve))]
    sharpe_ratio = _calculate_sharpe_ratio(returns)
    
    # Calculate max drawdown
    max_drawdown = _calculate_max_drawdown(equity_curve)
    
    # Calculate probability of profit
    probability_of_profit = options_pricing.calculate_probability_of_profit(
        spread_type='bull_call',
        underlying_price=data.iloc[-1]['Close'],
        strikes=[lower_strike, upper_strike],
        days_to_expiration=days_to_expiration,
        volatility=volatility,
        dividend_yield=dividend_yield
    )
    
    # Calculate risk-reward ratio
    risk_reward_ratio = max_profit_seen / max_loss_seen if max_loss_seen > 0 else 0
    
    # Calculate breakeven point
    breakeven = lower_strike + entry_debit
    
    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate * 100, 2),
        "total_trades": total_trades,
        "avg_pnl_per_trade": round(avg_pnl, 2),
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "probability_of_profit": round(probability_of_profit * 100, 2),
        "risk_reward_ratio": round(risk_reward_ratio, 2),
        "max_profit": round(max_profit_seen, 2),
        "max_loss": round(max_loss_seen, 2),
        "breakeven_points": [round(breakeven, 2)],
        "avg_days_held": days_to_expiration,
        "strategy_details": {
            "lower_strike": lower_strike,
            "upper_strike": upper_strike,
            "entry_debit": round(entry_debit * 100, 2),
            "spread_width": round(upper_strike - lower_strike, 2)
        }
    }
