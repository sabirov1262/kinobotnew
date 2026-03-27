import os


def as_int(value: str, default: int = 0) -> int:
    try:
        return int((value or "").strip())
    except (TypeError, ValueError):
        return default


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SUPER_ADMIN_ID = as_int(os.getenv("SUPER_ADMIN_ID", "0"))

# Kino bazasi saqlanadigan kanal ID
# Masalan: -1001234567890
MOVIES_CHANNEL_ID = as_int(os.getenv("MOVIES_CHANNEL_ID", "0"))

PROTECT_CONTENT_DEFAULT = os.getenv("PROTECT_CONTENT_DEFAULT", "0").strip() == "1"

STORAGE_TYPE = "telegram_channel"
BOT_NAME = os.getenv("BOT_NAME", "Kinolar").strip() or "Kinolar"
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "").strip().lstrip("@")
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "").strip()
PAYMENT_OWNER = os.getenv("PAYMENT_OWNER", "").strip()
