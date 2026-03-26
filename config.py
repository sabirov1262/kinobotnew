from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    super_admin_id: int = int(os.getenv("SUPER_ADMIN_ID", "0"))
    channel_id: int = int(os.getenv("CHANNEL_ID", "0"))
    webhook_host: str = os.getenv("WEBHOOK_HOST", "")
    webhook_path: str = os.getenv("WEBHOOK_PATH", "/webhook")
    port: int = int(os.getenv("PORT", "10000"))
    bot_name: str = os.getenv("BOT_NAME", "Kinolar")
    protect_content_default: bool = _bool_env("PROTECT_CONTENT_DEFAULT", False)

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_host.rstrip('/')}{self.webhook_path}"

    def validate(self) -> None:
        required = {
            "BOT_TOKEN": self.bot_token,
            "DATABASE_URL": self.database_url,
            "SUPER_ADMIN_ID": self.super_admin_id,
            "CHANNEL_ID": self.channel_id,
            "WEBHOOK_HOST": self.webhook_host,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


settings = Settings()
