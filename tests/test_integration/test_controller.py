"""Integration tests for Controller."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from mrci.config.schema import TriggerConfig, WindowInfo
from mrci.controller import Controller


def _make_mock_app() -> MagicMock:
    """Create a mock MrciApplication with sentinel."""
    app = QApplication.instance()
    mock_app = MagicMock(wraps=app)
    mock_sentinel = MagicMock()
    mock_sentinel.display_changed = MagicMock()
    mock_sentinel.display_changed.connect = MagicMock()
    mock_sentinel.winId.return_value = 0
    mock_app.sentinel = mock_sentinel
    mock_app.primaryScreen = app.primaryScreen  # type: ignore[union-attr]
    return mock_app


class TestController:
    def test_controller_creates_tray(self, qtbot: object) -> None:
        """Controller should create a system tray icon."""
        mock_app = _make_mock_app()
        with patch("mrci.controller.MouseHook") as MockHook:
            mock_hook = MagicMock()
            mock_hook.long_press_detected = MagicMock()
            mock_hook.long_press_detected.connect = MagicMock()
            mock_hook.install.return_value = True
            MockHook.return_value = mock_hook

            controller = Controller(mock_app)
            assert controller._tray is not None
            assert controller._tray.isVisible()
            controller.cleanup()

    def test_controller_trigger_creates_overlay(self, qtbot: object) -> None:
        """When a trigger activates, overlay should be created and shown."""
        mock_app = _make_mock_app()
        with patch("mrci.controller.MouseHook") as MockHook:
            mock_hook = MagicMock()
            mock_hook.long_press_detected = MagicMock()
            mock_hook.long_press_detected.connect = MagicMock()
            mock_hook.install.return_value = True
            MockHook.return_value = mock_hook

            controller = Controller(mock_app)
            trigger = TriggerConfig(
                name="Test",
                aspect_ratio_min=0.4,
                aspect_ratio_max=0.65,
            )
            controller._on_trigger_activated(trigger)
            assert controller._overlay is not None
            assert controller._overlay_visible is True
            controller.cleanup()

    def test_controller_trigger_deactivation_hides_overlay(self, qtbot: object) -> None:
        """When trigger deactivates, overlay should hide."""
        mock_app = _make_mock_app()
        with patch("mrci.controller.MouseHook") as MockHook:
            mock_hook = MagicMock()
            mock_hook.long_press_detected = MagicMock()
            mock_hook.long_press_detected.connect = MagicMock()
            mock_hook.install.return_value = True
            MockHook.return_value = mock_hook

            controller = Controller(mock_app)
            trigger = TriggerConfig(
                name="Test",
                aspect_ratio_min=0.4,
                aspect_ratio_max=0.65,
            )
            controller._on_trigger_activated(trigger)
            controller._on_trigger_deactivated()
            assert controller._overlay_visible is False
            controller.cleanup()

    def test_long_press_toggles_overlay(self, qtbot: object) -> None:
        """Long press should toggle overlay visibility."""
        mock_app = _make_mock_app()
        with patch("mrci.controller.MouseHook") as MockHook:
            mock_hook = MagicMock()
            mock_hook.long_press_detected = MagicMock()
            mock_hook.long_press_detected.connect = MagicMock()
            mock_hook.install.return_value = True
            MockHook.return_value = mock_hook

            controller = Controller(mock_app)
            trigger = TriggerConfig(
                name="Test",
                aspect_ratio_min=0.4,
                aspect_ratio_max=0.65,
            )
            controller._on_trigger_activated(trigger)
            assert controller._overlay_visible is True

            # Long press to hide
            controller._on_long_press()
            assert controller._overlay_visible is False

            # Long press to show again
            controller._on_long_press()
            assert controller._overlay_visible is True
            controller.cleanup()

    def test_app_tile_activation_by_hwnd(self, qtbot: object) -> None:
        """App tile activation should focus the correct window by hwnd."""
        mock_app = _make_mock_app()
        with patch("mrci.controller.MouseHook") as MockHook:
            mock_hook = MagicMock()
            mock_hook.long_press_detected = MagicMock()
            mock_hook.long_press_detected.connect = MagicMock()
            mock_hook.install.return_value = True
            MockHook.return_value = mock_hook

            controller = Controller(mock_app)
            trigger = TriggerConfig(
                name="Test",
                aspect_ratio_min=0.4,
                aspect_ratio_max=0.65,
            )
            controller._on_trigger_activated(trigger)

            # Set up window list manually
            controller._window_list = [
                WindowInfo(hwnd=100, title="First", process_name="a.exe", process_id=1),
                WindowInfo(hwnd=200, title="Second", process_name="b.exe", process_id=2),
                WindowInfo(hwnd=300, title="Third", process_name="c.exe", process_id=3),
            ]

            # Activate the second window by hwnd
            with patch.object(controller._window_manager, "is_window_valid", return_value=True), \
                 patch.object(controller._window_manager, "focus_window"), \
                 patch.object(controller._window_manager, "save_position"):
                controller._on_app_tile_activated(200)

            # MRU: hwnd 200 should now be first
            assert controller._window_list[0].hwnd == 200
            assert controller._window_list[1].hwnd == 100
            assert controller._window_list[2].hwnd == 300
            controller.cleanup()

    def test_shortcut_tile_activation(self, qtbot: object) -> None:
        """Shortcut tile activation should send the key sequence."""
        mock_app = _make_mock_app()
        with patch("mrci.controller.MouseHook") as MockHook:
            mock_hook = MagicMock()
            mock_hook.long_press_detected = MagicMock()
            mock_hook.long_press_detected.connect = MagicMock()
            mock_hook.install.return_value = True
            MockHook.return_value = mock_hook

            controller = Controller(mock_app)
            trigger = TriggerConfig(
                name="Test",
                aspect_ratio_min=0.4,
                aspect_ratio_max=0.65,
            )
            controller._on_trigger_activated(trigger)

            with patch("mrci.controller.send_key_sequence") as mock_send, \
                 patch.object(controller._window_manager, "get_foreground_window", return_value=0):
                controller._on_shortcut_tile_activated("ctrl+c")
                mock_send.assert_called_once_with("ctrl+c")
            controller.cleanup()
