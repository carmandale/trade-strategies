import numpy as np

# Historical end-of-month SPX closes (fetched via web tools; user can update)
data = {
    'Jul 2023': 4588.96,
    'Aug 2023': 4507.66,
    'Sep 2023': 4288.05,
    'Oct 2023': 4193.80,
    'Nov 2023': 4567.80,
    'Dec 2023': 4769.83,
    'Jan 2024': 4845.65,
    'Feb 2024': 5096.27,
    'Mar 2024': 5254.35,
    'Apr 2024': 5035.69,
    'May 2024': 5277.51,
    'Jun 2024': 5460.48,
    'Jul 2024': 5522.30
}
months = list(data.keys())
closes = list(data.values())

# Backtest trades
trades = []
for i in range(1, len(closes)):
    entry_month = months[i-1]
    exp_month = months[i]
    entry_price = closes[i-1]
    exp_price = closes[i]
    # Pick strikes, round to nearest 5
    def round_to_5(x):
        return round(x / 5) * 5
    lower_buy = round_to_5(entry_price * 0.94)
    lower_sell = round_to_5(entry_price * 0.95)
    upper_sell = round_to_5(entry_price * 1.05)
    upper_buy = round_to_5(entry_price * 1.06)
    # Assumed credit (adjustable)
    credit = 2.0
    # P/L calculation
    value_put_spread = max(0, lower_sell - exp_price) - max(0, lower_buy - exp_price)
    value_call_spread = max(0, exp_price - upper_sell) - max(0, exp_price - upper_buy)
    pl = credit - value_put_spread - value_call_spread
    trades.append({
        'Entry Month': entry_month,
        'Exp Month': exp_month,
        'Entry Price': entry_price,
        'Exp Price': exp_price,
        'Lower Buy': lower_buy,
        'Lower Sell': lower_sell,
        'Upper Sell': upper_sell,
        'Upper Buy': upper_buy,
        'P/L': pl
    })

# Output
print("Backtest Results for Monthly Iron Condors on SPX")
print("Assumed credit: 2.0 per condor")
total_pl = 0
wins = 0
for trade in trades:
    print(f"\nTrade exp {trade['Exp Month']}: Entry {trade['Entry Price']:.2f}, Exp {trade['Exp Price']:.2f}")
    print(f"Strikes: Put {trade['Lower Buy']}/{trade['Lower Sell']}, Call {trade['Upper Sell']}/{trade['Upper Buy']}")
    print(f"P/L: {trade['P/L']:.2f}")
    total_pl += trade['P/L']
    if trade['P/L'] > 0:
        wins += 1
print(f"\nTotal P/L: {total_pl:.2f}")
print(f"Win rate: {wins / len(trades) * 100:.2f}%")