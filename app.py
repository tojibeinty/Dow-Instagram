import os
from flask import Flask, request
import requests

app = Flask(__name__)

# 🔹 ضع بيانات البوت مباشرة هنا
BOT_TOKEN = "6360843107:AAE523o40KV4VwWdFj_D1rwI64ikMcPXjsM"
CHAT_ID = "6263195701"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    alert_message = (
        "🚨 تنبيه جديد من TradingView\n\n"
        f"الرمز: {data.get('symbol','غير متوفر')}\n"
        f"السعر: {data.get('price','غير متوفر')}\n"
        f"الوقت: {data.get('time','غير متوفر')}"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": alert_message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway يعطي Port تلقائي
    app.run(host="0.0.0.0", port=port)
