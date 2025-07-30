"""Iron Condor strategy service for backtesting data aggregation and analysis."""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database.models import Strategy, Backtest, Trade
from api.exceptions import ResourceNotFoundError, BusinessLogicError

logger = logging.getLogger(__name__)

class IronCondorService:
    """Service class for Iron Condor strategy data management and analysis."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.strategy_type = "iron_condor"
        
    def get_all_timeframes_data(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get Iron Condor strategy data for all timeframes."""
        try:
            timeframes = ["daily", "weekly", "monthly"]
            strategies_data = {}
            
            for timeframe in timeframes:
                timeframe_data = self._get_timeframe_data(
                    timeframe=timeframe,
                    limit=limit,
                    offset=offset
                )
                if timeframe_data:
                    strategies_data[timeframe] = timeframe_data
            
            if not strategies_data:
                raise ResourceNotFoundError("Iron Condor strategies", "all timeframes")
            
            return {"strategies": strategies_data}
            
        except Exception as e:
            logger.error(f"Error retrieving Iron Condor strategies: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve strategy data: {str(e)}")
    
    def get_timeframe_data(
        self,
        timeframe: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get Iron Condor strategy data for a specific timeframe."""
        try:
            # Validate timeframe
            valid_timeframes = ["daily", "weekly", "monthly"]
            if timeframe not in valid_timeframes:
                raise BusinessLogicError(
                    f"Invalid timeframe '{timeframe}'. Must be one of: {', '.join(valid_timeframes)}"
                )
            
            timeframe_data = self._get_timeframe_data(
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )
            
            if not timeframe_data:
                raise ResourceNotFoundError("Iron Condor strategies", f"timeframe: {timeframe}")
            
            return timeframe_data
            
        except BusinessLogicError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving {timeframe} Iron Condor data: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve {timeframe} strategy data: {str(e)}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get aggregated performance metrics across all timeframes."""
        try:
            timeframes = ["daily", "weekly", "monthly"]
            summary_data = {
                "total_trades": 0,
                "overall_win_rate": 0.0,
                "total_pnl": 0.0,
                "best_timeframe": None,
                "worst_drawdown": 0.0
            }
            
            by_timeframe = {}
            best_pnl = float('-inf')
            worst_drawdown = 0.0
            
            for timeframe in timeframes:
                tf_performance = self._calculate_timeframe_performance(timeframe)
                if tf_performance:
                    by_timeframe[timeframe] = tf_performance
                    
                    # Update summary metrics
                    summary_data["total_trades"] += tf_performance["total_trades"]
                    summary_data["total_pnl"] += tf_performance["total_pnl"]
                    
                    # Track best performing timeframe
                    if tf_performance["total_pnl"] > best_pnl:
                        best_pnl = tf_performance["total_pnl"]
                        summary_data["best_timeframe"] = timeframe
                    
                    # Track worst drawdown
                    if tf_performance["max_drawdown"] < worst_drawdown:
                        worst_drawdown = tf_performance["max_drawdown"]
            
            # Calculate overall win rate
            if summary_data["total_trades"] > 0:
                winning_trades = sum(
                    tf_data["winning_trades"] 
                    for tf_data in by_timeframe.values()
                )
                summary_data["overall_win_rate"] = winning_trades / summary_data["total_trades"]
            
            summary_data["worst_drawdown"] = worst_drawdown
            
            # Simplify by_timeframe data for response
            simplified_by_timeframe = {
                tf: {"win_rate": data["win_rate"], "pnl": data["total_pnl"]}
                for tf, data in by_timeframe.items()
            }
            
            return {
                "summary": summary_data,
                "by_timeframe": simplified_by_timeframe
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance summary: {str(e)}")
            raise BusinessLogicError(f"Failed to calculate performance metrics: {str(e)}")
    
    def _get_timeframe_data(
        self,
        timeframe: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Get strategy data for a specific timeframe with optional date filtering."""
        try:
            # Get strategies for this timeframe
            strategies_query = self.db.query(Strategy).filter(
                and_(
                    Strategy.strategy_type == self.strategy_type,
                    Strategy.parameters.op("->>")('"timeframe"') == timeframe
                )
            )
            
            strategies = strategies_query.all()
            if not strategies:
                return None
            
            strategy_ids = [s.id for s in strategies]
            
            # Get trades for these strategies
            trades_query = self.db.query(Trade).filter(
                Trade.strategy_id.in_(strategy_ids)
            )
            
            # Apply date filtering if provided
            if start_date:
                trades_query = trades_query.filter(Trade.trade_date >= start_date)
            if end_date:
                trades_query = trades_query.filter(Trade.trade_date <= end_date)
            
            # Get total count for metadata
            total_trades = trades_query.count()
            
            # Apply pagination
            trades = trades_query.order_by(Trade.trade_date.desc()).offset(offset).limit(limit).all()
            
            if not trades:
                return None
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(trades)
            
            # Get date range
            date_range = self._get_date_range(trades)
            
            # Transform trades to API format
            trades_data = [self._transform_trade_to_api_format(trade) for trade in trades]
            
            return {
                "metadata": {
                    "timeframe": timeframe,
                    "total_trades": total_trades,
                    "date_range": date_range
                },
                "performance": performance,
                "trades": trades_data
            }
            
        except Exception as e:
            logger.error(f"Error getting {timeframe} timeframe data: {str(e)}")
            return None
    
    def _calculate_timeframe_performance(self, timeframe: str) -> Optional[Dict[str, Any]]:
        """Calculate performance metrics for a specific timeframe."""
        try:
            # Get all trades for this timeframe (no pagination for performance calculation)
            timeframe_data = self._get_timeframe_data(
                timeframe=timeframe,
                limit=10000,  # Large limit to get all trades
                offset=0
            )
            
            if not timeframe_data or not timeframe_data["trades"]:
                return None
            
            trades = timeframe_data["trades"]
            performance = timeframe_data["performance"]
            
            # Add additional metrics needed for summary
            performance["total_trades"] = len(trades)
            performance["winning_trades"] = sum(1 for t in trades if t["pnl"] > 0)
            
            return performance
            
        except Exception as e:
            logger.error(f"Error calculating {timeframe} performance: {str(e)}")
            return None
    
    def _calculate_performance_metrics(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate performance metrics from a list of trades."""
        if not trades:
            return {}
        
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade.realized_pnl and trade.realized_pnl > 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Calculate P&L metrics
        pnl_values = [float(trade.realized_pnl or trade.credit_debit or 0) for trade in trades]
        total_pnl = sum(pnl_values)
        average_trade = total_pnl / total_trades if total_trades > 0 else 0.0
        
        # Calculate running balance for drawdown
        running_balance = []
        balance = 0.0
        for pnl in pnl_values:
            balance += pnl
            running_balance.append(balance)
        
        # Calculate maximum drawdown
        max_drawdown = 0.0
        peak = 0.0
        for balance in running_balance:
            if balance > peak:
                peak = balance
            drawdown = peak - balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown = -max_drawdown  # Make negative for consistency
        
        # Calculate Sharpe ratio (simplified)
        if len(pnl_values) > 1:
            import statistics
            returns_std = statistics.stdev(pnl_values)
            sharpe_ratio = (average_trade / returns_std) if returns_std > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        return {
            "win_rate": round(win_rate, 4),
            "total_pnl": round(total_pnl, 2),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "max_drawdown": round(max_drawdown, 2),
            "average_trade": round(average_trade, 2)
        }
    
    def _get_date_range(self, trades: List[Trade]) -> Dict[str, str]:
        """Get the date range for a list of trades."""
        if not trades:
            return {"start": None, "end": None}
        
        dates = [trade.trade_date for trade in trades if trade.trade_date]
        if not dates:
            return {"start": None, "end": None}
        
        return {
            "start": min(dates).isoformat(),
            "end": max(dates).isoformat()
        }
    
    def _transform_trade_to_api_format(self, trade: Trade) -> Dict[str, Any]:
        """Transform a Trade model to API response format."""
        try:
            # Extract strike prices from the strikes list
            # Assumes strikes are ordered: [put_long, put_short, call_short, call_long]
            strikes = trade.strikes or []
            strike_dict = {}
            
            if len(strikes) >= 4:
                strike_dict = {
                    "put_long": strikes[0],
                    "put_short": strikes[1], 
                    "call_short": strikes[2],
                    "call_long": strikes[3]
                }
            elif len(strikes) == 2:
                # Handle old format with just put/call strikes
                strike_dict = {
                    "put_short": strikes[0],
                    "call_short": strikes[1],
                    "put_long": strikes[0] - 5,  # Assume 5-point spread
                    "call_long": strikes[1] + 5
                }
            
            # Determine outcome based on P&L
            pnl = float(trade.realized_pnl or trade.credit_debit or 0)
            outcome = "win" if pnl > 0 else "loss"
            
            return {
                "id": trade.id,
                "entry_date": trade.trade_date.isoformat() if trade.trade_date else None,
                "expiration_date": trade.trade_date.isoformat() if trade.trade_date else None,  # Assume same day for 0DTE
                "strikes": strike_dict,
                "credit_received": float(trade.credit_debit or 0),
                "pnl": pnl,
                "outcome": outcome
            }
            
        except Exception as e:
            logger.error(f"Error transforming trade {trade.id}: {str(e)}")
            return {
                "id": trade.id,
                "entry_date": None,
                "expiration_date": None,
                "strikes": {},
                "credit_received": 0.0,
                "pnl": 0.0,
                "outcome": "unknown"
            }
    
    def validate_parameters(
        self,
        timeframe: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """Validate and normalize API parameters."""
        validated = {}
        
        # Validate timeframe
        if timeframe:
            valid_timeframes = ["daily", "weekly", "monthly"]
            if timeframe not in valid_timeframes:
                raise BusinessLogicError(
                    f"Invalid timeframe '{timeframe}'. Must be one of: {', '.join(valid_timeframes)}"
                )
            validated["timeframe"] = timeframe
        
        # Validate dates
        if start_date:
            try:
                validated["start_date"] = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise BusinessLogicError(f"Invalid start_date format. Expected YYYY-MM-DD, got: {start_date}")
        
        if end_date:
            try:
                validated["end_date"] = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise BusinessLogicError(f"Invalid end_date format. Expected YYYY-MM-DD, got: {end_date}")
        
        # Validate pagination
        if limit is not None:
            if limit < 1 or limit > 1000:
                raise BusinessLogicError("Limit must be between 1 and 1000")
            validated["limit"] = limit
        else:
            validated["limit"] = 100
        
        if offset is not None:
            if offset < 0:
                raise BusinessLogicError("Offset must be non-negative")
            validated["offset"] = offset
        else:
            validated["offset"] = 0
        
        # Validate date range logic
        if "start_date" in validated and "end_date" in validated:
            if validated["start_date"] > validated["end_date"]:
                raise BusinessLogicError("start_date must be before or equal to end_date")
        
        return validated