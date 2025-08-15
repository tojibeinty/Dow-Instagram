local https = require("ssl.https")
local ltn12 = require("ltn12")
local json = require("cjson")

-- التوكن الخاص بالبوت
local BOT_TOKEN = os.getenv("8402805384:AAEHuN5nATyZAn-ea10htyoD5ax62cs0fL4") or "PUT-YOUR-BOT-TOKEN-HERE"
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
local offset = 0

print("🤖 البوت يعمل الآن ...")

while true do
    local url = BASE_URL .. "/getUpdates?timeout=20&offset=" .. offset
    local res, code = https.request(url)

    if code == 200 and res then
        local data = json.decode(res)
        for _, update in ipairs(data.result) do
            offset = update.update_id + 1
            local message = update.message
            if message and message.text then
                local chat_id = message.chat.id
                local text = message.text

                -- منطق المحادثة
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
    end
end
