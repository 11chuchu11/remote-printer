from config import is_allowed, get_user_name


class TestIsAllowed:
    def test_known_user_is_allowed(self):
        assert is_allowed(111111111) is True

    def test_second_known_user_is_allowed(self):
        assert is_allowed(222222222) is True

    def test_unknown_user_is_denied(self):
        assert is_allowed(999999999) is False

    def test_zero_id_is_denied(self):
        assert is_allowed(0) is False


class TestGetUserName:
    def test_known_user_returns_name(self):
        assert get_user_name(111111111) == "Alice"

    def test_second_known_user_returns_name(self):
        assert get_user_name(222222222) == "Bob"

    def test_unknown_user_returns_none(self):
        assert get_user_name(999999999) is None
