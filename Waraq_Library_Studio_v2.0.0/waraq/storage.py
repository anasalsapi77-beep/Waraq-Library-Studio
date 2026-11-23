"""SQLite connection management, schema creation and safe demo seeding."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import DB_PATH


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 20000")
    return connection


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    """Create current schema and seed examples only when the tables are empty."""
    from .security import hash_password
    with db() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('manager', 'member')),
            member_id INTEGER UNIQUE REFERENCES members(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL CHECK(item_type IN ('book', 'project')),
            title TEXT NOT NULL,
            publication_year INTEGER NOT NULL,
            specialization TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL DEFAULT '',
            pages INTEGER,
            publisher TEXT NOT NULL DEFAULT '',
            project_year TEXT NOT NULL DEFAULT '',
            team TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
            member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
            borrowed_at TEXT NOT NULL,
            due_at TEXT NOT NULL,
            returned_at TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_loan_per_item
            ON loans(item_id) WHERE returned_at IS NULL;
        CREATE INDEX IF NOT EXISTS loans_member_idx ON loans(member_id, returned_at);
        CREATE INDEX IF NOT EXISTS loans_due_idx ON loans(due_at, returned_at);
        CREATE INDEX IF NOT EXISTS items_search_idx ON items(title, specialization, author);
        """)

        # Preserve existing catalogue and member data. Seed only empty collections.
        if connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0:
            connection.executemany("""INSERT INTO items
                (id, item_type, title, publication_year, specialization, description, author, pages, publisher, project_year, team)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [
                (1, "book", "Deep Learning", 2012, "Artificial Intelligence",
                 "A foundational technical title exploring neural networks and modern machine learning.", "Ahmad", 451, "ACM", "", ""),
                (2, "book", "Cyber Security", 2022, "Networks",
                 "An introduction to security concepts, network protection, and digital risk.", "Nawar", 551, "FBI", "", ""),
                (3, "project", "DataBase", 2025, "Software",
                 "A student project from the original library system sample collection.", "", None, "", "Third", "Kings"),
            ])

        if connection.execute("SELECT COUNT(*) FROM members").fetchone()[0] == 0:
            connection.executemany("INSERT INTO members(id, name) VALUES (?, ?)", [
                (101, "Saif"), (102, "Rida"), (103, "Aws")
            ])

        manager = connection.execute("SELECT id FROM users WHERE username='admin' COLLATE NOCASE").fetchone()
        if manager is None:
            connection.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, 'manager')",
                ("admin", hash_password("admin123")),
            )

        # Repair missing demo logins without overwriting passwords set by users.
        for member_id, name in [(101, "Saif"), (102, "Rida"), (103, "Aws")]:
            member = connection.execute("SELECT id FROM members WHERE id=?", (member_id,)).fetchone()
            if member is None:
                continue
            linked = connection.execute("SELECT id FROM users WHERE member_id=?", (member_id,)).fetchone()
            if linked is None:
                username = f"{name.lower()}_{member_id}"
                connection.execute(
                    "INSERT OR IGNORE INTO users(username, password_hash, role, member_id) VALUES (?, ?, 'member', ?)",
                    (username, hash_password(f"{name.lower()}123"), member_id),
                )


def database_health() -> dict[str, object]:
    with db() as connection:
        result = connection.execute("PRAGMA quick_check").fetchone()[0]
        return {
            "ok": result == "ok",
            "check": result,
            "items": connection.execute("SELECT COUNT(*) FROM items").fetchone()[0],
            "members": connection.execute("SELECT COUNT(*) FROM members").fetchone()[0],
        }
