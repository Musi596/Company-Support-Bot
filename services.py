import asyncpg

async def save_or_update_user(pool: asyncpg.Pool, user_id: int, name: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, name) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET name = $2;
        """, user_id, name)

async def is_admin(pool: asyncpg.Pool, user_id: int):
    async with pool.acquire() as conn:
        role = await conn.fetchval("SELECT role FROM users WHERE user_id = $1;", user_id)
        return role == 'Admin'

async def get_all_admins(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users WHERE role = 'Admin';")
        return [row['user_id'] for row in rows]

async def create_ticket(pool: asyncpg.Pool, user_id: int, user_name: str, question_text: str):
    async with pool.acquire() as conn:
        ticket_id = await conn.fetchval("""
            INSERT INTO tickets (user_id, user_name, question)
            VALUES ($1, $2, $3)
            RETURNING ticket_id;
        """, user_id, user_name, question_text)
        return ticket_id

async def get_ticket_by_id(pool: asyncpg.Pool, ticket_id: int):
    async with pool.acquire() as conn:
        ticket = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_id = $1;", ticket_id)
        return ticket

async def close_ticket(pool: asyncpg.Pool, ticket_id: int, admin_id: int, answer_text: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tickets
            SET status = 'closed', answer = $1, admin_id = $2, answered_at = CURRENT_TIMESTAMP
            WHERE ticket_id = $3;
        """, answer_text, admin_id, ticket_id)