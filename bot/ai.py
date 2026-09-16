"""AI pipeline: STYLE -> IDEA -> GENERATE -> VALIDATE -> founder review.
Uses google-genai SDK + local Python exec for quiz ground truth."""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

from google import genai

from .config import settings
from . import db as dbmod

DATA = Path(__file__).resolve().parent.parent / "data"
PROMPTS = DATA / "prompts"


def _load(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


def _style() -> dict:
    try:
        prof = dbmod.get_style_profile()
        if prof:
            prof.pop("id", None)
            return prof
    except Exception:
        pass
    return json.loads((DATA / "style_profile.json").read_text(encoding="utf-8"))


def _recent(n: int = 12) -> str:
    try:
        posts = dbmod.recent_posts(n)
    except Exception:
        posts = []
    if not posts:
        # fallback to local history excerpt
        hist = DATA / "channel_history.json"
        if hist.exists():
            items = json.loads(hist.read_text(encoding="utf-8"))[:n]
            posts = [{"content": p.get("text", "")[:400], "content_type": p.get("type", "")} for p in items]
    lines = []
    for p in posts:
        txt = (p.get("content") or p.get("text") or "")[:300].replace("\n", " / ")
        lines.append(f"- [{p.get('content_type', '?')}] {txt}")
    return "\n".join(lines) or "(no history yet)"


def _client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _generate_json(model: str, prompt: str) -> dict:
    client = _client()
    for m in [model, settings.gemini_fallback_model]:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            text = resp.text or "{}"
            text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M)
            return json.loads(text)
        except Exception:
            if m == settings.gemini_fallback_model:
                raise
    return {}


def suggest_ideas(n: int = 2) -> list[dict]:
    prompt = _load("ideas.txt").replace("{style_profile}", json.dumps(_style(), ensure_ascii=False))
    prompt = prompt.replace("{recent_posts}", _recent())
    out = _generate_json(settings.gemini_model, prompt)
    ideas = out if isinstance(out, list) else out.get("ideas", out)
    if isinstance(ideas, dict):
        ideas = [ideas]
    return (ideas or [])[:n]


def _exec_python(code: str) -> str:
    """Run quiz snippet sandboxed-ish (timeout 5s, no network). Returns stdout or 'Error: ...'."""
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            err = (r.stderr.strip().splitlines() or ["Error"])[-1]
            # normalise to short Error / exception name
            m = re.search(r"(\w+Error)(?::.*)?$", err)
            return m.group(1) if m else "Error"
        return r.stdout.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: timeout"
    except Exception as e:  # noqa: BLE001
        return f"Error: {e}"


def _extract_code(post_text: str) -> str:
    # posts are plain text; take the largest code-looking block:
    # lines that look like python between $ execute and > WHAT
    m = re.search(r"\$ ?execut\w+.*?\n(.*?)> WHAT", post_text, re.S | re.I)
    block = m.group(1) if m else post_text
    # strip header/var lines
    lines = [ln for ln in block.splitlines() if not re.match(r"\s*[>$].*:$", ln.strip())]
    return "\n".join(lines).strip()


def generate_post(content_type: str, language: str = "python", difficulty: str = "medium",
                  topic_hint: str = "") -> dict:
    base = _load("generate.txt").replace("{style_profile}", json.dumps(_style(), ensure_ascii=False))
    base = base.replace("{recent_posts}", _recent())
    task = (f"\n=== TASK ===\ncontent_type={content_type}\nlanguage={language}\n"
            f"difficulty={difficulty}\ntopic_hint={topic_hint}\nGenerate now.")
    for attempt in range(3):  # generate -> validate -> retry
        cand = _generate_json(settings.gemini_model, base + task)
        exec_result = ""
        if content_type == "quiz" and language == "python":
            exec_result = _exec_python(_extract_code(cand.get("post_text", "")))
        vprompt = (_load("validate.txt")
                   .replace("{style_profile}", json.dumps(_style(), ensure_ascii=False))
                   .replace("{candidate}", json.dumps(cand, ensure_ascii=False))
                   .replace("{exec_result}", exec_result or "(n/a)"))
        verdict = _generate_json(settings.gemini_validator_model, vprompt)
        ok = bool(verdict.get("pass"))
        try:
            dbmod.save_generation_run({
                "model": settings.gemini_model, "prompt_version": "v1",
                "content_type": content_type, "passed": ok,
                "issues": verdict.get("issues", []),
                "exec_result": exec_result,
            })
        except Exception:
            pass
        if ok:
            if verdict.get("fixed_post_text"):
                cand["post_text"] = verdict["fixed_post_text"]
            if verdict.get("fixed_correct_option") is not None:
                cand["correct_option"] = verdict["fixed_correct_option"]
            cand["_exec_result"] = exec_result
            return cand
        task += f"\nPREVIOUS ATTEMPT FAILED: {verdict.get('issues')}. Fix and regenerate."
    cand["_exec_result"] = exec_result
    cand["_unvalidated"] = True
    return cand
