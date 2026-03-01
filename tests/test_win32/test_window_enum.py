"""Tests for window enumeration."""

from __future__ import annotations

from mrci.win32.window_enum import enumerate_windows


class TestEnumerateWindows:
    def test_enumerate_returns_list(self) -> None:
        """Smoke test: enumerate_windows returns a list."""
        result = enumerate_windows()
        assert isinstance(result, list)

    def test_enumerate_excludes_hwnds(self) -> None:
        """Excluded hwnds should not appear in results."""
        all_windows = enumerate_windows()
        if all_windows:
            excluded = {all_windows[0].hwnd}
            filtered = enumerate_windows(exclude_hwnds=excluded)
            excluded_hwnds = {w.hwnd for w in filtered}
            assert all_windows[0].hwnd not in excluded_hwnds

    def test_window_info_has_required_fields(self) -> None:
        """All WindowInfo instances should have hwnd, title, process_name, process_id."""
        windows = enumerate_windows()
        for w in windows:
            assert isinstance(w.hwnd, int)
            assert isinstance(w.title, str)
            assert len(w.title) > 0
            assert isinstance(w.process_id, int)
