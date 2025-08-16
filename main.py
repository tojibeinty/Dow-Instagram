# main.py
import os
import io
import tempfile
import logging
import requests
from typing import List, Dict, Optional

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from yt_dlp import YoutubeDL

logging.basicConfig(level=logging.INFO)

# ⚠️ ضع توكن البوت هنا (بدون Environment Variables)
API_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# إعداد yt-dlp لاستخراج الروابط (بدون تنزيل)
YDL_OPTS = {
    "quiet": True,
    "skip_download": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "noplaylist": False,   # نسمح بالقوائم لأن الكاروسيل قد يرجع entries
    "extract_flat": False,
    "http_headers": {"User-Agent": "Mozilla/5.0"},
}

TG_MAX_UPLOAD = 49 * 1024 * 1024  # ~49MB احترازيًا

def _best_video_format(formats: List[Dict]) -> Optional[Dict]:
    best = None
    for f in formats or []:
        # نفضّل mp4 وبوجود فيديو حقيقي
        if f.get("vcodec") != "none" and (f.get("ext") == "mp4" or str(f.get("mime_type","")).startswith("video")):
            if not best or (f.get("height") or 0) > (best.get("height") or 0):
                best = f
    return best

def _info_to_media_items(info: Dict) -> List[Dict]:
    """
    يحول معلومات yt-dlp إلى قائمة عناصر وسائط موحدة:
    كل عنصر: {"type": "video"|"photo", "url": "...", "caption": "..."}
    يدعم: فيديو/صورة/كاروسيل
    """
    items = []

    def _single(info_obj: Dict):
        # فيديو؟
        if info_obj.get("formats"):
            vf = _best_video_format(info_obj.get("formats"))
            url = (vf or {}).get("url") or info_obj.get("url")
            if url:
                items.append({"type": "video", "url": url, "caption": info_obj.get("title")})
                return
        # صورة؟
        # بعض الأحيان تكون ext=jpg/png/webp مع url مباشر
        ext = (info_obj.get("ext") or "").lower()
        if info_obj.get("url") and ext in ("jpg", "jpeg", "png", "webp"):
            items.append({"type": "photo", "url": info_obj["url"], "caption": info_obj.get("title")})
            return
        # fallback: جرّب الثمبنيل كصورة
        if info_obj.get("thumbnail"):
            items.append({"type": "photo", "url": info_obj["thumbnail"], "caption": info_obj.get("title")})

    # إذا كان كاروسيل/قائمة
    if info.get("_type") == "playlist" and info.get("entries"):
        for ent in info["entries"]:
            _single(ent or {})
    else:
        _single(info)

    # إزالة العناصر الفارغة
    return [x for x in items if x.get("url")]

def _download_to_temp(url: str) -> Optional[str]:
    """
    يحاول تنزيل الوسيط إلى ملف مؤقت (للرفع المباشر في حال فشل الإرسال كرابط).
    """
    try:
        with requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0"}, timeout=30) as r:
            r.raise_for_status()
            # لا نحمل ملفات ضخمة جدًا
            total = int(r.headers.get("Content-Length", "0") or 0)
            if total and total > TG_MAX_UPLOAD:
                return None
            # أنشئ ملفًا مؤقتًا
            suffix = ".mp4" if "video" in r.headers.get("Content-Type","") else ".jpg"
            fd, temp_path = tempfile.mkstemp(suffix=suffix)
            with os.fdopen(fd, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 512):
                    if not chunk:
                        continue
                    f.write(chunk)
                    # حماية حجم
                    if f.tell() > TG_MAX_UPLOAD:
                        f.close()
                        os.remove(temp_path)
                        return None
            return temp_path
    except Exception:
        return None

@dp.message_handler(commands=["start", "help"])
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 أهلاً!\n"
        "أرسل رابط إنستغرام عام (Post / Reel / Story / Carousel) وسأحمّله لك بأعلى جودة ممكنة.\n"
        "▫️ يدعم صور متعددة وفيديوهات.\n"
        "⚠️ الروابط الخاصة أو من حسابات مغلقة لن تعمل."
    )

@dp.message_handler()
async def handle_instagram(message: types.Message):
    url = (message.text or "").strip()
    if "instagram.com" not in url:
        await message.reply("❌ أرسل رابط إنستغرام صحيح (عام).")
        return

    status = await message.reply("⏳ جاري التحليل والاستخراج...")

    try:
        with YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

        media = _info_to_media_items(info)
        if not media:
            await status.edit_text("❌ لم أعثر على وسائط قابلة للتحميل من هذا الرابط. تأكد أنه عام.")
            return

        await status.edit_text("📤 جاري الإرسال إلى تيليجرام...")

        # إذا كان هناك عناصر كثيرة، نرسل بالتتابع
        for item in media:
            media_url = item["url"]
            caption = item.get("caption") or ""

            # حاول أولاً الإرسال كرابط مباشر (Telegram يجلبه ذاتياً)
            try:
                if item["type"] == "video":
                    await message.answer_video(video=media_url, caption=caption)
                else:
                    await message.answer_photo(photo=media_url, caption=caption)
                continue
            except Exception:
                pass  # جرّب التنزيل ثم الرفع

            # تنزيل لرفع مباشر
            temp_path = _download_to_temp(media_url)
            if temp_path:
                try:
                    if item["type"] == "video":
                        with open(temp_path, "rb") as f:
                            await message.answer_video(video=f, caption=caption)
                    else:
                        with open(temp_path, "rb") as f:
                            await message.answer_photo(photo=f, caption=caption)
                except Exception as e:
                    await message.answer(f"⚠️ تعذر رفع هذا الوسيط: {e}")
                finally:
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
            else:
                # إن فشل التنزيل/الحجم كبير: أرسل الرابط للمستخدم ليستطيع حفظه خارج تيليجرام
                await message.answer(f"🔗 لم أستطع الرفع مباشرة (قد يكون الملف كبيرًا). رابط الوسيط:\n{media_url}")

        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ حدث خطأ أثناء المعالجة: {e}\nجرّب رابطًا آخر أو تأكد أنه عام.")

if __name__ == "__main__":
    print("🤖 البوت يعمل باستخدام Polling… أرسل /start ثم أرسل رابط إنستغرام.")
    executor.start_polling(dp, skip_updates=True)
