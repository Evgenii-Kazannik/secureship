import json
import os
from collections.abc import AsyncGenerator
from typing import Any

import psycopg

DATABASE_URL = os.getenv("DATABASE_URL") or (
    "postgresql://"
    f"{os.getenv('POSTGRES_USER', '')}:"
    f"{os.getenv('POSTGRES_PASSWORD', '')}@"
    f"localhost:5432/"
    f"{os.getenv('POSTGRES_DB', 'secureship')}"
)


async def get_connection() -> AsyncGenerator[psycopg.AsyncConnection[Any], None]:
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        yield conn


async def get_or_create_session(
    conn: psycopg.AsyncConnection[Any], session_id: str
) -> tuple[str, list]:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT state, transcript FROM sessions WHERE id = %s",
            (session_id,),
        )
        row = await cur.fetchone()
        if row:
            return row[0], row[1]
        await cur.execute(
            "INSERT INTO sessions (id) VALUES (%s) ON CONFLICT (id) DO NOTHING",
            (session_id,),
        )
    return "anonymous", []


async def save_turns(
    conn: psycopg.AsyncConnection[Any],
    session_id: str,
    user_msg: str,
    assistant_reply: str,
) -> None:
    new_turns = json.dumps(
        [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_reply},
        ]
    )
    async with conn.cursor() as cur:
        await cur.execute(
            """
            UPDATE sessions
            SET transcript = transcript || %s::jsonb,
                updated_at  = NOW()
            WHERE id = %s
            """,
            (new_turns, session_id),
        )
