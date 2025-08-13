"""
Options Pricing Service - Black-Scholes Implementation

This service provides accurate options pricing using the Black-Scholes model,
which accounts for strike price, time to expiration, volatility, interest rates,
and underlying price.

Features:
- Calculate option prices for calls and puts
- Calculate option Greeks (delta, gamma, theta, vega, rho)
- Calculate implied volatility from option prices
- Support for European-style options
"""

import math
import numpy as np
from scipy.stats import norm
from typing import Dict, Tuple, Literal, Optional, Union
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class OptionsPricingService:
    """Service for calculating option prices and Greeks using Black-Scholes model."""
    
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize the options pricing service.
        
        Args:
            risk_free_rate: Annual risk-free interest rate (default: 5%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_option_price(
        self,
        option_type: Literal['call', 'put'],
        underlying_price: float,
        strike_price: float,
        days_to_expiration: float,
        volatility: float,
        dividend_yield: float = 0.0
    ) -> float:
        """
        Calculate the theoretical price of an option using the Black-Scholes model.
        
        Args:
            option_type: 'call' or 'put'
            underlying_price: Current price of the underlying asset
            strike_price: Strike price of the option
            days_to_expiration: Number of days until expiration
            volatility: Implied volatility as a decimal (e.g., 0.20 for 20%)
            dividend_yield: Annual dividend yield as a decimal (default: 0)
            
        Returns:
            Theoretical option price
        """
        # Convert days to years for the model
        time_to_expiration = days_to_expiration / 365.0
        
        # Handle expired or nearly expired options
        if time_to_expiration <= 0.0001:  # Approximately 1 hour
            if option_type == 'call':
                return max(0, underlying_price - strike_price)
            else:
                return max(0, strike_price - underlying_price)
        
        # Calculate d1 and d2
        d1, d2 = self._calculate_d1_d2(
            underlying_price, strike_price, time_to_expiration, 
            volatility, self.risk_free_rate, dividend_yield
        )
        
        # Calculate option price
        if option_type == 'call':
            option_price = (underlying_price * math.exp(-dividend_yield * time_to_expiration) * 
                           norm.cdf(d1)) - (strike_price * math.exp(-self.risk_free_rate * 
                           time_to_expiration) * norm.cdf(d2))
        else:  # put
            option_price = (strike_price * math.exp(-self.risk_free_rate * time_to_expiration) * 
                           norm.cdf(-d2)) - (underlying_price * 
                           math.exp(-dividend_yield * time_to_expiration) * norm.cdf(-d1))
        
        return max(0.01, option_price)  # Ensure minimum price of $0.01
    
    def calculate_greeks(
        self,
        option_type: Literal['call', 'put'],
        underlying_price: float,
        strike_price: float,
        days_to_expiration: float,
        volatility: float,
        dividend_yield: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate option Greeks using the Black-Scholes model.
        
        Args:
            option_type: 'call' or 'put'
            underlying_price: Current price of the underlying asset
            strike_price: Strike price of the option
            days_to_expiration: Number of days until expiration
            volatility: Implied volatility as a decimal (e.g., 0.20 for 20%)
            dividend_yield: Annual dividend yield as a decimal (default: 0)
            
        Returns:
            Dictionary containing delta, gamma, theta, vega, and rho
        """
        # Convert days to years for the model
        time_to_expiration = days_to_expiration / 365.0
        
        # Handle expired or nearly expired options
        if time_to_expiration <= 0.0001:  # Approximately 1 hour
            return {
                'delta': 1.0 if option_type == 'call' and underlying_price > strike_price else 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0
            }
        
        # Calculate d1 and d2
        d1, d2 = self._calculate_d1_d2(
            underlying_price, strike_price, time_to_expiration, 
            volatility, self.risk_free_rate, dividend_yield
        )
        
        # Calculate delta
        if option_type == 'call':
            delta = math.exp(-dividend_yield * time_to_expiration) * norm.cdf(d1)
        else:  # put
            delta = math.exp(-dividend_yield * time_to_expiration) * (norm.cdf(d1) - 1)
        
        # Calculate gamma (same for calls and puts)
        gamma = (norm.pdf(d1) * math.exp(-dividend_yield * time_to_expiration)) / (
            underlying_price * volatility * math.sqrt(time_to_expiration)
        )
        
        # Calculate vega (same for calls and puts)
        # Vega is expressed as change per 1% change in volatility
        vega = 0.01 * underlying_price * math.sqrt(time_to_expiration) * norm.pdf(d1) * math.exp(
            -dividend_yield * time_to_expiration
        )
        
        # Calculate theta
        # Theta is expressed as change per calendar day
        theta_factor = -underlying_price * volatility * math.exp(-dividend_yield * time_to_expiration) * norm.pdf(d1) / (
            2 * math.sqrt(time_to_expiration)
        ) / 365.0
        
        if option_type == 'call':
            theta = theta_factor - self.risk_free_rate * strike_price * math.exp(
                -self.risk_free_rate * time_to_expiration
            ) * norm.cdf(d2) / 365.0 + dividend_yield * underlying_price * math.exp(
                -dividend_yield * time_to_expiration
            ) * norm.cdf(d1) / 365.0
        else:  # put
            theta = theta_factor + self.risk_free_rate * strike_price * math.exp(
                -self.risk_free_rate * time_to_expiration
            ) * norm.cdf(-d2) / 365.0 - dividend_yield * underlying_price * math.exp(
                -dividend_yield * time_to_expiration
            ) * norm.cdf(-d1) / 365.0
        
        # Calculate rho
        # Rho is expressed as change per 1% change in interest rate
        if option_type == 'call':
            rho = 0.01 * strike_price * time_to_expiration * math.exp(
                -self.risk_free_rate * time_to_expiration
            ) * norm.cdf(d2)
        else:  # put
            rho = -0.01 * strike_price * time_to_expiration * math.exp(
                -self.risk_free_rate * time_to_expiration
            ) * norm.cdf(-d2)
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }
    
    def calculate_implied_volatility(
        self,
        option_type: Literal['call', 'put'],
        option_price: float,
        underlying_price: float,
        strike_price: float,
        days_to_expiration: float,
        dividend_yield: float = 0.0,
        precision: float = 0.0001,
        max_iterations: int = 100
    ) -> Optional[float]:
        """
        Calculate implied volatility using the Newton-Raphson method.
        
        Args:
            option_type: 'call' or 'put'
            option_price: Market price of the option
            underlying_price: Current price of the underlying asset
            strike_price: Strike price of the option
            days_to_expiration: Number of days until expiration
            dividend_yield: Annual dividend yield as a decimal (default: 0)
            precision: Desired precision for implied volatility calculation
            max_iterations: Maximum number of iterations for the algorithm
            
        Returns:
            Implied volatility as a decimal, or None if calculation fails
        """
        # Convert days to years for the model
        time_to_expiration = days_to_expiration / 365.0
        
        # Handle expired or nearly expired options
        if time_to_expiration <= 0.0001:  # Approximately 1 hour
            return None
        
        # Initial guess for implied volatility
        # Use different initial guesses based on moneyness
        moneyness = underlying_price / strike_price
        if 0.8 <= moneyness <= 1.2:
            # Near the money
            vol = 0.3
        elif moneyness < 0.8:
            # Deep out of the money
            vol = 0.5
        else:
            # Deep in the money
            vol = 0.2
        
        # Newton-Raphson method to find implied volatility
        for i in range(max_iterations):
            # Calculate option price with current volatility estimate
            price = self.calculate_option_price(
                option_type, underlying_price, strike_price, 
                days_to_expiration, vol, dividend_yield
            )
            
            # Calculate price difference
            price_diff = price - option_price
            
            # If we're within precision, return the volatility
            if abs(price_diff) < precision:
                return vol
            
            # Calculate vega
            vega = self.calculate_greeks(
                option_type, underlying_price, strike_price,
                days_to_expiration, vol, dividend_yield
            )['vega']
            
            # Avoid division by zero
            if abs(vega) < 1e-10:
                vega = 1e-10
            
            # Update volatility estimate
            vol = vol - price_diff / (vega * 100)  # Adjust for vega scaling
            
            # Ensure volatility stays within reasonable bounds
            vol = max(0.001, min(5.0, vol))
        
        # If we reach here, we didn't converge
        logger.warning(
            f"Implied volatility calculation did not converge for {option_type} option "
            f"with price {option_price}, underlying {underlying_price}, strike {strike_price}, "
            f"and {days_to_expiration} days to expiration."
        )
        return None
    
    def calculate_spread_prices(
        self,
        spread_type: Literal['bull_call', 'bear_call', 'bull_put', 'bear_put', 'iron_condor', 'butterfly'],
        underlying_price: float,
        strikes: list,
        days_to_expiration: float,
        volatility: Union[float, list],
        dividend_yield: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate prices and Greeks for common option spreads.
        
        Args:
            spread_type: Type of spread strategy
            underlying_price: Current price of the underlying asset
            strikes: List of strike prices for the spread
            days_to_expiration: Number of days until expiration
            volatility: Either a single volatility value or a list of volatilities for each option
            dividend_yield: Annual dividend yield as a decimal (default: 0)
            
        Returns:
            Dictionary containing spread price, max profit, max loss, and breakeven points
        """
        # Validate inputs based on spread type
        if spread_type == 'bull_call' or spread_type == 'bear_put':
            if len(strikes) != 2:
                raise ValueError(f"{spread_type} requires exactly 2 strikes")
        elif spread_type == 'bear_call' or spread_type == 'bull_put':
            if len(strikes) != 2:
                raise ValueError(f"{spread_type} requires exactly 2 strikes")
        elif spread_type == 'iron_condor':
            if len(strikes) != 4:
                raise ValueError("Iron condor requires exactly 4 strikes")
        elif spread_type == 'butterfly':
            if len(strikes) != 3:
                raise ValueError("Butterfly requires exactly 3 strikes")
        
        # Ensure volatility is a list with the right length
        if isinstance(volatility, float):
            if spread_type == 'iron_condor':
                volatility = [volatility] * 4
            elif spread_type == 'butterfly':
                volatility = [volatility] * 3
            else:
                volatility = [volatility] * 2
        
        # Calculate prices based on spread type
        if spread_type == 'bull_call':
            # Buy lower strike call, sell higher strike call
            lower_call = self.calculate_option_price(
                'call', underlying_price, strikes[0], days_to_expiration, volatility[0], dividend_yield
            )
            higher_call = self.calculate_option_price(
                'call', underlying_price, strikes[1], days_to_expiration, volatility[1], dividend_yield
            )
            
            net_debit = lower_call - higher_call
            max_profit = strikes[1] - strikes[0] - net_debit
            max_loss = net_debit
            breakeven = strikes[0] + net_debit
            
            return {
                'net_debit': net_debit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'breakeven': breakeven
            }
            
        elif spread_type == 'bear_call':
            # Sell lower strike call, buy higher strike call
            lower_call = self.calculate_option_price(
                'call', underlying_price, strikes[0], days_to_expiration, volatility[0], dividend_yield
            )
            higher_call = self.calculate_option_price(
                'call', underlying_price, strikes[1], days_to_expiration, volatility[1], dividend_yield
            )
            
            net_credit = lower_call - higher_call
            max_profit = net_credit
            max_loss = (strikes[1] - strikes[0]) - net_credit
            breakeven = strikes[0] + net_credit
            
            return {
                'net_credit': net_credit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'breakeven': breakeven
            }
            
        elif spread_type == 'bull_put':
            # Sell higher strike put, buy lower strike put
            lower_put = self.calculate_option_price(
                'put', underlying_price, strikes[0], days_to_expiration, volatility[0], dividend_yield
            )
            higher_put = self.calculate_option_price(
                'put', underlying_price, strikes[1], days_to_expiration, volatility[1], dividend_yield
            )
            
            net_credit = higher_put - lower_put
            max_profit = net_credit
            max_loss = (strikes[1] - strikes[0]) - net_credit
            breakeven = strikes[1] - net_credit
            
            return {
                'net_credit': net_credit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'breakeven': breakeven
            }
            
        elif spread_type == 'bear_put':
            # Buy higher strike put, sell lower strike put
            lower_put = self.calculate_option_price(
                'put', underlying_price, strikes[0], days_to_expiration, volatility[0], dividend_yield
            )
            higher_put = self.calculate_option_price(
                'put', underlying_price, strikes[1], days_to_expiration, volatility[1], dividend_yield
            )
            
            net_debit = higher_put - lower_put
            max_profit = strikes[1] - strikes[0] - net_debit
            max_loss = net_debit
            breakeven = strikes[1] - net_debit
            
            return {
                'net_debit': net_debit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'breakeven': breakeven
            }
            
        elif spread_type == 'iron_condor':
            # Strikes should be in order: [put_buy, put_sell, call_sell, call_buy]
            put_buy = self.calculate_option_price(
                'put', underlying_price, strikes[0], days_to_expiration, volatility[0], dividend_yield
            )
            put_sell = self.calculate_option_price(
                'put', underlying_price, strikes[1], days_to_expiration, volatility[1], dividend_yield
            )
            call_sell = self.calculate_option_price(
                'call', underlying_price, strikes[2], days_to_expiration, volatility[2], dividend_yield
            )
            call_buy = self.calculate_option_price(
                'call', underlying_price, strikes[3], days_to_expiration, volatility[3], dividend_yield
            )
            
            # Credit from selling put spread and call spread
            put_credit = put_sell - put_buy
            call_credit = call_sell - call_buy
            net_credit = put_credit + call_credit
            
            # Max loss is the wider of the two spreads minus the credit received
            put_width = strikes[1] - strikes[0]
            call_width = strikes[3] - strikes[2]
            max_loss = max(put_width, call_width) - net_credit
            
            # Max profit is the credit received
            max_profit = net_credit
            
            # Breakeven points
            lower_breakeven = strikes[1] - net_credit
            upper_breakeven = strikes[2] + net_credit
            
            return {
                'net_credit': net_credit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'lower_breakeven': lower_breakeven,
                'upper_breakeven': upper_breakeven,
                'put_credit': put_credit,
                'call_credit': call_credit
            }
            
        elif spread_type == 'butterfly':
            # Strikes should be in order: [lower, middle, upper]
            # For call butterfly: Buy lower, sell 2x middle, buy upper
            lower_call = self.calculate_option_price(
                'call', underlying_price, strikes[0], days_to_expiration, volatility[0], dividend_yield
            )
            middle_call = self.calculate_option_price(
                'call', underlying_price, strikes[1], days_to_expiration, volatility[1], dividend_yield
            )
            upper_call = self.calculate_option_price(
                'call', underlying_price, strikes[2], days_to_expiration, volatility[2], dividend_yield
            )
            
            # Net debit for butterfly
            net_debit = lower_call + upper_call - (2 * middle_call)
            
            # Max profit occurs at middle strike at expiration
            max_profit = strikes[1] - strikes[0] - net_debit
            
            # Max loss is limited to the initial debit
            max_loss = net_debit
            
            # Breakeven points
            lower_breakeven = strikes[0] + net_debit
            upper_breakeven = strikes[2] - net_debit
            
            return {
                'net_debit': net_debit,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'lower_breakeven': lower_breakeven,
                'upper_breakeven': upper_breakeven
            }
        
        else:
            raise ValueError(f"Unsupported spread type: {spread_type}")
    
    def calculate_probability_of_profit(
        self,
        spread_type: str,
        underlying_price: float,
        strikes: list,
        days_to_expiration: float,
        volatility: float,
        dividend_yield: float = 0.0
    ) -> float:
        """
        Calculate the approximate probability of profit for a spread.
        
        Args:
            spread_type: Type of spread strategy
            underlying_price: Current price of the underlying asset
            strikes: List of strike prices for the spread
            days_to_expiration: Number of days until expiration
            volatility: Implied volatility as a decimal
            dividend_yield: Annual dividend yield as a decimal (default: 0)
            
        Returns:
            Probability of profit as a decimal (0-1)
        """
        # Convert days to years for the model
        time_to_expiration = days_to_expiration / 365.0
        
        # Calculate standard deviation of returns
        std_dev = volatility * math.sqrt(time_to_expiration)
        
        # Calculate probability based on spread type
        if spread_type == 'bull_call':
            # Profit if price > lower_strike + net_debit
            spread_prices = self.calculate_spread_prices(
                spread_type, underlying_price, strikes, days_to_expiration, volatility, dividend_yield
            )
            breakeven = spread_prices['breakeven']
            
            # Calculate probability that price will be above breakeven at expiration
            z_score = (math.log(breakeven / underlying_price) - 
                      (self.risk_free_rate - dividend_yield - 0.5 * volatility**2) * time_to_expiration) / std_dev
            
            return 1 - norm.cdf(z_score)
            
        elif spread_type == 'bear_call':
            # Profit if price <= higher_strike - net_credit
            spread_prices = self.calculate_spread_prices(
                spread_type, underlying_price, strikes, days_to_expiration, volatility, dividend_yield
            )
            breakeven = spread_prices['breakeven']
            
            # Calculate probability that price will be below breakeven at expiration
            z_score = (math.log(breakeven / underlying_price) - 
                      (self.risk_free_rate - dividend_yield - 0.5 * volatility**2) * time_to_expiration) / std_dev
            
            return norm.cdf(z_score)
            
        elif spread_type == 'bull_put':
            # Profit if price >= lower_strike
            spread_prices = self.calculate_spread_prices(
                spread_type, underlying_price, strikes, days_to_expiration, volatility, dividend_yield
            )
            breakeven = spread_prices['breakeven']
            
            # Calculate probability that price will be above breakeven at expiration
            z_score = (math.log(breakeven / underlying_price) - 
                      (self.risk_free_rate - dividend_yield - 0.5 * volatility**2) * time_to_expiration) / std_dev
            
            return 1 - norm.cdf(z_score)
            
        elif spread_type == 'bear_put':
            # Profit if price <= higher_strike - net_debit
            spread_prices = self.calculate_spread_prices(
                spread_type, underlying_price, strikes, days_to_expiration, volatility, dividend_yield
            )
            breakeven = spread_prices['breakeven']
            
            # Calculate probability that price will be below breakeven at expiration
            z_score = (math.log(breakeven / underlying_price) - 
                      (self.risk_free_rate - dividend_yield - 0.5 * volatility**2) * time_to_expiration) / std_dev
            
            return norm.cdf(z_score)
            
        elif spread_type == 'iron_condor':
            # Profit if price stays between the short strikes
            spread_prices = self.calculate_spread_prices(
                spread_type, underlying_price, strikes, days_to_expiration, volatility, dividend_yield
            )
            lower_breakeven = spread_prices['lower_breakeven']
            upper_breakeven = spread_prices['upper_breakeven']
            
            # Calculate probability that price will be between breakeven points at expiration
            lower_z_score = (math.log(lower_breakeven / underlying_price) - 
                           (self.risk_free_rate - dividend_yield - 0.5 * volatility**2) * time_to_expiration) / std_dev
            upper_z_score = (math.log(upper_breakeven / underlying_price) - 
                           (self.risk_free_rate - dividend_yield - 0.5 * volatility**2) * time_to_expiration) / std_dev
            
            return norm.cdf(upper_z_score) - norm.cdf(lower_z_score)
            
        elif spread_type == 'butterfly':
            # Profit if price is between the breakeven points
            spread_prices = self.calculate_spread_prices(
                spread_type, underlying_price, strikes, days_to_expiration, volatility, dividend_yield
            )
            lower_breakeven = spread_prices['lower_breakeven']
            upper_breakeven = spread_prices['upper_breakeven']
            
            # Calculate probability that price will be between breakeven points at expiration
            lower_z_score = (math.log(lower_breakeven / underlying_price) - 
                           (self.risk_free_rate - dividend_yield - 0.5 * volatility**2) * time_to_expiration) / std_dev
            upper_z_score = (math.log(upper_breakeven / underlying_price) - 
                           (self.risk_free_rate - dividend_yield - 0.5 * volatility**2) * time_to_expiration) / std_dev
            
            return norm.cdf(upper_z_score) - norm.cdf(lower_z_score)
            
        else:
            raise ValueError(f"Unsupported spread type: {spread_type}")
    
    def _calculate_d1_d2(
        self,
        underlying_price: float,
        strike_price: float,
        time_to_expiration: float,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float
    ) -> Tuple[float, float]:
        """
        Calculate d1 and d2 parameters for Black-Scholes model.
        
        Args:
            underlying_price: Current price of the underlying asset
            strike_price: Strike price of the option
            time_to_expiration: Time to expiration in years
            volatility: Implied volatility as a decimal
            risk_free_rate: Annual risk-free interest rate as a decimal
            dividend_yield: Annual dividend yield as a decimal
            
        Returns:
            Tuple containing d1 and d2 values
        """
        # Handle edge cases
        if volatility <= 0 or time_to_expiration <= 0:
            raise ValueError("Volatility and time to expiration must be positive")
        
        # Calculate d1
        d1 = (math.log(underlying_price / strike_price) + 
             (risk_free_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiration) / (
            volatility * math.sqrt(time_to_expiration)
        )
        
        # Calculate d2
        d2 = d1 - volatility * math.sqrt(time_to_expiration)
        
        return d1, d2

