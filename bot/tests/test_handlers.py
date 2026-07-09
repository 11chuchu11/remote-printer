import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import handlers.print as print_handler
import handlers.queue as queue_handler
import handlers.callbacks as callbacks_handler
import handlers.common as common_handler
import handlers.help as help_handler
import handlers.config as config_handler


# ── helpers ──────────────────────────────────────────────────────────────────

DEFAULT_CFG = {"copies": 1, "color": "color", "sides": "one-sided", "media": "A4", "pages": "all"}


# ── handle_document ───────────────────────────────────────────────────────────

class TestHandleDocument:
    async def test_unauthorized_calls_reply_unauthorized(self, make_update, make_context):
        update = make_update(user_id=999999999)
        ctx = make_context()
        mock_unauth = AsyncMock()
        with patch.object(print_handler, "is_allowed", return_value=False), \
             patch.object(print_handler, "log_event"), \
             patch.object(print_handler, "reply_unauthorized", mock_unauth):
            await print_handler.handle_document(update, ctx)
        mock_unauth.assert_called_once_with(update)

    async def test_unauthorized_logs_warning(self, make_update, make_context):
        update = make_update(user_id=999999999)
        ctx = make_context()
        with patch.object(print_handler, "is_allowed", return_value=False), \
             patch.object(print_handler, "log_event") as mock_log, \
             patch.object(print_handler, "reply_unauthorized", AsyncMock()):
            await print_handler.handle_document(update, ctx)
        mock_log.assert_called_with("WARNING", "unauthorized", 999999999)

    async def test_invalid_extension_replies_with_error(self, make_update, make_context):
        update = make_update(filename="malware.exe")
        ctx = make_context()
        with patch.object(print_handler, "is_allowed", return_value=True), \
             patch.object(print_handler, "log_event"):
            await print_handler.handle_document(update, ctx)
        update.message.reply_text.assert_called_once()
        assert "Solo acepto" in update.message.reply_text.call_args[0][0]

    async def test_valid_file_stores_pending(self, make_update, make_context):
        update = make_update(filename="doc.pdf")
        ctx = make_context()
        with patch.object(print_handler, "is_allowed", return_value=True), \
             patch.object(print_handler, "log_event"), \
             patch.object(print_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(print_handler, "get_user_name", return_value=None):
            await print_handler.handle_document(update, ctx)
        assert "pending" in ctx.user_data
        assert ctx.user_data["pending"]["filename"] == "doc.pdf"

    async def test_valid_file_shows_keyboard(self, make_update, make_context):
        update = make_update(filename="doc.pdf")
        ctx = make_context()
        with patch.object(print_handler, "is_allowed", return_value=True), \
             patch.object(print_handler, "log_event"), \
             patch.object(print_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(print_handler, "get_user_name", return_value=None):
            await print_handler.handle_document(update, ctx)
        update.message.reply_text.assert_called_once()

    async def test_caption_page_range_is_preselected(self, make_update, make_context):
        update = make_update(filename="doc.pdf", caption="1-3,5")
        ctx = make_context()
        with patch.object(print_handler, "is_allowed", return_value=True), \
             patch.object(print_handler, "log_event"), \
             patch.object(print_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(print_handler, "get_user_name", return_value=None):
            await print_handler.handle_document(update, ctx)
        assert ctx.user_data["pending"]["config"]["pages"] == "1-3,5"

    async def test_invalid_caption_defaults_to_all(self, make_update, make_context):
        update = make_update(filename="doc.pdf", caption="not a range")
        ctx = make_context()
        with patch.object(print_handler, "is_allowed", return_value=True), \
             patch.object(print_handler, "log_event"), \
             patch.object(print_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(print_handler, "get_user_name", return_value=None):
            await print_handler.handle_document(update, ctx)
        assert ctx.user_data["pending"]["config"]["pages"] == "all"

    async def test_path_traversal_filename_is_sanitized(self, make_update, make_context):
        update = make_update(filename="../../etc/passwd.pdf")
        ctx = make_context()
        with patch.object(print_handler, "is_allowed", return_value=True), \
             patch.object(print_handler, "log_event"), \
             patch.object(print_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(print_handler, "get_user_name", return_value=None):
            await print_handler.handle_document(update, ctx)
        assert ctx.user_data["pending"]["filename"] == "passwd.pdf"
        assert "/" not in ctx.user_data["pending"]["filename"]

    async def test_new_file_discards_previous_pending(self, make_update, make_context, tmp_path):
        old_file = tmp_path / "old.pdf"
        old_file.write_bytes(b"old")
        update = make_update(filename="new.pdf")
        ctx = make_context(user_data={"pending": {"path": str(old_file), "filename": "old.pdf"}})
        with patch.object(print_handler, "is_allowed", return_value=True), \
             patch.object(print_handler, "log_event"), \
             patch.object(print_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(print_handler, "get_user_name", return_value=None):
            await print_handler.handle_document(update, ctx)
        assert not old_file.exists()
        assert ctx.user_data["pending"]["filename"] == "new.pdf"


# ── callbacks — pj:* ─────────────────────────────────────────────────────────

class TestJobCallbacks:
    def _pending(self, path="/tmp/test.pdf", filename="doc.pdf", cfg=None, name=None):
        return {
            "path": path,
            "filename": filename,
            "config": cfg or dict(DEFAULT_CFG),
            "name": name,
        }

    async def test_copies_inc(self, make_callback_query, make_context):
        query = make_callback_query(data="pj:copies_inc")
        ctx = make_context(user_data={"pending": self._pending()})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        assert ctx.user_data["pending"]["config"]["copies"] == 2

    async def test_copies_dec_minimum_is_1(self, make_callback_query, make_context):
        pending = self._pending(cfg={**DEFAULT_CFG, "copies": 1})
        query = make_callback_query(data="pj:copies_dec")
        ctx = make_context(user_data={"pending": pending})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        assert ctx.user_data["pending"]["config"]["copies"] == 1

    async def test_color_toggle(self, make_callback_query, make_context):
        query = make_callback_query(data="pj:color")
        ctx = make_context(user_data={"pending": self._pending()})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        assert ctx.user_data["pending"]["config"]["color"] == "gray"

    async def test_sides_cycles(self, make_callback_query, make_context):
        query = make_callback_query(data="pj:sides")
        ctx = make_context(user_data={"pending": self._pending()})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        assert ctx.user_data["pending"]["config"]["sides"] == "two-sided-long-edge"

    async def test_media_cycles(self, make_callback_query, make_context):
        query = make_callback_query(data="pj:media")
        ctx = make_context(user_data={"pending": self._pending()})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        assert ctx.user_data["pending"]["config"]["media"] == "Letter"

    async def test_pages_cycles(self, make_callback_query, make_context):
        query = make_callback_query(data="pj:pages")
        ctx = make_context(user_data={"pending": self._pending()})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        assert ctx.user_data["pending"]["config"]["pages"] == "odd"

    async def test_pages_custom_range_resets_to_all_then_cycles(self, make_callback_query, make_context):
        pending = self._pending(cfg={**DEFAULT_CFG, "pages": "1-3,5"})
        query = make_callback_query(data="pj:pages")
        ctx = make_context(user_data={"pending": pending})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        assert ctx.user_data["pending"]["config"]["pages"] == "odd"

    async def test_cancel_cleans_up(self, make_callback_query, make_context, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"data")
        query = make_callback_query(data="pj:cancel")
        ctx = make_context(user_data={"pending": self._pending(path=str(f))})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        assert not f.exists()
        assert "pending" not in ctx.user_data
        query.edit_message_text.assert_called_once()

    async def test_confirm_prints_and_cleans_up(self, make_callback_query, make_context, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"data")
        query = make_callback_query(data="pj:confirm")
        ctx = make_context(user_data={"pending": self._pending(path=str(f))})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "print_file") as mock_print, \
             patch.object(callbacks_handler, "log_print"), \
             patch.object(callbacks_handler, "log_event"):
            await callbacks_handler.handle_callback(update, ctx)
        mock_print.assert_called_once()
        assert not f.exists()
        assert "pending" not in ctx.user_data

    async def test_confirm_with_name_shows_personalized_message(self, make_callback_query, make_context, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"data")
        query = make_callback_query(data="pj:confirm")
        ctx = make_context(user_data={"pending": self._pending(path=str(f), name="Alice")})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "print_file"), \
             patch.object(callbacks_handler, "log_print"), \
             patch.object(callbacks_handler, "log_event"):
            await callbacks_handler.handle_callback(update, ctx)
        msg = query.edit_message_text.call_args[0][0]
        assert "Alice" in msg

    async def test_confirm_missing_file_shows_error(self, make_callback_query, make_context):
        query = make_callback_query(data="pj:confirm")
        ctx = make_context(user_data={"pending": self._pending(path="/tmp/does_not_exist.pdf")})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        query.edit_message_text.assert_called_once()
        assert "pending" not in ctx.user_data

    async def test_no_pending_shows_unavailable(self, make_callback_query, make_context):
        query = make_callback_query(data="pj:copies_inc")
        ctx = make_context(user_data={})
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True):
            await callbacks_handler.handle_callback(update, ctx)
        query.edit_message_text.assert_called_once()

    async def test_unauthorized_callback_is_rejected(self, make_callback_query, make_context):
        query = make_callback_query(user_id=999999999, data="pj:confirm")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=False):
            await callbacks_handler.handle_callback(update, ctx)
        query.answer.assert_called_with("No autorizado.", show_alert=True)


# ── callbacks — cfg:* ────────────────────────────────────────────────────────

class TestConfigCallbacks:
    async def test_copies_inc_persists(self, make_callback_query, make_context):
        query = make_callback_query(data="cfg:copies_inc")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(callbacks_handler, "set_print_config") as mock_set, \
             patch.object(callbacks_handler, "log_event"):
            await callbacks_handler.handle_callback(update, ctx)
        mock_set.assert_called_once_with(query.from_user.id, "copies", 2)

    async def test_color_toggle_persists(self, make_callback_query, make_context):
        query = make_callback_query(data="cfg:color")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(callbacks_handler, "set_print_config") as mock_set, \
             patch.object(callbacks_handler, "log_event"):
            await callbacks_handler.handle_callback(update, ctx)
        mock_set.assert_called_once_with(query.from_user.id, "color", "gray")

    async def test_sides_cycles_and_persists(self, make_callback_query, make_context):
        query = make_callback_query(data="cfg:sides")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(callbacks_handler, "set_print_config") as mock_set, \
             patch.object(callbacks_handler, "log_event"):
            await callbacks_handler.handle_callback(update, ctx)
        mock_set.assert_called_once_with(query.from_user.id, "sides", "two-sided-long-edge")

    async def test_media_cycles_and_persists(self, make_callback_query, make_context):
        query = make_callback_query(data="cfg:media")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_print_config", return_value=dict(DEFAULT_CFG)), \
             patch.object(callbacks_handler, "set_print_config") as mock_set, \
             patch.object(callbacks_handler, "log_event"):
            await callbacks_handler.handle_callback(update, ctx)
        mock_set.assert_called_once_with(query.from_user.id, "media", "Letter")

    async def test_done_shows_confirmation(self, make_callback_query, make_context):
        query = make_callback_query(data="cfg:done")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_print_config", return_value=dict(DEFAULT_CFG)):
            await callbacks_handler.handle_callback(update, ctx)
        assert "guardada" in query.edit_message_text.call_args[0][0]


# ── callbacks — menu:* ───────────────────────────────────────────────────────

class TestMenuCallbacks:
    async def test_back_shows_menu(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:back")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_user_name", return_value=None):
            await callbacks_handler.handle_callback(update, ctx)
        assert "hacemos" in query.edit_message_text.call_args[0][0]

    async def test_status_shows_status_and_ink(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:status")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(common_handler, "get_status", return_value="idle"), \
             patch.object(common_handler, "get_queue", return_value=[]), \
             patch.object(common_handler, "get_ink", return_value="Marker: 45"):
            await callbacks_handler.handle_callback(update, ctx)
        msg = query.edit_message_text.call_args[0][0]
        assert "idle" in msg
        assert "45" in msg

    async def test_queue_empty(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:queue")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_queue", return_value=[]):
            await callbacks_handler.handle_callback(update, ctx)
        assert "vacía" in query.edit_message_text.call_args[0][0]

    async def test_queue_with_jobs(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:queue")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_queue", return_value=["DCPT300-1 alice"]):
            await callbacks_handler.handle_callback(update, ctx)
        assert "DCPT300-1" in query.edit_message_text.call_args[0][0]

    async def test_history_empty(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:history")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_history", return_value=[]):
            await callbacks_handler.handle_callback(update, ctx)
        assert "Sin historial" in query.edit_message_text.call_args[0][0]

    async def test_history_with_rows(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:history")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        rows = [{"filename": "a.pdf", "printed_at": "2026-07-09", "status": "ok", "file_path": None}]
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "get_history", return_value=rows):
            await callbacks_handler.handle_callback(update, ctx)
        assert "a.pdf" in query.edit_message_text.call_args[0][0]

    async def test_config_shows_config_menu(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:config")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch("storage.get_print_config", return_value=dict(DEFAULT_CFG)):
            await callbacks_handler.handle_callback(update, ctx)
        query.edit_message_text.assert_called_once()

    async def test_cancel_all_jobs(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:cancel")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "cancel_all", return_value=3), \
             patch.object(callbacks_handler, "log_event"):
            await callbacks_handler.handle_callback(update, ctx)
        assert "3" in query.edit_message_text.call_args[0][0]

    async def test_cancel_no_jobs(self, make_callback_query, make_context):
        query = make_callback_query(data="menu:cancel")
        ctx = make_context()
        update = MagicMock()
        update.callback_query = query
        with patch.object(callbacks_handler, "is_allowed", return_value=True), \
             patch.object(callbacks_handler, "cancel_all", return_value=0), \
             patch.object(callbacks_handler, "log_event"):
            await callbacks_handler.handle_callback(update, ctx)
        assert "No había" in query.edit_message_text.call_args[0][0]


# ── handle_status / handle_cancel / handle_queue ─────────────────────────────

class TestQueueHandlers:
    async def test_status_unauthorized(self, make_update, make_context):
        update = make_update(user_id=999999999)
        ctx = make_context()
        mock_unauth = AsyncMock()
        with patch.object(queue_handler, "is_allowed", return_value=False), \
             patch.object(queue_handler, "reply_unauthorized", mock_unauth):
            await queue_handler.handle_status(update, ctx)
        mock_unauth.assert_called_once_with(update)

    async def test_status_authorized_shows_status_and_ink(self, make_update, make_context):
        update = make_update()
        ctx = make_context()
        with patch.object(queue_handler, "is_allowed", return_value=True), \
             patch.object(common_handler, "get_status", return_value="idle"), \
             patch.object(common_handler, "get_queue", return_value=["DCPT300-1 alice"]), \
             patch.object(common_handler, "get_ink", return_value="Marker: 45"):
            await queue_handler.handle_status(update, ctx)
        msg = update.message.reply_text.call_args[0][0]
        assert "idle" in msg
        assert "45" in msg
        assert "1" in msg

    async def test_cancel_no_args_cancels_all(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=[])
        with patch.object(queue_handler, "is_allowed", return_value=True), \
             patch.object(queue_handler, "cancel_all", return_value=2) as mock_cancel, \
             patch.object(queue_handler, "log_event"):
            await queue_handler.handle_cancel(update, ctx)
        mock_cancel.assert_called_once()
        update.message.reply_text.assert_called_once()

    async def test_cancel_with_job_id_cancels_specific(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=["DCPT300-3"])
        with patch.object(queue_handler, "is_allowed", return_value=True), \
             patch.object(queue_handler, "cancel_job") as mock_cancel, \
             patch.object(queue_handler, "log_event"):
            await queue_handler.handle_cancel(update, ctx)
        mock_cancel.assert_called_once_with("DCPT300-3")

    async def test_cancel_invalid_job_id_shows_error(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=["DCPT300-99"])
        with patch.object(queue_handler, "is_allowed", return_value=True), \
             patch.object(queue_handler, "cancel_job", side_effect=Exception("not found")), \
             patch.object(queue_handler, "log_event"):
            await queue_handler.handle_cancel(update, ctx)
        assert "Error" in update.message.reply_text.call_args[0][0]

    async def test_queue_empty_replies_cola_vacia(self, make_update, make_context):
        update = make_update()
        ctx = make_context()
        with patch.object(queue_handler, "is_allowed", return_value=True), \
             patch.object(queue_handler, "get_queue", return_value=[]):
            await queue_handler.handle_queue(update, ctx)
        assert "vacía" in update.message.reply_text.call_args[0][0]

    async def test_queue_with_jobs_shows_list(self, make_update, make_context):
        update = make_update()
        ctx = make_context()
        with patch.object(queue_handler, "is_allowed", return_value=True), \
             patch.object(queue_handler, "get_queue", return_value=["DCPT300-1 alice"]):
            await queue_handler.handle_queue(update, ctx)
        assert "DCPT300-1" in update.message.reply_text.call_args[0][0]


# ── handle_history ────────────────────────────────────────────────────────────

class TestHistoryHandler:
    async def test_unauthorized(self, make_update, make_context):
        update = make_update(user_id=999999999)
        ctx = make_context()
        mock_unauth = AsyncMock()
        with patch.object(queue_handler, "is_allowed", return_value=False), \
             patch.object(queue_handler, "reply_unauthorized", mock_unauth):
            await queue_handler.handle_history(update, ctx)
        mock_unauth.assert_called_once_with(update)

    async def test_empty_shows_sin_historial(self, make_update, make_context):
        update = make_update()
        ctx = make_context()
        with patch.object(queue_handler, "is_allowed", return_value=True), \
             patch.object(queue_handler, "get_history", return_value=[]):
            await queue_handler.handle_history(update, ctx)
        assert "Sin historial" in update.message.reply_text.call_args[0][0]

    async def test_shows_rows(self, make_update, make_context):
        update = make_update()
        ctx = make_context()
        rows = [{"filename": "a.pdf", "printed_at": "2026-07-09", "status": "ok", "file_path": None}]
        with patch.object(queue_handler, "is_allowed", return_value=True), \
             patch.object(queue_handler, "get_history", return_value=rows):
            await queue_handler.handle_history(update, ctx)
        assert "a.pdf" in update.message.reply_text.call_args[0][0]


# ── handle_start / handle_help ────────────────────────────────────────────────

class TestHelpHandlers:
    async def test_start_unauthorized_shows_user_id(self, make_update, make_context):
        update = make_update(user_id=999999999)
        ctx = make_context()
        with patch.object(help_handler, "is_allowed", return_value=False):
            await help_handler.handle_start(update, ctx)
        msg = update.message.reply_text.call_args[0][0]
        assert "999999999" in msg

    async def test_start_authorized_shows_menu(self, make_update, make_context):
        update = make_update(user_id=111111111)
        ctx = make_context()
        with patch.object(help_handler, "is_allowed", return_value=True), \
             patch.object(help_handler, "get_user_name", return_value=None):
            await help_handler.handle_start(update, ctx)
        call_kwargs = update.message.reply_text.call_args[1]
        assert call_kwargs.get("reply_markup") is not None

    async def test_help_unauthorized_shows_user_id(self, make_update, make_context):
        update = make_update(user_id=999999999)
        ctx = make_context()
        with patch.object(help_handler, "is_allowed", return_value=False):
            await help_handler.handle_help(update, ctx)
        msg = update.message.reply_text.call_args[0][0]
        assert "999999999" in msg

    async def test_help_authorized_lists_commands(self, make_update, make_context):
        update = make_update()
        ctx = make_context()
        with patch.object(help_handler, "is_allowed", return_value=True):
            await help_handler.handle_help(update, ctx)
        msg = update.message.reply_text.call_args[0][0]
        assert "/status" in msg
        assert "/config" in msg


# ── handle_config (command) ───────────────────────────────────────────────────

class TestConfigCommand:
    async def test_unauthorized(self, make_update, make_context):
        update = make_update(user_id=999999999)
        ctx = make_context()
        mock_unauth = AsyncMock()
        with patch.object(config_handler, "is_allowed", return_value=False), \
             patch.object(config_handler, "reply_unauthorized", mock_unauth):
            await config_handler.handle_config(update, ctx)
        mock_unauth.assert_called_once_with(update)

    async def test_no_args_shows_menu(self, make_update, make_context):
        update = make_update()
        ctx = make_context()
        with patch.object(config_handler, "is_allowed", return_value=True), \
             patch.object(config_handler, "get_print_config", return_value=dict(DEFAULT_CFG)):
            await config_handler.handle_config(update, ctx)
        update.message.reply_text.assert_called_once()

    async def test_valid_param_sets_value(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=["color", "gray"])
        with patch.object(config_handler, "is_allowed", return_value=True), \
             patch.object(config_handler, "set_print_config") as mock_set, \
             patch.object(config_handler, "log_event"):
            await config_handler.handle_config(update, ctx)
        mock_set.assert_called_once_with(update.effective_user.id, "color", "gray")
        assert "gray" in update.message.reply_text.call_args[0][0]

    async def test_valid_copies_sets_int_value(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=["copies", "5"])
        with patch.object(config_handler, "is_allowed", return_value=True), \
             patch.object(config_handler, "set_print_config") as mock_set, \
             patch.object(config_handler, "log_event"):
            await config_handler.handle_config(update, ctx)
        mock_set.assert_called_once_with(update.effective_user.id, "copies", 5)

    async def test_unknown_param_shows_error(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=["bogus", "x"])
        with patch.object(config_handler, "is_allowed", return_value=True):
            await config_handler.handle_config(update, ctx)
        assert "desconocido" in update.message.reply_text.call_args[0][0]

    async def test_invalid_value_shows_error(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=["color", "purple"])
        with patch.object(config_handler, "is_allowed", return_value=True):
            await config_handler.handle_config(update, ctx)
        assert "inválido" in update.message.reply_text.call_args[0][0].lower()

    async def test_copies_out_of_range_shows_error(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=["copies", "150"])
        with patch.object(config_handler, "is_allowed", return_value=True):
            await config_handler.handle_config(update, ctx)
        assert "1 y 99" in update.message.reply_text.call_args[0][0]

    async def test_wrong_arg_count_shows_usage(self, make_update, make_context):
        update = make_update()
        ctx = make_context(args=["color"])
        with patch.object(config_handler, "is_allowed", return_value=True):
            await config_handler.handle_config(update, ctx)
        assert "Uso" in update.message.reply_text.call_args[0][0]
