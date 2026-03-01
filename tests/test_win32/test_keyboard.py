"""Tests for keyboard shortcut parsing and sending."""

from __future__ import annotations

import pytest

from mrci.win32.keyboard import parse_key_sequence


class TestParseKeySequence:
    def test_single_modifier(self) -> None:
        codes = parse_key_sequence("ctrl")
        assert len(codes) == 1
        assert codes[0] == 0x11  # VK_CONTROL

    def test_ctrl_c(self) -> None:
        codes = parse_key_sequence("ctrl+c")
        assert len(codes) == 2
        assert codes[0] == 0x11  # VK_CONTROL

    def test_ctrl_shift_f12(self) -> None:
        codes = parse_key_sequence("ctrl+shift+f12")
        assert len(codes) == 3
        assert codes[0] == 0x11  # VK_CONTROL
        assert codes[1] == 0x10  # VK_SHIFT
        assert codes[2] == 0x7B  # VK_F12

    def test_alt_tab(self) -> None:
        codes = parse_key_sequence("alt+tab")
        assert len(codes) == 2
        assert codes[0] == 0x12  # VK_MENU
        assert codes[1] == 0x09  # VK_TAB

    def test_unknown_key_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown key"):
            parse_key_sequence("ctrl+unknownkey")

    def test_case_insensitive(self) -> None:
        codes1 = parse_key_sequence("Ctrl+C")
        codes2 = parse_key_sequence("ctrl+c")
        assert codes1 == codes2

    def test_spaces_stripped(self) -> None:
        codes = parse_key_sequence("ctrl + c")
        assert len(codes) == 2

    def test_single_letter(self) -> None:
        codes = parse_key_sequence("a")
        assert len(codes) == 1

    def test_escape(self) -> None:
        codes = parse_key_sequence("escape")
        assert codes == [0x1B]

    def test_delete(self) -> None:
        codes = parse_key_sequence("delete")
        assert codes == [0x2E]
