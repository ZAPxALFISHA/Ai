import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import MARKETS, TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_ID
from market_data import fetch_history, signal_for
from paper_trader import load_state, load_trades

def authorized(update: Update) -> bool:
    uid = str(update.effective_user.id) if update.effective_user else ""
    return bool(TELEGRAM_ALLOWED_USER_ID) and uid == TELEGRAM_ALLOWED_USER_ID

async def gate(update: Update) -> bool:
    if not authorized(update):
        if update.message:
            await update.message.reply_text("Access denied. This bot is configured for one authorized Telegram user.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update): return
    await update.message.reply_text(
        "Private Forex + Gold Paper Lab\\n"
        "/market — latest available prices\\n/analyze — educational signals\\n"
        "/portfolio — virtual balance\\n/trades — recent virtual trades\\n/report — performance summary"
    )

async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update): return
    lines = ["Latest available data (may be delayed):"]
    for name, symbol in MARKETS.items():
        df = fetch_history(symbol, period="5d", interval="1h")
        if df.empty: lines.append(f"{name}: data unavailable")
        else: lines.append(f"{name}: {float(df['Close'].iloc[-1]):.5f}")
    await update.message.reply_text("\\n".join(lines))

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update): return
    lines = ["Educational indicator signals (not predictions):"]
    for name, symbol in MARKETS.items():
        df = fetch_history(symbol, period="3mo", interval="1h")
        result = signal_for(df)
        p = result["price"]
        price = f"{p:.5f}" if p is not None else "N/A"
        lines.append(f"{name}: {result['signal']} | price={price} | {result['reason']}")
    await update.message.reply_text("\\n".join(lines))

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update): return
    state = load_state()
    await update.message.reply_text(
        f"Virtual balance: {float(state['balance']):,.2f}\\n"
        f"Starting virtual balance: {float(state['starting_balance']):,.2f}"
    )

async def trades_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update): return
    trades = load_trades()
    if not trades:
        await update.message.reply_text("No virtual trades yet.")
        return
    lines = []
    for t in trades[-10:][::-1]:
        lines.append(f"{t['market']} {t['side']} @ {t['entry']} — {t['status']} — P/L {t.get('pnl', 0)}")
    await update.message.reply_text("\\n".join(lines))

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update): return
    trades = load_trades()
    closed = [t for t in trades if t.get("status") != "OPEN (VIRTUAL)"]
    pnl = sum(float(t.get("pnl", 0)) for t in closed)
    wins = sum(float(t.get("pnl", 0)) > 0 for t in closed)
    rate = 100 * wins / len(closed) if closed else 0
    await update.message.reply_text(
        f"Closed virtual trades: {len(closed)}\\nVirtual realized P/L: {pnl:.2f}\\nWin rate: {rate:.1f}%"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await gate(update): return
    await update.message.reply_text("/start /market /analyze /portfolio /trades /report /help")

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ALLOWED_USER_ID:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_ID in .env first.")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("trades", trades_cmd))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("help", help_cmd))
    print("Private paper-trading Telegram bot running. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
