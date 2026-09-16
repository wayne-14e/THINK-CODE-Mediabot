"""Ingest ChatExport_2026-09-16/messages.html -> data/channel_history.json (+ Firestore).
Usage: py scripts/ingest_history.py [--upload]
Parses terminal-style posts + polls + reactions; used as LLM reference for new posts.
"""
from __future__ import annotations

import html
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "ChatExport_2026-09-16" / "messages.html"
DST = ROOT / "data" / "channel_history.json"

try:  # so FIREBASE_* / GOOGLE_APPLICATION_CREDENTIALS from .env are visible
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(ROOT / ".env")
except Exception:  # noqa: BLE001
    pass


def clean(s: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<blockquote>(.*?)</blockquote>", r"\n> \1\n", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip()


def parse() -> list[dict]:
    h = io.open(SRC, encoding="utf-8").read()
    parts = re.split(r'<div class="message default', h)[1:]
    out = []
    for p in parts:
        m_date = re.search(r'title="([^"]+)"', p)
        texts = re.findall(r'<div class="text[^"]*"[^>]*>(.*?)</div>', p, re.S)
        poll_q = re.search(r'<div class="question bold">(.*?)</div>', p, re.S)
        poll_a = re.findall(r'<div class="answer">(.*?)</div>', p, re.S)
        reacts = re.findall(
            r'<span class="emoji">\s*(.*?)\s*</span>\s*<span class="count">\s*(.*?)\s*</span>', p, re.S)
        media = []
        if "media_photo" in p:
            media.append("photo")
        if "media_video" in p or "Animation" in p:
            media.append("video")
        if "media_audio" in p:
            media.append("audio")
        for t in texts:
            c = clean(t)
            if not c or len(c) < 5:
                continue
            kind = "post"
            low = c.lower()
            if "quiz" in c[:30].lower() or "what_is_the_output" in low or "what is the output" in low:
                kind = "quiz"
            elif "solution" in c[:30].lower() or "correct_output" in low:
                kind = "solution"
            elif "workshop" in low:
                kind = "workshop"
            elif "confession" in low or "fuel" in low:
                kind = "community"
            elif "archive" in low or "telehack" in low or "yopta" in low:
                kind = "topic"
            out.append({"date": m_date.group(1) if m_date else "?",
                        "type": kind, "text": c, "media": media,
                        "reactions": [f"{e.strip()}x{c2.strip()}" for e, c2 in reacts]})
        if poll_q:
            out.append({"date": m_date.group(1) if m_date else "?/", "type": "poll",
                        "text": "POLL: " + clean(poll_q.group(1)) + "\n" +
                        "\n".join("- " + clean(a) for a in poll_a),
                        "media": [], "reactions": []})
    return out


if __name__ == "__main__":
    items = parse()
    DST.parent.mkdir(exist_ok=True)
    DST.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(items)} items -> {DST}")
    if "--upload" in sys.argv:
        sys.path.insert(0, str(ROOT))
        from bot import db as dbmod
        prof = json.loads((ROOT / "data" / "style_profile.json").read_text(encoding="utf-8"))
        prof["updated_at"] = dbmod.now_iso()
        try:
            dbmod.get_db().collection("style_profile").add(prof)
            print("style_profile uploaded")
        except Exception as e:  # noqa: BLE001
            print("style upload failed:", e)
        # default weekly schedule per IDEA §6
        sched = [("MONDAY", "quiz"), ("TUESDAY", "fact"), ("WEDNESDAY", "meme"),
                 ("THURSDAY", "quiz"), ("FRIDAY", "topic"),
                 ("SATURDAY", "community"), ("SUNDAY", "workshop")]
        for wd, ct in sched:
            try:
                dbmod.get_db().collection("content_schedule").add(
                    {"weekday": wd, "content_type": ct, "preferred_time": "12:00", "enabled": True})
            except Exception as e:  # noqa: BLE001
                print("schedule upload failed:", e)
                break
        else:
            print("schedule uploaded")
        n = 0
        for it in items:
            try:
                dbmod.save_post({"content": it["text"], "content_type": it["type"],
                                 "status": "published", "source": "history",
                                 "published_at": it["date"]})
                n += 1
            except Exception as e:  # noqa: BLE001
                print("post upload stopped:", e)
                break
        print(f"uploaded {n} history posts")
