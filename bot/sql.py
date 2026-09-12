import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set in environment")
    return value


async def connect() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=_require_env("DB_NAME"),
        user=_require_env("DB_USER"),
        password=_require_env("DB_PASSWORD"),
        min_size=1,
        max_size=10,
        command_timeout=60,
    )


async def create_tables(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'Client' CHECK (role IN ('Admin', 'Client')),
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                user_name VARCHAR(255) NOT NULL,
                question TEXT NOT NULL,
                photo TEXT DEFAULT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'open',
                answer TEXT DEFAULT NULL,
                admin_id BIGINT DEFAULT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                answered_at TIMESTAMPTZ DEFAULT NULL,
                CONSTRAINT fk_tickets_user FOREIGN KEY (user_id)
                    REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bot_chats (
                chat_id BIGINT PRIMARY KEY,
                chat_type VARCHAR(40) NOT NULL,
                title VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_id BIGSERIAL PRIMARY KEY,
                slug VARCHAR(100) NOT NULL UNIQUE,
                lang VARCHAR(10) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                photo TEXT DEFAULT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        print("Tables Created")