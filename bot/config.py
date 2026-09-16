"""Central config — all secrets come from environment, never hard-coded."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _int_list(raw: str) -> list[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


@dataclass
class Settings:
    telegram_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    channel_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHANNEL_ID", "@think_code"))
    admin_ids: list[int] = field(default_factory=lambda: _int_list(os.getenv("TELEGRAM_ADMIN_IDS", "")))
    # Admin review group: previews + approve/reject buttons live here,
    # channel receives posts ONLY after approval. Group id looks like -100123....
    review_group_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_REVIEW_GROUP_ID", ""))

    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    # IDEA.md baseline is gemini-3.8-flash; env-overridable so we default to a
    # model ID that exists today while allowing the future ID without code change.
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))
    gemini_fallback_model: str = field(default_factory=lambda: os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite"))
    gemini_validator_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_VALIDATOR_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))
    )

    firebase_project_id: str = field(
        default_factory=lambda: os.getenv("FIREBASE_PROJECT_ID", "think-code-mediabot")
    )
    fly_app_name: str = field(default_factory=lambda: os.getenv("FLY_APP_NAME", "think-code-mediabot"))
    default_publish_time: str = field(default_factory=lambda: os.getenv("DEFAULT_PUBLISH_TIME", "12:00"))
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Asia/Tashkent"))

    def validate_for_bot(self) -> list[str]:
        missing = []
        if not self.telegram_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.admin_ids:
            missing.append("TELEGRAM_ADMIN_IDS")
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        return missing


settings = Settings()
