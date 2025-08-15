"""AI assessment service for trading strategies."""
import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from database.models import (
    AIAssessment, AISettings, AIUsageLog, MarketDataSnapshot,
    AIRecommendation
)
from database.config import SessionLocal
from services.market_data_service import MarketDataCollector

logger = logging.getLogger(__name__)


class AIAssessmentService:
    """Service for AI-powered strategy assessment using OpenAI GPT."""
    
    def __init__(self):
        """Initialize AI assessment service."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key and self.api_key != 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx':
            # Log API key format for debugging (safely)
            if self.api_key.startswith('sk-'):
                logger.info(f"OpenAI API key found - format looks correct (sk-****...{self.api_key[-4:]})")
            else:
                logger.warning(f"OpenAI API key found but format looks incorrect - should start with 'sk-'")
            
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                self.client = None
        else:
            self.client = None
            logger.warning("OpenAI API key not configured - AI assessments unavailable")
        
        self.market_data_collector = MarketDataCollector()
        
        # Rate limiting
        self._rate_limit_window = time.time()
        self._rate_limit_count = 0
        self._rate_limit_max = 10  # 10 requests per minute
        
        # Default settings
        self.default_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.default_temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
        self.default_max_tokens = int(os.getenv('OPENAI_MAX_COMPLETION_TOKENS', '2000'))
        self.default_reasoning_effort = os.getenv('OPENAI_REASONING_EFFORT', 'high')  # Only for reasoning models
        self.cache_ttl = int(os.getenv('AI_ASSESSMENT_CACHE_TTL', '300'))  # 5 minutes
        self.timeout = int(os.getenv('AI_ASSESSMENT_TIMEOUT', '30'))
    
    def assess_strategy(self, strategy_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Assess a trading strategy using AI.
        
        Args:
            strategy_params: Strategy configuration including type, strikes, expiration, etc.
            
        Returns:
            Assessment result with recommendation, confidence, and reasoning
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return None
        
        # Check rate limit
        if not self._check_rate_limit():
            logger.warning("Rate limit exceeded for AI assessments")
            return {"error": "Rate limit exceeded. Please try again later."}
        
        with SessionLocal() as db:
            # Check for cached assessment
            strategy_hash = self._calculate_strategy_hash(strategy_params)
            cached = self._get_cached_assessment(db, strategy_hash)
            if cached:
                logger.info(f"Returning cached assessment for hash {strategy_hash[:8]}...")
                return cached.to_dict()
            
            # Get current market data
            market_data = self._get_market_data()
            if not market_data:
                logger.error("Failed to fetch market data")
                return None
            
            # Build prompt
            prompt = self._build_prompt(strategy_params, market_data)
            
            # Get AI assessment
            start_time = time.time()
            try:
                # Note: response_format might not be supported on all models
                # Try with response_format first, fall back if not supported
                try:
                    # Prepare API parameters
                    api_params = {
                        "model": self.default_model,
                        "messages": [
                            {"role": "system", "content": "You are an expert options trader providing strategy analysis. Always respond with valid JSON."},
                            {"role": "user", "content": prompt}
                        ]
                    }
                    
                    # GPT-5 needs higher token limit because it uses tokens for reasoning
                    if self.default_model.startswith('gpt-5'):
                        api_params["max_completion_tokens"] = 8000  # Allow plenty for reasoning + output
                    else:
                        api_params["max_completion_tokens"] = self.default_max_tokens
                    
                    # Add response_format only for non-GPT-5 models (GPT-5 might not support it yet)
                    if not self.default_model.startswith('gpt-5'):
                        api_params["response_format"] = {"type": "json_object"}
                    
                    # Add temperature only for non-GPT-5 models (GPT-5 only supports default temperature)
                    if not self.default_model.startswith('gpt-5'):
                        api_params["temperature"] = self.default_temperature
                    
                    # Add reasoning effort only for o1 models (GPT-5 might not support it yet)
                    if self.default_model.startswith('o1'):
                        api_params["reasoning_effort"] = self.default_reasoning_effort
                    
                    logger.info(f"Calling OpenAI with model: {api_params['model']}")
                    logger.info(f"API params: {list(api_params.keys())}")
                    response = self.client.chat.completions.create(**api_params)
                except Exception as format_error:
                    if "response_format" in str(format_error):
                        logger.warning("response_format not supported, retrying without it")
                        # Retry without response_format parameter but keep reasoning
                        fallback_params = {
                            "model": self.default_model,
                            "messages": [
                                {"role": "system", "content": "You are an expert options trader providing strategy analysis. Always respond with valid JSON."},
                                {"role": "user", "content": prompt}
                            ]
                        }
                        
                        # GPT-5 needs higher token limit
                        if self.default_model.startswith('gpt-5'):
                            fallback_params["max_completion_tokens"] = 8000
                        else:
                            fallback_params["max_completion_tokens"] = self.default_max_tokens
                        
                        # Add temperature only for non-GPT-5 models
                        if not self.default_model.startswith('gpt-5'):
                            fallback_params["temperature"] = self.default_temperature
                        
                        # Add reasoning effort only for o1 models
                        if self.default_model.startswith('o1'):
                            fallback_params["reasoning_effort"] = self.default_reasoning_effort
                        
                        response = self.client.chat.completions.create(**fallback_params)
                    else:
                        # Log the specific error for debugging
                        logger.error(f"OpenAI API call failed: {str(format_error)}")
                        logger.error(f"Error type: {type(format_error)}")
                        
                        # Check for authentication errors
                        if "401" in str(format_error) or "unauthorized" in str(format_error).lower():
                            logger.error("Authentication error - check OPENAI_API_KEY")
                        elif "402" in str(format_error) or "billing" in str(format_error).lower():
                            logger.error("Billing/quota error - check OpenAI account")
                        elif "403" in str(format_error):
                            logger.error("Forbidden - API key might not have access to this model")
                        elif "404" in str(format_error):
                            logger.error(f"Model not found - {self.default_model} might not be available")
                        
                        raise format_error
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Debug the full response structure
                logger.info(f"OpenAI response object type: {type(response)}")
                logger.info(f"Response has {len(response.choices)} choices")
                
                if response.choices:
                    choice = response.choices[0]
                    logger.info(f"Choice object type: {type(choice)}")
                    logger.info(f"Choice has message: {hasattr(choice, 'message')}")
                    
                    if hasattr(choice, 'message'):
                        message = choice.message
                        logger.info(f"Message object type: {type(message)}")
                        logger.info(f"Message has content: {hasattr(message, 'content')}")
                        
                        if hasattr(message, 'content'):
                            content = message.content
                            logger.info(f"Content type: {type(content)}")
                            logger.info(f"Content value: {repr(content)}")
                            logger.info(f"Content is None: {content is None}")
                            logger.info(f"Content length: {len(content) if content else 0}")
                            
                            # Check if GPT-5 uses a different attribute
                            if not content and self.default_model.startswith('gpt-5'):
                                logger.info(f"GPT-5 detected with empty content. Checking all message attributes...")
                                for attr in dir(message):
                                    if not attr.startswith('_'):
                                        attr_value = getattr(message, attr, None)
                                        if attr_value and not callable(attr_value):
                                            logger.info(f"  {attr}: {repr(attr_value)[:200]}")
                        else:
                            logger.error("Message object has no 'content' attribute")
                            # Try to see what attributes it has
                            logger.info(f"Message attributes: {dir(message)}")
                    else:
                        logger.error("Choice object has no 'message' attribute")
                        logger.info(f"Choice attributes: {dir(choice)}")
                else:
                    logger.error("Response has no choices")
                
                # Log the raw response for debugging
                response_content = response.choices[0].message.content if response.choices else None
                logger.info(f"Raw OpenAI response content (first 200 chars): {response_content[:200] if response_content else 'None'}...")
                logger.info(f"Response content type: {type(response_content)}")
                logger.info(f"Response content length: {len(response_content) if response_content else 0}")
                
                # Parse response
                assessment_data = self._parse_openai_response(response_content)
                if not assessment_data:
                    logger.error("Failed to parse OpenAI response")
                    return None
                
                # Debug usage information
                if hasattr(response, 'usage') and response.usage:
                    logger.info(f"Usage object: {response.usage}")
                    logger.info(f"Prompt tokens: {response.usage.prompt_tokens}")
                    logger.info(f"Completion tokens: {response.usage.completion_tokens}")
                    logger.info(f"Total tokens: {response.usage.total_tokens}")
                else:
                    logger.error("Response has no usage information")
                
                # Calculate cost
                tokens_input = response.usage.prompt_tokens if response.usage else 0
                tokens_output = response.usage.completion_tokens if response.usage else 0
                tokens_total = response.usage.total_tokens if response.usage else 0
                cost_usd = self._calculate_cost(self.default_model, tokens_input, tokens_output)
                
                # Save assessment
                saved = self._save_assessment(
                    db, assessment_data, strategy_params, market_data,
                    tokens_total, processing_time_ms
                )
                
                # Log usage
                self._log_usage(
                    db,
                    assessment_id=saved.assessment_id,
                    operation="assess_strategy",
                    model=self.default_model,
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    tokens_total=tokens_total,
                    cost_usd=cost_usd,
                    response_time_ms=processing_time_ms,
                    success=True,
                    error_message=None
                )
                
                db.commit()
                return saved.to_dict()
                
            except Exception as e:
                logger.error(f"AI assessment failed: {str(e)}")
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Log failed usage
                self._log_usage(
                    db,
                    assessment_id=None,
                    operation="assess_strategy",
                    model=self.default_model,
                    tokens_input=0,
                    tokens_output=0,
                    tokens_total=0,
                    cost_usd=Decimal("0.00"),
                    response_time_ms=processing_time_ms,
                    success=False,
                    error_message=str(e)
                )
                db.commit()
                return None
    
    def _get_market_data(self) -> Optional[Dict[str, Any]]:
        """Get current market data for assessment context."""
        try:
            with SessionLocal() as db:
                snapshot = self.market_data_collector.get_or_create_snapshot(db)
                if snapshot:
                    return snapshot.to_dict()
                else:
                    # Fallback to collecting fresh data
                    return self.market_data_collector.collect_market_snapshot()
        except Exception as e:
            logger.error(f"Failed to get market data: {str(e)}")
            return None
    
    def _build_prompt(self, strategy_params: Dict[str, Any], market_data: Dict[str, Any]) -> str:
        """Build structured prompt for OpenAI."""
        # Convert Decimal values to float for formatting
        def to_float(val):
            return float(val) if isinstance(val, Decimal) else val
        
        spx_price = to_float(market_data.get('spx_price', 0))
        spx_change = to_float(market_data.get('spx_change', 0))
        spx_change_percent = to_float(market_data.get('spx_change_percent', 0))
        vix_level = to_float(market_data.get('vix_level', 0))
        vix_change = to_float(market_data.get('vix_change', 0))
        volume_vs_avg = to_float(market_data.get('volume_vs_avg', 1))
        
        # Get correct symbol and price data
        symbol = strategy_params.get('symbol', 'SPY')
        
        # Use the correct price data based on symbol
        if symbol.upper() == 'SPY':
            # Use SPY data if available, fallback to collecting fresh SPY data, then SPX data
            spy_price_from_db = market_data.get('spy_price')
            if spy_price_from_db is not None:
                current_price = to_float(spy_price_from_db)
                price_change = to_float(market_data.get('spy_change', 0))
                change_percent = to_float(market_data.get('spy_change_percent', 0))
            else:
                # Fallback: get fresh SPY data directly
                try:
                    fresh_spy_data = self.market_data_collector.get_current_price('SPY')
                    if fresh_spy_data:
                        current_price = to_float(fresh_spy_data['price'])
                        price_change = to_float(fresh_spy_data['change'])
                        change_percent = to_float(fresh_spy_data['change_percent'])
                    else:
                        # Final fallback to SPX data
                        current_price = spx_price
                        price_change = spx_change
                        change_percent = spx_change_percent
                except Exception as e:
                    logger.warning(f"Failed to get fresh SPY data: {e}")
                    current_price = spx_price
                    price_change = spx_change
                    change_percent = spx_change_percent
        elif symbol.upper() == 'SPX':
            # Use SPX data
            current_price = spx_price
            price_change = spx_change
            change_percent = spx_change_percent
        else:
            # Default to SPX data for other symbols
            current_price = spx_price
            price_change = spx_change
            change_percent = spx_change_percent
        
        # Calculate key metrics for analysis
        strikes = strategy_params.get('strikes', {})
        strike_list = sorted([float(v) for v in strikes.values()])
        expiration_date = strategy_params.get('expiration', 'unknown')
        
        # Handle None values for profit/loss calculations
        max_profit = strategy_params.get('max_profit') or 0
        max_loss = strategy_params.get('max_loss') or 0
        quantity = strategy_params.get('quantity') or 1
        
        # Calculate days to expiration and time decay urgency
        try:
            from datetime import datetime
            exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
            current_date = datetime.now()
            days_to_exp = (exp_date - current_date).days
            # For 0DTE strategies, ensure we show 0 days correctly
            days_to_exp = max(0, days_to_exp)  # Don't show negative days
            time_decay_urgency = "EXTREME" if days_to_exp == 0 else "HIGH" if days_to_exp <= 7 else "MODERATE" if days_to_exp <= 30 else "LOW"
        except:
            days_to_exp = 0  # Default to 0DTE
            time_decay_urgency = "EXTREME"
            
        # Calculate strike distances and moneyness
        strike_analysis = {}
        for strike_type, strike_price in strikes.items():
            distance_pct = ((float(strike_price) - current_price) / current_price) * 100
            moneyness = "ITM" if ((strike_type.lower().find('put') >= 0 and float(strike_price) > current_price) or 
                                 (strike_type.lower().find('call') >= 0 and float(strike_price) < current_price)) else "OTM"
            strike_analysis[strike_type] = {
                "price": float(strike_price),
                "distance": f"{distance_pct:+.1f}%",
                "moneyness": moneyness
            }

        prompt = f"""You are a veteran options trader and educator providing comprehensive analysis for a {symbol} options strategy. Use your reasoning capabilities to provide deep, thoughtful analysis that demonstrates your analytical process.

REASONING APPROACH:
Think step-by-step through this strategy analysis. Consider multiple perspectives, weigh conflicting factors, and show your analytical reasoning process. Your response should demonstrate sophisticated understanding of options mechanics, market dynamics, and risk management.

STRATEGY DETAILS:
- Strategy Type: {strategy_params.get('strategy_type', 'unknown').replace('_', ' ').title()}
- Underlying: {symbol} (Current: ${current_price:.2f}, {price_change:+.2f} / {change_percent:+.2f}% today)
- Strike Analysis: {json.dumps(strike_analysis)}
- Expiration: {expiration_date} ({days_to_exp} days remaining)
- Time Decay Urgency: {time_decay_urgency}
- Position Size: {quantity} contracts
- Max Profit: ${max_profit:,.0f}
- Max Loss: ${max_loss:,.0f}
- Risk/Reward Ratio: 1:{(max_profit / max_loss if max_loss > 0 else 0):,.2f}

CURRENT MARKET ENVIRONMENT:
- {symbol} Momentum: {change_percent:+.2f}% today, ${price_change:+.2f} move
- Volatility Environment: VIX at {vix_level:.1f} ({vix_change:+.1f} change) - {"Low" if vix_level < 15 else "Moderate" if vix_level < 25 else "High"} volatility regime
- Volume Activity: {volume_vs_avg:.0%} of average daily volume - {"Heavy" if volume_vs_avg > 1.5 else "Above Average" if volume_vs_avg > 1.1 else "Normal" if volume_vs_avg > 0.9 else "Light"} trading
- Technical Context: {json.dumps(market_data.get('technical_indicators', {}))}

DEEP REASONING ANALYSIS REQUIRED:
Use your advanced reasoning to provide comprehensive analysis. Think through each aspect systematically:

1. STRATEGY MECHANICS REASONING: Analyze the mathematical structure of this strategy. Consider profit zones, loss zones, and break-even points. Reason through why this strategy exists and when traders typically deploy it.

2. CURRENT MARKET CONDITIONS ASSESSMENT: Evaluate TODAY's specific conditions step-by-step. Consider {symbol}'s recent momentum, implied volatility levels, and how these factors interact with the strategy's success probability.

3. GREEKS IMPACT ANALYSIS: Reason through how each Greek (Delta, Gamma, Theta, Vega) will affect this position over time. Consider how Greeks change as price moves and time passes. Calculate the net Greek exposure.

4. TIME DECAY REASONING: With {days_to_exp} days to expiration and {time_decay_urgency} time decay urgency, reason through the time decay trajectory. Consider optimal timing for entry and exit.

5. VOLATILITY ENVIRONMENT EVALUATION: Analyze VIX at {vix_level:.1f} and its implications. Consider implied vs realized volatility and how vol changes would impact the strategy.

6. PROBABILITY ASSESSMENT: Using your reasoning, estimate the probability of success for this specific setup given current conditions. Consider price distribution, time remaining, and volatility.

7. RISK MANAGEMENT FRAMEWORK: Develop a comprehensive risk management approach. Consider position sizing, stop-losses, profit targets, and adjustment techniques.

8. COMPARATIVE ANALYSIS: Compare this strategy to alternatives given current conditions. What other strategies might be better or worse right now?

Return comprehensive JSON analysis:
{{
  "recommendation": "GO/CAUTION/NO-GO",
  "confidence": 85,
  "reasoning": {{
    "supporting_factors": [
      "Specific technical reason with price levels and percentages",
      "Volatility environment advantage with VIX analysis", 
      "Time decay scenario with days to expiration context",
      "Market momentum factor with directional bias support"
    ],
    "risk_factors": [
      "Specific risk with quantified impact (e.g., 'If {symbol} drops below $X')",
      "Time decay risk with timeline (e.g., 'Theta burn of $X per day')",
      "Volatility risk scenario with VIX threshold",
      "Liquidity or execution risk with specific concerns"
    ]
  }},
  "market_regime": "Educational explanation: Current {symbol} conditions show [specific technical pattern] with VIX at {vix_level:.1f} indicating [vol regime], creating [favorable/unfavorable] environment for this strategy because [specific reason related to Greeks and strategy mechanics]",
  "strategy_education": {{
    "how_it_works": "Clear explanation of strategy mechanics and profit/loss dynamics",
    "why_use_now": "Specific reasons this strategy fits current market conditions",
    "greeks_impact": "How Delta, Theta, Vega affect this position with current market data",
    "success_criteria": "Specific price targets and timeframe for profitable outcome",
    "failure_scenarios": "Specific conditions that would cause losses with price levels",
    "key_learning": "Main options trading concept this strategy demonstrates"
  }},
  "exit_strategy": {{
    "profit_target": "Specific profit level to close (e.g., 50% max profit)",
    "stop_loss": "Specific loss level to exit (e.g., 200% of premium paid)",
    "time_exit": "Timeline considerations (e.g., close 7 days before expiration)",
    "adjustment_opportunities": "How to modify position if market moves against you"
  }}
}}"""
        
        return prompt
    
    def _calculate_strategy_hash(self, strategy_params: Dict[str, Any]) -> str:
        """Calculate unique hash for strategy parameters."""
        # Sort parameters for consistent hashing
        sorted_params = json.dumps(strategy_params, sort_keys=True)
        return hashlib.sha256(sorted_params.encode()).hexdigest()
    
    def _parse_openai_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse and validate OpenAI response."""
        if not response:
            logger.error("Empty response received from OpenAI")
            return None
        
        # Log response details for debugging
        logger.info(f"Attempting to parse response of length {len(response)}")
        
        # Handle common cases where response might not be JSON
        response_stripped = response.strip()
        
        # Check if it looks like an HTML error page
        if response_stripped.startswith('<!DOCTYPE') or response_stripped.startswith('<html'):
            logger.error("Response appears to be HTML (possibly error page), not JSON")
            logger.error(f"HTML response content: {response_stripped[:500]}...")
            return None
        
        # Check if it looks like a plain text error message
        if not response_stripped.startswith('{') and not response_stripped.startswith('['):
            logger.error(f"Response doesn't appear to be JSON. Content: {response_stripped[:200]}...")
            return None
        
        try:
            data = json.loads(response_stripped)
            
            # Validate required fields
            if not self._validate_assessment(data):
                return None
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response content that failed to parse: {response_stripped[:500]}...")
            
            # Try to extract JSON if it's wrapped in other text
            try:
                # Look for JSON object in the response
                start_idx = response_stripped.find('{')
                end_idx = response_stripped.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_part = response_stripped[start_idx:end_idx]
                    logger.info(f"Attempting to parse extracted JSON: {json_part[:200]}...")
                    data = json.loads(json_part)
                    
                    if self._validate_assessment(data):
                        logger.info("Successfully parsed extracted JSON")
                        return data
            except Exception as extract_error:
                logger.error(f"Failed to extract and parse JSON: {str(extract_error)}")
            
            return None
    
    def _validate_assessment(self, data: Dict[str, Any]) -> bool:
        """Validate assessment data structure."""
        required_fields = ['recommendation', 'confidence', 'reasoning', 'market_regime']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate recommendation
        if data['recommendation'] not in ['GO', 'CAUTION', 'NO-GO']:
            logger.error(f"Invalid recommendation: {data['recommendation']}")
            return False
        
        # Validate confidence
        if not isinstance(data['confidence'], (int, float)) or not 0 <= data['confidence'] <= 100:
            logger.error(f"Invalid confidence: {data['confidence']}")
            return False
        
        # Validate reasoning structure
        if not isinstance(data['reasoning'], dict):
            logger.error("Invalid reasoning structure")
            return False
        
        if 'supporting_factors' not in data['reasoning'] or 'risk_factors' not in data['reasoning']:
            logger.error("Missing reasoning factors")
            return False
        
        # Optional enhanced fields (don't fail validation if missing)
        if 'strategy_education' in data:
            if not isinstance(data['strategy_education'], dict):
                logger.warning("Invalid strategy_education structure - ignoring")
                
        if 'exit_strategy' in data:
            if not isinstance(data['exit_strategy'], dict):
                logger.warning("Invalid exit_strategy structure - ignoring")
        
        return True
    
    def _get_cached_assessment(self, db: Session, strategy_hash: str) -> Optional[AIAssessment]:
        """Get cached assessment if not expired."""
        assessment = db.query(AIAssessment).filter(
            AIAssessment.strategy_hash == strategy_hash,
            AIAssessment.expires_at > datetime.now(timezone.utc)
        ).first()
        return assessment
    
    def _save_assessment(self, db: Session, assessment_data: Dict[str, Any],
                        strategy_params: Dict[str, Any], market_conditions: Dict[str, Any],
                        token_usage: int, processing_time_ms: int) -> AIAssessment:
        """Save assessment to database."""
        # Convert any Decimal values to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            return obj
        
        market_conditions_clean = convert_decimals(market_conditions)
        
        # Add market_regime from AI response to market_conditions
        market_conditions_clean['market_regime'] = assessment_data.get('market_regime', '')
        
        assessment = AIAssessment(
            assessment_id=f"assess_{datetime.now().strftime('%Y%m%d%H%M%S')}_{strategy_params.get('symbol', 'SPY')}",
            strategy_hash=self._calculate_strategy_hash(strategy_params),
            strategy_type=strategy_params.get('strategy_type', 'unknown'),
            symbol=strategy_params.get('symbol', 'SPY'),
            strategy_params=strategy_params,
            recommendation=assessment_data['recommendation'],
            confidence=assessment_data['confidence'],
            reasoning=assessment_data['reasoning'],
            market_conditions=market_conditions_clean,
            model_used=self.default_model,
            token_usage=token_usage,
            cost_usd=self._calculate_cost(self.default_model, token_usage, 0),
            processing_time_ms=processing_time_ms,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.cache_ttl)
        )
        
        db.add(assessment)
        db.flush()  # Flush to get the ID without committing the transaction
        return assessment
    
    def _log_usage(self, db: Session, assessment_id: Optional[str], operation: str,
                  model: str, tokens_input: int, tokens_output: int, tokens_total: int,
                  cost_usd: Decimal, response_time_ms: int, success: bool,
                  error_message: Optional[str]):
        """Log AI usage for monitoring and cost tracking."""
        usage_log = AIUsageLog(
            assessment_id=assessment_id,
            operation=operation,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message
        )
        db.add(usage_log)
    
    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limit."""
        current_time = time.time()
        
        # Reset window if expired (60 seconds)
        if current_time - self._rate_limit_window > 60:
            self._rate_limit_window = current_time
            self._rate_limit_count = 0
        
        # Check if under limit
        if self._rate_limit_count < self._rate_limit_max:
            self._rate_limit_count += 1
            return True
        
        return False
    
    def _reset_rate_limiter(self):
        """Reset rate limiter (for testing)."""
        self._rate_limit_window = time.time()
        self._rate_limit_count = 0
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost for API usage."""
        # Pricing per 1M tokens (example rates, adjust as needed)
        pricing = {
            'gpt-4': {'input': 30.00, 'output': 60.00},  # $30/$60 per 1M tokens
            'gpt-4-turbo': {'input': 10.00, 'output': 30.00},  # $10/$30 per 1M tokens
            'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},  # $0.50/$1.50 per 1M tokens
            'gpt-5': {'input': 50.00, 'output': 100.00}  # Estimated for GPT-5
        }
        
        # Get pricing for model or use GPT-4 as default
        model_pricing = pricing.get(model, pricing['gpt-4'])
        
        # Calculate cost
        input_cost = Decimal(str(input_tokens * model_pricing['input'] / 1_000_000))
        output_cost = Decimal(str(output_tokens * model_pricing['output'] / 1_000_000))
        
        return input_cost + output_cost
    
    def _get_settings(self, db: Session) -> AISettings:
        """Get or create AI settings."""
        settings = db.query(AISettings).filter(AISettings.user_id == None).first()
        if not settings:
            settings = AISettings(
                user_id=None,
                model='gpt-5',
                temperature=Decimal('0.30'),
                max_tokens=800,
                cache_ttl=300,
                reasoning_effort='high',  # Use high reasoning for better analysis
                auto_assess=False
            )
            db.add(settings)
            # Don't commit here as it's called within another transaction
        return settings