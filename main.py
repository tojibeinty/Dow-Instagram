# main.py
import os
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN") or "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"

# حالة المستخدم
user_state = {}

# دالة لحساب الوزن المثالي
def calc_ideal_weight(height, gender):
    h_m = height / 100
    min_healthy = 18.5 * (h_m ** 2)
    max_healthy = 24.9 * (h_m ** 2)
    ideal_point = (height - 100) * 0.9 if gender == "ذكر" else (height - 100) * 0.85
    return f"✅ الطول: {height} سم\nالجنس: {gender}\n\n📌 الوزن الصحي (BMI): {min_healthy:.1f} - {max_healthy:.1f} كغ\n⭐ الوزن المثالي: {ideal_point:.1f} كغ"

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلًا! أرسل /ideal لحساب وزنك المثالي.\nاكتب /cancel للإلغاء.")

# /ideal
async def ideal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user_state[chat_id] = {"step": "gender"}
    await update.message.reply_text("اختر الجنس: ذكر أو أنثى")

# /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user_state.pop(chat_id, None)
    await update.message.reply_text("تم إلغاء العملية ✅")

# معالجة الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    text = update.message.text

    if chat_id in user_state:
        step = user_state[chat_id]["step"]

        if step == "gender":
            if text in ["ذكر", "أنثى"]:
                user_state[chat_id]["gender"] = text
                user_state[chat_id]["step"] = "height"
                await update.message.reply_text("أرسل طولك بالسنتيمتر (مثال: 170)")
            else:
                await update.message.reply_text("اختر الجنس من الخيارات: ذكر أو أنثى")

        elif step == "height":
            try:
                height = int(text)
                if 100 <= height <= 250:
                    gender = user_state[chat_id]["gender"]
                    result = calc_ideal_weight(height, gender)
                    await update.message.reply_text(result)
                    user_state.pop(chat_id)
                else:
                    await update.message.reply_text("أدخل طول صحيح بين 100 و 250 سم.")
            except:
                await update.message.reply_text("أدخل طول صحيح بين 100 و 250 سم.")

# إنشاء التطبيق
app = ApplicationBuilder().token(BOT_TOKEN).build()

# إضافة الـ Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ideal", ideal))
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# تشغيل البوت
print("🤖 البوت جاهز ويعمل باستخدام Polling...")
app.run_polling()
