import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# إعدادات البوت
BOT_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"

# إعداد سجل الأخطاء
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# دالة لجلب سعر البيتكوين
def get_crypto_price(symbol: str = "BTCUSDT") -> str:
    try:
        response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
        data = response.json()
        return f"سعر {symbol}: {data['price']} USDT"
    except Exception as e:
        return f"حدث خطأ: {e}"

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً! أرسل /price لمعرفة سعر البيتكوين.")

# أمر /price
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_crypto_price()
    await update.message.reply_text(text)

async def main():
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()

    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))

    # تشغيل البوت
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
