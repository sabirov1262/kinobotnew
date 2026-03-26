import os

# =========================
# 🔑 BOT SOZLAMALARI
# =========================

# Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    raise ValueError("❌ BOT_TOKEN topilmadi! Render env ga qo‘shing")

# =========================
# 👑 ADMIN
# =========================

SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "123456789"))

# =========================
# ⚙️ BOT PARAMETRLARI
# =========================

STORAGE_TYPE = "telegram"   # kinolar Telegramda saqlanadi
BOT_NAME = "Kinolar"

# =========================
# 🌐 WEBHOOK (Render uchun)
# =========================

# Render avtomatik beradi
PORT = int(os.getenv("PORT", "10000"))

# Asosiy URL (Render beradi)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")

# Agar qo‘lda bersangiz ishlaydi
WEBHOOK_URL = (
    os.getenv("WEBHOOK_URL")
    or RENDER_EXTERNAL_URL
    or ""
).rstrip("/")

if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL topilmadi! Render URL ni tekshiring")

# =========================
# 🧪 DEBUG (optional)
# =========================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
