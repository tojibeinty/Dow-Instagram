from flask import Flask, request
import requests

app = Flask(__name__)

# 🔹 ضع بيانات البوت هنا مباشرة
BOT_TOKEN = "6360843107:AAE523o40KV4VwWdFj_D1rwI64ikMcPXjsM"
CHAT_ID = "6263195701"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # 🔹 نص الرسالة اللي توصل على التليجرام
    alert_message = f"🚨 تنبيه من TradingView\n\n{data}"

    # 🔹 إرسال الرسالة للبوت
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": alert_message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

    return "OK"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
