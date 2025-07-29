import numpy as np

# Historical Friday SPX closes (fetched from reliable sources; user can update)
data = {
    '2024-05-03': 5127.79,
    '2024-05-10': 5222.68,
    '2024-05-17': 5303.27,
    '2024-05-24': 5304.72,
    '2024-05-31': 5277.51,
    '2024-06-07': 5346.99,
    '2024-06-14': 5431.60,
    '2024-06-21': 5464.62,
    '2024-06-28': 5460.48,
    '2024-07-05': 5567.19,
    '2024-07-12': 5615.35,
    '2024-07-19': 5505.00,
    '2024-07-26': 5459.10
}
dates = list(data.keys())
closes = list(data.values())

# Backtest trades
trades = []
for i in range(1, len(closes)):
    entry_date = dates[i-1]
    exp_date = dates[i]
    entry_price = closes[i-1]
    exp_price = closes[i]
    # Pick strikes, round to nearest 5
    def round_to_5(x):
        return round(x / 5) * 5
    lower_buy = round_to_5(entry_price * 0.965)
    lower_sell = round_to_5(entry_price * 0.97)
    upper_sell = round_to_5(entry_price * 1.03)
    upper_buy = round_to_5(entry_price * 1.035)
    # Assumed credit (adjustable)
    credit = 1.0
    # P/L calculation
    value_put_spread = max(0, lower_sell - exp_price) - max(0, lower_buy - exp_price)
    value_call_spread = max(0, exp_price - upper_sell) - max(0, exp_price - upper_buy)
    pl = credit - value_put_spread - value_call_spread
    trades.append({
        'Entry Date': entry_date,
        'Exp Date': exp_date,
        'Entry Price': entry_price,
        'Exp Price': exp_price,
        'Lower Buy': lower_buy,
        'Lower Sell': lower_sell,
        'Upper Sell': upper_sell,
        'Upper Buy': upper_buy,
        'P/L': pl
    })

# Output
print("Backtest Results for Weekly Iron Condors on SPX")
print("Assumed credit: 1.0 per condor")
total_pl = 0
wins = 0
for trade in trades:
    print(f"\nTrade exp {trade['Exp Date']}: Entry {trade['Entry Price']:.2f}, Exp {trade['Exp Price']:.2f}")
    print(f"Strikes: Put {trade['Lower Buy']}/{trade['Lower Sell']}, Call {trade['Upper Sell']}/{trade['Upper Buy']}")
    print(f"P/L: {trade['P/L']:.2f}")
    total_pl += trade['P/L']
    if trade['P/L'] > 0:
        wins += 1
print(f"\nTotal P/L: {total_pl:.2f}")
print(f"Win rate: {wins / len(trades) * 100:.2f}%")