import logging
import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ===== إعدادات البوت =====
BOT_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"
WEBHOOK_URL = "https://delightful-smile.up.railway.app"  # عدل إلى رابط مشروعك على Railway
API_URL = "https://api.coingecko.com/api/v3/simple/price"
PORT = int(os.environ.get("PORT", 8000))

# ===== تفعيل اللوغ =====
logging.basicConfig(level=logging.INFO)

# ===== دالة البداية =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا! أرسل اسم أي عملة رقمية لأعطيك السعر بالدولار 💰.\nمثال: bitcoin أو ethereum"
    )

# ===== دالة جلب السعر =====
async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = update.message.text.strip().lower()
    params = {"ids": coin, "vs_currencies": "usd"}
    try:
        response = requests.get(API_URL, params=params, timeout=10).json()
        if coin in response:
            price = response[coin]["usd"]
            await update.message.reply_text(f"💰 سعر {coin.capitalize()} هو: {price} USD")
        else:
            await update.message.reply_text("⚠️ لم أتمكن من العثور على هذه العملة. حاول باسم صحيح.")
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ أثناء جلب السعر. حاول لاحقًا.")

# ===== الدالة الرئيسية =====
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_price))

    print("✅ البوت يعمل الآن باستخدام Webhook...")

    await app.start()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )
    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
