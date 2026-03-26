import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "123456789"))

STORAGE_TYPE = "telegram"
BOT_NAME = "Kinolar"

PORT = int(os.getenv("PORT", "10000"))

WEBHOOK_URL = (
    os.getenv("WEBHOOK_URL")
    or os.getenv("RENDER_EXTERNAL_URL")
    or ""
).rstrip("/")
