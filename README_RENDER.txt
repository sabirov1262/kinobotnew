1) Render'da New + -> Background Worker tanlang.
2) GitHub repo tanlang.
3) Build Command: pip install -r requirements.txt
4) Start Command: python bot.py
5) Environment variables qo'shing:
   BOT_TOKEN=...
   SUPER_ADMIN_ID=...
   DB_PATH=/var/data/kinobot.db
   MOVIES_CHANNEL_ID=-1001234567890
   BOT_NAME=Kinolar
   SUPPORT_USERNAME=your_username
   PAYMENT_CARD=8600....
   PAYMENT_OWNER=Ism Familiya
   PROTECT_CONTENT_DEFAULT=0
6) Ma'lumotlar saqlanib qolishi uchun Render Disk ulang va mount path ni /var/data qiling.
7) Botni kino baza kanalga admin qiling.

ISHLASH TARTIBI
- Admin kinoni avval MOVIES_CHANNEL_ID kanalga joylaydi.
- Botda kino qo'shishda faqat kod va kanal postining message ID si kiritiladi.
- User kod yuborganda bot kinoni kanaldan copy_message orqali beradi.
- Premium uchun user tarif tanlaydi, to'lov qiladi, screenshot yuboradi.
- Admin screenshotni tugma orqali tasdiqlasa premium avtomatik beriladi.
