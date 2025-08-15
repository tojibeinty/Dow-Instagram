local https = require("ssl.https")
local ltn12 = require("ltn12")
local json = require("cjson")

-- قراءة BOT_TOKEN من Environment Variables
local BOT_TOKEN = os.getenv("BOT_TOKEN")
print("DEBUG: BOT_TOKEN =", BOT_TOKEN)

if not BOT_TOKEN or BOT_TOKEN == "" then
    print("❌ خطأ: BOT_TOKEN غير موجود. اضف توكن البوت في Environment Variables في Project Settings.")
    os.exit(1)
end

local BASE_URL = "https://api.telegram.org/bot" .. BOT_TOKEN

local function sendMessage(chat_id, text)
    local payload = { chat_id = chat_id, text = text }
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

-- فتح خادم ويب لاستقبال Webhook
local http = require("socket.http")
local ltn12 = require("ltn12")
local port = tonumber(os.getenv("PORT") or 3000)
print("🤖 البوت جاهز على PORT:", port)

-- حالة المستخدم
local user_state = {}

-- دالة لحساب الوزن المثالي
local function calcIdealWeight(height, gender)
    local h_m = height / 100
    local min_healthy = 18.5 * (h_m ^ 2)
    local max_healthy = 24.9 * (h_m ^ 2)
    local ideal_point = (gender == "ذكر") and (height - 100) * 0.9 or (height - 100) * 0.85

    return string.format(
        "✅ الطول: %.0f سم\nالجنس: %s\n\n📌 الوزن الصحي (BMI): %.1f - %.1f كغ\n⭐ الوزن المثالي: %.1f كغ",
        height, gender, min_healthy, max_healthy, ideal_point
    )
end

-- معالجة الرسائل
local function handleUpdate(update)
    local message = update.message
    if message and message.text then
        local chat_id = message.chat.id
        local text = message.text

        if text == "/start" then
            sendMessage(chat_id, "أهلًا! أرسل /ideal لحساب وزنك المثالي.\nاكتب /cancel للإلغاء.")
        elseif text == "/ideal" then
            user_state[chat_id] = { step = "gender" }
            sendMessage(chat_id, "اختر الجنس: ذكر أو أنثى")
        elseif text == "/cancel" then
            user_state[chat_id] = nil
            sendMessage(chat_id, "تم إلغاء العملية ✅")
        elseif user_state[chat_id] and user_state[chat_id].step == "gender" then
            if text == "ذكر" or text == "أنثى" then
                user_state[chat_id].gender = text
                user_state[chat_id].step = "height"
                sendMessage(chat_id, "أرسل طولك بالسنتيمتر (مثال: 170)")
            else
                sendMessage(chat_id, "اختر الجنس من الخيارات: ذكر أو أنثى")
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

print("🤖 البوت جاهز للعمل عبر Webhook!")
