import os

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_IDS = frozenset(int(x) for x in os.environ["ALLOWED_USER_IDS"].split(","))
PRINTER = os.environ.get("CUPS_PRINTER", "DCPT300")
ALLOWED_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".txt")
DB_PATH = os.environ.get("DB_PATH", "/data/bot.db")
PERSIST_FILES = os.environ.get("PERSIST_FILES", "false").lower() == "true"
FILES_DIR = os.environ.get("FILES_DIR", "/data/files")

USER_NAMES: dict[int, str] = {}
for _entry in os.environ.get("USER_NAMES", "").split(","):
    if ":" in _entry:
        _uid, _name = _entry.split(":", 1)
        try:
            USER_NAMES[int(_uid.strip())] = _name.strip()
        except ValueError:
            pass


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_IDS


def get_user_name(user_id: int) -> str | None:
    return USER_NAMES.get(user_id)
