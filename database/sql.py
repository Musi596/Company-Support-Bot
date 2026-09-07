import asyncpg
import os

from dotenv import load_dotenv

load_dotenv()

async def connect():
        pool = asyncpg.create_pool(
            host="localhost",port=5432,database=os.getenv("DB_NAME"),user=os.getenv("DB_USER"),password=os.getenv("DB_PASSWORD")
        )
        return pool
