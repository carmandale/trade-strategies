import numpy as np

# Historical daily SPX closes for Jul 16-29, 2024 (fetched via web tools; user can update)
data = {
    '2024-07-16': 5631.22,
    '2024-07-17': 5568.41,
    '2024-07-18': 5544.59,
    '2024-07-19': 5505.00,
    '2024-07-22': 5564.41,
    '2024-07-23': 5555.74,
    '2024-07-24': 5427.13,
    '2024-07-25': 5399.22,
    '2024-07-26': 5459.10,
    '2024-07-29': 5463.54,
    '2024-07-30': 5436.44,
    '2024-07-31': 5522.30
}
dates = list(data.keys())
closes = list(data.values())

# Backtest trades
trades = []
for i in range(len(closes)):
    date = dates[i]
    entry_price = closes[i]
    exp_price = closes[i]  # Same-day expiration
    # Pick strikes, round to nearest 5
    def round_to_5(x):
        return round(x / 5) * 5
    lower_buy = round_to_5(entry_price * 0.975)
    lower_sell = round_to_5(entry_price * 0.98)
    upper_sell = round_to_5(entry_price * 1.02)
    upper_buy = round_to_5(entry_price * 1.025)
    # Assumed credit (adjustable)
    credit = 0.5
    # P/L calculation
    value_put_spread = max(0, lower_sell - exp_price) - max(0, lower_buy - exp_price)
    value_call_spread = max(0, exp_price - upper_sell) - max(0, exp_price - upper_buy)
    pl = credit - value_put_spread - value_call_spread
    trades.append({
        'Date': date,
        'Entry Price': entry_price,
        'Exp Price': exp_price,
        'Lower Buy': lower_buy,
        'Lower Sell': lower_sell,
        'Upper Sell': upper_sell,
        'Upper Buy': upper_buy,
        'P/L': pl
    })

# Output
print("Backtest Results for Daily (0DTE) Iron Condors on SPX")
print("Assumed credit: 0.5 per condor")
total_pl = 0
wins = 0
for trade in trades:
    print(f"\nTrade {trade['Date']}: Entry {trade['Entry Price']:.2f}, Exp {trade['Exp Price']:.2f}")
    print(f"Strikes: Put {trade['Lower Buy']}/{trade['Lower Sell']}, Call {trade['Upper Sell']}/{trade['Upper Buy']}")
    print(f"P/L: {trade['P/L']:.2f}")
    total_pl += trade['P/L']
    if trade['P/L'] > 0:
        wins += 1
print(f"\nTotal P/L: {total_pl:.2f}")
print(f"Win rate: {wins / len(trades) * 100:.2f}%")