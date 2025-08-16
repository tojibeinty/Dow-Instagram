# استخدام صورة بايثون 3.12 الرسمية
FROM python:3.12-slim

# إعداد مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع
COPY . /app

# تحديث pip وتثبيت المتطلبات
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# مجلد مؤقت للتحميلات
RUN mkdir downloads

# الأمر الأساسي لتشغيل البوت
CMD ["python", "main.py"]
