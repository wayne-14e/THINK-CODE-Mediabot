"""Telegram HTML formatting for THINK//CODE posts.

House rules (founder-set):
- <b> for titles/headers (all > HEADER and $ var lines), <blockquote> for
  important text, <pre> for code.
- NEVER italic / underline / strikethrough.
- Only <b>, <blockquote>, <pre> (+<code> inside <pre>) survive; everything else
  is stripped or escaped so Telegram never rejects the message.
"""
from __future__ import annotations

import html
import re

_FENCE = re.compile(r"```(?:\w+)?\n?(.*?)```", re.S)
_BOLD_MD = re.compile(r"\*\*(.+?)\*\*", re.S)
# banned tags: dropped, inner text kept (no italic/underline/strike/links)
_BANNED = re.compile(r"</?(?:i|em|u|ins|s|strike|del|span|div|p|h\d|a|hr)(?:\s+[^<>]*)?>", re.I)
_BR = re.compile(r"<br\s*/?>", re.I)
_STRONG = re.compile(r"</?strong>", re.I)
_PRE_BLOCK = re.compile(r"<pre>(.*?)</pre>", re.S)
_HEADER_LINE = re.compile(r"\s*[>$]\s*\S")
# after escaping, restore exactly these (blockquote may carry ` expandable`)
_RESTORE = re.compile(r"&lt;(/?(?:b|blockquote|pre|code))( expandable)?&gt;")


def _stash_pre(text: str, stashed: list[str]) -> str:
    def _stash(m: re.Match) -> str:
        stashed.append(f"<pre>{html.escape(m.group(1).strip(), quote=False)}</pre>")
        return f"\x00PRE{len(stashed) - 1}\x00"

    return _PRE_BLOCK.sub(_stash, text)


def to_telegram_html(text: str | None) -> str:
    """Convert LLM or human draft text into safe Telegram HTML."""
    # LLMs often pre-escape (emit &gt; themselves) — normalize first so we
    # escape exactly once and the channel never shows literal &gt;
    t = html.unescape(text or "")
    # markdown leftovers -> html
    t = _FENCE.sub(lambda m: f"<pre>{m.group(1).strip()}</pre>", t)
    t = _BOLD_MD.sub(lambda m: f"<b>{m.group(1)}</b>", t)
    t = _STRONG.sub(lambda m: "<b>" if not m.group(0).startswith("</") else "</b>", t)
    t = _BR.sub("\n", t)
    # strip banned tags, keep their inner text
    t = _BANNED.sub("", t)
    # code content is escaped now, block reinserted after global escape
    stashed: list[str] = []
    t = _stash_pre(t, stashed)
    # bold every terminal header/var line outside code
    lines = []
    for line in t.split("\n"):
        if "<b>" not in line and _HEADER_LINE.match(line):
            line = f"<b>{line}</b>"
        lines.append(line)
    t = html.escape("\n".join(lines), quote=False)
    t = _RESTORE.sub(lambda m: f"<{m.group(1)}{m.group(2) or ''}>", t)
    for i, block in enumerate(stashed):
        t = t.replace(f"\x00PRE{i}\x00", block)
    return t


def review_section(poll: dict | None, correct_idx: int | str | None = None,
                   explanation: str | None = None) -> str:
    """Review-only appendix: poll question + per-option copy blocks + answer.

    Each option's TEXT (letter outside) sits in its own <pre> so one tap copies
    exactly that option. The explanation gets its own <pre> too.
    Never published to the channel (publish sends a native Telegram poll)."""
    lines: list[str] = []
    if poll and (poll.get("question") or poll.get("options")):
        lines.append("────────")
        lines.append("$ POLL_PREVIEW (review only — native poll on publish):")
        if poll.get("question"):
            lines.append(f"$ Q: {poll['question']}")
        for i, opt in enumerate(poll.get("options", [])[:10]):
            letter = "ABCD"[i] if i < 4 else "•"
            lines.append(f"{letter}) <pre>{opt}</pre>")
    if correct_idx is not None:
        try:
            letter = "ABCD"[int(correct_idx)] if 0 <= int(correct_idx) < 4 else str(correct_idx)
        except (TypeError, ValueError):  # noqa: BLE001
            letter = str(correct_idx)
        lines.append(f"$ CORRECT: {letter}")
        expl = (explanation or "").strip().replace("\n", " ")
        if expl:
            lines.append(f"<pre>{expl[:500]}</pre>")
    return ("\n" + "\n".join(lines)) if lines else ""
