Render deploy:

1) Render'da Web Service yarating.
2) GitHub repo ulang.
3) Build Command:
   pip install -r requirements.txt
4) Start Command:
   python main.py
5) Environment Variables:
   BOT_TOKEN=...
   DATABASE_URL=...
   SUPER_ADMIN_ID=...
   CHANNEL_ID=-100...
   WEBHOOK_HOST=https://your-service.onrender.com
   WEBHOOK_PATH=/webhook
   PORT=10000

Muhim:
- Bot kanalga admin bo‘lishi kerak.
- Baza kanal: https://t.me/kinolar040
- Userga kino yuborishda copy_message ishlatiladi, shuning uchun kanal manbasi ko‘rinmaydi.
