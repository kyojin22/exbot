"""SQLite setup and queries for the `expenses` table.

Plain SQL, no ORM — this project is small enough that an ORM would just add
indirection. See CLAUDE.md section 5 for the schema.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id     INTEGER NOT NULL,
    amount      REAL NOT NULL,
    currency    TEXT NOT NULL,
    category    TEXT NOT NULL,
    note        TEXT NOT NULL,
    raw_message TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""

_INDEX = """
CREATE INDEX IF NOT EXISTS idx_expenses_chat_created
    ON expenses (chat_id, created_at);
"""


@dataclass
class Expense:
    id: int
    chat_id: int
    amount: float
    currency: str
    category: str
    note: str
    raw_message: str
    created_at: str


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(_SCHEMA)
        conn.execute(_INDEX)
        conn.commit()
    finally:
        conn.close()


def insert_expense(
    conn: sqlite3.Connection,
    *,
    chat_id: int,
    amount: float,
    currency: str,
    category: str,
    note: str,
    raw_message: str,
    created_at: datetime,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO expenses (chat_id, amount, currency, category, note, raw_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (chat_id, amount, currency, category, note, raw_message, created_at.isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def get_expenses_since(conn: sqlite3.Connection, *, chat_id: int, since: datetime) -> list[Expense]:
    rows = conn.execute(
        """
        SELECT id, chat_id, amount, currency, category, note, raw_message, created_at
        FROM expenses
        WHERE chat_id = ? AND created_at >= ?
        ORDER BY created_at ASC
        """,
        (chat_id, since.isoformat()),
    ).fetchall()
    return [Expense(**dict(row)) for row in rows]


def get_all_expenses(conn: sqlite3.Connection, *, chat_id: int) -> list[Expense]:
    rows = conn.execute(
        """
        SELECT id, chat_id, amount, currency, category, note, raw_message, created_at
        FROM expenses
        WHERE chat_id = ?
        ORDER BY created_at ASC
        """,
        (chat_id,),
    ).fetchall()
    return [Expense(**dict(row)) for row in rows]


def get_last_expense(conn: sqlite3.Connection, *, chat_id: int) -> Expense | None:
    row = conn.execute(
        """
        SELECT id, chat_id, amount, currency, category, note, raw_message, created_at
        FROM expenses
        WHERE chat_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (chat_id,),
    ).fetchone()
    return Expense(**dict(row)) if row else None


def delete_expense(conn: sqlite3.Connection, *, expense_id: int) -> None:
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
