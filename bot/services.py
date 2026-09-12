import asyncpg


async def save_or_update_user(pool: asyncpg.Pool, user_id: int, name: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, name)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET name = EXCLUDED.name;
            """,
            user_id,
            name,
        )


async def is_admin(pool: asyncpg.Pool, user_id: int) -> bool:
    async with pool.acquire() as conn:
        role = await conn.fetchval("SELECT role FROM users WHERE user_id = $1;", user_id)
        return role == "Admin"


async def get_all_admins(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users WHERE role = 'Admin';")
        return [row["user_id"] for row in rows]


async def save_or_update_chat(pool: asyncpg.Pool, chat_id: int, chat_type: str, title: str | None = None) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO bot_chats (chat_id, chat_type, title)
            VALUES ($1, $2, $3)
            ON CONFLICT (chat_id)
            DO UPDATE SET
                chat_type = EXCLUDED.chat_type,
                title = EXCLUDED.title;
            """,
            chat_id,
            chat_type,
            title,
        )


async def get_broadcast_chat_ids(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT chat_id
            FROM bot_chats
            WHERE chat_type IN ('group', 'supergroup', 'channel')
            ORDER BY chat_id;
            """
        )
        return [row["chat_id"] for row in rows]


async def get_registered_chats(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT chat_id, chat_type, title, created_at
            FROM bot_chats
            WHERE chat_type IN ('group', 'supergroup', 'channel')
            ORDER BY title NULLS LAST, chat_id;
            """
        )


async def delete_chat(pool: asyncpg.Pool, chat_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM bot_chats WHERE chat_id = $1;", chat_id)


async def is_chat_registered(pool: asyncpg.Pool, chat_id: int) -> bool:
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM bot_chats WHERE chat_id = $1);",
            chat_id,
        )
        return bool(exists)


async def get_open_tickets(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT *
            FROM tickets
            WHERE status = 'open'
            ORDER BY created_at DESC;
            """
        )


async def create_ticket(pool: asyncpg.Pool, user_id: int, user_name: str, question_text: str, photo_file_id: str | None = None):
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO tickets (user_id, user_name, question, photo)
            VALUES ($1, $2, $3, $4)
            RETURNING ticket_id;
            """,
            user_id,
            user_name,
            question_text,
            photo_file_id,
        )


async def get_ticket_by_id(pool: asyncpg.Pool, ticket_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM tickets WHERE ticket_id = $1;", ticket_id)


async def close_ticket(pool: asyncpg.Pool, ticket_id: int, admin_id: int, answer_text: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tickets
            SET status = 'closed', answer = $1, admin_id = $2, answered_at = CURRENT_TIMESTAMP
            WHERE ticket_id = $3;
            """,
            answer_text,
            admin_id,
            ticket_id,
        )


async def create_course(pool: asyncpg.Pool, slug: str, lang: str, title: str, description: str, photo: str | None = None):
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO courses (slug, lang, title, description, photo)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING course_id;
            """,
            slug,
            lang,
            title,
            description,
            photo,
        )


async def get_courses_by_lang(pool: asyncpg.Pool, lang: str):
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM courses WHERE lang = $1 ORDER BY created_at;", lang)


async def get_course_by_slug(pool: asyncpg.Pool, slug: str, lang: str | None = None):
    async with pool.acquire() as conn:
        if lang:
            return await conn.fetchrow(
                "SELECT * FROM courses WHERE slug = $1 AND lang = $2;",
                slug,
                lang,
            )
        return await conn.fetchrow("SELECT * FROM courses WHERE slug = $1;", slug)


async def get_course_by_id(pool: asyncpg.Pool, course_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM courses WHERE course_id = $1;", course_id)


async def update_course(pool: asyncpg.Pool, course_id: int, title: str | None = None, description: str | None = None, slug: str | None = None) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE courses
            SET title = COALESCE($1, title),
                description = COALESCE($2, description),
                slug = COALESCE($3, slug),
                updated_at = CURRENT_TIMESTAMP
            WHERE course_id = $4;
            """,
            title,
            description,
            slug,
            course_id,
        )


async def set_course_photo(pool: asyncpg.Pool, course_id: int, photo: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE courses
            SET photo = $1, updated_at = CURRENT_TIMESTAMP
            WHERE course_id = $2;
            """,
            photo,
            course_id,
        )


async def remove_course_photo(pool: asyncpg.Pool, course_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE courses
            SET photo = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE course_id = $1;
            """,
            course_id,
        )


async def delete_course(pool: asyncpg.Pool, course_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM courses WHERE course_id = $1;", course_id)

