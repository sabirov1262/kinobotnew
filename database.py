import aiosqlite
import os

DEFAULT_DB_PATH = "/var/data/kinobot.db" if os.path.isdir("/var/data") else "kinobot.db"
DB_PATH = os.getenv("DB_PATH", DEFAULT_DB_PATH)

async def get_db():
    return await aiosqlite.connect(DB_PATH)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_expire TEXT,
                joined_at TEXT DEFAULT (datetime('now')),
                last_active TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Adminlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                added_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # Kinolar jadvali - asosiy saqlash joyi Telegram baza kanal
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                file_id TEXT,
                file_type TEXT DEFAULT 'video',
                caption TEXT,
                source_chat_id TEXT,
                source_message_id INTEGER,
                views INTEGER DEFAULT 0,
                added_at TEXT DEFAULT (datetime('now')),
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Majburiy obuna kanallar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT,
                channel_link TEXT,
                channel_type TEXT DEFAULT 'public',
                added_at TEXT DEFAULT (datetime('now')),
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Premium tariflar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tariffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        # To'lovlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tariff_id INTEGER,
                amount INTEGER NOT NULL,
                payment_type TEXT DEFAULT 'manual',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                confirmed_at TEXT
            )
        """)
        

        # Premium so'rovlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS premium_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tariff_id INTEGER NOT NULL,
                screenshot_file_id TEXT,
                note TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                reviewed_at TEXT,
                reviewed_by INTEGER
            )
        """)

        # Bot sozlamalari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        

        # Schema migratsiyalari
        async with db.execute("PRAGMA table_info(movies)") as cur:
            movie_cols = {row[1] for row in await cur.fetchall()}
        if 'source_chat_id' not in movie_cols:
            await db.execute("ALTER TABLE movies ADD COLUMN source_chat_id TEXT")
        if 'source_message_id' not in movie_cols:
            await db.execute("ALTER TABLE movies ADD COLUMN source_message_id INTEGER")
        if 'file_id' not in movie_cols:
            await db.execute("ALTER TABLE movies ADD COLUMN file_id TEXT")

        # Default sozlamalar
        defaults = [
            ('sharing_enabled', '1'),
            ('premium_enabled', '1'),
            ('bot_name', 'Kinolar'),
            ('welcome_message', '👋 Assalomu alaykum {name} botimizga xush kelibsiz.\n\n🤝 Kino kodini yuboring...'),
            ('subscription_required', '1'),
            ('payment_card', ''),
            ('payment_owner', ''),
            ('payment_note', "To'lovdan keyin chek yoki screenshot yuboring. Admin tasdiqlagach premium beriladi."),
        ]
        for key, val in defaults:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, val)
            )
        
        await db.commit()
    print("✅ Database tayyor!")


# ==================== USER FUNCTIONS ====================

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            return await cur.fetchone()

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO users (user_id, username, full_name) 
               VALUES (?, ?, ?)""",
            (user_id, username, full_name)
        )
        await db.execute(
            """UPDATE users SET username=?, full_name=?, last_active=datetime('now')
               WHERE user_id=?""",
            (username, full_name, user_id)
        )
        await db.commit()

async def get_user_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0]

async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]

async def get_premium_user_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE is_premium=1 AND (premium_expire IS NULL OR premium_expire > datetime('now'))"
        ) as cur:
            row = await cur.fetchone()
            return row[0]

async def get_premium_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE is_premium=1 ORDER BY premium_expire DESC"
        ) as cur:
            return await cur.fetchall()

async def set_premium(user_id: int, days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users SET is_premium=1, 
               premium_expire=datetime('now', '+' || ? || ' days')
               WHERE user_id=?""",
            (days, user_id)
        )
        await db.commit()

async def remove_premium(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_premium=0, premium_expire=NULL WHERE user_id=?",
            (user_id,)
        )
        await db.commit()

async def is_premium_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT 1 FROM users WHERE user_id=? AND is_premium=1 
               AND (premium_expire IS NULL OR premium_expire > datetime('now'))""",
            (user_id,)
        ) as cur:
            return await cur.fetchone() is not None


# ==================== ADMIN FUNCTIONS ====================

async def is_admin(user_id: int):
    from config import SUPER_ADMIN_ID
    if user_id == SUPER_ADMIN_ID:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM admins WHERE user_id=?", (user_id,)
        ) as cur:
            return await cur.fetchone() is not None

async def add_admin(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, username, full_name) VALUES (?,?,?)",
            (user_id, username, full_name)
        )
        await db.commit()

async def remove_admin(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        await db.commit()

async def get_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM admins") as cur:
            return await cur.fetchall()


# ==================== MOVIE FUNCTIONS ====================

async def add_movie(
    code: str,
    title: str,
    file_id: str | None,
    file_type: str,
    caption: str,
    source_chat_id: str | None = None,
    source_message_id: int | None = None,
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO movies
               (code, title, file_id, file_type, caption, source_chat_id, source_message_id)
               VALUES (?,?,?,?,?,?,?)""",
            (code, title, file_id, file_type, caption, source_chat_id, source_message_id)
        )
        await db.commit()

async def get_movie(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies WHERE code=? AND is_active=1", (code,)
        ) as cur:
            return await cur.fetchone()

async def get_all_movies():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies WHERE is_active=1 ORDER BY added_at DESC"
        ) as cur:
            return await cur.fetchall()

async def delete_movie(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET is_active=0 WHERE code=?", (code,))
        await db.commit()

async def increment_views(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET views=views+1 WHERE code=?", (code,))
        await db.commit()

async def get_movie_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM movies WHERE is_active=1") as cur:
            row = await cur.fetchone()
            return row[0]

async def get_total_views():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT SUM(views) FROM movies WHERE is_active=1") as cur:
            row = await cur.fetchone()
            return row[0] or 0

async def update_movie(code: str, field: str, value: str):
    allowed = ['title', 'caption']
    if field not in allowed:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE movies SET {field}=? WHERE code=?", (value, code))
        await db.commit()


# ==================== CHANNEL FUNCTIONS ====================

async def add_channel(channel_id: str, name: str, link: str, ch_type: str = 'public'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO channels (channel_id, channel_name, channel_link, channel_type)
               VALUES (?,?,?,?)""",
            (channel_id, name, link, ch_type)
        )
        await db.commit()

async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM channels WHERE is_active=1"
        ) as cur:
            return await cur.fetchall()

async def delete_channel(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE channels SET is_active=0 WHERE channel_id=?", (channel_id,))
        await db.commit()


# ==================== TARIFF FUNCTIONS ====================

async def add_tariff(name: str, duration: int, price: int, desc: str = ''):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tariffs (name, duration_days, price, description) VALUES (?,?,?,?)",
            (name, duration, price, desc)
        )
        await db.commit()

async def get_tariffs():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tariffs WHERE is_active=1") as cur:
            return await cur.fetchall()

async def get_tariff(tariff_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tariffs WHERE id=?", (tariff_id,)) as cur:
            return await cur.fetchone()

async def update_tariff(tariff_id: int, field: str, value):
    allowed = ['name', 'duration_days', 'price', 'is_active']
    if field not in allowed:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE tariffs SET {field}=? WHERE id=?", (value, tariff_id))
        await db.commit()

async def delete_tariff(tariff_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tariffs SET is_active=0 WHERE id=?", (tariff_id,))
        await db.commit()


# ==================== SETTINGS FUNCTIONS ====================

async def get_setting(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
            (key, value)
        )
        await db.commit()


# ==================== PREMIUM REQUEST FUNCTIONS ====================

async def create_premium_request(user_id: int, tariff_id: int, screenshot_file_id: str | None = None, note: str = ''):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO premium_requests (user_id, tariff_id, screenshot_file_id, note)
               VALUES (?, ?, ?, ?)""",
            (user_id, tariff_id, screenshot_file_id, note)
        )
        await db.commit()
        return cur.lastrowid

async def get_premium_request(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT pr.*, u.full_name, u.username, t.name AS tariff_name, t.duration_days, t.price
               FROM premium_requests pr
               LEFT JOIN users u ON u.user_id = pr.user_id
               LEFT JOIN tariffs t ON t.id = pr.tariff_id
               WHERE pr.id=?""",
            (request_id,)
        ) as cur:
            return await cur.fetchone()

async def get_pending_premium_requests():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT pr.*, u.full_name, u.username, t.name AS tariff_name, t.duration_days, t.price
               FROM premium_requests pr
               LEFT JOIN users u ON u.user_id = pr.user_id
               LEFT JOIN tariffs t ON t.id = pr.tariff_id
               WHERE pr.status='pending'
               ORDER BY pr.id DESC"""
        ) as cur:
            return await cur.fetchall()

async def get_user_premium_requests(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT pr.*, t.name AS tariff_name, t.duration_days, t.price
               FROM premium_requests pr
               LEFT JOIN tariffs t ON t.id = pr.tariff_id
               WHERE pr.user_id=?
               ORDER BY pr.id DESC""",
            (user_id,)
        ) as cur:
            return await cur.fetchall()

async def update_premium_request_status(request_id: int, status: str, reviewed_by: int | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE premium_requests
               SET status=?, reviewed_at=datetime('now'), reviewed_by=?
               WHERE id=?""",
            (status, reviewed_by, request_id)
        )
        await db.commit()
