"""
Integration tests for the strategy analysis flow.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
import pandas as pd
import numpy as np

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the database modules
sys.modules['database.config'] = MagicMock()
sys.modules['database.models'] = MagicMock()

from api.routes.strategies import _backtest_iron_condor_enhanced, _backtest_bull_call_enhanced, TimeFrame
from services.options_pricing_service import OptionsPricingService

class TestStrategyAnalysis(unittest.TestCase):
    """Integration tests for the strategy analysis flow."""

    def setUp(self):
        """Set up the test environment."""
        # Create a mock DataFrame for testing with actual data
        dates = pd.date_range(start='2023-01-01', periods=60)
        prices = np.linspace(95, 105, 60)  # Price range from 95 to 105
        self.mock_data = pd.DataFrame({
            'Close': prices,
            'Open': prices - 0.5,
            'High': prices + 1.0,
            'Low': prices - 1.0,
            'Volume': np.random.randint(1000000, 5000000, 60)
        }, index=dates)
        
        # Create an options pricing service
        self.options_pricing = OptionsPricingService(risk_free_rate=0.05)

    @patch('api.routes.strategies._calculate_sharpe_ratio')
    @patch('api.routes.strategies._calculate_max_drawdown')
    def test_iron_condor_analysis(self, mock_max_drawdown, mock_sharpe_ratio):
        """Test the iron condor analysis flow."""
        # Mock the Sharpe ratio and max drawdown calculations
        mock_sharpe_ratio.return_value = 0.8
        mock_max_drawdown.return_value = 15.0
        
        # Test with custom strikes
        custom_strikes = [90.0, 95.0, 105.0, 110.0]
        
        # Run the backtest
        result = _backtest_iron_condor_enhanced(
            data=self.mock_data,
            timeframe=TimeFrame.DAILY,
            options_pricing=self.options_pricing,
            volatility=0.2,
            dividend_yield=0.0,
            contracts=1,
            custom_strikes=custom_strikes
        )
        
        # Verify the result contains all expected fields
        self.assertIn('total_pnl', result)
        self.assertIn('win_rate', result)
        self.assertIn('total_trades', result)
        self.assertIn('avg_pnl_per_trade', result)
        self.assertIn('max_drawdown', result)
        self.assertIn('sharpe_ratio', result)
        self.assertIn('probability_of_profit', result)
        self.assertIn('risk_reward_ratio', result)
        self.assertIn('max_profit', result)
        self.assertIn('max_loss', result)
        self.assertIn('breakeven_points', result)
        
        # Verify the values are reasonable
        self.assertGreaterEqual(result['probability_of_profit'], 0.0)
        self.assertLessEqual(result['probability_of_profit'], 100.0)
        self.assertGreaterEqual(result['max_profit'], 0.0)
        self.assertGreaterEqual(result['max_loss'], 0.0)
        self.assertEqual(len(result['breakeven_points']), 2)
        
        # Verify the strategy details
        self.assertIn('strategy_details', result)
        self.assertEqual(result['strategy_details']['put_long'], custom_strikes[0])
        self.assertEqual(result['strategy_details']['put_short'], custom_strikes[1])
        self.assertEqual(result['strategy_details']['call_short'], custom_strikes[2])
        self.assertEqual(result['strategy_details']['call_long'], custom_strikes[3])

    @patch('api.routes.strategies._calculate_sharpe_ratio')
    @patch('api.routes.strategies._calculate_max_drawdown')
    def test_bull_call_analysis(self, mock_max_drawdown, mock_sharpe_ratio):
        """Test the bull call analysis flow."""
        # Mock the Sharpe ratio and max drawdown calculations
        mock_sharpe_ratio.return_value = 0.7
        mock_max_drawdown.return_value = 20.0
        
        # Test with custom strikes
        custom_strikes = [95.0, 105.0]
        
        # Run the backtest
        result = _backtest_bull_call_enhanced(
            data=self.mock_data,
            timeframe=TimeFrame.DAILY,
            options_pricing=self.options_pricing,
            volatility=0.2,
            dividend_yield=0.0,
            contracts=1,
            custom_strikes=custom_strikes
        )
        
        # Verify the result contains all expected fields
        self.assertIn('total_pnl', result)
        self.assertIn('win_rate', result)
        self.assertIn('total_trades', result)
        self.assertIn('avg_pnl_per_trade', result)
        self.assertIn('max_drawdown', result)
        self.assertIn('sharpe_ratio', result)
        self.assertIn('probability_of_profit', result)
        self.assertIn('risk_reward_ratio', result)
        self.assertIn('max_profit', result)
        self.assertIn('max_loss', result)
        self.assertIn('breakeven_points', result)
        
        # Verify the values are reasonable
        self.assertGreaterEqual(result['probability_of_profit'], 0.0)
        self.assertLessEqual(result['probability_of_profit'], 100.0)
        self.assertGreaterEqual(result['max_profit'], 0.0)
        self.assertGreaterEqual(result['max_loss'], 0.0)
        self.assertEqual(len(result['breakeven_points']), 1)
        
        # Verify the strategy details
        self.assertIn('strategy_details', result)
        self.assertEqual(result['strategy_details']['lower_strike'], custom_strikes[0])
        self.assertEqual(result['strategy_details']['upper_strike'], custom_strikes[1])

    def test_edge_cases(self):
        """Test edge cases for strategy analysis."""
        # Test with very high volatility
        high_vol_result = _backtest_iron_condor_enhanced(
            data=self.mock_data,
            timeframe=TimeFrame.DAILY,
            options_pricing=self.options_pricing,
            volatility=0.5,  # Very high volatility
            dividend_yield=0.0,
            contracts=1,
            custom_strikes=[90.0, 95.0, 105.0, 110.0]
        )
        
        # Test with very low volatility
        low_vol_result = _backtest_iron_condor_enhanced(
            data=self.mock_data,
            timeframe=TimeFrame.DAILY,
            options_pricing=self.options_pricing,
            volatility=0.1,  # Very low volatility
            dividend_yield=0.0,
            contracts=1,
            custom_strikes=[90.0, 95.0, 105.0, 110.0]
        )
        
        # Higher volatility should result in higher option prices and thus higher credit
        self.assertGreater(high_vol_result['strategy_details']['entry_credit'], 
                          low_vol_result['strategy_details']['entry_credit'])
        
        # Test with different timeframes
        monthly_result = _backtest_bull_call_enhanced(
            data=self.mock_data,
            timeframe=TimeFrame.MONTHLY,
            options_pricing=self.options_pricing,
            volatility=0.2,
            dividend_yield=0.0,
            contracts=1,
            custom_strikes=[95.0, 105.0]
        )
        
        # Monthly options should have more time value
        self.assertGreater(monthly_result['avg_days_held'], 7)

if __name__ == '__main__':
    unittest.main()
