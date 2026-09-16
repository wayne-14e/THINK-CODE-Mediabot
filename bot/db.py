"""Firestore wrapper. All collections per IDEA.md §14 + admin_users."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

try:  # make GOOGLE_APPLICATION_CREDENTIALS / FIREBASE_* from .env visible
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:  # noqa: BLE001
    pass

_db = None


def get_db():
    global _db
    if _db is not None:
        return _db
    if not firebase_admin._apps:
        inline = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        if inline:
            cred = credentials.Certificate(json.loads(inline))
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        ):
            cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        else:
            # Falls back to Application Default Credentials (gcloud / Cloud Run)
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(
            cred, {"projectId": os.getenv("FIREBASE_PROJECT_ID", "think-code-mediabot")}
        )
    _db = firestore.client()
    return _db


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- generic helpers (kept tiny for MVP) ----

def save_post(data: dict[str, Any]) -> str:
    db = get_db()
    data.setdefault("created_at", now_iso())
    data.setdefault("status", "draft")
    _, ref = db.collection("posts").add(data)
    return ref.id


def update_post(post_id: str, data: dict[str, Any]) -> None:
    get_db().collection("posts").document(post_id).update(data)


def get_post(post_id: str) -> dict[str, Any] | None:
    doc = get_db().collection("posts").document(post_id).get()
    return {"id": doc.id, **doc.to_dict()} if doc.exists else None


def recent_posts(limit: int = 20) -> list[dict[str, Any]]:
    db = get_db()
    q = db.collection("posts").order_by("created_at", direction="DESCENDING").limit(limit)
    return [{"id": d.id, **d.to_dict()} for d in q.stream()]


def save_ideas(ideas: list[dict[str, Any]]) -> None:
    db = get_db()
    for idea in ideas:
        idea.setdefault("created_at", now_iso())
        idea.setdefault("status", "suggested")
        db.collection("ideas").add(idea)


def get_style_profile() -> dict[str, Any]:
    docs = list(get_db().collection("style_profile").limit(1).stream())
    if docs:
        return {"id": docs[0].id, **docs[0].to_dict()}
    return {}


def save_generation_run(data: dict[str, Any]) -> None:
    data.setdefault("created_at", now_iso())
    get_db().collection("generation_runs").add(data)


def get_schedule() -> list[dict[str, Any]]:
    db = get_db()
    return [{"id": d.id, **d.to_dict()} for d in db.collection("content_schedule").stream()]


def log_publish(post_id: str, where: str, message_id: str) -> None:
    update_post(post_id, {f"{where}_message_id": message_id, "status": "published",
                          "published_at": now_iso()})
