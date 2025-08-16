FROM python:3.12-slim

# تثبيت الأدوات الأساسية لبناء مكتبات Python
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المشروع
WORKDIR /app
COPY . /app

# تثبيت المتطلبات
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
