import sqlite3
from typing import Optional
from config import DB_PATH


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                filename   TEXT,
                file_path  TEXT,
                printed_at TEXT DEFAULT (datetime('now')),
                status     TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                logged_at TEXT DEFAULT (datetime('now')),
                level     TEXT,
                event     TEXT,
                user_id   INTEGER,
                detail    TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS print_config (
                user_id INTEGER PRIMARY KEY,
                copies  INTEGER DEFAULT 1,
                media   TEXT    DEFAULT 'A4',
                sides   TEXT    DEFAULT 'one-sided',
                color   TEXT    DEFAULT 'color'
            )
        """)
        conn.commit()


def log_event(level: str, event: str, user_id: Optional[int] = None, detail: Optional[str] = None) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO logs (level, event, user_id, detail) VALUES (?, ?, ?, ?)",
            (level, event, user_id, detail),
        )
        conn.commit()


def log_print(user_id: int, filename: str, status: str, file_path: Optional[str] = None) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO history (user_id, filename, file_path, status) VALUES (?, ?, ?, ?)",
            (user_id, filename, file_path, status),
        )
        conn.commit()
    log_event("INFO" if status == "ok" else "ERROR", f"print_{status}", user_id, filename)


PRINT_CONFIG_DEFAULTS = {"copies": 1, "media": "A4", "sides": "one-sided", "color": "color"}

PRINT_CONFIG_OPTIONS = {
    "copies": range(1, 100),
    "media":  ("A4", "Letter", "A5", "Legal"),
    "sides":  ("one-sided", "two-sided-long-edge", "two-sided-short-edge"),
    "color":  ("color", "gray"),
}


def get_print_config(user_id: int) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT copies, media, sides, color FROM print_config WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if row:
        return {"copies": row[0], "media": row[1], "sides": row[2], "color": row[3]}
    return dict(PRINT_CONFIG_DEFAULTS)


def set_print_config(user_id: int, param: str, value) -> None:
    with _conn() as conn:
        conn.execute(
            f"INSERT INTO print_config (user_id, {param}) VALUES (?, ?)"
            f" ON CONFLICT(user_id) DO UPDATE SET {param} = excluded.{param}",
            (user_id, value),
        )
        conn.commit()


def get_history(user_id: int, limit: int = 10) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT filename, printed_at, status, file_path FROM history"
            " WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [{"filename": r[0], "printed_at": r[1], "status": r[2], "file_path": r[3]} for r in rows]
