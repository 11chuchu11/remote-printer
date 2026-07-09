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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ink_tracking (
                id          INTEGER PRIMARY KEY CHECK (id = 1),
                black_pages INTEGER DEFAULT 0,
                color_pages INTEGER DEFAULT 0,
                reset_at    TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("INSERT OR IGNORE INTO ink_tracking (id) VALUES (1)")
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


# Rendimiento estimado (ISO/IEC 24711) de las botellas de la Brother DCP-T300:
# BTD60BK (negro) y BT5000 C/M/Y (color). Números de laboratorio — el consumo
# real varía según cobertura de tinta de cada documento.
BLACK_YIELD_PAGES = 6000
COLOR_YIELD_PAGES = 5000


def record_ink_usage(pages: int, color: bool) -> None:
    with _conn() as conn:
        if color:
            conn.execute(
                "UPDATE ink_tracking SET black_pages = black_pages + ?, color_pages = color_pages + ? WHERE id = 1",
                (pages, pages),
            )
        else:
            conn.execute(
                "UPDATE ink_tracking SET black_pages = black_pages + ? WHERE id = 1",
                (pages,),
            )
        conn.commit()


def reset_ink() -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE ink_tracking SET black_pages = 0, color_pages = 0, reset_at = datetime('now') WHERE id = 1"
        )
        conn.commit()


def get_ink_estimate() -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT black_pages, color_pages, reset_at FROM ink_tracking WHERE id = 1"
        ).fetchone()
    black_pages, color_pages, reset_at = row
    return {
        "black_pages": black_pages,
        "color_pages": color_pages,
        "reset_at": reset_at,
        "black_pct": max(0, round(100 - (black_pages / BLACK_YIELD_PAGES * 100))),
        "color_pct": max(0, round(100 - (color_pages / COLOR_YIELD_PAGES * 100))),
    }
