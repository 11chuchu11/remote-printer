import os

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_IDS = frozenset(int(x) for x in os.environ["ALLOWED_USER_IDS"].split(","))
PRINTER = os.environ.get("CUPS_PRINTER", "DCPT300")
ALLOWED_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".txt")
DB_PATH = os.environ.get("DB_PATH", "/data/bot.db")
PERSIST_FILES = os.environ.get("PERSIST_FILES", "false").lower() == "true"
FILES_DIR = os.environ.get("FILES_DIR", "/data/files")


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_IDS
