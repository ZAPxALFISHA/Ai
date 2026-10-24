from __future__ import annotations
import pandas as pd
import yfinance as yf

def fetch_history(symbol: str, period: str = "3mo", interval: str = "1h") -> pd.DataFrame:
    """Fetch market history. Provider availability and freshness are not guaranteed."""
    data = yf.download(
        symbol, period=period, interval=interval,
        auto_adjust=True, progress=False, threads=False
    )
    if data is None or data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    needed = ["Open", "High", "Low", "Close", "Volume"]
    for col in needed:
        if col not in data.columns:
            data[col] = 0.0
    data = data[needed].copy()
    data = data.dropna(subset=["Close"])
    return data

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    close = out["Close"].astype(float)
    out["SMA20"] = close.rolling(20).mean()
    out["SMA50"] = close.rolling(50).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    out["RSI14"] = 100 - (100 / (1 + rs))
    out["RSI14"] = out["RSI14"].fillna(50)
    return out

def signal_for(df: pd.DataFrame) -> dict:
    """Simple educational baseline signal, not a forecast."""
    if df.empty or len(df) < 55:
        return {"signal": "NO DATA", "reason": "Need at least 55 candles.", "price": None, "rsi": None}
    x = add_indicators(df).dropna(subset=["SMA20", "SMA50"])
    if x.empty:
        return {"signal": "NO TRADE", "reason": "Indicators not ready.", "price": None, "rsi": None}
    last = x.iloc[-1]
    price = float(last["Close"])
    rsi = float(last["RSI14"])
    if last["SMA20"] > last["SMA50"] and 50 <= rsi < 70:
        sig, reason = "BUY (SIMULATED)", "SMA20 above SMA50 and RSI supports momentum."
    elif last["SMA20"] < last["SMA50"] and 30 < rsi <= 50:
        sig, reason = "SELL (SIMULATED)", "SMA20 below SMA50 and RSI supports downside momentum."
    else:
        sig, reason = "NO TRADE", "Trend/RSI conditions are not aligned."
    return {"signal": sig, "reason": reason, "price": price, "rsi": rsi}
