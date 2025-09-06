import os
from flask import Flask, request
import requests

app = Flask(__name__)

# 🔹 ضع بيانات البوت هنا
BOT_TOKEN = "6360843107:AAE523o40KV4VwWdFj_D1rwI64ikMcPXjsM"
CHAT_ID = "6263195701"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        # إذا كان JSON صالح، ننسق الرسالة
        if data and isinstance(data, dict):
            alert_message = (
                "🚨 تنبيه من TradingView\n\n"
                f"الرمز: {data.get('symbol','غير متوفر')}\n"
                f"السعر: {data.get('price','غير متوفر')}\n"
                f"الوقت: {data.get('time','غير متوفر')}"
            )
        else:
            # إذا كان نص عادي، نرسل كما هو
            alert_message = request.data.decode("utf-8")
    except Exception as e:
        alert_message = f"Error processing alert: {e}"

    # إرسال الرسالة للبوت
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": alert_message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
