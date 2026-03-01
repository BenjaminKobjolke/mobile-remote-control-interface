"""Borderless always-on-top overlay panel occupying the bottom portion of the screen."""

from __future__ import annotations

import logging
from typing import cast

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QBoxLayout, QVBoxLayout, QWidget

from mrci.overlay.paginated_section import PaginatedTileSection

logger = logging.getLogger(__name__)


class OverlayWindow(QWidget):
    """Borderless, always-on-top overlay panel that sits in the bottom portion of the screen.

    Shows two paginated sections: one for running apps and one for custom shortcut tiles.
    Each section has its own left/right navigation arrows.
    """

    app_tile_activated = Signal(int)  # hwnd
    shortcut_tile_activated = Signal(str)  # key_sequence
    previous_window_requested = Signal()
    next_window_requested = Signal()
    apps_collapsed = Signal(bool)  # True = collapsed

    def __init__(
        self,
        top_region_percent: int = 40,
        app_area_percent: int = 30,
        tile_columns: int = 2,
        tile_rows: int = 2,
        tile_bg_color: str = "#0078D4",
        tile_text_color: str = "#FFFFFF",
        icon_size: int = 48,
        font_size: int = 12,
        tile_padding: int = 4,
        nav_button_size: int = 60,
        max_app_tiles: int = 4,
        max_shortcut_tiles: int = 4,
        show_tile_text: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._top_region_percent = top_region_percent
        self._app_area_percent = app_area_percent
        self._tile_columns = tile_columns
        self._tile_rows = tile_rows
        self._tile_bg_color = tile_bg_color
        self._tile_text_color = tile_text_color
        self._icon_size = icon_size
        self._font_size = font_size
        self._tile_padding = tile_padding
        self._nav_button_size = nav_button_size
        self._max_app_tiles = max_app_tiles
        self._max_shortcut_tiles = max_shortcut_tiles
        self._show_tile_text = show_tile_text

        # Window flags: frameless, always on top, tool (no taskbar entry)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet("background-color: #1a1a1a;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App section
        self._app_section = PaginatedTileSection(
            label="Apps",
            columns=tile_columns,
            rows=tile_rows,
            items_per_page=max_app_tiles,
            bg_color=tile_bg_color,
            text_color=tile_text_color,
            icon_size=icon_size,
            font_size=font_size,
            padding=tile_padding,
            nav_button_size=nav_button_size,
            show_text=show_tile_text,
            show_window_nav=True,
            collapsible=True,
            parent=self,
        )
        self._app_section.tile_activated.connect(self._on_app_tile)
        self._app_section.prev_window_clicked.connect(self.previous_window_requested)
        self._app_section.next_window_clicked.connect(self.next_window_requested)
        self._app_section.collapse_toggled.connect(self._on_app_collapse)
        overlay_total = 100 - top_region_percent
        shortcut_stretch = max(1, overlay_total - app_area_percent)
        app_stretch = max(1, app_area_percent)
        layout.addWidget(self._app_section, stretch=app_stretch)

        # Shortcut section
        self._shortcut_section = PaginatedTileSection(
            label="Shortcuts",
            columns=tile_columns,
            rows=tile_rows,
            items_per_page=max_shortcut_tiles,
            bg_color=tile_bg_color,
            text_color=tile_text_color,
            icon_size=icon_size,
            font_size=font_size,
            padding=tile_padding,
            nav_button_size=nav_button_size,
            show_text=show_tile_text,
            parent=self,
        )
        self._shortcut_section.tile_activated.connect(self._on_shortcut_tile)
        layout.addWidget(self._shortcut_section, stretch=shortcut_stretch)

    @property
    def app_section(self) -> PaginatedTileSection:
        return self._app_section

    @property
    def shortcut_section(self) -> PaginatedTileSection:
        return self._shortcut_section

    def _on_app_tile(self, tile_data: object) -> None:
        """Forward app tile activation with hwnd."""
        if isinstance(tile_data, int):
            self.app_tile_activated.emit(tile_data)

    def _on_shortcut_tile(self, tile_data: object) -> None:
        """Forward shortcut tile activation with key_sequence."""
        if isinstance(tile_data, str):
            self.shortcut_tile_activated.emit(tile_data)

    def _on_app_collapse(self, collapsed: bool) -> None:
        """Handle app section collapse/expand."""
        layout = cast(QBoxLayout | None, self.layout())
        if layout is not None:
            # Set stretch to 0 when collapsed so shortcut section takes all space
            stretch = 0 if collapsed else max(1, self._app_area_percent)
            layout.setStretchFactor(self._app_section, stretch)
        self.apps_collapsed.emit(collapsed)

    @property
    def effective_top_percent(self) -> int:
        """Return the effective top region percent, accounting for collapse state."""
        if self._app_section.is_collapsed:
            # Give the freed app-tile space to the top window region
            return self._top_region_percent + self._app_area_percent
        return self._top_region_percent

    def position_on_screen(self) -> None:
        """Position the overlay in the bottom portion of the screen."""
        qapp = cast(QApplication | None, QApplication.instance())
        if qapp is None:
            return
        screen = qapp.primaryScreen()
        if screen is None:
            return

        avail = screen.availableGeometry()  # usable area (excludes taskbar)
        top_pct = self.effective_top_percent
        top_height = int(avail.height() * top_pct / 100)
        overlay_height = avail.height() - top_height

        self.setFixedSize(avail.width(), overlay_height)
        self.setGeometry(avail.x(), avail.y() + top_height, avail.width(), overlay_height)

        full = screen.geometry()
        actual = self.geometry()
        logger.info(
            "Display resolution: %dx%d | GUI requested: %dx%d | GUI actual: %dx%d | GUI pos: (%d, %d)",
            full.width(), full.height(),
            avail.width(), overlay_height,
            actual.width(), actual.height(),
            actual.x(), actual.y(),
        )

    def show_overlay(self) -> None:
        """Position and show the overlay."""
        self.position_on_screen()
        self.show()
        logger.info("Overlay shown")

    def hide_overlay(self) -> None:
        """Hide the overlay."""
        self.hide()
        logger.info("Overlay hidden")

    def set_app_tiles(self, items: list[tuple[str, QPixmap | None, int]]) -> None:
        """Set running app tiles. Each item is (title, icon, hwnd)."""
        self._app_section.set_items(items)

    def set_shortcut_tiles(self, items: list[tuple[str, QPixmap | None, str]]) -> None:
        """Set custom shortcut tiles. Each item is (name, icon, key_sequence)."""
        self._shortcut_section.set_items(items)

    def update_config(
        self,
        top_region_percent: int,
        app_area_percent: int,
        tile_columns: int,
        tile_bg_color: str,
        tile_text_color: str,
        icon_size: int,
        font_size: int,
        tile_padding: int,
        nav_button_size: int,
        max_app_tiles: int,
        max_shortcut_tiles: int,
        show_tile_text: bool,
    ) -> None:
        """Update overlay configuration and rebuild sections."""
        self._top_region_percent = top_region_percent
        self._app_area_percent = app_area_percent

        # Remove old sections
        layout = cast(QBoxLayout | None, self.layout())
        if layout is not None:
            layout.removeWidget(self._app_section)
            layout.removeWidget(self._shortcut_section)
        self._app_section.deleteLater()
        self._shortcut_section.deleteLater()

        # Recreate app section
        self._app_section = PaginatedTileSection(
            label="Apps",
            columns=tile_columns,
            rows=tile_columns,
            items_per_page=max_app_tiles,
            bg_color=tile_bg_color,
            text_color=tile_text_color,
            icon_size=icon_size,
            font_size=font_size,
            padding=tile_padding,
            nav_button_size=nav_button_size,
            show_text=show_tile_text,
            show_window_nav=True,
            collapsible=True,
            parent=self,
        )
        self._app_section.tile_activated.connect(self._on_app_tile)
        self._app_section.prev_window_clicked.connect(self.previous_window_requested)
        self._app_section.next_window_clicked.connect(self.next_window_requested)
        self._app_section.collapse_toggled.connect(self._on_app_collapse)
        overlay_total = 100 - top_region_percent
        app_stretch = max(1, app_area_percent)
        shortcut_stretch = max(1, overlay_total - app_area_percent)
        if layout is not None:
            layout.addWidget(self._app_section, app_stretch)

        # Recreate shortcut section
        self._shortcut_section = PaginatedTileSection(
            label="Shortcuts",
            columns=tile_columns,
            rows=tile_columns,
            items_per_page=max_shortcut_tiles,
            bg_color=tile_bg_color,
            text_color=tile_text_color,
            icon_size=icon_size,
            font_size=font_size,
            padding=tile_padding,
            nav_button_size=nav_button_size,
            show_text=show_tile_text,
            parent=self,
        )
        self._shortcut_section.tile_activated.connect(self._on_shortcut_tile)
        if layout is not None:
            layout.addWidget(self._shortcut_section, shortcut_stretch)

        self.position_on_screen()
