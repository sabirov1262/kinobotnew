import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "123456789"))

# Kino bazasi saqlanadigan kanal/guruh ID si
MOVIES_CHANNEL_ID = os.getenv("MOVIES_CHANNEL_ID", "").strip()
PROTECT_CONTENT_DEFAULT = os.getenv("PROTECT_CONTENT_DEFAULT", "0").strip() == "1"

STORAGE_TYPE = "telegram_channel"
BOT_NAME = os.getenv("BOT_NAME", "Kinolar")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "").strip().lstrip("@")
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "").strip()
PAYMENT_OWNER = os.getenv("PAYMENT_OWNER", "").strip()
