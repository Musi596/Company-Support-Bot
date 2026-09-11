import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def connect():
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return pool

async def create_tables(pool):
    async with pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'Client' CHECK(role IN ('Admin','Client')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                user_name VARCHAR(255) NOT NULL,
                question TEXT NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'open',
                answer TEXT DEFAULT NULL,
                admin_id BIGINT DEFAULT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                answered_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
                CONSTRAINT fk_tickets_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bot_chats (
                chat_id BIGINT PRIMARY KEY,
                chat_type VARCHAR(40) NOT NULL,
                title VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );""")

        await connection.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id BIGSERIAL PRIMARY KEY,
                slug VARCHAR(100) NOT NULL UNIQUE,
                lang VARCHAR(10) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                photo TEXT DEFAULT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );""")
        print("Tables Created")
