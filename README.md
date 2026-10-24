# AI Forex + Gold Paper Trading Simulator

Educational project for **market monitoring, historical backtesting, virtual trades, a web dashboard, and private Telegram alerts**.
It does **not** place real orders and has no broker execution integration.

## Markets and data notes
- Forex symbols use Yahoo Finance symbols such as `EURUSD=X`, `GBPUSD=X`, `USDJPY=X`.
- Gold uses `GC=F` (COMEX gold futures proxy), **not a guaranteed XAUUSD spot quote**.
- Yahoo Finance data can be delayed, incomplete, rate-limited, or unavailable. It is not an execution-grade feed.
- Backtests are simplified and do not perfectly model spreads, slippage, swaps, or market gaps.

## 1) Install (Android Termux or Linux)
Python 3.10+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Termux, if `python -m venv` is unavailable, install Python with `pkg install python` and use `pip install -r requirements.txt` (a virtual environment is recommended where available).

## 2) Run the dashboard
```bash
streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501
```
Open `http://127.0.0.1:8501` on the same device. If running on a VPS, secure the dashboard behind a firewall/reverse proxy and do not expose it publicly without authentication.

## 3) Optional private Telegram bot
1. Create a bot with `@BotFather`.
2. Put the token in `.env` as `TELEGRAM_BOT_TOKEN=...`.
3. Find your numeric Telegram user ID and set `TELEGRAM_ALLOWED_USER_ID=...`.
4. Run:
```bash
python telegram_bot.py
```
The bot denies requests from other user IDs. Keep the token private.

Commands: `/start`, `/market`, `/analyze`, `/portfolio`, `/trades`, `/report`, `/help`.

## 4) Paper-trading behavior
- Signals are educational rules based on moving averages and RSI, not a predictive guarantee.
- A virtual position is opened only when you click **Run one paper cycle** in the dashboard.
- The simulator tracks a virtual balance. No real funds, broker login, or real orders are used.
- Stop-loss/take-profit are simulated using recent candle prices; real execution can differ materially.

## Troubleshooting
- If data download fails, check internet access and try again later.
- If Telegram is not configured, the dashboard still works; leave token empty.
- Do not paste API keys or bot tokens into chat or commit `.env` to GitHub.
