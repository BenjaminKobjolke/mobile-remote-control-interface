"""Tests for WindowManager."""

from __future__ import annotations

from mrci.win32.window_manager import WindowManager


class TestWindowManager:
    def test_save_and_restore_position(self) -> None:
        """Test position save/restore with current foreground window."""
        wm = WindowManager()
        hwnd = wm.get_foreground_window()
        if hwnd:
            wm.save_position(hwnd)
            assert hwnd in wm.saved_positions
            restored = wm.restore_position(hwnd)
            assert restored is True
            assert hwnd not in wm.saved_positions

    def test_restore_nonexistent_returns_false(self) -> None:
        wm = WindowManager()
        assert wm.restore_position(0xDEAD) is False

    def test_restore_all(self) -> None:
        wm = WindowManager()
        # Manually add fake positions
        wm._saved_positions[1] = (0, 0, 100, 100)
        wm._saved_positions[2] = (10, 10, 200, 200)
        wm.restore_all()
        assert len(wm.saved_positions) == 0

    def test_is_window_valid(self) -> None:
        wm = WindowManager()
        # Invalid handle should return False
        assert wm.is_window_valid(0) is False

    def test_get_foreground_window(self) -> None:
        wm = WindowManager()
        hwnd = wm.get_foreground_window()
        assert isinstance(hwnd, int)
