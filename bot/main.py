"""Entry point: python -m bot.main"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .config import settings
from .handlers import admin_router, approval_router

logging.basicConfig(level=logging.INFO)


async def main():
    missing = settings.validate_for_bot()
    if missing:
        logging.warning("missing env: %s — bot will start but commands need them", missing)
    # HTML parse mode is back ON: all outgoing texts go through
    # bot.format.to_telegram_html, which escapes stray < > & and allows only
    # <b> <blockquote> <pre> — Telegram never sees a broken tag.
    bot = Bot(token=settings.telegram_token or "0:placeholder",
              default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(approval_router)
    # No auto-publishing: founder copies approved posts and publishes manually.
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
