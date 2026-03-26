import os

# Bot token - .env yoki to'g'ridan-to'g'ri kiriting
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Super admin ID (asosiy admin)
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "123456789"))

# Kanal linki (majburiy obuna uchun default)
# Qo'shimcha kanallar database orqali boshqariladi

# Fayl saqlash usuli: "telegram" (server yo'q, Telegram serverida saqlanadi)
STORAGE_TYPE = "telegram"

# Bot nomi
BOT_NAME = "Kinolar"
