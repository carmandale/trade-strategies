import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta import momentum, volatility, trend  # pip install ta
from datetime import datetime, timedelta
import os

# Define parameters
ticker = "SPY"
contracts = 200
dates = ["2025-07-25", "2025-07-28"]  # Historical dates; replace with real past dates for testing
today = datetime.now().strftime("%Y-%m-%d")  # For projections
times = ["07:30:00", "12:00:00", "14:30:00", "16:00:00"]  # Central Time
strikes_bull_call = [637, 640]  # Example; adjust
strikes_iron_condor = [633, 638, 631, 640]  # Short low/high, long low/high
strikes_butterfly = [637, 638, 639]  # Wing low, body, wing high

# Function to fetch intraday data (1-min interval)
def get_spy_data(date):
    start = f"{date}T12:30:00Z"  # UTC for 7:30 AM Central (UTC-5)
    end = f"{date}T21:00:00Z"    # After close
    data = yf.download(ticker, start=date, end=(datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"), interval="1m")
    data.index = data.index.tz_convert('America/Chicago')  # To Central
    return data

# Calculate technical indicators
def calculate_indicators(data):
    # Ensure Close is a 1D Series
    close_series = data['Close'].squeeze() if len(data['Close'].shape) > 1 else data['Close']
    
    bb = volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    data['BB_Mid'] = bb.bollinger_mavg()
    data['BB_Upper'] = bb.bollinger_hband()
    data['BB_Lower'] = bb.bollinger_lband()
    data['RSI'] = momentum.RSIIndicator(close=close_series, window=14).rsi()
    macd = trend.MACD(close=close_series)
    data['MACD'] = macd.macd()
    data['MACD_Signal'] = macd.macd_signal()
    return data

# Analyze spread profit/risk (simplified Black-Scholes for estimates; real options need chain data)
def analyze_spread(data, spread_type, strikes, entry_time, exit_time):
    try:
        entry_price = float(data.loc[entry_time, 'Close'].squeeze()) if entry_time in data.index else float(data.iloc[0]['Close'].squeeze())
        exit_price = float(data.loc[exit_time, 'Close'].squeeze()) if exit_time and exit_time in data.index else float(data.iloc[-1]['Close'].squeeze())
    except:
        return {"max_profit": 0, "max_loss": 0, "profit_at_exit": 0}
    if spread_type == "bull_call":
        debit = (strikes[1] - strikes[0]) * 0.3  # Estimated premium
        max_profit = (strikes[1] - strikes[0] - debit) * contracts * 100
        max_loss = debit * contracts * 100
        profit = max(0, min(exit_price - strikes[0], strikes[1] - strikes[0]) - debit) * contracts * 100
    elif spread_type == "iron_condor":
        credit = 0.4  # Estimated
        width = strikes[3] - strikes[2]
        max_profit = credit * contracts * 100
        max_loss = (width - credit) * contracts * 100
        profit = max_profit if strikes[0] < exit_price < strikes[1] else -max_loss
    elif spread_type == "butterfly":
        debit = 0.25  # Estimated
        width = strikes[2] - strikes[0]
        max_profit = (width / 2 - debit) * contracts * 100
        max_loss = debit * contracts * 100
        dist = abs(exit_price - strikes[1])
        profit = max(0, (width / 2 - dist - debit)) * contracts * 100
    return {"max_profit": max_profit, "max_loss": max_loss, "profit_at_exit": profit}

# Plot data
def plot_data(data, date, indicators=True):
    plt.figure(figsize=(12, 6))
    plt.plot(data['Close'], label='Close Price')
    if indicators:
        plt.plot(data['BB_Mid'], label='BB Mid')
        plt.plot(data['BB_Upper'], label='BB Upper')
        plt.plot(data['BB_Lower'], label='BB Lower')
        plt.twinx().plot(data['RSI'], 'r--', label='RSI')
        plt.twinx().plot(data['MACD'], 'g-', label='MACD')
    plt.title(f"SPY on {date}")
    plt.legend()
    plt.savefig(f"spy_plot_{date}.png")
    plt.close()

# Main execution
all_results = {}
for date in dates + [today]:
    try:
        data = get_spy_data(date)
        data = calculate_indicators(data)
        plot_data(data, date)
        day_results = {}
        for t in times:
            timestamp = f"{date} {t}"
            try:
                if timestamp in data.index:
                    day_results[t] = {col: float(data.loc[timestamp, col].squeeze()) for col in data.columns}
            except:
                pass
        # Analyze spreads (example for bull call at 8:30 entry, 14:30 exit)
        spreads = {
            "bull_call": analyze_spread(data, "bull_call", strikes_bull_call, f"{date} 08:30:00", f"{date} 14:30:00"),
            "iron_condor": analyze_spread(data, "iron_condor", strikes_iron_condor, f"{date} 08:30:00", None),
            "butterfly": analyze_spread(data, "butterfly", strikes_butterfly, f"{date} 08:30:00", f"{date} 14:30:00")
        }
        all_results[date] = {"data_points": day_results, "spreads": spreads}
    except Exception as e:
        print(f"Error for {date}: {e}")

# Hindsight optimization (simple: best strikes around close)
for date in dates:
    if date in all_results and "data_points" in all_results[date] and "16:00:00" in all_results[date]["data_points"]:
        close = all_results[date]["data_points"]["16:00:00"]["Close"]
        best_butterfly_strikes = [round(close - 2), round(close), round(close + 2)]
        print(f"Best hindsight butterfly for {date}: {best_butterfly_strikes}")

# Get current price
def get_current_price():
    try:
        spy = yf.Ticker(ticker)
        current_data = spy.history(period="1d", interval="1m")
        if not current_data.empty:
            return float(current_data['Close'].iloc[-1])
        else:
            # Fallback to daily data
            current_data = spy.history(period="1d")
            return float(current_data['Close'].iloc[-1])
    except:
        return None

# Generate strategy summary
def generate_strategy_summary(all_results, current_price):
    print("\n" + "="*60)
    print(f"SPY SPREAD STRATEGIES ANALYSIS")
    print(f"Current SPY Price: ${current_price:.2f}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CT")
    print("="*60)
    
    # Calculate aggregate results for each strategy
    strategy_totals = {
        "bull_call": {"total_profit": 0, "wins": 0, "losses": 0},
        "iron_condor": {"total_profit": 0, "wins": 0, "losses": 0},
        "butterfly": {"total_profit": 0, "wins": 0, "losses": 0}
    }
    
    for date, results in all_results.items():
        if "spreads" in results:
            for strategy, performance in results["spreads"].items():
                profit = performance["profit_at_exit"]
                strategy_totals[strategy]["total_profit"] += profit
                if profit > 0:
                    strategy_totals[strategy]["wins"] += 1
                else:
                    strategy_totals[strategy]["losses"] += 1
    
    # Display results for each strategy
    print("\n1. BULL CALL SPREAD (Strikes: {}-{})".format(strikes_bull_call[0], strikes_bull_call[1]))
    print("-" * 40)
    print(f"   Total P/L: ${strategy_totals['bull_call']['total_profit']:,.2f}")
    print(f"   Win Rate: {strategy_totals['bull_call']['wins']}/{len(all_results)} trades")
    print(f"   Max Profit per trade: $42,000")
    print(f"   Max Loss per trade: $18,000")
    print(f"   Risk/Reward Ratio: 1:2.33")
    
    print("\n2. IRON CONDOR (Strikes: {}/{} - {}/{})".format(
        strikes_iron_condor[0], strikes_iron_condor[2], 
        strikes_iron_condor[1], strikes_iron_condor[3]))
    print("-" * 40)
    print(f"   Total P/L: ${strategy_totals['iron_condor']['total_profit']:,.2f}")
    print(f"   Win Rate: {strategy_totals['iron_condor']['wins']}/{len(all_results)} trades")
    print(f"   Max Profit per trade: $8,000")
    print(f"   Max Loss per trade: $172,000")
    print(f"   Risk/Reward Ratio: 1:0.05")
    
    print("\n3. BUTTERFLY SPREAD (Strikes: {}-{}-{})".format(
        strikes_butterfly[0], strikes_butterfly[1], strikes_butterfly[2]))
    print("-" * 40)
    print(f"   Total P/L: ${strategy_totals['butterfly']['total_profit']:,.2f}")
    print(f"   Win Rate: {strategy_totals['butterfly']['wins']}/{len(all_results)} trades")
    print(f"   Max Profit per trade: $35,000")
    print(f"   Max Loss per trade: $5,000")
    print(f"   Risk/Reward Ratio: 1:7")
    
    # Recommendation based on current price
    print("\n" + "="*60)
    print("RECOMMENDATION BASED ON CURRENT PRICE:")
    print("="*60)
    
    if current_price:
        # Bull Call recommendation
        if current_price < strikes_bull_call[0]:
            print("• Bull Call: FAVORABLE - Price below lower strike")
        elif current_price > strikes_bull_call[1]:
            print("• Bull Call: UNFAVORABLE - Price above upper strike")
        else:
            print("• Bull Call: NEUTRAL - Price between strikes")
        
        # Iron Condor recommendation
        if strikes_iron_condor[0] < current_price < strikes_iron_condor[1]:
            print("• Iron Condor: FAVORABLE - Price within profit zone")
        else:
            print("• Iron Condor: UNFAVORABLE - Price outside profit zone")
        
        # Butterfly recommendation
        butterfly_center = strikes_butterfly[1]
        distance_from_center = abs(current_price - butterfly_center)
        if distance_from_center < 0.5:
            print(f"• Butterfly: HIGHLY FAVORABLE - Price ${distance_from_center:.2f} from center strike")
        elif distance_from_center < 1.5:
            print(f"• Butterfly: FAVORABLE - Price ${distance_from_center:.2f} from center strike")
        else:
            print(f"• Butterfly: UNFAVORABLE - Price ${distance_from_center:.2f} from center strike")

# Get current price and generate summary
current_price = get_current_price()
if current_price:
    generate_strategy_summary(all_results, current_price)
else:
    print("Unable to fetch current price")

# Output detailed results
print("\n" + "="*60)
print("DETAILED RESULTS BY DATE:")
print("="*60)
for date, results in all_results.items():
    if "spreads" in results:
        print(f"\n{date}:")
        for strategy, performance in results["spreads"].items():
            print(f"  {strategy}:")
            print(f"    P/L: ${performance['profit_at_exit']:,.2f}")
            print(f"    Max Profit: ${performance['max_profit']:,.2f}")
            print(f"    Max Loss: ${performance['max_loss']:,.2f}")

print("\nPlots saved as PNG files.")