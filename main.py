import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import instaloader
import os
import requests

# ضع توكن البوت مباشرة
API_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# مجلد مؤقت لتحميل الملفات
TEMP_DIR = "downloads"
os.makedirs(TEMP_DIR, exist_ok=True)

loader = instaloader.Instaloader(download_videos=True, download_video_thumbnails=False, download_comments=False)

@dp.message(Command(commands=["start"]))
async def start_handler(message: types.Message):
    await message.answer("مرحباً! أرسل رابط إنستاغرام لتحميل الفيديو أو البوست أو الستوري.")

@dp.message()
async def download_instagram(message: types.Message):
    url = message.text.strip()
    await message.answer("جارٍ تحميل المحتوى من إنستاغرام... ⏳")
    
    try:
        # تحميل المنشور
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        filename = os.path.join(TEMP_DIR, f"{shortcode}.mp4")
        loader.download_post(post, target=TEMP_DIR)

        # البحث عن الملف الناتج
        for file in os.listdir(TEMP_DIR):
            if file.endswith(".mp4") and shortcode in file:
                file_path = os.path.join(TEMP_DIR, file)
                await message.answer_video(open(file_path, "rb"))
                os.remove(file_path)
                return

        await message.answer("لم يتم العثور على فيديو.")
    except Exception as e:
        await message.answer(f"حدث خطأ: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
