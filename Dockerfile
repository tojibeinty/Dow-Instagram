# استخدم صورة Ubuntu أساسية
FROM ubuntu:22.04

# تحديث النظام وتثبيت الأدوات الأساسية + libssl-dev لتثبيت luasec
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    unzip \
    lua5.4 \
    lua5.4-dev \
    git \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# تثبيت LuaRocks
RUN wget https://luarocks.github.io/luarocks/releases/luarocks-3.11.1.tar.gz \
    && tar xzf luarocks-3.11.1.tar.gz \
    && cd luarocks-3.11.1 \
    && ./configure --with-lua=/usr --lua-version=5.4 \
    && make \
    && make install \
    && cd / \
    && rm -rf luarocks-3.11.1*

# تثبيت مكتبات Lua المطلوبة
RUN luarocks install luasocket
RUN luarocks install lua-cjson
RUN luarocks install luasec       # لإضافة دعم HTTPS
RUN luarocks install telegram-bot-lua

# نسخ ملفات البوت إلى الحاوية
WORKDIR /bot
COPY . /bot

# تعيين أمر التشغيل الافتراضي
CMD ["lua5.4", "main.lua"]
