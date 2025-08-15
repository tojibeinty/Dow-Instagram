# استخدم صورة Python الرسمية
FROM python:3.12-slim

# تعيين مجلد العمل
WORKDIR /app

# نسخ الملفات
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir python-telegram-bot==20.3

# تعيين البيئة (اختياري، يمكن ضبطه في Railway)
# ENV BOT_TOKEN=6360843107:AAFtAbfyKv4_OCP0Cjkhsq7vHg6mi-VfdcE

# أمر التشغيل
CMD ["python", "main.py"]
