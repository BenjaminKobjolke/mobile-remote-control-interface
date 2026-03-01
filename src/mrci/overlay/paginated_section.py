"""Paginated tile section with header navigation arrows and a tile grid."""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mrci.overlay.tile_widget import TileWidget

logger = logging.getLogger(__name__)


class PaginatedTileSection(QWidget):
    """A section with [<] Label [>] header and a paginated grid of tiles.

    Each item is a (name, icon, tile_data) tuple.
    Emits ``tile_activated(object)`` with the tile_data of the clicked tile.
    """

    tile_activated = Signal(object)
    prev_window_clicked = Signal()
    next_window_clicked = Signal()
    collapse_toggled = Signal(bool)  # True = collapsed

    def __init__(
        self,
        label: str,
        columns: int = 2,
        rows: int = 2,
        items_per_page: int = 4,
        bg_color: str = "#0078D4",
        text_color: str = "#FFFFFF",
        icon_size: int = 48,
        font_size: int = 12,
        padding: int = 4,
        nav_button_size: int = 60,
        show_text: bool = True,
        show_window_nav: bool = False,
        collapsible: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._collapsible = collapsible
        self._collapsed = False
        self._columns = columns
        self._rows = rows
        self._items_per_page = items_per_page
        self._bg_color = bg_color
        self._text_color = text_color
        self._icon_size = icon_size
        self._font_size = font_size
        self._padding = padding
        self._show_text = show_text
        self._page_index = 0
        self._items: list[tuple[str, QPixmap | None, object]] = []
        self._tiles: list[TileWidget] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- Header with nav arrows ---
        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 4, 4, 4)
        header_layout.setSpacing(8)

        button_style = (
            "QPushButton {"
            "  background-color: #333333;"
            "  color: #FFFFFF;"
            "  border: 1px solid #555555;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #555555;"
            "}"
        )
        nav_font = QFont()
        nav_font.setPixelSize(24)

        if show_window_nav:
            self._prev_win_btn = QPushButton("<<", header)
            self._prev_win_btn.setFixedSize(nav_button_size, nav_button_size)
            self._prev_win_btn.setFont(nav_font)
            self._prev_win_btn.setStyleSheet(button_style)
            self._prev_win_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._prev_win_btn.clicked.connect(self.prev_window_clicked)
            header_layout.addWidget(self._prev_win_btn)

        self._prev_btn = QPushButton("<", header)
        self._prev_btn.setFixedSize(nav_button_size, nav_button_size)
        self._prev_btn.setFont(nav_font)
        self._prev_btn.setStyleSheet(button_style)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self._go_prev)
        header_layout.addWidget(self._prev_btn)

        self._label_widget = QLabel(label, header)
        self._label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_font = QFont()
        label_font.setPixelSize(16)
        label_font.setBold(True)
        self._label_widget.setFont(label_font)
        self._label_widget.setStyleSheet("color: #FFFFFF; background: transparent;")
        header_layout.addWidget(self._label_widget, stretch=1)

        self._next_btn = QPushButton(">", header)
        self._next_btn.setFixedSize(nav_button_size, nav_button_size)
        self._next_btn.setFont(nav_font)
        self._next_btn.setStyleSheet(button_style)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._go_next)
        header_layout.addWidget(self._next_btn)

        if show_window_nav:
            self._next_win_btn = QPushButton(">>", header)
            self._next_win_btn.setFixedSize(nav_button_size, nav_button_size)
            self._next_win_btn.setFont(nav_font)
            self._next_win_btn.setStyleSheet(button_style)
            self._next_win_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._next_win_btn.clicked.connect(self.next_window_clicked)
            header_layout.addWidget(self._next_win_btn)

        if collapsible:
            self._collapse_btn = QPushButton("v", header)
            self._collapse_btn.setFixedSize(nav_button_size, nav_button_size)
            self._collapse_btn.setFont(nav_font)
            self._collapse_btn.setStyleSheet(button_style)
            self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._collapse_btn.clicked.connect(self._toggle_collapse)
            header_layout.addWidget(self._collapse_btn)

        self._header = header
        outer.addWidget(header)

        # --- Tile grid area ---
        self._grid_container = QWidget(self)
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_container.setMinimumWidth(0)
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(self._padding)
        p = self._padding
        self._grid_layout.setContentsMargins(p, p, p, p)
        for col in range(self._columns):
            self._grid_layout.setColumnStretch(col, 1)
        outer.addWidget(self._grid_container, stretch=1)

    @property
    def tiles(self) -> list[TileWidget]:
        return list(self._tiles)

    @property
    def page_index(self) -> int:
        return self._page_index

    @property
    def total_pages(self) -> int:
        if not self._items:
            return 1
        return max(1, math.ceil(len(self._items) / self._items_per_page))

    def set_items(self, items: Sequence[tuple[str, QPixmap | None, object]]) -> None:
        """Set the full list of items and reset to page 0."""
        self._items = list(items)
        self._page_index = 0
        self._update_page()

    def _update_page(self) -> None:
        """Show only items for the current page."""
        # Clear existing tiles
        for tile in self._tiles:
            tile.clicked.disconnect()
            self._grid_layout.removeWidget(tile)
            tile.deleteLater()
        self._tiles.clear()

        start = self._page_index * self._items_per_page
        end = start + self._items_per_page
        page_items = self._items[start:end]

        for i, (name, icon, tile_data) in enumerate(page_items):
            tile = TileWidget(
                name=name,
                icon=icon,
                bg_color=self._bg_color,
                text_color=self._text_color,
                icon_size=self._icon_size,
                font_size=self._font_size,
                padding=self._padding,
                tile_data=tile_data,
                show_text=self._show_text,
            )
            row = i // self._columns
            col = i % self._columns
            self._grid_layout.addWidget(tile, row, col)
            tile.clicked.connect(lambda td=tile_data: self.tile_activated.emit(td))
            self._tiles.append(tile)

        # Update label with page info
        total = self.total_pages
        self._label_widget.setText(f"{self._label} ({self._page_index + 1}/{total})")

        overlay = self.window()
        if overlay is not None:
            logger.info(
                "%s page %d/%d: overlay width=%d",
                self._label, self._page_index + 1, total, overlay.width(),
            )

        # Log tile sizes after layout pass completes
        QTimer.singleShot(0, self._log_tile_sizes)

    def _log_tile_sizes(self) -> None:
        """Log actual tile dimensions after the layout pass."""
        for i, tile in enumerate(self._tiles):
            logger.info(
                "%s tile[%d] %r: size=%dx%d pos=(%d, %d)",
                self._label, i, tile.tile_name,
                tile.width(), tile.height(),
                tile.x(), tile.y(),
            )

    def highlight_tile_by_data(self, tile_data: object) -> None:
        """Highlight the tile whose tile_data matches, unhighlight all others."""
        for tile in self._tiles:
            tile.set_highlighted(tile.tile_data == tile_data)

    def go_to_page(self, page: int) -> None:
        """Navigate to a specific page (clamped to valid range)."""
        total = self.total_pages
        clamped = max(0, min(page, total - 1))
        if clamped != self._page_index:
            self._page_index = clamped
            self._update_page()

    def _go_prev(self) -> None:
        """Navigate to previous page, wrapping around."""
        total = self.total_pages
        self._page_index = (self._page_index - 1) % total
        self._update_page()

    def _go_next(self) -> None:
        """Navigate to next page, wrapping around."""
        total = self.total_pages
        self._page_index = (self._page_index + 1) % total
        self._update_page()

    @property
    def is_collapsed(self) -> bool:
        return self._collapsed

    def _toggle_collapse(self) -> None:
        """Toggle collapse state — hide/show the tile grid and header widgets."""
        self._collapsed = not self._collapsed
        visible = not self._collapsed
        self._grid_container.setVisible(visible)
        # Hide all header widgets except the collapse button itself
        for w in [self._prev_btn, self._next_btn, self._label_widget]:
            w.setVisible(visible)
        if hasattr(self, "_prev_win_btn"):
            self._prev_win_btn.setVisible(visible)
        if hasattr(self, "_next_win_btn"):
            self._next_win_btn.setVisible(visible)
        if self._collapsible:
            self._collapse_btn.setText("^" if self._collapsed else "v")
        self.collapse_toggled.emit(self._collapsed)
