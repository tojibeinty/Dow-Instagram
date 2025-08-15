# صورة Ubuntu أساسية
FROM ubuntu:22.04

# تثبيت الأدوات الأساسية + Lua + LuaRocks + SSL
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    unzip \
    lua5.4 \
    lua5.4-dev \
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

# تثبيت المكتبات المطلوبة
RUN luarocks install luasocket
RUN luarocks install lua-cjson
RUN luarocks install luasec   # لدعم HTTPS

# نسخ ملفات المشروع
WORKDIR /bot
COPY . /bot

# تشغيل البوت
CMD ["lua5.4", "main.lua"]
