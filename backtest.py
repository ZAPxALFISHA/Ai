"""Simple educational moving-average/RSI backtest; ignores real trading costs."""
import argparse
import pandas as pd
from config import MARKETS
from market_data import fetch_history, add_indicators

def run_backtest(symbol: str, period: str, interval: str, starting_balance: float = 10000.0):
    df = add_indicators(fetch_history(symbol, period, interval)).dropna()
    if len(df) < 55:
        print("Not enough historical data for a basic backtest.")
        return
    balance = starting_balance
    position = 0
    entry = 0.0
    trades = []
    for idx, row in df.iterrows():
        price = float(row["Close"])
        signal = 0
        if row["SMA20"] > row["SMA50"] and 50 <= row["RSI14"] < 70:
            signal = 1
        elif row["SMA20"] < row["SMA50"] and 30 < row["RSI14"] <= 50:
            signal = -1
        # Close on opposite signal; position sizing is intentionally simplified.
        if position and signal == -position:
            pnl = (price - entry) * position
            balance += pnl
            trades.append(pnl)
            position = 0
        if not position and signal:
            position, entry = signal, price
    if position:
        final_price = float(df["Close"].iloc[-1])
        pnl = (final_price - entry) * position
        balance += pnl
        trades.append(pnl)
    wins = sum(p > 0 for p in trades)
    print(f"Symbol: {symbol}")
    print(f"Candles: {len(df)} | Closed trades: {len(trades)}")
    print(f"Starting virtual balance: {starting_balance:.2f}")
    print(f"Ending virtual balance: {balance:.2f}")
    print(f"Net P/L (simplified): {balance-starting_balance:.2f}")
    print(f"Win rate: {100*wins/len(trades):.1f}%" if trades else "Win rate: N/A")
    print("Note: simplified, no spread/slippage/swap and not a prediction of future results.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", default="EUR/USD", choices=list(MARKETS))
    parser.add_argument("--period", default="1y", choices=["1mo", "3mo", "6mo", "1y", "2y"])
    parser.add_argument("--interval", default="1d", choices=["30m", "1h", "1d"])
    args = parser.parse_args()
    run_backtest(MARKETS[args.market], args.period, args.interval)
