from unittest.mock import patch
import handlers.common as common


class TestFormatStatusMessage:
    def test_includes_status_and_queue_count(self):
        with patch.object(common, "get_status", return_value="idle"), \
             patch.object(common, "get_queue", return_value=["DCPT300-1 alice", "DCPT300-2 bob"]), \
             patch.object(common, "get_ink", return_value=""):
            msg = common.format_status_message("DCPT300")
        assert "idle" in msg
        assert "2" in msg

    def test_zero_queue_shows_zero(self):
        with patch.object(common, "get_status", return_value="idle"), \
             patch.object(common, "get_queue", return_value=[]), \
             patch.object(common, "get_ink", return_value=""):
            msg = common.format_status_message("DCPT300")
        assert "Trabajos en cola:</b> 0" in msg

    def test_omits_ink_section_when_empty(self):
        with patch.object(common, "get_status", return_value="idle"), \
             patch.object(common, "get_queue", return_value=[]), \
             patch.object(common, "get_ink", return_value=""):
            msg = common.format_status_message("DCPT300")
        assert "Tinta" not in msg

    def test_includes_ink_section_when_present(self):
        with patch.object(common, "get_status", return_value="idle"), \
             patch.object(common, "get_queue", return_value=[]), \
             patch.object(common, "get_ink", return_value="MarkerLevels: 45"):
            msg = common.format_status_message("DCPT300")
        assert "Tinta" in msg
        assert "45" in msg
