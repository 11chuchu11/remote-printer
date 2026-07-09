from unittest.mock import patch
import handlers.common as common


ESTIMATE = {
    "black_pages": 100,
    "color_pages": 50,
    "reset_at": "2026-01-01 00:00:00",
    "black_pct": 98,
    "color_pct": 99,
}


class TestFormatStatusMessage:
    def test_includes_status_and_queue_count(self):
        with patch.object(common, "get_status", return_value="idle"), \
             patch.object(common, "get_queue", return_value=["DCPT300-1 alice", "DCPT300-2 bob"]), \
             patch.object(common, "get_ink", return_value=""), \
             patch.object(common, "get_ink_estimate", return_value=ESTIMATE):
            msg = common.format_status_message("DCPT300")
        assert "idle" in msg
        assert "2" in msg

    def test_zero_queue_shows_zero(self):
        with patch.object(common, "get_status", return_value="idle"), \
             patch.object(common, "get_queue", return_value=[]), \
             patch.object(common, "get_ink", return_value=""), \
             patch.object(common, "get_ink_estimate", return_value=ESTIMATE):
            msg = common.format_status_message("DCPT300")
        assert "Trabajos en cola:</b> 0" in msg

    def test_falls_back_to_estimate_when_no_real_ink_data(self):
        with patch.object(common, "get_status", return_value="idle"), \
             patch.object(common, "get_queue", return_value=[]), \
             patch.object(common, "get_ink", return_value=""), \
             patch.object(common, "get_ink_estimate", return_value=ESTIMATE):
            msg = common.format_status_message("DCPT300")
        assert "estimado" in msg
        assert "98" in msg

    def test_prefers_real_ink_data_when_present(self):
        with patch.object(common, "get_status", return_value="idle"), \
             patch.object(common, "get_queue", return_value=[]), \
             patch.object(common, "get_ink", return_value="MarkerLevels: 45"):
            msg = common.format_status_message("DCPT300")
        assert "Tinta:" in msg
        assert "45" in msg
        assert "estimado" not in msg


class TestFormatInkMessage:
    def test_includes_percentages_and_reset_date(self):
        with patch.object(common, "get_ink_estimate", return_value=ESTIMATE):
            msg = common.format_ink_message()
        assert "98" in msg
        assert "99" in msg
        assert "2026-01-01" in msg
