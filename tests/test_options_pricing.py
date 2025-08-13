"""
Tests for the Black-Scholes options pricing service.
"""
import sys
import os
import unittest
import math
from decimal import Decimal

# Add the parent directory to the path so we can import the service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.options_pricing_service import OptionsPricingService

class TestOptionsPricingService(unittest.TestCase):
    """Test cases for the OptionsPricingService."""

    def setUp(self):
        """Set up the test environment."""
        self.options_pricing = OptionsPricingService(risk_free_rate=0.05)
        
        # Standard test parameters
        self.underlying_price = 100.0
        self.strike_price = 100.0
        self.days_to_expiration = 30
        self.volatility = 0.2
        self.dividend_yield = 0.0

    def test_call_option_price(self):
        """Test the calculation of call option prices."""
        # At-the-money call option
        call_price = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Expected price based on Black-Scholes formula
        # For ATM call with 30 days to expiration and 20% volatility
        # Price should be around 2.0-3.5
        self.assertGreater(call_price, 2.0)
        self.assertLess(call_price, 4.0)
        
        # In-the-money call option
        itm_call_price = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=110.0,
            strike_price=100.0,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # ITM call should be more expensive than ATM call
        self.assertGreater(itm_call_price, call_price)
        
        # Out-of-the-money call option
        otm_call_price = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=90.0,
            strike_price=100.0,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # OTM call should be less expensive than ATM call
        self.assertLess(otm_call_price, call_price)

    def test_put_option_price(self):
        """Test the calculation of put option prices."""
        # At-the-money put option
        put_price = self.options_pricing.calculate_option_price(
            option_type='put',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Expected price based on Black-Scholes formula
        # For ATM put with 30 days to expiration and 20% volatility
        # Price should be around 2.5-3.5 (slightly less than call due to interest rate)
        self.assertGreater(put_price, 2.0)
        self.assertLess(put_price, 4.0)
        
        # In-the-money put option
        itm_put_price = self.options_pricing.calculate_option_price(
            option_type='put',
            underlying_price=90.0,
            strike_price=100.0,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # ITM put should be more expensive than ATM put
        self.assertGreater(itm_put_price, put_price)
        
        # Out-of-the-money put option
        otm_put_price = self.options_pricing.calculate_option_price(
            option_type='put',
            underlying_price=110.0,
            strike_price=100.0,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # OTM put should be less expensive than ATM put
        self.assertLess(otm_put_price, put_price)

    def test_put_call_parity(self):
        """Test that put-call parity holds."""
        # Calculate call and put prices for the same parameters
        call_price = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        put_price = self.options_pricing.calculate_option_price(
            option_type='put',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Put-call parity: C + K*e^(-rt) = P + S
        # Where C is call price, K is strike, r is risk-free rate, t is time to expiration,
        # P is put price, and S is underlying price
        time_to_expiration = self.days_to_expiration / 365.0
        discounted_strike = self.strike_price * math.exp(-self.options_pricing.risk_free_rate * time_to_expiration)
        
        left_side = call_price + discounted_strike
        right_side = put_price + self.underlying_price
        
        # Allow for a small margin of error due to floating point calculations
        self.assertAlmostEqual(left_side, right_side, delta=0.01)

    def test_greeks(self):
        """Test the calculation of option Greeks."""
        # Calculate Greeks for an ATM call option
        greeks = self.options_pricing.calculate_greeks(
            option_type='call',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Delta for ATM call should be around 0.5
        self.assertGreater(greeks['delta'], 0.45)
        self.assertLess(greeks['delta'], 0.55)
        
        # Gamma should be positive
        self.assertGreater(greeks['gamma'], 0)
        
        # Theta should be negative for long options
        self.assertLess(greeks['theta'], 0)
        
        # Vega should be positive
        self.assertGreater(greeks['vega'], 0)
        
        # Calculate Greeks for an ATM put option
        put_greeks = self.options_pricing.calculate_greeks(
            option_type='put',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Delta for ATM put should be around -0.5
        self.assertLess(put_greeks['delta'], -0.45)
        self.assertGreater(put_greeks['delta'], -0.55)
        
        # Gamma should be the same for calls and puts with the same parameters
        self.assertAlmostEqual(greeks['gamma'], put_greeks['gamma'], delta=0.0001)
        
        # Vega should be the same for calls and puts with the same parameters
        self.assertAlmostEqual(greeks['vega'], put_greeks['vega'], delta=0.0001)

    def test_implied_volatility(self):
        """Test the calculation of implied volatility."""
        # Calculate a call option price with known volatility
        known_volatility = 0.25
        call_price = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=known_volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Calculate implied volatility from the option price
        implied_vol = self.options_pricing.calculate_implied_volatility(
            option_type='call',
            option_price=call_price,
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            dividend_yield=self.dividend_yield
        )
        
        # Implied volatility should be close to the known volatility
        self.assertIsNotNone(implied_vol)
        self.assertAlmostEqual(implied_vol, known_volatility, delta=0.01)

    def test_spread_prices(self):
        """Test the calculation of spread prices."""
        # Test bull call spread
        bull_call = self.options_pricing.calculate_spread_prices(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[95.0, 105.0],
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Net debit should be positive
        self.assertGreater(bull_call['net_debit'], 0)
        
        # Max profit should be positive and less than the spread width
        self.assertGreater(bull_call['max_profit'], 0)
        self.assertLess(bull_call['max_profit'], (105.0 - 95.0) * 100)
        
        # Max loss should be equal to the net debit
        self.assertAlmostEqual(bull_call['max_loss'], bull_call['net_debit'], delta=0.01)
        
        # Test iron condor
        iron_condor = self.options_pricing.calculate_spread_prices(
            spread_type='iron_condor',
            underlying_price=self.underlying_price,
            strikes=[90.0, 95.0, 105.0, 110.0],
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Net credit should be positive
        self.assertGreater(iron_condor['net_credit'], 0)
        
        # Max profit should be equal to the net credit
        self.assertAlmostEqual(iron_condor['max_profit'], iron_condor['net_credit'], delta=0.01)
        
        # Max loss should be positive and greater than max profit
        self.assertGreater(iron_condor['max_loss'], 0)
        self.assertGreater(iron_condor['max_loss'], iron_condor['max_profit'])
        
        # Lower breakeven should be below the put short strike
        self.assertLess(iron_condor['lower_breakeven'], 95.0)
        
        # Upper breakeven should be above the call short strike
        self.assertGreater(iron_condor['upper_breakeven'], 105.0)

    def test_probability_of_profit(self):
        """Test the calculation of probability of profit."""
        # Test probability of profit for bull call spread
        bull_call_pop = self.options_pricing.calculate_probability_of_profit(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[95.0, 105.0],
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Probability should be between 0 and 1
        self.assertGreater(bull_call_pop, 0)
        self.assertLess(bull_call_pop, 1)
        
        # Test probability of profit for iron condor
        iron_condor_pop = self.options_pricing.calculate_probability_of_profit(
            spread_type='iron_condor',
            underlying_price=self.underlying_price,
            strikes=[90.0, 95.0, 105.0, 110.0],
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Probability should be between 0 and 1
        self.assertGreater(iron_condor_pop, 0)
        self.assertLess(iron_condor_pop, 1)
        
        # Iron condor with wider strikes should have higher probability of profit
        wider_iron_condor_pop = self.options_pricing.calculate_probability_of_profit(
            spread_type='iron_condor',
            underlying_price=self.underlying_price,
            strikes=[85.0, 90.0, 110.0, 115.0],
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        self.assertGreater(wider_iron_condor_pop, iron_condor_pop)

    def test_edge_cases(self):
        """Test edge cases for option pricing."""
        # Test very short expiration (0DTE)
        zero_dte_call = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=0.1,  # Almost expired
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # For ATM option with almost no time, price should be very small
        self.assertLess(zero_dte_call, 1.0)
        
        # Test deep ITM call
        deep_itm_call = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=120.0,
            strike_price=100.0,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Deep ITM call should be worth at least the intrinsic value
        self.assertGreater(deep_itm_call, 20.0)
        
        # Test deep OTM call
        deep_otm_call = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=80.0,
            strike_price=100.0,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Deep OTM call should have a small price
        self.assertLess(deep_otm_call, 1.0)
        
        # Test high volatility
        normal_vol_call = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        high_vol_call = self.options_pricing.calculate_option_price(
            option_type='call',
            underlying_price=self.underlying_price,
            strike_price=self.strike_price,
            days_to_expiration=self.days_to_expiration,
            volatility=0.5,  # Very high volatility
            dividend_yield=self.dividend_yield
        )
        
        # High volatility should result in higher option price
        self.assertGreater(high_vol_call, normal_vol_call)

if __name__ == '__main__':
    unittest.main()
