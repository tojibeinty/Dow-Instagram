local telegram = require("telegram-bot-lua")
local json = require("dkjson")

-- ===== إعدادات عامة =====
local BOT = telegram.Bot(os.getenv("BOT_TOKEN"))

-- ===== نطاقات طبيعية + شرح =====
local TESTS = {
  Hb = {
    ranges = {
      male = {min=13, max=17, unit="g/dL"},
      female = {min=12, max=15, unit="g/dL"},
      child = {min=11, max=16, unit="g/dL"},
      newborn = {min=14, max=24, unit="g/dL"},
    },
    description = "هيموغلوبين الدم: البروتين الحامل للأكسجين في كريات الدم الحمراء."
  },
  WBC = {
    ranges = {
      all = {min=4000, max=11000, unit="/µL"}
    },
    description = "خلايا الدم البيضاء: تقيس قدرة الجسم على مكافحة العدوى."
  },
  FastingGlucose = {
    ranges = {all={min=70, max=100, unit="mg/dL"}},
    description = "سكر صائم: مستوى الجلوكوز في الدم بعد صيام 8 ساعات."
  },
  Creatinine = {
    ranges = {
      male = {min=0.7, max=1.3, unit="mg/dL"},
      female = {min=0.6, max=1.1, unit="mg/dL"},
      child = {min=0.2, max=0.7, unit="mg/dL"},
      newborn = {min=0.3, max=1.0, unit="mg/dL"},
    },
    description = "كرياتينين: مؤشر لوظائف الكلى."
  },
  TSH = {
    ranges = {all={min=0.4, max=4.0, unit="mIU/L"}},
    description = "الهرمون المنبه للغدة الدرقية."
  },
  FreeT4 = {
    ranges = {all={min=0.8, max=1.8, unit="ng/dL"}},
    description = "هرمون الغدة الدرقية الحر (T4)."
  },
}

local CATEGORIES = {
  CBC = {title="🩸 تحاليل الدم", tests={"Hb","WBC"}},
  CHEM = {title="🧪 كيمياء", tests={"FastingGlucose","Creatinine"}},
  HORM = {title="🔥 هرمونات", tests={"TSH","FreeT4"}},
}

local PAGE_SIZE = 10

local function kb_category_root()
  local kb = {inline_keyboard = {}}
  for _,cat_key in ipairs({"CBC","CHEM","HORM"}) do
    table.insert(kb.inline_keyboard, {{text=CATEGORIES[cat_key].title, callback_data="cat:"..cat_key..":0"}})
  end
  return kb
end

local function kb_tests_for(category_key, page)
  local cat = CATEGORIES[category_key]
  if not cat then return kb_category_root() end
  local tests = cat.tests
  local total = #tests
  local start_i = page*PAGE_SIZE + 1
  local end_i = math.min(start_i+PAGE_SIZE-1, total)
  local rows = {}
  local row = {}
  for i=start_i,end_i do
    table.insert(row, {text=tests[i], callback_data="test:"..tests[i]})
    if #row == 2 then table.insert(rows,row); row={} end
  end
  if #row>0 then table.insert(rows,row) end
  local nav = {}
  if page>0 then table.insert(nav,{text="◀️ السابق", callback_data="cat:"..category_key..":"..(page-1)}) end
  if end_i<total then table.insert(nav,{text="التالي ▶️", callback_data="cat:"..category_key..":"..(page+1)}) end
  if #nav>0 then table.insert(rows, nav) end
  table.insert(rows, {{text="🔙 الأنواع", callback_data="home"}})
  return {inline_keyboard = rows}
end

local function welcome(chat_id)
  local txt = "👋 أهلاً بك!\nاختر نوع التحليل من القائمة أدناه:"
  BOT.sendMessage(chat_id, txt, {reply_markup = kb_category_root()})
end

BOT.on("message", function(msg)
  local chat_id = msg.chat.id
  local text = msg.text or ""
  if text:match("^/start") or text:match("^/help") then
    welcome(chat_id); return
  end
  BOT.sendMessage(chat_id,"📌 أرسل /start لاختيار التحاليل من القوائم")
end)

BOT.on("callback_query", function(q)
  local data = q.data or ""
  local chat_id = q.message.chat.id
  if data == "home" then
    BOT.answerCallbackQuery(q.id)
    BOT.editMessageText(chat_id, q.message.message_id,"اختر التصنيف:",{reply_markup=kb_category_root()})
    return
  end
  local cat,page = data:match("^cat:(%u+):(%d+)$")
  if cat and page then
    page = tonumber(page)
    BOT.answerCallbackQuery(q.id)
    BOT.editMessageText(chat_id, q.message.message_id, CATEGORIES[cat].title.." — اختر التحليل:", {reply_markup=kb_tests_for(cat,page)})
    return
  end
  local test = data:match("^test:(%S+)$")
  if test then
    BOT.answerCallbackQuery(q.id)
    local t = TESTS[test]
    if not t then
      BOT.sendMessage(chat_id,"❌ التحليل غير متوفر حالياً"); return
    end
    local msg_txt = "🔹 التحليل: "..test.."\n📌 شرح: "..(t.description or "-").."\n✅ النطاق الطبيعي:\n"
    if t.ranges.all then
      local r = t.ranges.all
      msg_txt = msg_txt..string.format("- عام: %.2f – %.2f %s",r.min,r.max,r.unit)
    else
      for cat_name,r in pairs(t.ranges) do
        msg_txt = msg_txt..string.format("- %s: %.2f – %.2f %s\n",cat_name,r.min,r.max,r.unit)
      end
    end
    BOT.sendMessage(chat_id,msg_txt)
    return
  end
end)

BOT.run()
