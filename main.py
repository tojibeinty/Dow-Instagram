#!/usr/bin/env python3
"""
Telegram Crypto Bot — Python (python-telegram-bot v20+)

Features:
- /start: quick intro + buttons for top coins
- /price <COIN> [FIAT]: current price, 24h change, market cap (default USD)
- Inline buttons for quick prices (BTC/ETH/BNB/SOL/ADA/DOGE/XRP)
- /convert <AMOUNT> <FROM_COIN> <TO_FIAT>: simple conversion using live price
- /setalert <COIN> <TARGET> [above|below]: price alerts (checked every 60s)
- /listalerts and /delalert <INDEX>
- Coin IDs auto-resolved via CoinGecko (no API key required)
- Simple persistence (Pickle) to keep alerts after restart

Quick start:
1) pip install python-telegram-bot==20.7 requests python-dotenv
2) Create a bot with @BotFather and copy the token
3) Put BOT_TOKEN in a .env file: BOT_TOKEN=123456:ABC-DEF...
4) python bot.py

Note: For servers, consider using a process manager (systemd/pm2) or Docker.
"""

import asyncio
import logging
import math
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    PicklePersistence,
)

# =============== Config & Globals ===============
load_dotenv()
BOT_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"

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

# Common fiat codes supported by CG /simple/price
FIAT_WHITELIST = {
    "usd", "eur", "gbp", "try", "aed", "sar", "kwd", "qar", "omr", "bhd", "jod", "ils", "irr", "iqd"
}

# Cache for coins list to resolve user symbols -> coingecko IDs
_COINS_CACHE: List[Dict] = []
_COINS_CACHE_TS = 0.0
_COINS_CACHE_TTL = 60 * 60 * 12  # 12 hours


# =============== Helper Functions ===============

def _fetch(url: str, params: Optional[dict] = None) -> dict:
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _load_coins_cache(force: bool = False) -> List[Dict]:
    global _COINS_CACHE, _COINS_CACHE_TS
    now = time.time()
    if force or not _COINS_CACHE or (now - _COINS_CACHE_TS) > _COINS_CACHE_TTL:
        _COINS_CACHE = _fetch(f"{COINGECKO_API}/coins/list")
        _COINS_CACHE_TS = now
    return _COINS_CACHE


def resolve_coin(query: str) -> Optional[str]:
    """Resolve user input like 'btc' or 'Bitcoin' to a CoinGecko coin id (e.g., 'bitcoin')."""
    if not query:
        return None
    q = query.strip().lower()

    # Quick wins for top coins
    for cid, sym in TOP_COINS:
        if q in (cid, sym.lower(), sym):
            return cid

    # Search coins list
    for c in _load_coins_cache():
        if q == c.get("id", "").lower():
            return c["id"]
        if q == c.get("symbol", "").lower():
            return c["id"]
        if q == c.get("name", "").lower():
            return c["id"]

    # Partial match (starts with)
    for c in _load_coins_cache():
        if c.get("name", "").lower().startswith(q) or c.get("id", "").lower().startswith(q):
            return c["id"]

    return None


def get_market(coin_id: str, vs: str = DEFAULT_FIAT) -> Optional[dict]:
    vs = vs.lower()
    data = _fetch(
        f"{COINGECKO_API}/coins/markets",
        params={"vs_currency": vs, "ids": coin_id},
    )
    if not data:
        return None
    return data[0]


def get_simple_price(coin_id: str, vs: str = DEFAULT_FIAT) -> Optional[float]:
    vs = vs.lower()
    data = _fetch(
        f"{COINGECKO_API}/simple/price",
        params={"ids": coin_id, "vs_currencies": vs},
    )
    try:
        return float(data[coin_id][vs])
    except Exception:
        return None


def fmt_money(v: Optional[float], vs: str) -> str:
    if v is None:
        return "?"
    # Simple formatting; IQD has no decimals typically, USD 2 decimals, others general
    if vs.lower() in {"iqd", "irr"}:
        return f"{int(round(v)):,} {vs.upper()}"
    return f"{v:,.2f} {vs.upper()}"


def build_top_keyboard(vs: str = DEFAULT_FIAT) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for cid, sym in TOP_COINS:
        row.append(InlineKeyboardButton(sym, callback_data=f"PRICE:{cid}:{vs}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(f"Change fiat ({vs.upper()})", callback_data=f"FIAT:{vs}")])
    return InlineKeyboardMarkup(rows)


# =============== Alert Dataclass ===============
@dataclass
class Alert:
    coin_id: str
    vs: str
    target: float
    direction: str  # 'above' or 'below'

    def to_text(self) -> str:
        arrow = "📈" if self.direction == "above" else "📉"
        return f"{arrow} {self.coin_id} {self.direction} {self.target} {self.vs.upper()}"


# =============== Command Handlers ===============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    vs = context.user_data.get("vs", DEFAULT_FIAT)
    text = (
        "👋 أهلاً! أنا بوت أسعار العملات الرقمية.\n\n"
        "الأوامر المتاحة:\n"
        "• /price <coin> [fiat] — السعر الحالي (مثال: /price BTC USD)\n"
        "• /convert <amount> <coin> <fiat> — تحويل (مثال: /convert 0.5 BTC IQD)\n"
        "• /setalert <coin> <target> [above|below] — تنبيه سعر\n"
        "• /listalerts — عرض التنبيهات\n"
        "• /delalert <index> — حذف تنبيه\n\n"
        "اختر عملة سريعة من الأزرار أدناه:"
    )
    await update.effective_chat.send_message(text, reply_markup=build_top_keyboard(vs))


async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("اكتب: /price <coin> [fiat]")
        return

    coin_q = args[0]
    vs = args[1].lower() if len(args) > 1 else context.user_data.get("vs", DEFAULT_FIAT)
    if vs not in FIAT_WHITELIST:
        vs = DEFAULT_FIAT

    cid = resolve_coin(coin_q)
    if not cid:
        await update.message.reply_text("❌ لم أتعرف على العملة.")
        return

    m = get_market(cid, vs)
    if not m:
        await update.message.reply_text("تعذر جلب السعر الآن.")
        return

    text = (
        f"💰 *{m['name']}* ({m['symbol'].upper()})\n"
        f"السعر: *{fmt_money(m.get('current_price'), vs)}*\n"
        f"التغير 24h: *{m.get('price_change_percentage_24h', 0):.2f}%*\n"
        f"القيمة السوقية: *{fmt_money(m.get('market_cap'), vs)}*\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=build_top_keyboard(vs))


async def convert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("اكتب: /convert <amount> <coin> <fiat>\nمثال: /convert 0.25 BTC IQD")
        return

    try:
        amount = float(args[0])
    except ValueError:
        await update.message.reply_text("القيمة غير صحيحة.")
        return

    cid = resolve_coin(args[1])
    vs = args[2].lower()
    if not cid or vs not in FIAT_WHITELIST:
        await update.message.reply_text("عملة/عملة ورقية غير معروفة.")
        return

    price = get_simple_price(cid, vs)
    if price is None:
        await update.message.reply_text("تعذر جلب السعر.")
        return

    total = amount * price
    await update.message.reply_text(
        f"{amount:g} {args[1].upper()} ≈ {fmt_money(total, vs)}"
    )


async def setalert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("اكتب: /setalert <coin> <target> [above|below]")
        return

    cid = resolve_coin(args[0])
    if not cid:
        await update.message.reply_text("عملة غير معروفة.")
        return

    try:
        target = float(args[1])
    except ValueError:
        await update.message.reply_text("القيمة الهدف غير صحيحة.")
        return

    direction = args[2].lower() if len(args) >= 3 else "above"
    if direction not in {"above", "below"}:
        direction = "above"

    vs = context.user_data.get("vs", DEFAULT_FIAT)
    alerts: List[Alert] = context.chat_data.get("alerts", [])
    alert = Alert(coin_id=cid, vs=vs, target=target, direction=direction)
    alerts.append(alert)
    context.chat_data["alerts"] = alerts
    await update.message.reply_text(f"تم حفظ التنبيه: {alert.to_text()}")


async def listalerts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    alerts: List[Alert] = context.chat_data.get("alerts", [])
    if not alerts:
        await update.message.reply_text("لا توجد تنبيهات.")
        return
    lines = [f"#{i+1}) {a.to_text()}" for i, a in enumerate(alerts)]
    await update.message.reply_text("\n".join(lines))


async def delalert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("اكتب: /delalert <index>")
        return
    try:
        idx = int(args[0]) - 1
    except ValueError:
        await update.message.reply_text("رقم غير صحيح.")
        return

    alerts: List[Alert] = context.chat_data.get("alerts", [])
    if 0 <= idx < len(alerts):
        removed = alerts.pop(idx)
        context.chat_data["alerts"] = alerts
        await update.message.reply_text(f"تم حذف: {removed.to_text()}")
    else:
        await update.message.reply_text("الفهرس غير موجود.")


# =============== Jobs (Price Alerts) ===============
async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    alerts: List[Alert] = context.chat_data.get("alerts", [])
    if not alerts:
        return

    # Group alerts by (coin, vs) to minimize API calls
    groups: Dict[Tuple[str, str], List[int]] = {}
    for i, a in enumerate(alerts):
        groups.setdefault((a.coin_id, a.vs), []).append(i)

    triggered = []
    for (coin_id, vs), idxs in groups.items():
        price = get_simple_price(coin_id, vs)
        if price is None:
            continue
        for i in idxs:
            a = alerts[i]
            if (a.direction == "above" and price >= a.target) or (
                a.direction == "below" and price <= a.target
            ):
                triggered.append((i, a, price))

    # Send notifications and remove triggered alerts
    if triggered:
        # Remove in reverse index order to avoid shifting
        for i, a, price in sorted(triggered, key=lambda x: x[0], reverse=True):
            alerts.pop(i)
        context.chat_data["alerts"] = alerts

        for _, a, price in triggered:
            msg = (
                f"🔔 تنبيه سعر {a.coin_id}:\n"
                f"الحالي: {fmt_money(price, a.vs)} — الهدف: {fmt_money(a.target, a.vs)} ({a.direction})"
            )
            await context.bot.send_message(chat_id=chat_id, text=msg)


# =============== Callback Queries ===============
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()

    data = q.data or ""
    if data.startswith("PRICE:"):
        _, cid, vs = data.split(":", 2)
        m = get_market(cid, vs)
        if not m:
            await q.edit_message_text("تعذر جلب السعر.")
            return
        text = (
            f"💰 *{m['name']}* ({m['symbol'].upper()})\n"
            f"السعر: *{fmt_money(m.get('current_price'), vs)}*\n"
            f"التغير 24h: *{m.get('price_change_percentage_24h', 0):.2f}%*\n"
            f"القيمة السوقية: *{fmt_money(m.get('market_cap'), vs)}*\n"
        )
        await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=build_top_keyboard(vs))
        return

    if data.startswith("FIAT:"):
        vs = data.split(":", 1)[1]
        # Cycle a few popular fiats
        order = ["usd", "eur", "gbp", "iqd", "try", "aed", "sar"]
        cur = order.index(vs) if vs in order else 0
        vs2 = order[(cur + 1) % len(order)]
        context.user_data["vs"] = vs2
        await q.edit_message_reply_markup(reply_markup=build_top_keyboard(vs2))
        return


# =============== Main ===============
async def main() -> None:
    if not BOT_TOKEN or "PUT-YOUR-" in BOT_TOKEN:
        raise SystemExit("Please set BOT_TOKEN in .env or in the script.")

    persistence = PicklePersistence(filepath="crypto_bot.pickle")
    app: Application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("convert", convert_cmd))
    app.add_handler(CommandHandler("setalert", setalert_cmd))
    app.add_handler(CommandHandler("listalerts", listalerts_cmd))
    app.add_handler(CommandHandler("delalert", delalert_cmd))

    # Inline buttons
    app.add_handler(CallbackQueryHandler(on_button))

    # Jobs
    app.job_queue.run_repeating(check_alerts_job, interval=60, first=10, name="alerts")

    logging.basicConfig(level=logging.INFO)
    print("Bot is running...")
    await app.run_polling(close_loop=False)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
