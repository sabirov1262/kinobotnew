import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "123456789"))

# Kino bazasi saqlanadigan kanal/guruh ID si.
# Misol: -1001234567890
MOVIES_CHANNEL_ID = os.getenv("MOVIES_CHANNEL_ID", "").strip()

# Telegram copy_message orqali kanal manbasini yashirish uchun himoya.
PROTECT_CONTENT_DEFAULT = os.getenv("PROTECT_CONTENT_DEFAULT", "0").strip() == "1"

STORAGE_TYPE = "telegram_channel"
BOT_NAME = os.getenv("BOT_NAME", "Kinolar")
