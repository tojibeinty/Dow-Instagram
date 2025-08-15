local https = require("ssl.https")
local ltn12 = require("ltn12")
local json = require("cjson")
local socket = require("socket") -- للتأخير إذا لزم

local BOT_TOKEN = os.getenv("6360843107:AAFtAbfyKv4_OCP0Cjkhsq7vHg6mi-VfdcE")
if not BOT_TOKEN or BOT_TOKEN == "" then
    print("❌ خطأ: BOT_TOKEN غير موجود. اضف توكن البوت في Environment Variables.")
    os.exit(1)
end

local BASE_URL = "https://api.telegram.org/bot" .. BOT_TOKEN

-- دالة إرسال الرسائل
local function sendMessage(chat_id, text, keyboard, remove_keyboard)
    local payload = { chat_id = chat_id, text = text }

    if keyboard then
        payload.reply_markup = { keyboard = keyboard, one_time_keyboard = true, resize_keyboard = true }
    elseif remove_keyboard then
        payload.reply_markup = { remove_keyboard = true }
    end

    local body = json.encode(payload)
    https.request{
        url = BASE_URL .. "/sendMessage",
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json",
            ["Content-Length"] = #body
        },
        source = ltn12.source.string(body),
        sink = ltn12.sink.null()
    }
end

-- حساب الوزن المثالي
local function calcIdealWeight(height, gender)
    local h_m = height / 100
    local min_healthy = 18.5 * (h_m ^ 2)
    local max_healthy = 24.9 * (h_m ^ 2)

    local ideal_point
    if gender == "ذكر" then
        ideal_point = (height - 100) * 0.9
    else
        ideal_point = (height - 100) * 0.85
    end

    return string.format(
        "✅ الطول: %.0f سم\nالجنس: %s\n\n📌 الوزن الصحي (BMI): %.1f - %.1f كغ\n⭐ الوزن المثالي (بروكا): %.1f كغ",
        height, gender, min_healthy, max_healthy, ideal_point
    )
end

-- حفظ حالة المستخدم
local user_state = {}

-- HTTP Server صغير لاستقبال Webhook
local http = require("socket.http")
local ltn12 = require("ltn12")
local server = require("socket.http").server

-- في Railway سنستخدم port من ENV
local PORT = os.getenv("PORT") or 3000
print("🤖 البوت يعمل الآن على Webhook، Port: " .. PORT)

-- استخدام مكتبة wsapi / lhttpd على Railway:
-- هنا مجرد مثال تخيلي:  
-- على Railway يمكنك ربط Node.js أو Lua server يرسل POST request للبوت
-- الفكرة الأساسية: عند وصول POST request، تنفذ الكود التالي:

local function handleUpdate(update)
    local message = update.message
    if message and message.text then
        local chat_id = message.chat.id
        local text = message.text

        if text == "/start" then
            sendMessage(chat_id, "أهلًا! أرسل /ideal لحساب وزنك المثالي.\nاكتب /cancel للإلغاء.")
        elseif text == "/ideal" then
            user_state[chat_id] = { step = "gender" }
            sendMessage(chat_id, "اختر الجنس:", { { "ذكر", "أنثى" } })
        elseif text == "/cancel" then
            user_state[chat_id] = nil
            sendMessage(chat_id, "تم إلغاء العملية ✅", nil, true)
        elseif user_state[chat_id] and user_state[chat_id].step == "gender" then
            if text == "ذكر" or text == "أنثى" then
                user_state[chat_id].gender = text
                user_state[chat_id].step = "height"
                sendMessage(chat_id, "أرسل طولك بالسنتيمتر (مثال: 170):", nil, true)
            else
                sendMessage(chat_id, "اختر الجنس من الأزرار:", { { "ذكر", "أنثى" } })
            end
        elseif user_state[chat_id] and user_state[chat_id].step == "height" then
            local height = tonumber(text)
            if height and height >= 100 and height <= 250 then
                local gender = user_state[chat_id].gender
                local result = calcIdealWeight(height, gender)
                sendMessage(chat_id, result)
                user_state[chat_id] = nil
            else
                sendMessage(chat_id, "أدخل طول صحيح بين 100 و 250 سم.")
            end
        end
    end
end

print("✅ الآن البوت جاهز لاستقبال الرسائل عبر Webhook!")
