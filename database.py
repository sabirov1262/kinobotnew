from __future__ import annotations

import asyncpg
from typing import Any


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=10)

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args) -> str:
        assert self.pool is not None, "Database pool is not initialized"
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        assert self.pool is not None, "Database pool is not initialized"
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> asyncpg.Record | None:
        assert self.pool is not None, "Database pool is not initialized"
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        assert self.pool is not None, "Database pool is not initialized"
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def init(self) -> None:
        await self.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id BIGSERIAL PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            channel_message_id BIGINT NOT NULL,
            file_type TEXT,
            caption TEXT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """)

        await self.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id BIGSERIAL PRIMARY KEY,
            link_type TEXT NOT NULL CHECK (link_type IN ('telegram','private','external')),
            value TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """)

        await self.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        await self.execute("""
        INSERT INTO settings (key, value)
        VALUES ('protect_content', '0'), ('force_subscriptions_enabled', '1')
        ON CONFLICT (key) DO NOTHING;
        """)

        await self.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """)

    async def upsert_user(self, user_id: int, username: str | None, first_name: str | None) -> None:
        await self.execute("""
        INSERT INTO users (user_id, username, first_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE
        SET username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            updated_at = NOW();
        """, user_id, username, first_name)

    async def add_movie(self, code: str, channel_message_id: int, file_type: str | None = None, caption: str | None = None) -> None:
        await self.execute("""
        INSERT INTO movies (code, channel_message_id, file_type, caption)
        VALUES ($1, $2, $3, $4);
        """, code.strip(), channel_message_id, file_type, caption)

    async def get_movie_by_code(self, code: str) -> dict[str, Any] | None:
        row = await self.fetchrow("SELECT * FROM movies WHERE code = $1 AND is_active = TRUE;", code.strip())
        return dict(row) if row else None

    async def delete_movie_by_code(self, code: str) -> str:
        return await self.execute("DELETE FROM movies WHERE code = $1;", code.strip())

    async def list_movies(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = await self.fetch("""
        SELECT code, channel_message_id, created_at
        FROM movies
        WHERE is_active = TRUE
        ORDER BY created_at DESC
        LIMIT $1;
        """, limit)
        return [dict(r) for r in rows]

    async def add_subscription(self, link_type: str, value: str) -> None:
        await self.execute("""
        INSERT INTO subscriptions (link_type, value)
        VALUES ($1, $2);
        """, link_type, value.strip())

    async def list_subscriptions(self) -> list[dict[str, Any]]:
        rows = await self.fetch("""
        SELECT id, link_type, value, is_active, created_at
        FROM subscriptions
        WHERE is_active = TRUE
        ORDER BY id DESC;
        """)
        return [dict(r) for r in rows]

    async def delete_subscription(self, item_id: int) -> str:
        return await self.execute("DELETE FROM subscriptions WHERE id = $1;", item_id)

    async def get_setting(self, key: str, default: str = "0") -> str:
        value = await self.fetchval("SELECT value FROM settings WHERE key = $1;", key)
        return value if value is not None else default

    async def set_setting(self, key: str, value: str) -> None:
        await self.execute("""
        INSERT INTO settings (key, value)
        VALUES ($1, $2)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
        """, key, value)

    async def get_stats(self) -> dict[str, int]:
        movies = await self.fetchval("SELECT COUNT(*) FROM movies WHERE is_active = TRUE;")
        users = await self.fetchval("SELECT COUNT(*) FROM users;")
        links = await self.fetchval("SELECT COUNT(*) FROM subscriptions WHERE is_active = TRUE;")
        return {"movies": movies or 0, "users": users or 0, "links": links or 0}
