import pytest
from handlers.keyboards import (
    next_in_cycle,
    job_keyboard, config_keyboard,
    job_text, config_text,
    PAGES_CYCLE, SIDES_CYCLE, MEDIA_CYCLE,
)


class TestNextInCycle:
    def test_advances_to_next(self):
        assert next_in_cycle(["a", "b", "c"], "a") == "b"
        assert next_in_cycle(["a", "b", "c"], "b") == "c"

    def test_wraps_around(self):
        assert next_in_cycle(["a", "b", "c"], "c") == "a"

    def test_unknown_value_starts_from_beginning(self):
        # unknown → idx=0, so next is cycle[1]
        assert next_in_cycle(["a", "b", "c"], "z") == "b"

    def test_pages_cycle_order(self):
        assert next_in_cycle(PAGES_CYCLE, "all") == "odd"
        assert next_in_cycle(PAGES_CYCLE, "odd") == "even"
        assert next_in_cycle(PAGES_CYCLE, "even") == "all"

    def test_sides_cycle_has_three_options(self):
        assert len(SIDES_CYCLE) == 3

    def test_media_cycle_has_four_options(self):
        assert len(MEDIA_CYCLE) == 4


class TestJobKeyboard:
    @pytest.fixture
    def cfg(self):
        return {"copies": 1, "color": "color", "sides": "one-sided", "media": "A4", "pages": "all"}

    def _all_data(self, kb):
        return [btn.callback_data for row in kb.inline_keyboard for btn in row]

    def _all_text(self, kb):
        return [btn.text for row in kb.inline_keyboard for btn in row]

    def test_has_confirm_and_cancel(self, cfg):
        kb = job_keyboard(cfg)
        data = self._all_data(kb)
        assert "pj:confirm" in data
        assert "pj:cancel" in data

    def test_has_copies_controls(self, cfg):
        kb = job_keyboard(cfg)
        data = self._all_data(kb)
        assert "pj:copies_inc" in data
        assert "pj:copies_dec" in data

    def test_shows_current_copies(self, cfg):
        cfg["copies"] = 5
        kb = job_keyboard(cfg)
        text = self._all_text(kb)
        assert any("5" in t for t in text)

    def test_has_color_button(self, cfg):
        kb = job_keyboard(cfg)
        data = self._all_data(kb)
        assert "pj:color" in data

    def test_has_sides_button(self, cfg):
        kb = job_keyboard(cfg)
        data = self._all_data(kb)
        assert "pj:sides" in data

    def test_has_media_button(self, cfg):
        kb = job_keyboard(cfg)
        data = self._all_data(kb)
        assert "pj:media" in data

    def test_has_pages_button(self, cfg):
        kb = job_keyboard(cfg)
        data = self._all_data(kb)
        assert "pj:pages" in data


class TestConfigKeyboard:
    @pytest.fixture
    def cfg(self):
        return {"copies": 1, "color": "color", "sides": "one-sided", "media": "A4"}

    def _all_data(self, kb):
        return [btn.callback_data for row in kb.inline_keyboard for btn in row]

    def test_has_done_button(self, cfg):
        kb = config_keyboard(cfg)
        assert "cfg:done" in self._all_data(kb)

    def test_uses_cfg_prefix(self, cfg):
        kb = config_keyboard(cfg)
        data = self._all_data(kb)
        assert all(d.startswith("cfg:") for d in data)


class TestJobText:
    @pytest.fixture
    def cfg(self):
        return {"copies": 1, "color": "color", "sides": "one-sided", "media": "A4", "pages": "all"}

    def test_includes_filename(self, cfg):
        text = job_text("documento.pdf", cfg)
        assert "documento.pdf" in text

    def test_with_name_includes_greeting(self, cfg):
        text = job_text("documento.pdf", cfg, name="Alice")
        assert "Alice" in text

    def test_without_name_no_greeting(self, cfg):
        text = job_text("documento.pdf", cfg, name=None)
        assert "Alice" not in text
        assert "Hola" not in text

    def test_shows_copies(self, cfg):
        cfg["copies"] = 3
        text = job_text("doc.pdf", cfg)
        assert "3" in text

    def test_shows_pages(self, cfg):
        cfg["pages"] = "odd"
        text = job_text("doc.pdf", cfg)
        assert "mpar" in text  # "Impares"

    def test_custom_page_range_shown(self, cfg):
        cfg["pages"] = "1-3,5"
        text = job_text("doc.pdf", cfg)
        assert "1-3,5" in text


class TestConfigText:
    @pytest.fixture
    def cfg(self):
        return {"copies": 2, "color": "gray", "sides": "two-sided-long-edge", "media": "Letter"}

    def test_shows_copies(self, cfg):
        assert "2" in config_text(cfg)

    def test_shows_color(self, cfg):
        assert "gray" in config_text(cfg)

    def test_shows_media(self, cfg):
        assert "Letter" in config_text(cfg)
