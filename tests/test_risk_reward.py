"""
Tests for the risk-reward ratio calculation in the options pricing service.
"""
import sys
import os
import unittest

# Add the parent directory to the path so we can import the service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.options_pricing_service import OptionsPricingService

class TestRiskRewardRatio(unittest.TestCase):
    """Test cases for the risk-reward ratio calculation."""

    def setUp(self):
        """Set up the test environment."""
        self.options_pricing = OptionsPricingService(risk_free_rate=0.05)
        
        # Standard test parameters
        self.underlying_price = 100.0
        self.days_to_expiration = 30
        self.volatility = 0.2
        self.dividend_yield = 0.0

    def test_bull_call_risk_reward(self):
        """Test the risk-reward ratio for a bull call spread."""
        # Bull call spread (debit spread)
        rr_bull_call = self.options_pricing.calculate_risk_reward_ratio(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[95.0, 105.0],
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Risk-reward ratio should be positive
        self.assertGreater(rr_bull_call, 0.0)
        
        # For a bull call spread, risk-reward ratio depends on market conditions
        # and strike selection, but should be reasonable
        self.assertLess(rr_bull_call, 5.0)

    def test_iron_condor_risk_reward(self):
        """Test the risk-reward ratio for an iron condor."""
        # Iron condor (credit spread)
        rr_iron_condor = self.options_pricing.calculate_risk_reward_ratio(
            spread_type='iron_condor',
            underlying_price=self.underlying_price,
            strikes=[90.0, 95.0, 105.0, 110.0],
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield
        )
        
        # Risk-reward ratio should be positive
        self.assertGreater(rr_iron_condor, 0.0)
        
        # For an iron condor, risk-reward ratio is typically greater than 1
        # (risk more to make less, but with higher probability)
        self.assertGreater(rr_iron_condor, 1.0)

    def test_volatility_impact(self):
        """Test the impact of volatility on risk-reward ratio."""
        # Test with different volatilities
        rr_high_vol = self.options_pricing.calculate_risk_reward_ratio(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[95.0, 105.0],
            days_to_expiration=self.days_to_expiration,
            volatility=0.4  # Higher volatility
        )
        
        rr_low_vol = self.options_pricing.calculate_risk_reward_ratio(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[95.0, 105.0],
            days_to_expiration=self.days_to_expiration,
            volatility=0.1  # Lower volatility
        )
        
        # Higher volatility should result in a different risk-reward ratio
        self.assertNotEqual(rr_high_vol, rr_low_vol)

    def test_time_impact(self):
        """Test the impact of time to expiration on risk-reward ratio."""
        # Test with different times to expiration
        rr_long_time = self.options_pricing.calculate_risk_reward_ratio(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[95.0, 105.0],
            days_to_expiration=60,  # Longer time
            volatility=self.volatility
        )
        
        rr_short_time = self.options_pricing.calculate_risk_reward_ratio(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[95.0, 105.0],
            days_to_expiration=7,  # Shorter time
            volatility=self.volatility
        )
        
        # Different times to expiration should result in different risk-reward ratios
        self.assertNotEqual(rr_long_time, rr_short_time)

    def test_strike_width_impact(self):
        """Test the impact of strike width on risk-reward ratio."""
        # Test with different strike widths
        rr_narrow = self.options_pricing.calculate_risk_reward_ratio(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[95.0, 105.0],  # 10-point spread
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility
        )
        
        rr_wide = self.options_pricing.calculate_risk_reward_ratio(
            spread_type='bull_call',
            underlying_price=self.underlying_price,
            strikes=[90.0, 110.0],  # 20-point spread
            days_to_expiration=self.days_to_expiration,
            volatility=self.volatility
        )
        
        # Different strike widths should result in different risk-reward ratios
        self.assertNotEqual(rr_narrow, rr_wide)

if __name__ == '__main__':
    unittest.main()
