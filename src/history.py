"""History module — SQLite-backed translation history.

Pure Python, no tkinter dependency.  All functions are importable from any thread,
but database writes should be serialised externally.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/translations.db")


def init_db() -> None:
    """Create the database file and schema if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS translations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text     TEXT    NOT NULL,
            translated_text TEXT    NOT NULL,
            source_lang     TEXT    NOT NULL,
            target_lang     TEXT    NOT NULL,
            direction       TEXT    NOT NULL,
            created_at      TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_translation(
    source_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    direction: str,
) -> int:
    """Insert a translation record.  Returns the new row id."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute(
        """
        INSERT INTO translations
            (source_text, translated_text, source_lang, target_lang, direction, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            source_text,
            translated_text,
            source_lang,
            target_lang,
            direction,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_translations(
    limit: int = 50,
    offset: int = 0,
    keyword: Optional[str] = None,
) -> list[tuple]:
    """Return recent translations, newest first.

    If *keyword* is provided, only rows whose source or translated text
    contain the keyword (case-insensitive) are returned.
    """
    conn = sqlite3.connect(str(DB_PATH))
    if keyword:
        pattern = f"%{keyword}%"
        rows = conn.execute(
            """
            SELECT id, source_text, translated_text, direction, created_at
            FROM translations
            WHERE source_text LIKE ? OR translated_text LIKE ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (pattern, pattern, limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, source_text, translated_text, direction, created_at
            FROM translations
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    conn.close()
    return rows


def count_translations(keyword: Optional[str] = None) -> int:
    """Return the total number of translation records."""
    conn = sqlite3.connect(str(DB_PATH))
    if keyword:
        pattern = f"%{keyword}%"
        row = conn.execute(
            "SELECT COUNT(*) FROM translations WHERE source_text LIKE ? OR translated_text LIKE ?",
            (pattern, pattern),
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) FROM translations").fetchone()
    conn.close()
    return row[0] if row else 0


def delete_translation(record_id: int) -> None:
    """Delete a single translation record by id."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM translations WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
