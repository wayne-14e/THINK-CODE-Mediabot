"""Fly.io webhook server."""
import logging
import os
import threading

from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting app.py")

app = Flask(__name__)

bot = None
dp = None
_loop = None


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/webhook", methods=["POST"])
def webhook():
    if bot and dp and _loop:
        import asyncio
        update = request.get_json(force=True)
        from aiogram.types import Update
        tg_update = Update.model_validate(update)
        asyncio.run_coroutine_threadsafe(dp.feed_update(bot, tg_update), _loop)
    return "", 200


def _init_bot():
    global bot, dp, _loop
    try:
        logger.info("Bot thread starting")
        import asyncio
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from bot.config import settings
        from bot.handlers import admin_router, approval_router
        from aiogram import Bot, Dispatcher
        from aiogram.client.default import DefaultBotProperties

        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)

        missing = settings.validate_for_bot()
        if missing:
            logger.warning("missing env: %s", missing)

        bot = Bot(token=settings.telegram_token,
                  default=DefaultBotProperties(parse_mode="HTML"))
        dp = Dispatcher()
        dp.include_router(admin_router)
        dp.include_router(approval_router)

        import aiohttp, time
        time.sleep(3)
        url = f"https://{settings.fly_app_name}.fly.dev/webhook"
        async def reg():
            async with aiohttp.ClientSession() as s:
                r = await s.get(
                    f"https://api.telegram.org/bot{settings.telegram_token}/setWebhook",
                    json={"url": url, "allowed_updates": ["message", "callback_query"]},
                )
                d = await r.json()
                logger.info("Webhook: %s", d)
        _loop.run_until_complete(reg())
        logger.info("Bot ready, webhook registered")
        _loop.run_forever()
    except Exception:
        logger.exception("Bot init failed")


t = threading.Thread(target=_init_bot, daemon=True)
t.start()
logger.info("Thread started")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    logger.info("Flask listening on 0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port)
