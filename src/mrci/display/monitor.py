"""Display change monitor with dual detection paths and debouncing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from mrci.config.schema import ScreenGeometry, TriggerConfig
from mrci.display.aspect_ratio import match_trigger

if TYPE_CHECKING:
    from mrci.app import SentinelWindow

logger = logging.getLogger(__name__)


class DisplayMonitor(QObject):
    """Monitors display resolution changes via QScreen signals and WM_DISPLAYCHANGE.

    Emits `trigger_activated` when a trigger matches, `trigger_deactivated` when none match.
    Uses a 100ms debounce to merge rapid successive change events.
    """

    trigger_activated = Signal(object)  # TriggerConfig
    trigger_deactivated = Signal()

    def __init__(
        self,
        triggers: list[TriggerConfig],
        sentinel: SentinelWindow | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._triggers = triggers
        self._active_trigger: TriggerConfig | None = None
        self._pending_geometry: ScreenGeometry | None = None

        # Debounce timer
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(100)
        self._debounce_timer.timeout.connect(self._process_change)

        # Connect to QScreen signals
        qapp = cast(QApplication | None, QApplication.instance())
        if qapp is not None:
            screen = qapp.primaryScreen()
            if screen is not None:
                screen.geometryChanged.connect(self._on_screen_geometry_changed)

        # Connect to sentinel WM_DISPLAYCHANGE
        if sentinel is not None:
            sentinel.display_changed.connect(self._on_wm_display_change)

    @property
    def active_trigger(self) -> TriggerConfig | None:
        return self._active_trigger

    def update_triggers(self, triggers: list[TriggerConfig]) -> None:
        """Update the list of triggers and re-evaluate."""
        self._triggers = triggers
        self.check_now()

    def check_now(self) -> None:
        """Force an immediate display check using current screen geometry."""
        qapp = cast(QApplication | None, QApplication.instance())
        if qapp is None:
            return
        screen = qapp.primaryScreen()
        if screen is None:
            return
        geo = screen.geometry()
        self._schedule_change(ScreenGeometry(width=geo.width(), height=geo.height()))

    @Slot()
    def _on_screen_geometry_changed(self) -> None:
        qapp = cast(QApplication | None, QApplication.instance())
        if qapp is None:
            return
        screen = qapp.primaryScreen()
        if screen is None:
            return
        geo = screen.geometry()
        logger.debug("QScreen geometry changed: %dx%d", geo.width(), geo.height())
        self._schedule_change(ScreenGeometry(width=geo.width(), height=geo.height()))

    @Slot(int, int)
    def _on_wm_display_change(self, width: int, height: int) -> None:
        logger.debug("WM_DISPLAYCHANGE: %dx%d", width, height)
        self._schedule_change(ScreenGeometry(width=width, height=height))

    def _schedule_change(self, geometry: ScreenGeometry) -> None:
        """Debounce: schedule evaluation after 100ms."""
        self._pending_geometry = geometry
        self._debounce_timer.start()

    @Slot()
    def _process_change(self) -> None:
        """Process the latest pending geometry change."""
        if self._pending_geometry is None:
            return

        geometry = self._pending_geometry
        self._pending_geometry = None

        matched = match_trigger(geometry, self._triggers)

        if matched is not None and matched != self._active_trigger:
            self._active_trigger = matched
            logger.info(
                "Trigger activated: %s (ratio=%.3f)",
                matched.name,
                geometry.aspect_ratio,
            )
            self.trigger_activated.emit(matched)
        elif matched is None and self._active_trigger is not None:
            logger.info("Trigger deactivated (ratio=%.3f)", geometry.aspect_ratio)
            self._active_trigger = None
            self.trigger_deactivated.emit()
