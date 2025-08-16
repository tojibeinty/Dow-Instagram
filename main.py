import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import instaloader
import os

API_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

L = instaloader.Instaloader()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("مرحبًا! أرسل رابط منشور أو Reel أو Story من انستاجرام لتحميله.")

@dp.message_handler()
async def download_instagram(message: types.Message):
    url = message.text.strip()
    try:
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        filename = f"{shortcode}.jpg"
        post.download_pic(filename, post.url)
        await message.reply_document(open(filename, 'rb'))
        os.remove(filename)
    except Exception as e:
        await message.reply(f"حدث خطأ: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
