import os
import asyncio
from aiogram import Bot, Dispatcher, types
import requests

# ضع التوكن هنا مباشرة
BOT_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# دالة لتحميل الفيديو من الانستجرام عبر API خارجي
def download_instagram(url):
    api = "https://api.save-insta.com/download"  # API خارجي جاهز
    response = requests.post(api, data={"url": url})
    if response.status_code == 200:
        data = response.json()
        if "media" in data:
            return [item["url"] for item in data["media"]]
    return []

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("أرسل رابط الفيديو من إنستجرام لتنزيله بجودة عالية ✅")

@dp.message_handler()
async def get_instagram(message: types.Message):
    url = message.text.strip()
    if "instagram.com" in url:
        await message.answer("⏳ جاري التحميل...")
        media_links = download_instagram(url)
        if media_links:
            for link in media_links:
                if link.endswith(".mp4"):
                    await message.answer_video(link)
                else:
                    await message.answer_photo(link)
        else:
            await message.answer("❌ لم أتمكن من التحميل. تأكد من صحة الرابط.")
    else:
        await message.answer("أرسل رابط إنستجرام فقط.")

async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
