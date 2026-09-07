import asyncpg
import os

from dotenv import load_dotenv

load_dotenv()

async def connect():
        pool = asyncpg.create_pool(
            host="localhost",port=5432,database=os.getenv("DB_NAME"),user=os.getenv("DB_USER"),password=os.getenv("DB_PASSWORD")
        )
        return pool.acquire

async def create_tables():
        async with connect() as pool:
            async with pool.acquire() as connection:
                await connection.execute("""
                    CREATE TABLE users (
                        user_id BIGINT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE tickets (
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
                    );""")
                print("Tables Created")