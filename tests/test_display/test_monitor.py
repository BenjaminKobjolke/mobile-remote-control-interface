"""Tests for DisplayMonitor."""

from __future__ import annotations

from unittest.mock import MagicMock

from mrci.config.schema import ScreenGeometry, TriggerConfig
from mrci.display.monitor import DisplayMonitor


class TestDisplayMonitor:
    def test_process_change_activates_trigger(self, qtbot: object) -> None:
        triggers = [
            TriggerConfig(name="Phone", aspect_ratio_min=0.4, aspect_ratio_max=0.65),
        ]
        monitor = DisplayMonitor(triggers=triggers)
        callback = MagicMock()
        monitor.trigger_activated.connect(callback)

        # Directly invoke _process_change with portrait geometry
        monitor._pending_geometry = ScreenGeometry(width=1080, height=1920)
        monitor._process_change()

        callback.assert_called_once()
        assert monitor.active_trigger is not None
        assert monitor.active_trigger.name == "Phone"

    def test_process_change_deactivates_trigger(self, qtbot: object) -> None:
        triggers = [
            TriggerConfig(name="Phone", aspect_ratio_min=0.4, aspect_ratio_max=0.65),
        ]
        monitor = DisplayMonitor(triggers=triggers)

        # First activate
        monitor._pending_geometry = ScreenGeometry(width=1080, height=1920)
        monitor._process_change()
        assert monitor.active_trigger is not None

        # Then deactivate with landscape
        deactivate_callback = MagicMock()
        monitor.trigger_deactivated.connect(deactivate_callback)
        monitor._pending_geometry = ScreenGeometry(width=1920, height=1080)
        monitor._process_change()

        deactivate_callback.assert_called_once()
        assert monitor.active_trigger is None

    def test_no_duplicate_activation(self, qtbot: object) -> None:
        triggers = [
            TriggerConfig(name="Phone", aspect_ratio_min=0.4, aspect_ratio_max=0.65),
        ]
        monitor = DisplayMonitor(triggers=triggers)
        callback = MagicMock()
        monitor.trigger_activated.connect(callback)

        # Activate once
        monitor._pending_geometry = ScreenGeometry(width=1080, height=1920)
        monitor._process_change()

        # Same trigger shouldn't fire again
        monitor._pending_geometry = ScreenGeometry(width=1080, height=1920)
        monitor._process_change()

        assert callback.call_count == 1

    def test_update_triggers(self, qtbot: object) -> None:
        monitor = DisplayMonitor(triggers=[])
        assert monitor.active_trigger is None

        new_triggers = [
            TriggerConfig(name="New", aspect_ratio_min=0.4, aspect_ratio_max=0.65),
        ]
        monitor.update_triggers(new_triggers)
        assert monitor._triggers == new_triggers

    def test_no_emit_when_no_pending(self, qtbot: object) -> None:
        monitor = DisplayMonitor(triggers=[])
        callback = MagicMock()
        monitor.trigger_activated.connect(callback)
        monitor._process_change()
        callback.assert_not_called()
