"""Fly.io webhook server — receives Telegram updates, no polling."""
from __future__ import annotations

import asyncio
import logging
import os
import sys

import aiohttp
from flask import Flask, jsonify, request
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

sys.path.insert(0, os.path.dirname(__file__))

from bot.config import settings
from bot.handlers import admin_router, approval_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

bot: Bot | None = None
dp: Dispatcher | None = None
_loop: asyncio.AbstractEventLoop | None = None


async def _register_webhook():
    """Register Telegram webhook on startup."""
    url = f"https://{settings.fly_app_name}.fly.dev/webhook"
    async with aiohttp.ClientSession() as s:
        resp = await s.get(
            f"https://api.telegram.org/bot{settings.telegram_token}/setWebhook",
            json={"url": url, "allowed_updates": ["message", "callback_query"]},
        )
        data = await resp.json()
        if data.get("ok"):
            logger.info("Webhook registered: %s", url)
        else:
            logger.error("Webhook failed: %s", data)


async def _init():
    """Init bot + dispatcher (no polling)."""
    global bot, dp, _loop
    _loop = asyncio.get_event_loop()

    missing = settings.validate_for_bot()
    if missing:
        logger.warning("missing env: %s", missing)

    bot = Bot(token=settings.telegram_token or "0:placeholder",
              default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(approval_router)

    await _register_webhook()


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive Telegram updates via webhook."""
    if bot and dp and _loop:
        update = request.get_json(force=True)
        from aiogram.types import Update
        tg_update = Update.model_validate(update)
        asyncio.run_coroutine_threadsafe(dp.feed_update(bot, tg_update), _loop)
    return "", 200


# Init bot on module load (Fly.io runs this as the WSGI app)
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)
_loop.run_until_complete(_init())


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
