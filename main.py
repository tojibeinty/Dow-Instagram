import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ====== إعدادات البوت ======
BOT_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"
API_URL = "https://api.coingecko.com/api/v3/simple/price"

# ====== تفعيل اللوغ ======
logging.basicConfig(level=logging.INFO)

# ====== دالة البدء ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً! أرسل لي اسم أي عملة رقمية لأعطيك السعر بالدولار 💰.\nمثال: bitcoin أو ethereum")

# ====== جلب السعر ======
async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = update.message.text.strip().lower()
    params = {
        "ids": coin,
        "vs_currencies": "usd"
    }
    try:
        response = requests.get(API_URL, params=params).json()
        if coin in response:
            price = response[coin]['usd']
            await update.message.reply_text(f"💰 سعر {coin.capitalize()} هو: {price} USD")
        else:
            await update.message.reply_text("⚠️ لم أتمكن من العثور على هذه العملة. حاول مرة أخرى باسم صحيح.")
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ أثناء جلب السعر. حاول لاحقاً.")

# ====== الدالة الرئيسية ======
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", get_price))  # يمكن كتابة /price bitcoin
    app.add_handler(CommandHandler("help", start))

    # التعامل مع النصوص العادية كأسماء عملات
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_price))

    print("✅ البوت يعمل الآن ...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
