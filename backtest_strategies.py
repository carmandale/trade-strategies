import argparse
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta

class OptionsBacktester:
    def __init__(self, timeframe, start_date, end_date, strike_pct_lower=0.05, strike_pct_upper=0.05, credit=2.0, manage_early=False):
        self.timeframe = timeframe.lower()
        self.start_date = start_date
        self.end_date = end_date
        self.strike_pct_lower = strike_pct_lower  # % below entry for lower sell (adjustable)
        self.strike_pct_upper = strike_pct_upper  # % above entry for upper sell
        self.credit = credit  # Base credit; scaled by timeframe in run_backtest
        self.manage_early = manage_early  # If True, simulate 50% profit take
        self.data = self.fetch_data()
        self.trades = pd.DataFrame()

    def fetch_data(self):
        """Fetch historical SPX data using yfinance and resample based on timeframe."""
        ticker = '^GSPC'
        df = yf.download(ticker, start=self.start_date, end=self.end_date)
        if self.timeframe == 'daily':
            return df[['Open', 'Close']].rename(columns={'Open': 'Entry', 'Close': 'Exp'})
        elif self.timeframe == 'weekly':
            return df.resample('W-FRI').last()[['Close']].shift(1).join(df.resample('W-FRI').last()['Close'], lsuffix='_entry', rsuffix='_exp').dropna()
        elif self.timeframe == 'monthly':
            return df.resample('M').last()[['Close']].shift(1).join(df.resample('M').last()['Close'], lsuffix='_entry', rsuffix='_exp').dropna()
        else:
            raise ValueError("Timeframe must be 'daily', 'weekly', or 'monthly'.")

    def round_to_5(self, x):
        return round(x / 5) * 5

    def calculate_pl(self, entry_price, exp_price, lower_buy, lower_sell, upper_sell, upper_buy, credit):
        value_put_spread = max(0, lower_sell - exp_price) - max(0, lower_buy - exp_price)
        value_call_spread = max(0, exp_price - upper_sell) - max(0, exp_price - upper_buy)
        pl = credit - value_put_spread - value_call_spread
        if self.manage_early and pl > 0:
            pl *= 0.5  # Simulate taking 50% profit early
        return pl

    def run_backtest(self):
        """Run the iron condor backtest and compute metrics."""
        trades_list = []
        for date, row in self.data.iterrows():
            entry_price = row.get('Entry', row['Close_entry']) if self.timeframe == 'daily' else row['Close_entry']
            exp_price = row.get('Exp', row['Close_exp']) if self.timeframe == 'daily' else row['Close_exp']
            
            # Adjust params by timeframe for realism
            adj_lower_pct_buy = 1 - self.strike_pct_lower - 0.005
            adj_lower_pct_sell = 1 - self.strike_pct_lower
            adj_upper_pct_sell = 1 + self.strike_pct_upper
            adj_upper_pct_buy = 1 + self.strike_pct_upper + 0.005
            adj_credit = self.credit * (0.25 if self.timeframe == 'daily' else 0.5 if self.timeframe == 'weekly' else 1)
            
            lower_buy = self.round_to_5(entry_price * adj_lower_pct_buy)
            lower_sell = self.round_to_5(entry_price * adj_lower_pct_sell)
            upper_sell = self.round_to_5(entry_price * adj_upper_pct_sell)
            upper_buy = self.round_to_5(entry_price * adj_upper_pct_buy)
            
            pl = self.calculate_pl(entry_price, exp_price, lower_buy, lower_sell, upper_sell, upper_buy, adj_credit)
            trades_list.append({
                'Date': date,
                'Entry Price': entry_price,
                'Exp Price': exp_price,
                'Lower Buy': lower_buy,
                'Lower Sell': lower_sell,
                'Upper Sell': upper_sell,
                'Upper Buy': upper_buy,
                'P/L': pl
            })
        
        self.trades = pd.DataFrame(trades_list)
        self.trades['Cumulative P/L'] = self.trades['P/L'].cumsum()
        
        # Metrics
        win_rate = (self.trades['P/L'] > 0).mean() * 100
        total_pl = self.trades['P/L'].sum()
        avg_pl = self.trades['P/L'].mean()
        max_drawdown = (self.trades['Cumulative P/L'].cummax() - self.trades['Cumulative P/L']).max()
        sharpe = (self.trades['P/L'].mean() / self.trades['P/L'].std()) * (252 ** 0.5 if self.timeframe == 'daily' else 52 ** 0.5 if self.timeframe == 'weekly' else 12 ** 0.5)  # Annualized
        
        print(f"Backtest Results for {self.timeframe.capitalize()} Iron Condors on SPX")
        print(f"Assumed base credit: {self.credit}; Early management: {self.manage_early}")
        print(self.trades.to_string(index=False))
        print(f"\nWin rate: {win_rate:.2f}%")
        print(f"Total P/L: {total_pl:.2f}")
        print(f"Avg P/L: {avg_pl:.2f}")
        print(f"Max Drawdown: {max_drawdown:.2f}")
        print(f"Sharpe Ratio: {sharpe:.2f}")
        
        return self.trades

    def plot_results(self):
        """Plot equity curve and P/L histogram."""
        fig, axs = plt.subplots(2, 1, figsize=(10, 8))
        self.trades.plot(x='Date', y='Cumulative P/L', ax=axs[0], title='Equity Curve')
        self.trades['P/L'].hist(ax=axs[1], bins=20, title='P/L Distribution')
        plt.tight_layout()
        plt.show()

    def export_to_csv(self, filename='backtest_results.csv'):
        self.trades.to_csv(filename, index=False)
        print(f"Exported to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Backtest Iron Condor Strategies on SPX")
    parser.add_argument('--timeframe', type=str, default='monthly', choices=['daily', 'weekly', 'monthly'], help='Strategy timeframe')
    parser.add_argument('--start_date', type=str, default=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'), help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, default=datetime.now().strftime('%Y-%m-%d'), help='End date (YYYY-MM-DD)')
    parser.add_argument('--strike_pct_lower', type=float, default=0.05, help='Lower strike % below entry')
    parser.add_argument('--strike_pct_upper', type=float, default=0.05, help='Upper strike % above entry')
    parser.add_argument('--credit', type=float, default=2.0, help='Base credit per condor')
    parser.add_argument('--manage_early', action='store_true', help='Simulate early 50% profit take')
    parser.add_argument('--plot', action='store_true', help='Show plots')
    parser.add_argument('--export', action='store_true', help='Export to CSV')
    
    args = parser.parse_args()
    
    backtester = OptionsBacktester(
        args.timeframe, args.start_date, args.end_date,
        args.strike_pct_lower, args.strike_pct_upper, args.credit, args.manage_early
    )
    trades = backtester.run_backtest()
    if args.plot:
        backtester.plot_results()
    if args.export:
        backtester.export_to_csv()

if __name__ == "__main__":
    main()