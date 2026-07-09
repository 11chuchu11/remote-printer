from unittest.mock import patch, MagicMock
import cups


def _called_args(mock):
    return mock.call_args[0][0]


class TestPrintFile:
    def test_basic_call(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf")
            args = _called_args(mock_run)
        assert args == ["lp", "-d", "DCPT300", "/tmp/test.pdf"]

    def test_copies_adds_n_flag(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"copies": 3})
            args = _called_args(mock_run)
        assert "-n" in args
        assert "3" in args

    def test_copies_1_skips_n_flag(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"copies": 1})
            args = _called_args(mock_run)
        assert "-n" not in args

    def test_grayscale_adds_colormodel(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"color": "gray"})
            args = " ".join(_called_args(mock_run))
        assert "ColorModel=Gray" in args

    def test_color_does_not_add_colormodel(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"color": "color"})
            args = " ".join(_called_args(mock_run))
        assert "ColorModel" not in args

    def test_sides_duplex(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"sides": "two-sided-long-edge"})
            args = " ".join(_called_args(mock_run))
        assert "sides=two-sided-long-edge" in args

    def test_media_letter(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"media": "Letter"})
            args = " ".join(_called_args(mock_run))
        assert "media=Letter" in args

    def test_pages_odd(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"pages": "odd"})
            args = " ".join(_called_args(mock_run))
        assert "page-set=odd" in args

    def test_pages_even(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"pages": "even"})
            args = " ".join(_called_args(mock_run))
        assert "page-set=even" in args

    def test_pages_custom_range(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"pages": "1-3,5,7-9"})
            args = " ".join(_called_args(mock_run))
        assert "page-ranges=1-3,5,7-9" in args

    def test_pages_all_adds_no_option(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", {"pages": "all"})
            args = " ".join(_called_args(mock_run))
        assert "page" not in args

    def test_none_config_uses_defaults(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.print_file("DCPT300", "/tmp/test.pdf", None)
            args = _called_args(mock_run)
        assert args == ["lp", "-d", "DCPT300", "/tmp/test.pdf"]


class TestGetQueue:
    def test_returns_empty_list_when_no_jobs(self):
        with patch("cups.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            result = cups.get_queue("DCPT300")
        assert result == []

    def test_returns_job_lines(self):
        output = "DCPT300-1  alice  1024  Mon 07 Jul\nDCPT300-2  bob  512  Mon 07 Jul\n"
        with patch("cups.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = cups.get_queue("DCPT300")
        assert len(result) == 2


class TestGetStatus:
    def test_uses_long_form_for_reasons_and_location(self):
        with patch("cups.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="DCPT300 is idle.", stderr="")
            cups.get_status("DCPT300")
            args = _called_args(mock_run)
        assert args == ["lpstat", "-l", "-p", "DCPT300"]

    def test_returns_stdout_when_present(self):
        with patch("cups.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="DCPT300 is idle.", stderr="")
            result = cups.get_status("DCPT300")
        assert result == "DCPT300 is idle."

    def test_falls_back_to_stderr(self):
        with patch("cups.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="lpstat: Invalid destination")
            result = cups.get_status("DCPT300")
        assert result == "lpstat: Invalid destination"

    def test_falls_back_to_default_message(self):
        with patch("cups.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            result = cups.get_status("DCPT300")
        assert result == "Sin respuesta de CUPS."


class TestGetInk:
    def test_extracts_marker_lines(self):
        output = "printer DCPT300 is idle\nMarkerLevels: 45\n"
        with patch("cups.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=output)
            result = cups.get_ink("DCPT300")
        assert "MarkerLevels: 45" in result

    def test_returns_empty_when_no_marker_info(self):
        with patch("cups.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="printer DCPT300 is idle\n")
            result = cups.get_ink("DCPT300")
        assert result == ""


class TestCancelJob:
    def test_calls_cancel_with_job_id(self):
        with patch("cups.subprocess.run") as mock_run:
            cups.cancel_job("DCPT300-5")
            args = _called_args(mock_run)
        assert args == ["cancel", "DCPT300-5"]


class TestCancelAll:
    def test_returns_zero_when_queue_empty(self):
        with patch("cups.get_queue", return_value=[]):
            count = cups.cancel_all("DCPT300")
        assert count == 0

    def test_cancels_each_job_and_returns_count(self):
        jobs = ["DCPT300-1  alice  1024", "DCPT300-2  bob  512"]
        with patch("cups.get_queue", return_value=jobs), \
             patch("cups.cancel_job") as mock_cancel:
            count = cups.cancel_all("DCPT300")
        assert count == 2
        assert mock_cancel.call_count == 2
