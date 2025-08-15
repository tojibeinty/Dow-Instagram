-- main.lua
local telegram = require("telegram-bot-lua")
local cjson = require("cjson")

-- BOT_TOKEN
local BOT_TOKEN = os.getenv("BOT_TOKEN") or "6360843107:AAFnP3OC3aU6dfUvGC3KZ0ZMZWtzs_4qaBU"
print("DEBUG: BOT_TOKEN =", BOT_TOKEN)

local bot = telegram.new(BOT_TOKEN)

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

-- دالة معالجة الرسائل
local function handleUpdate(update)
    local message = update.message
    if message and message.text then
        local chat_id = message.chat.id
        local text = message.text

        if text == "/start" then
            bot:sendMessage(chat_id, "أهلًا! أرسل /ideal لحساب وزنك المثالي.\nاكتب /cancel للإلغاء.")
        elseif text == "/ideal" then
            user_state[chat_id] = { step = "gender" }
            bot:sendMessage(chat_id, "اختر الجنس: ذكر أو أنثى")
        elseif text == "/cancel" then
            user_state[chat_id] = nil
            bot:sendMessage(chat_id, "تم إلغاء العملية ✅")
        elseif user_state[chat_id] and user_state[chat_id].step == "gender" then
            if text == "ذكر" or text == "أنثى" then
                user_state[chat_id].gender = text
                user_state[chat_id].step = "height"
                bot:sendMessage(chat_id, "أرسل طولك بالسنتيمتر (مثال: 170)")
            else
                bot:sendMessage(chat_id, "اختر الجنس من الخيارات: ذكر أو أنثى")
            end
        elseif user_state[chat_id] and user_state[chat_id].step == "height" then
            local height = tonumber(text)
            if height and height >= 100 and height <= 250 then
                local gender = user_state[chat_id].gender
                local result = calcIdealWeight(height, gender)
                bot:sendMessage(chat_id, result)
                user_state[chat_id] = nil
            else
                bot:sendMessage(chat_id, "أدخل طول صحيح بين 100 و 250 سم.")
            end
        end
    end
end

print("🤖 البوت يعمل باستخدام Polling...")

-- حلقة Polling مستمرة
while true do
    local updates = bot:getUpdates()
    for _, update in ipairs(updates) do
        handleUpdate(update)
    end
    os.execute("sleep 1") -- تأخير 1 ثانية
end
