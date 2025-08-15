
FROM debian:stable-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    lua5.4 lua-socket lua-sec ca-certificates git curl build-essential unzip wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://luarocks.github.io/luarocks/releases/luarocks-3.11.1.tar.gz \
    && tar xzf luarocks-3.11.1.tar.gz \
    && cd luarocks-3.11.1 \
    && ./configure --with-lua=/usr --lua-version=5.4 \
    && make \
    && make install \
    && cd / && rm -rf luarocks-3.11.1*

RUN luarocks install telegram-bot-lua && luarocks install dkjson

WORKDIR /app
COPY . /app

ENV BOT_TOKEN=""
CMD ["lua", "main.lua"]
