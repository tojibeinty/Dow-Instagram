-- main.lua
local http_server_available, http_server = pcall(require, "http.server")
if not http_server_available then
    print("❌ خطأ: مكتبة http.server غير موجودة. تأكد من تثبيت Lua 5.4 مع مكتبات الشبكة.")
    os.exit(1)
end

local https = require("ssl.https")
local ltn12 = require("ltn12")
local cjson = require("cjson")

-- قراءة BOT_TOKEN
local BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN or BOT_TOKEN == "" then
    print("⚠️ تحذير: BOT_TOKEN غير موجود في Environment Variables، سيتم استخدام التوكن المباشر.")
    BOT_TOKEN = "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"
end
print("DEBUG: BOT_TOKEN =", BOT_TOKEN)

local BASE_URL = "https://api.telegram.org/bot" .. BOT_TOKEN

-- دالة إرسال رسالة
local function sendMessage(chat_id, text)
    local payload = { chat_id = chat_id, text = text }
    local body = cjson.encode(payload)
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

-- دالة لمعالجة الرسائل
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

-- فتح خادم ويب لاستقبال Webhook
local PORT = tonumber(os.getenv("PORT") or 8080)
local server = http_server.new("0.0.0.0", PORT)
local http_headers = require("http.headers")

server:on("request", function(req, res)
    local body = req:read_body()
    if body and #body > 0 then
        local ok, update = pcall(cjson.decode, body)
        if ok and update then
            handleUpdate(update)
        end
    end
    res:write_head(200, {["Content-Type"] = "text/plain"})
    res:finish("OK")
end)

print("🤖 البوت جاهز للعمل على PORT:", PORT)
server:loop()
