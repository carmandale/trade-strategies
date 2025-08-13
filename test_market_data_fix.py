#!/usr/bin/env python3
"""Test script to verify the SPY/SPX market data fix."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.market_data_service import MarketDataCollector
from services.ai_assessment_service import AIAssessmentService

def test_market_data_collection():
    """Test the market data collection for both SPY and SPX."""
    print("🧪 Testing Market Data Collection")
    print("=" * 50)
    
    collector = MarketDataCollector()
    
    # Test SPY data collection
    print("📊 Testing SPY data collection...")
    spy_data = collector.get_current_price('SPY')
    if spy_data:
        print(f"✅ SPY Data: ${spy_data['price']:.2f} ({spy_data['change']:+.2f}, {spy_data['change_percent']:+.2f}%)")
        print(f"   Symbol: {spy_data['symbol']}")
    else:
        print("❌ Failed to get SPY data")
    
    print()
    
    # Test SPX data collection
    print("📊 Testing SPX data collection...")
    spx_data = collector.get_current_price('SPX')
    if spx_data:
        print(f"✅ SPX Data: ${spx_data['price']:.2f} ({spx_data['change']:+.2f}, {spx_data['change_percent']:+.2f}%)")
        print(f"   Symbol: {spx_data['symbol']}")
    else:
        print("❌ Failed to get SPX data")
    
    print()
    
    # Test full market snapshot
    print("📊 Testing complete market snapshot...")
    snapshot = collector.collect_market_snapshot()
    
    print(f"SPX Price: ${snapshot.get('spx_price', 'N/A')}")
    print(f"SPY Price: ${snapshot.get('spy_price', 'N/A')}")
    
    print()
    
    # Compare prices to verify they're different
    spx_price = float(snapshot.get('spx_price', 0))
    spy_price = float(snapshot.get('spy_price', 0))
    
    if spx_price > 0 and spy_price > 0:
        ratio = spx_price / spy_price
        print(f"📈 Price Ratio Check:")
        print(f"   SPX/SPY Ratio: {ratio:.2f}")
        if 9 < ratio < 12:
            print("✅ Ratio looks correct (SPX ~10x SPY)")
        else:
            print("⚠️  Ratio seems off - should be ~10:1")
        
        if spy_price > 1000:
            print("❌ CRITICAL: SPY price still looks like SPX price!")
        else:
            print("✅ SPY price looks correct")
    
def test_ai_assessment_prompt():
    """Test that AI assessment uses correct symbol data."""
    print("\n🤖 Testing AI Assessment Symbol Logic")
    print("=" * 50)
    
    ai_service = AIAssessmentService()
    
    # Test strategy parameters
    strategy_params = {
        'symbol': 'SPY',
        'strategy_type': 'iron_condor',
        'strikes': {
            'short_put': 640,
            'long_put': 635,
            'short_call': 650,
            'long_call': 655
        },
        'expiration': '2025-08-13',
        'quantity': 1,
        'max_profit': 500,
        'max_loss': 1000
    }
    
    # Get market data
    market_data = ai_service._get_market_data()
    if market_data:
        print("📊 Market Data Available:")
        print(f"   SPX Price: ${market_data.get('spx_price', 'N/A')}")
        print(f"   SPY Price: ${market_data.get('spy_price', 'N/A')}")
        
        # Build prompt to see what price gets used
        prompt = ai_service._build_prompt(strategy_params, market_data)
        
        # Extract the price line from prompt
        lines = prompt.split('\n')
        price_line = None
        for line in lines:
            if 'Current:' in line and '$' in line:
                price_line = line.strip()
                break
        
        if price_line:
            print(f"\n📝 AI Prompt Price Line:")
            print(f"   {price_line}")
            
            if 'SPY' in price_line and '$6' in price_line:
                print("❌ STILL BROKEN: SPY showing SPX-like price")
            elif 'SPY' in price_line and ('$6' not in price_line):
                print("✅ FIXED: SPY showing reasonable price")
            else:
                print("ℹ️  Price line format different than expected")
        
    else:
        print("❌ No market data available")

if __name__ == "__main__":
    try:
        test_market_data_collection()
        test_ai_assessment_prompt()
        
        print("\n" + "=" * 50)
        print("🏁 Test Complete")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()