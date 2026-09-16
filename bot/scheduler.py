"""APScheduler: publish due `scheduled` posts at DEFAULT_PUBLISH_TIME."""
from __future__ import annotations

import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import settings
from . import db as dbmod
from .format import to_telegram_html

log = logging.getLogger(__name__)


async def _notify_group(bot: Bot, text: str):
    if settings.review_group_id:
        try:
            await bot.send_message(settings.review_group_id, text)
        except Exception:  # noqa: BLE001
            pass


async def _publish_due(bot: Bot):
    try:
        posts = dbmod.recent_posts(30)
    except Exception as e:  # noqa: BLE001
        return log.warning("scheduler db unavailable: %s", e)
    for p in posts:
        if p.get("status") != "scheduled":
            continue
        try:
            sent = await bot.send_message(settings.channel_id,
                                          to_telegram_html(p.get("content", "")))
            poll = p.get("poll") or {}
            if poll.get("question") and poll.get("options"):
                await bot.send_poll(settings.channel_id, poll["question"],
                                    poll["options"][:10], is_anonymous=True)
            dbmod.log_publish(p["id"], "telegram", str(sent.message_id))
            notice = f"> AUTO_PUBLISHED_ ✅\n\n$ post: {p['id']}"
            await _notify_group(bot, notice)
            for admin in settings.admin_ids:
                try:
                    await bot.send_message(admin, notice)
                except Exception:  # noqa: BLE001
                    pass
        except Exception as e:  # noqa: BLE001
            # Never die silently (this is how the old Approve button "did nothing").
            log.exception("publish failed %s: %s", p.get("id"), e)
            err = str(e)[:300]
            dbmod.update_post(p["id"], {"status": "publish_failed", "publish_error": err})
            await _notify_group(
                bot, f"> PUBLISH_FAILED_ ❌\n\n$ post: {p['id']}\n$ error: {err}\n"
                "$ fix: bot must be admin of the channel, check TELEGRAM_CHANNEL_ID.")


def start(bot: Bot) -> AsyncIOScheduler:
    hh, mm = (settings.default_publish_time.split(":") + ["0"])[:2]
    sched = AsyncIOScheduler(timezone=settings.timezone)
    sched.add_job(_publish_due, "cron", hour=int(hh), minute=int(mm), args=[bot],
                  id="daily_publish")
    sched.start()
    log.info("scheduler started at %s %s", settings.default_publish_time, settings.timezone)
    return sched
