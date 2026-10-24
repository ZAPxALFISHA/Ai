import pandas as pd
import streamlit as st
from config import MARKETS, STARTING_BALANCE
from market_data import fetch_history, add_indicators, signal_for
from paper_trader import load_state, load_trades, run_paper_cycle, update_open_positions, reset_paper_account

st.set_page_config(page_title="AI Forex Paper Lab", page_icon="📈", layout="wide")
st.title("📈 AI Forex + Gold Paper Trading Lab")
st.caption("Educational simulator only — virtual trades, no broker connection and no real-money orders.")

with st.sidebar:
    st.header("Settings")
    market = st.selectbox("Market", list(MARKETS.keys()))
    period = st.selectbox("History period", ["1mo", "3mo", "6mo", "1y"], index=1)
    interval = st.selectbox("Candle interval", ["30m", "1h", "1d"], index=1)
    refresh = st.button("Refresh market data")
    st.divider()
    st.warning("Data may be delayed or unavailable. Gold symbol GC=F is a futures proxy, not spot XAUUSD.")

symbol = MARKETS[market]
with st.spinner("Fetching market data..."):
    df = fetch_history(symbol, period=period, interval=interval)

if df.empty:
    st.error("No data returned. Try another interval/period or try again later.")
    st.stop()

df = add_indicators(df)
sig = signal_for(df)
last_price = float(df["Close"].iloc[-1])
state = load_state()
trades = load_trades()
closed = [t for t in trades if t.get("status") != "OPEN (VIRTUAL)"]
wins = sum(1 for t in closed if float(t.get("pnl", 0)) > 0)
win_rate = (100 * wins / len(closed)) if closed else 0
realized_pnl = sum(float(t.get("pnl", 0)) for t in closed)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest available price", f"{last_price:.5f}")
c2.metric("Virtual balance", f"{state['balance']:,.2f}")
c3.metric("Closed virtual P/L", f"{realized_pnl:,.2f}")
c4.metric("Closed-trade win rate", f"{win_rate:.1f}%")

st.subheader(f"{market} — {symbol}")
st.write(f"**Signal:** {sig['signal']}  \n**Reason:** {sig['reason']}  \n**RSI(14):** {sig['rsi'] if sig['rsi'] is not None else 'N/A'}")
chart_cols = ["Close", "SMA20", "SMA50"]
st.line_chart(df[chart_cols].tail(250), height=360)

left, right = st.columns(2)
with left:
    st.subheader("Paper trading")
    st.write("The simulator opens at most one position per market per latest candle.")
    if st.button("Run one paper cycle", type="primary"):
        msg = run_paper_cycle(market, symbol, df, sig)
        prices = {}
        for name, sym in MARKETS.items():
            d = fetch_history(sym, period="5d", interval="1h")
            if not d.empty:
                prices[name] = float(d["Close"].iloc[-1])
        update_open_positions(prices)
        st.success(msg)
        st.rerun()
    if st.button("Reset virtual account"):
        reset_paper_account()
        st.success("Virtual account reset.")
        st.rerun()
with right:
    st.subheader("Recent candles")
    st.dataframe(df[["Open", "High", "Low", "Close", "SMA20", "SMA50", "RSI14"]].tail(12), use_container_width=True)

st.subheader("Virtual trade history")
if trades:
    st.dataframe(pd.DataFrame(trades[::-1]), use_container_width=True)
else:
    st.info("No virtual trades yet. Choose a market and click Run one paper cycle.")

st.subheader("Important limitations")
st.markdown("""
- This is a learning simulator, not financial advice or a profit guarantee.
- A signal is not proof of future price direction.
- This simplified simulation does not model real spreads, swaps, slippage, execution delays, or all gap scenarios.
- Live monitoring depends on the data provider and is not guaranteed to be real-time.
""")
