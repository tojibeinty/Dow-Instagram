FROM python:3.12-slim

WORKDIR /app
COPY . /app

# ffmpeg قد يُحسّن بعض حالات استخراج/تحويل الفيديو، اختياري
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
