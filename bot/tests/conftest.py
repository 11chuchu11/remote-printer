import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Set env vars before any project module is imported
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "1234567890:test_token_for_pytest")
os.environ.setdefault("ALLOWED_USER_IDS", "111111111,222222222")
os.environ.setdefault("USER_NAMES", "111111111:Alice,222222222:Bob")
os.environ.setdefault("CUPS_PRINTER", "DCPT300")


@pytest.fixture()
def test_db(tmp_path, monkeypatch):
    import storage
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr(storage, "DB_PATH", db_file)
    storage.init_db()
    return db_file


@pytest.fixture()
def make_update():
    def _make(user_id=111111111, caption=None, filename="test.pdf"):
        doc = MagicMock()
        doc.file_name = filename
        file_obj = MagicMock()
        file_obj.download_to_drive = AsyncMock()
        doc.get_file = AsyncMock(return_value=file_obj)

        update = MagicMock()
        update.effective_user.id = user_id
        update.message.reply_text = AsyncMock()
        update.message.caption = caption
        update.message.document = doc
        return update
    return _make


@pytest.fixture()
def make_context():
    def _make(user_data=None, args=None):
        ctx = MagicMock()
        ctx.user_data = user_data if user_data is not None else {}
        ctx.args = args or []
        return ctx
    return _make


@pytest.fixture()
def make_callback_query():
    def _make(user_id=111111111, data="pj:noop"):
        query = MagicMock()
        query.from_user.id = user_id
        query.data = data
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        return query
    return _make


@pytest.fixture()
def default_cfg():
    return {"copies": 1, "color": "color", "sides": "one-sided", "media": "A4", "pages": "all"}
