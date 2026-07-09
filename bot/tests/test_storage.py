import sqlite3
import pytest
import storage


class TestInitDb:
    def test_creates_history_table(self, test_db):
        with sqlite3.connect(test_db) as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        assert "history" in tables

    def test_creates_logs_table(self, test_db):
        with sqlite3.connect(test_db) as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        assert "logs" in tables

    def test_creates_print_config_table(self, test_db):
        with sqlite3.connect(test_db) as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        assert "print_config" in tables

    def test_creates_ink_tracking_table_with_seed_row(self, test_db):
        with sqlite3.connect(test_db) as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            row = conn.execute("SELECT black_pages, color_pages FROM ink_tracking WHERE id = 1").fetchone()
        assert "ink_tracking" in tables
        assert row == (0, 0)

    def test_idempotent(self, test_db):
        storage.init_db()  # second call should not raise
        storage.init_db()


class TestLogEvent:
    def test_inserts_record(self, test_db):
        storage.log_event("INFO", "test_event", user_id=123, detail="some detail")
        with sqlite3.connect(test_db) as conn:
            row = conn.execute("SELECT level, event, user_id, detail FROM logs").fetchone()
        assert row == ("INFO", "test_event", 123, "some detail")

    def test_without_optional_fields(self, test_db):
        storage.log_event("WARNING", "unauthorized")
        with sqlite3.connect(test_db) as conn:
            row = conn.execute("SELECT user_id, detail FROM logs").fetchone()
        assert row == (None, None)


class TestLogPrint:
    def test_inserts_history_record(self, test_db):
        storage.log_print(111111111, "doc.pdf", "ok")
        with sqlite3.connect(test_db) as conn:
            row = conn.execute("SELECT user_id, filename, status, file_path FROM history").fetchone()
        assert row == (111111111, "doc.pdf", "ok", None)

    def test_inserts_with_file_path(self, test_db):
        storage.log_print(111111111, "doc.pdf", "ok", "/data/files/111111111/doc.pdf")
        with sqlite3.connect(test_db) as conn:
            row = conn.execute("SELECT file_path FROM history").fetchone()
        assert row[0] == "/data/files/111111111/doc.pdf"

    def test_also_creates_log_entry(self, test_db):
        storage.log_print(111111111, "doc.pdf", "ok")
        with sqlite3.connect(test_db) as conn:
            row = conn.execute("SELECT event FROM logs").fetchone()
        assert row[0] == "print_ok"

    def test_error_status_logs_print_error(self, test_db):
        storage.log_print(111111111, "doc.pdf", "error")
        with sqlite3.connect(test_db) as conn:
            row = conn.execute("SELECT event FROM logs").fetchone()
        assert row[0] == "print_error"


class TestGetHistory:
    def test_returns_empty_for_new_user(self, test_db):
        result = storage.get_history(111111111)
        assert result == []

    def test_returns_user_prints(self, test_db):
        storage.log_print(111111111, "a.pdf", "ok")
        storage.log_print(111111111, "b.pdf", "error")
        result = storage.get_history(111111111)
        assert len(result) == 2

    def test_does_not_return_other_users(self, test_db):
        storage.log_print(111111111, "a.pdf", "ok")
        storage.log_print(222222222, "b.pdf", "ok")
        result = storage.get_history(111111111)
        assert len(result) == 1
        assert result[0]["filename"] == "a.pdf"

    def test_ordered_newest_first(self, test_db):
        storage.log_print(111111111, "first.pdf", "ok")
        storage.log_print(111111111, "second.pdf", "ok")
        result = storage.get_history(111111111)
        assert result[0]["filename"] == "second.pdf"

    def test_respects_limit(self, test_db):
        for i in range(15):
            storage.log_print(111111111, f"file{i}.pdf", "ok")
        result = storage.get_history(111111111, limit=5)
        assert len(result) == 5


class TestPrintConfig:
    def test_returns_defaults_for_new_user(self, test_db):
        cfg = storage.get_print_config(999999999)
        assert cfg == {"copies": 1, "media": "A4", "sides": "one-sided", "color": "color"}

    def test_set_and_get_copies(self, test_db):
        storage.set_print_config(111111111, "copies", 3)
        cfg = storage.get_print_config(111111111)
        assert cfg["copies"] == 3

    def test_set_and_get_color(self, test_db):
        storage.set_print_config(111111111, "color", "gray")
        cfg = storage.get_print_config(111111111)
        assert cfg["color"] == "gray"

    def test_upsert_updates_existing(self, test_db):
        storage.set_print_config(111111111, "copies", 2)
        storage.set_print_config(111111111, "copies", 5)
        cfg = storage.get_print_config(111111111)
        assert cfg["copies"] == 5

    def test_set_one_field_preserves_others(self, test_db):
        storage.set_print_config(111111111, "color", "gray")
        storage.set_print_config(111111111, "copies", 3)
        cfg = storage.get_print_config(111111111)
        assert cfg["color"] == "gray"
        assert cfg["copies"] == 3


class TestInkTracking:
    def test_starts_at_zero(self, test_db):
        est = storage.get_ink_estimate()
        assert est["black_pages"] == 0
        assert est["color_pages"] == 0
        assert est["black_pct"] == 100
        assert est["color_pct"] == 100

    def test_mono_job_only_consumes_black(self, test_db):
        storage.record_ink_usage(10, color=False)
        est = storage.get_ink_estimate()
        assert est["black_pages"] == 10
        assert est["color_pages"] == 0

    def test_color_job_consumes_both_tanks(self, test_db):
        storage.record_ink_usage(10, color=True)
        est = storage.get_ink_estimate()
        assert est["black_pages"] == 10
        assert est["color_pages"] == 10

    def test_usage_accumulates_across_jobs(self, test_db):
        storage.record_ink_usage(10, color=False)
        storage.record_ink_usage(5, color=True)
        est = storage.get_ink_estimate()
        assert est["black_pages"] == 15
        assert est["color_pages"] == 5

    def test_pct_decreases_with_usage(self, test_db):
        storage.record_ink_usage(storage.BLACK_YIELD_PAGES // 2, color=False)
        est = storage.get_ink_estimate()
        assert est["black_pct"] == 50

    def test_pct_never_goes_negative(self, test_db):
        storage.record_ink_usage(storage.BLACK_YIELD_PAGES * 2, color=True)
        est = storage.get_ink_estimate()
        assert est["black_pct"] == 0
        assert est["color_pct"] == 0

    def test_reset_zeroes_counters(self, test_db):
        storage.record_ink_usage(100, color=True)
        storage.reset_ink()
        est = storage.get_ink_estimate()
        assert est["black_pages"] == 0
        assert est["color_pages"] == 0

    def test_reset_updates_timestamp(self, test_db):
        before = storage.get_ink_estimate()["reset_at"]
        storage.reset_ink()
        after = storage.get_ink_estimate()["reset_at"]
        assert after >= before
