"""Admin commands: /start /schedule /today /generate /ideas /history /style /settings"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..ai import generate_post, suggest_ideas
from ..config import settings
from .. import db as dbmod
from ..format import to_telegram_html as _fmt

router = Router()


def _is_admin(uid: int) -> bool:
    return uid in settings.admin_ids


async def _deny(msg: Message):
    await msg.answer(_fmt("⛔ Admins only."))


WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]


@router.message(Command("start"))
async def start(msg: Message):
    if not _is_admin(msg.from_user.id):
        return await _deny(msg)
    name = msg.from_user.first_name or "founder"
    await msg.answer(_fmt(
        f"> SYSTEM_ONLINE_\n\n$ Welcome, {name}!\n\n"
        "$ THINK//CODE mediabot ready.\n"
        "$ previews land in the admin group with options + answer.\n"
        "$ you copy & post manually — bot never publishes.\n\n"
        "/today — today's scheduled content\n"
        "/generate type [lang] [diff] — e.g. /generate quiz python medium\n"
        "/ideas — 2 fresh suggestions\n"
        "/schedule — weekly plan\n"
        "/history — recent posts\n"
        "/style — current style profile\n"
        "/settings — env/model status"
    ))


@router.message(Command("settings"))
async def settings_cmd(msg: Message):
    if not _is_admin(msg.from_user.id):
        return await _deny(msg)
    miss = settings.validate_for_bot()
    await msg.answer(_fmt(
        f"> SETTINGS_\n\n$ model: {settings.gemini_model}\n"
        f"$ validator: {settings.gemini_validator_model}\n"
        f"$ channel: {settings.channel_id}\n"
        f"$ review_group: {settings.review_group_id or 'NOT SET — previews stay in DM'}\n"
        f"$ publish_time: {settings.default_publish_time} ({settings.timezone})\n"
        f"$ firebase: {settings.firebase_project_id}\n"
        f"$ missing: {', '.join(miss) or 'none ✅'}"
    ))


@router.message(Command("schedule"))
async def schedule(msg: Message):
    if not _is_admin(msg.from_user.id):
        return await _deny(msg)
    try:
        rows = dbmod.get_schedule()
    except Exception as e:  # noqa: BLE001
        return await msg.answer(_fmt(f"Firestore unavailable: {e}"))
    if not rows:
        return await msg.answer(_fmt(
            "> SCHEDULE_EMPTY_\n\n$ default:\nMONDAY Quiz\nTUESDAY Fact\nWEDNESDAY Meme\n"
            "THURSDAY Quiz\nFRIDAY Topic\nSATURDAY Community\nSUNDAY Workshop\n\n"
            "Seed Firestore collection `content_schedule` to customise."
        ))
    lines = [f"> {r.get('weekday', '?'):9} {r.get('content_type', '?')}" for r in rows]
    await msg.answer(_fmt("> SCHEDULE_\n\n" + "\n".join(lines)))


@router.message(Command("today"))
async def today(msg: Message):
    if not _is_admin(msg.from_user.id):
        return await _deny(msg)
    from datetime import datetime
    import zoneinfo

    try:
        tz = zoneinfo.ZoneInfo(settings.timezone)
    except Exception:  # noqa: BLE001
        tz = None
    weekday = datetime.now(tz).strftime("%A").upper() if tz else datetime.now().strftime("%A").upper()
    try:
        rows = {r.get("weekday", "").upper(): r for r in dbmod.get_schedule()}
    except Exception:
        rows = {}
    planned = rows.get(weekday, {}).get("content_type", "quiz (default)")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Generate", callback_data=f"gen:{planned}:python:medium")]
    ])
    await msg.answer(_fmt(f"> TODAY_\n\n$ weekday: {weekday}\n$ planned: {planned}"), reply_markup=kb)


@router.message(Command("ideas"))
async def ideas(msg: Message):
    if not _is_admin(msg.from_user.id):
        return await _deny(msg)
    await msg.answer(_fmt("$ generating_ideas... 🧠"))
    try:
        ideas = suggest_ideas(2)
        dbmod.save_ideas(ideas)
    except Exception as e:  # noqa: BLE001
        return await msg.answer(_fmt(f"❌ idea gen failed: {e}"))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚡ Generate #{i+1}: {d.get('title','')[:30]}",
                              callback_data=f"idea:{i}")]
        for i, d in enumerate(ideas)
    ] + [[InlineKeyboardButton(text="↻ Different ideas", callback_data="ideas:refresh")]])
    text = "> TODAY'S_CONTENT_IDEAS\n\n" + "\n\n".join(
        f"$ {i+1}. {d.get('title')}\n   {d.get('description')}" for i, d in enumerate(ideas)
    )
    await msg.answer(_fmt(text), reply_markup=kb)


@router.callback_query(F.data == "ideas:refresh")
async def ideas_refresh(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return await cb.answer("Admins only", show_alert=True)
    try:
        ideas = suggest_ideas(2)
        dbmod.save_ideas(ideas)
    except Exception as e:  # noqa: BLE001
        return await cb.message.answer(_fmt(f"❌ {e}"))
    text = "> TODAY'S_CONTENT_IDEAS\n\n" + "\n\n".join(
        f"$ {i+1}. {d.get('title')}\n   {d.get('description')}" for i, d in enumerate(ideas)
    )
    await cb.message.answer(_fmt(text))
    await cb.answer("done")


@router.message(Command("generate"))
async def generate(msg: Message):
    if not _is_admin(msg.from_user.id):
        return await _deny(msg)
    parts = (msg.text or "").split()
    ctype = parts[1].lower() if len(parts) > 1 else "quiz"
    lang = parts[2].lower() if len(parts) > 2 else "python"
    diff = parts[3].lower() if len(parts) > 3 else "medium"
    await _run_generation(msg, ctype, lang, diff)


async def _run_generation(msg: Message, ctype: str, lang: str, diff: str, topic_hint: str = ""):
    from .approval import preview_kb, send_preview

    status = await msg.answer(_fmt(f"$ generating {ctype}... 🧑‍🍳"))
    try:
        cand = generate_post(ctype, lang, diff, topic_hint)
        post_id = dbmod.save_post({
            "content": cand.get("post_text", ""), "content_type": ctype,
            "language": lang, "difficulty": diff, "status": "pending_review",
            "poll": cand.get("poll", {}), "solution": cand.get("solution_text", ""),
            "correct_option": cand.get("correct_option"),
            "image_brief": cand.get("image_brief", ""),
            "unvalidated": cand.get("_unvalidated", False),
        })
    except Exception as e:  # noqa: BLE001
        return await status.edit_text(_fmt(f"❌ generation failed: {e}"))
    warn = "\n⚠️ UNVALIDATED — check answer manually." if cand.get("_unvalidated") else ""
    from ..format import review_section, to_telegram_html

    poll, correct_idx, expl = cand.get("poll"), cand.get("correct_option"), cand.get("explanation")
    review_msg_id = await send_preview(msg.bot, post_id, cand.get("post_text", ""), warn,
                                       poll, correct_idx, expl)
    if review_msg_id is None:
        # No review group configured — preview in place (old DM behaviour)
        body = to_telegram_html(cand.get("post_text", "") + review_section(poll, correct_idx, expl))
        await status.edit_text(
            f"┌ Preview [{post_id}]{warn}\n\n{body}",
            reply_markup=preview_kb(post_id),
        )
    else:
        await status.edit_text(_fmt(
            f"$ review_card_sent → admin group ✅\n$ post: {post_id}\n"
            f"Open the group to Regenerate / Reject, then copy & post manually."
        ))


@router.callback_query(F.data.startswith("gen:"))
async def gen_cb(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return await cb.answer("Admins only", show_alert=True)
    _, ctype, lang, diff = (cb.data.split(":") + ["quiz", "python", "medium"])[:4]
    await _run_generation(cb.message, ctype, lang, diff)
    await cb.answer("generating...")


@router.message(Command("history"))
async def history(msg: Message):
    if not _is_admin(msg.from_user.id):
        return await _deny(msg)
    try:
        posts = dbmod.recent_posts(10)
    except Exception as e:  # noqa:BLE001
        return await msg.answer(_fmt(f"Firestore unavailable: {e}"))
    lines = [(p.get("content", "")[:80].replace("\n", " ") + f" [{p.get('status')}]") for p in posts]
    await msg.answer(_fmt("> HISTORY_\n\n" + ("\n".join(f"> {i+1}. {l}" for i, l in enumerate(lines)) or "empty")))


@router.message(Command("style"))
async def style(msg: Message):
    if not _is_admin(msg.from_user.id):
        return await _deny(msg)
    import json

    try:
        prof = dbmod.get_style_profile()
        prof.pop("id", None)
    except Exception:
        prof = {}
    if not prof:
        from pathlib import Path
        prof = json.loads((Path(__file__).resolve().parent.parent.parent
                           / "data" / "style_profile.json").read_text(encoding="utf-8"))
    await msg.answer(_fmt("> STYLE_PROFILE_\n\n" + json.dumps(prof, ensure_ascii=False)[:3000]))
