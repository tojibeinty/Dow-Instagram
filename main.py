from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random
import string
import json
import os

# ضع توكن البوت هنا مباشرة
TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"

# ملف حفظ الباسوردات
PASSWORD_FILE = "passwords.json"

# تحميل الباسوردات المحفوظة إذا وجدت
if os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE, "r") as f:
        generated_passwords = set(json.load(f))
else:
    generated_passwords = set()

def save_passwords():
    with open(PASSWORD_FILE, "w") as f:
        json.dump(list(generated_passwords), f)

def generate_password(length=12):
    while True:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for _ in range(length))
        if password not in generated_passwords:
            generated_passwords.add(password)
            save_passwords()
            return password

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! استخدم /password للحصول على باسورد قوي وفريد.")

async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pwd = generate_password(12)
    await update.message.reply_text(f"🛡️ باسوردك الجديد: {pwd}")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("password", password))

print("البوت يعمل الآن...")
app.run_polling()
