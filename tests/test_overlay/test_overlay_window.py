"""Tests for OverlayWindow."""

from __future__ import annotations

from unittest.mock import MagicMock

from mrci.overlay.overlay_window import OverlayWindow


class TestOverlayWindow:
    def test_create_overlay(self, qtbot: object) -> None:
        overlay = OverlayWindow()
        assert overlay.app_section is not None
        assert overlay.shortcut_section is not None

    def test_set_app_tiles(self, qtbot: object) -> None:
        overlay = OverlayWindow()
        overlay.set_app_tiles([("App 1", None, 100), ("App 2", None, 200)])
        assert len(overlay.app_section.tiles) == 2

    def test_set_shortcut_tiles(self, qtbot: object) -> None:
        overlay = OverlayWindow()
        overlay.set_shortcut_tiles([("Copy", None, "ctrl+c"), ("Paste", None, "ctrl+v")])
        assert len(overlay.shortcut_section.tiles) == 2

    def test_app_tile_activated_signal(self, qtbot: object) -> None:
        overlay = OverlayWindow()
        overlay.set_app_tiles([("App 1", None, 100)])
        callback = MagicMock()
        overlay.app_tile_activated.connect(callback)
        overlay.app_section.tiles[0].mousePressEvent(None)
        callback.assert_called_once_with(100)

    def test_shortcut_tile_activated_signal(self, qtbot: object) -> None:
        overlay = OverlayWindow()
        overlay.set_shortcut_tiles([("Copy", None, "ctrl+c")])
        callback = MagicMock()
        overlay.shortcut_tile_activated.connect(callback)
        overlay.shortcut_section.tiles[0].mousePressEvent(None)
        callback.assert_called_once_with("ctrl+c")

    def test_show_hide(self, qtbot: object) -> None:
        overlay = OverlayWindow()
        overlay.show_overlay()
        assert overlay.isVisible()
        overlay.hide_overlay()
        assert not overlay.isVisible()

    def test_two_sections_exist(self, qtbot: object) -> None:
        overlay = OverlayWindow()
        # Both sections should be separate widgets
        assert overlay.app_section is not overlay.shortcut_section
