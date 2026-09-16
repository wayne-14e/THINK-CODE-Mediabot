"""Review flow: previews land in the admin review group with Regenerate / Reject.
Founder copies the final text and publishes manually — the bot never posts itself."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from .. import db as dbmod
from ..ai import generate_post
from ..config import settings
from ..format import review_section, to_telegram_html

router = Router()


def review_chat_id() -> str:
    """Admin group where all previews live. Empty = fall back to origin chat (DM)."""
    return (settings.review_group_id or "").strip()


async def send_preview(bot: Bot, post_id: str, post_text: str, warn: str = "",
                     poll: dict | None = None, correct_idx: int | str | None = None,
                     explanation: str | None = None) -> int | None:
    """Post a preview card with approval keyboard to the review group.
    Text is formatted (bold titles / quotes / monospace code) via to_telegram_html.
    Poll options + correct answer are appended review-only (publish sends a poll).
    Returns the review message id, or None if no review group is configured."""
    dest = review_chat_id()
    if not dest:
        return None
    body = to_telegram_html(post_text + review_section(poll, correct_idx, explanation))
    sent = await bot.send_message(dest, f"┌ Preview [{post_id}]{warn}\n\n{body}",
                                  reply_markup=preview_kb(post_id))
    return sent.message_id


def preview_kb(post_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↻ Regenerate", callback_data=f"regen:{post_id}"),
         InlineKeyboardButton(text="✕ Reject", callback_data=f"rej:{post_id}")],
    ])


@router.callback_query(F.data.startswith("appr:"))
async def approve_deprecated(cb: CallbackQuery):
    # Stale cards (sent before the button was removed) still carry it.
    # Never fail silently — tell the founder what to press instead.
    if cb.from_user.id not in settings.admin_ids:
        return await cb.answer("Admins only", show_alert=True)
    await cb.answer("Removed — copy the post and publish manually.", show_alert=True)


@router.callback_query(F.data.startswith("sched:"))
async def schedule_deprecated(cb: CallbackQuery):
    # Scheduling removed (founder posts manually). Stale cards still carry it.
    if cb.from_user.id not in settings.admin_ids:
        return await cb.answer("Admins only", show_alert=True)
    await cb.answer("Scheduling removed — copy the post and publish manually.", show_alert=True)


@router.callback_query(F.data.startswith("rej:"))
async def reject(cb: CallbackQuery):
    if cb.from_user.id not in settings.admin_ids:
        return await cb.answer("Admins only", show_alert=True)
    post_id = cb.data.split(":", 1)[1]
    dbmod.update_post(post_id, {"status": "rejected"})
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(to_telegram_html(f"> REJECTED_ ❌\n\n$ post: {post_id}"))
    await cb.answer("rejected")


@router.callback_query(F.data.startswith("regen:"))
async def regen(cb: CallbackQuery):
    if cb.from_user.id not in settings.admin_ids:
        return await cb.answer("Admins only", show_alert=True)
    post_id = cb.data.split(":", 1)[1]
    old = dbmod.get_post(post_id) or {}
    await cb.message.answer(to_telegram_html(f"$ regenerating {old.get('content_type','quiz')}... 🧑‍🍳"))
    cand = generate_post(old.get("content_type", "quiz"), old.get("language", "python"),
                         old.get("difficulty", "medium"))
    new_id = dbmod.save_post({
        "content": cand.get("post_text", ""), "content_type": old.get("content_type", "quiz"),
        "language": old.get("language", "python"), "difficulty": old.get("difficulty", "medium"),
        "status": "pending_review", "poll": cand.get("poll", {}),
        "solution": cand.get("solution_text", ""), "correct_option": cand.get("correct_option"),
        "image_brief": cand.get("image_brief", ""),
    })
    dbmod.update_post(post_id, {"status": "regenerated"})
    warn = "\n⚠️ UNVALIDATED — check answer manually." if cand.get("_unvalidated") else ""
    poll, correct_idx, expl = cand.get("poll"), cand.get("correct_option"), cand.get("explanation")
    review_msg_id = await send_preview(cb.bot, new_id, cand.get("post_text", ""), warn,
                                       poll, correct_idx, expl)
    if review_msg_id is None:
        body = to_telegram_html(cand.get("post_text", "") + review_section(poll, correct_idx, expl))
        await cb.message.answer(f"┌ Preview [{new_id}]{warn}\n\n{body}",
                                reply_markup=preview_kb(new_id))
    else:
        await cb.message.answer(to_telegram_html(f"$ review_card_sent → admin group ✅\n$ post: {new_id}"))
    await cb.answer("regenerated")


@router.callback_query(F.data.startswith("edit:"))
async def edit_deprecated(cb: CallbackQuery):
    # In-bot editing removed (founder edits the copy when posting manually).
    if cb.from_user.id not in settings.admin_ids:
        return await cb.answer("Admins only", show_alert=True)
    await cb.answer("Editing removed — hit Regenerate or edit your copy when posting.", show_alert=True)
