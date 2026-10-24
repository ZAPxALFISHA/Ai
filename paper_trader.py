from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Any
from config import STARTING_BALANCE, RISK_PER_TRADE_PCT

STATE_FILE = "paper_state.json"
TRADES_FILE = "paper_trades.json"

def _read_json(path: str, default: Any):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default

def load_state() -> dict:
    return _read_json(STATE_FILE, {"balance": STARTING_BALANCE, "starting_balance": STARTING_BALANCE})

def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def load_trades() -> list:
    return _read_json(TRADES_FILE, [])

def save_trades(trades: list) -> None:
    with open(TRADES_FILE, "w", encoding="utf-8") as f:
        json.dump(trades, f, indent=2)

def run_paper_cycle(market: str, symbol: str, df, signal: dict) -> str:
    """One-candle educational simulation. Never places real orders."""
    if signal.get("price") is None or signal.get("signal") not in ("BUY (SIMULATED)", "SELL (SIMULATED)"):
        return f"{market}: no simulated trade — {signal.get('reason', 'no valid signal')}"
    trades = load_trades()
    # Avoid repeatedly creating the same signal for the same latest candle.
    candle_time = str(df.index[-1])
    if any(t.get("market") == market and t.get("candle_time") == candle_time for t in trades):
        return f"{market}: this candle has already been processed."
    price = float(signal["price"])
    state = load_state()
    risk_amount = max(0.0, float(state["balance"]) * RISK_PER_TRADE_PCT / 100.0)
    # For a simple simulator, stop distance is 1% of price. Virtual units are scaled by risk.
    stop_distance = max(price * 0.01, 1e-8)
    units = risk_amount / stop_distance if stop_distance else 0
    direction = 1 if signal["signal"].startswith("BUY") else -1
    stop = price - direction * stop_distance
    target = price + direction * stop_distance * 2
    trade = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "candle_time": candle_time,
        "market": market,
        "symbol": symbol,
        "side": "BUY" if direction == 1 else "SELL",
        "entry": price,
        "stop_loss": stop,
        "take_profit": target,
        "virtual_units": units,
        "risk_budget": risk_amount,
        "status": "OPEN (VIRTUAL)",
        "exit": None,
        "pnl": 0.0,
    }
    trades.append(trade)
    save_trades(trades)
    return f"{market}: opened {trade['side']} virtual position at {price:.5f}; SL {stop:.5f}; TP {target:.5f}."

def update_open_positions(prices: dict[str, float]) -> int:
    trades = load_trades()
    state = load_state()
    changed = 0
    for t in trades:
        if t.get("status") != "OPEN (VIRTUAL)" or t["market"] not in prices:
            continue
        price = float(prices[t["market"]])
        side = 1 if t["side"] == "BUY" else -1
        hit = None
        if side == 1 and price <= t["stop_loss"]: hit = "STOP LOSS (SIMULATED)"
        elif side == 1 and price >= t["take_profit"]: hit = "TAKE PROFIT (SIMULATED)"
        elif side == -1 and price >= t["stop_loss"]: hit = "STOP LOSS (SIMULATED)"
        elif side == -1 and price <= t["take_profit"]: hit = "TAKE PROFIT (SIMULATED)"
        if hit:
            pnl = (price - t["entry"]) * t["virtual_units"] * side
            t["exit"] = price
            t["pnl"] = round(pnl, 2)
            t["status"] = hit
            state["balance"] = round(float(state["balance"]) + pnl, 2)
            changed += 1
    save_trades(trades)
    save_state(state)
    return changed

def reset_paper_account() -> None:
    save_state({"balance": STARTING_BALANCE, "starting_balance": STARTING_BALANCE})
    save_trades([])
