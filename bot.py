import asyncio
import logging
import os
import threading
import time

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import db
import prices

load_dotenv()
TOKEN = os.getenv("TG_BOT_TOKEN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)


# ── Commands ────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 *Crypto Price Alert Bot*\n\n"
        "Set alerts and get notified when price hits your target.\n\n"
        "*Commands:*\n"
        "`/alert BTC below 50000` — notify when BTC < $50,000\n"
        "`/alert ETH above 3000` — notify when ETH > $3,000\n"
        "`/alerts` — list your active alerts\n"
        "`/remove 1` — remove alert by ID\n\n"
        "Prices from Binance (real-time).",
        parse_mode="Markdown"
    )


async def cmd_alert(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = ctx.args

    if len(args) != 3:
        await update.message.reply_text(
            "Usage: `/alert BTC below 50000` or `/alert ETH above 3000`",
            parse_mode="Markdown"
        )
        return

    symbol, condition, price_str = args
    symbol = symbol.upper()
    condition = condition.lower()

    if condition not in ("above", "below"):
        await update.message.reply_text("Condition must be `above` or `below`.", parse_mode="Markdown")
        return

    try:
        price = float(price_str.replace(",", ""))
    except ValueError:
        await update.message.reply_text("Price must be a number, e.g. `50000` or `0.5`", parse_mode="Markdown")
        return

    current = prices.get_price(symbol)
    if current is None:
        await update.message.reply_text(f"Could not find price for {symbol}. Check the ticker (BTC, ETH, SOL...)")
        return

    alert_id = db.add_alert(user_id, symbol, condition, price)
    await update.message.reply_text(
        f"✅ Alert #{alert_id} set!\n"
        f"*{symbol}* {condition} *${price:,.2f}*\n"
        f"Current price: ${current:,.2f}",
        parse_mode="Markdown"
    )


async def cmd_alerts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    alerts = db.get_alerts(user_id)

    if not alerts:
        await update.message.reply_text("You have no active alerts.\nUse `/alert BTC below 50000` to create one.", parse_mode="Markdown")
        return

    lines = ["📋 *Your active alerts:*\n"]
    for a in alerts:
        current = prices.get_price(a.symbol) or 0
        lines.append(f"#{a.id} — *{a.symbol}* {a.condition} ${a.price:,.2f}  _(now: ${current:,.2f})_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: `/remove 3` (use alert ID from /alerts)", parse_mode="Markdown")
        return

    alert_id = int(ctx.args[0])
    if db.remove_alert(user_id, alert_id):
        await update.message.reply_text(f"Deleted alert #{alert_id}.")
    else:
        await update.message.reply_text(f"Alert #{alert_id} not found.")


# ── Background checker ───────────────────────────────────────────────────────

def price_checker(app):
    """Runs in a background thread — checks alerts every 30 seconds."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            alerts = db.get_all_active()
            if alerts:
                symbols = list({a.symbol for a in alerts})
                current_prices = prices.get_prices_bulk(symbols)

                for alert in alerts:
                    current = current_prices.get(alert.symbol)
                    if current is None:
                        continue

                    triggered = (
                        (alert.condition == "below" and current <= alert.price) or
                        (alert.condition == "above" and current >= alert.price)
                    )

                    if triggered:
                        db.mark_triggered(alert.id)
                        arrow = "📉" if alert.condition == "below" else "📈"
                        text = (
                            f"{arrow} *Alert triggered!*\n"
                            f"*{alert.symbol}* is now ${current:,.2f}\n"
                            f"Your target: {alert.condition} ${alert.price:,.2f}"
                        )
                        loop.run_until_complete(
                            app.bot.send_message(chat_id=alert.user_id, text=text, parse_mode="Markdown")
                        )
                        log.info(f"Alert #{alert.id} triggered: {alert.symbol} @ {current}")
        except Exception as e:
            log.error(f"Checker error: {e}")

        time.sleep(30)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    db.init_db()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("alert", cmd_alert))
    app.add_handler(CommandHandler("alerts", cmd_alerts))
    app.add_handler(CommandHandler("remove", cmd_remove))

    thread = threading.Thread(target=price_checker, args=(app,), daemon=True)
    thread.start()

    log.info("Bot started. Checking prices every 30s.")
    app.run_polling()


if __name__ == "__main__":
    main()
