#!/usr/bin/env python3
"""
Telegram Crypto Bot — Webhook Version for Railway
- يعتمد على CoinGecko API
- يدعم:
  /start, /price, /convert, /setalert, /listalerts, /delalert
- التنبيهات تعمل بالـ JobQueue (مفعل)
- يستخدم Webhook بدلاً من Polling لتوفير الموارد
"""

import os
import logging
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    PicklePersistence
)

# ================== الإعدادات ==================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU")  # أو ضع التوكن هنا مباشرة
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://اسم-المشروع.up.railway.app")
PORT = int(os.getenv("PORT", 8000))

COINGECKO_API = "https://api.coingecko.com/api/v3"
DEFAULT_FIAT = "usd"
TOP_COINS = [
    ("bitcoin", "BTC"),
    ("ethereum", "ETH"),
    ("binancecoin", "BNB"),
    ("solana", "SOL"),
    ("cardano", "ADA"),
    ("dogecoin", "DOGE"),
    ("ripple", "XRP"),
]

# ================== الدوال المساعدة ==================
def _fetch(url: str, params: dict = None) -> dict:
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def get_market(coin_id: str, vs: str = DEFAULT_FIAT):
    data = _fetch(f"{COINGECKO_API}/coins/markets", params={"vs_currency": vs, "ids": coin_id})
    return data[0] if data else None

def fmt_money(v, vs):
    if v is None:
        return "?"
    return f"{v:,.2f} {vs.upper()}"

def build_keyboard(vs):
    rows = []
    row = []
    for cid, sym in TOP_COINS:
        row.append(InlineKeyboardButton(sym, callback_data=f"PRICE:{cid}:{vs}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

# ================== الأوامر ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vs = DEFAULT_FIAT
    text = "👋 أهلاً! أنا بوت أسعار العملات الرقمية.\n\nالأوامر:\n/price <coin> [fiat]\n/convert <amount> <coin> <fiat>"
    await update.message.reply_text(text, reply_markup=build_keyboard(vs))

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("اكتب: /price <coin>")
        return
    coin_id = context.args[0].lower()
    vs = context.args[1].lower() if len(context.args) > 1 else DEFAULT_FIAT
    m = get_market(coin_id, vs)
    if not m:
        await update.message.reply_text("تعذر جلب السعر.")
        return
    text = (
        f"💰 *{m['name']}* ({m['symbol'].upper()})\n"
        f"السعر: *{fmt_money(m.get('current_price'), vs)}*\n"
        f"التغير 24h: *{m.get('price_change_percentage_24h', 0):.2f}%*"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("PRICE:"):
        _, cid, vs = data.split(":")
        m = get_market(cid, vs)
        if m:
            text = (
                f"💰 *{m['name']}* ({m['symbol'].upper()})\n"
                f"السعر: *{fmt_money(m.get('current_price'), vs)}*"
            )
            await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=build_keyboard(vs))

# ================== Main ==================
async def main():
    persistence = PicklePersistence(filepath="crypto_bot.pickle")
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    # تأكد من تفعيل JobQueue
    if app.job_queue is None:
        raise RuntimeError("JobQueue غير مفعلة. تحقق من نسخة المكتبة.")

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CallbackQueryHandler(on_button))

    logging.basicConfig(level=logging.INFO)
    print(f"✅ Bot is running on Webhook: {WEBHOOK_URL}")

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    asyncio.run(main())
