import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, JobQueue
import asyncio

# ===== إعدادات البوت =====
BOT_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"
API_URL = "https://api.coingecko.com/api/v3/simple/price"
TOP_COINS = ["bitcoin", "ethereum", "tether", "bnb", "usd-coin",
             "xrp", "cardano", "dogecoin", "polygon", "solana"]

# ===== تفعيل اللوغ =====
logging.basicConfig(level=logging.INFO)

# قائمة لحفظ chat_ids للمستخدمين
user_chats = set()

# ===== دالة البداية =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_chats.add(chat_id)
    await update.message.reply_text(
        "مرحبًا! أرسل اسم أي عملة رقمية لأعطيك السعر بالدولار 💰.\n"
        "أو اكتب /top10 لرؤية أسعار أشهر 10 عملات.\n"
        "سيتم تحديث Top 10 تلقائيًا كل دقيقة."
    )

# ===== دالة جلب سعر العملة =====
async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_chats.add(chat_id)

    coin = update.message.text.strip().lower()
    params = {"ids": coin, "vs_currencies": "usd"}
    try:
        response = requests.get(API_URL, params=params, timeout=10).json()
        if coin in response:
            price = response[coin]["usd"]
            await update.message.reply_text(f"💰 سعر {coin.capitalize()} هو: {price} USD")
        else:
            await update.message.reply_text("⚠️ لم أتمكن من العثور على هذه العملة. حاول باسم صحيح.")
    except Exception:
        await update.message.reply_text("❌ حدث خطأ أثناء جلب السعر. حاول لاحقًا.")

# ===== دالة Top 10 العملات =====
async def top10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_chats.add(chat_id)

    coins_str = ",".join(TOP_COINS)
    params = {"ids": coins_str, "vs_currencies": "usd"}
    try:
        response = requests.get(API_URL, params=params, timeout=10).json()
        message = "💰 **Top 10 العملات الرقمية:**\n"
        for coin in TOP_COINS:
            price = response.get(coin, {}).get("usd", "N/A")
            message += f"{coin.capitalize()}: {price} USD\n"
        await update.message.reply_text(message)
    except Exception:
        await update.message.reply_text("❌ حدث خطأ أثناء جلب قائمة العملات. حاول لاحقًا.")

# ===== مهمة إرسال Top 10 تلقائيًا =====
async def send_top10_job(context: ContextTypes.DEFAULT_TYPE):
    coins_str = ",".join(TOP_COINS)
    params = {"ids": coins_str, "vs_currencies": "usd"}
    try:
        response = requests.get(API_URL, params=params, timeout=10).json()
        message = "💰 **Top 10 العملات الرقمية (تحديث تلقائي):**\n"
        for coin in TOP_COINS:
            price = response.get(coin, {}).get("usd", "N/A")
            message += f"{coin.capitalize()}: {price} USD\n"

        # إرسال الرسالة لكل المستخدمين
        for chat_id in user_chats:
            try:
                await context.bot.send_message(chat_id=chat_id, text=message)
            except:
                pass  # تجاهل الأخطاء إذا حذف المستخدم البوت
    except Exception:
        pass  # تجاهل أخطاء الشبكة

# ===== الدالة الرئيسية =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("top10", top10))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_price))

    # إضافة JobQueue لتحديث Top 10 كل دقيقة
    job_queue = app.job_queue
    job_queue.run_repeating(send_top10_job, interval=60, first=10)

    print("✅ البوت يعمل الآن مع تحديث Top 10 تلقائي كل دقيقة على Railway...")
    app.run_polling()

# ===== تشغيل البوت =====
if __name__ == "__main__":
    main()
