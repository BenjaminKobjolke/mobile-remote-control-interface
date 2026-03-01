"""Individual tile widget (icon + name, colored square)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class TileWidget(QFrame):
    """A single tile representing a running app or custom shortcut.

    Displays an icon and optionally a name. Emits `clicked` when tapped.
    Stores `tile_data` (hwnd int for apps, key_sequence str for shortcuts).
    """

    clicked = Signal()

    def __init__(
        self,
        name: str,
        icon: QPixmap | None = None,
        bg_color: str = "#0078D4",
        text_color: str = "#FFFFFF",
        icon_size: int = 48,
        font_size: int = 12,
        padding: int = 4,
        tile_data: object = None,
        show_text: bool = True,
        parent: QFrame | None = None,
    ) -> None:
        super().__init__(parent)
        self._name = name
        self._tile_data = tile_data
        self._bg_color = bg_color
        self._highlighted = False

        self.setStyleSheet(
            f"TileWidget {{ background-color: {bg_color};"
            f" border: 1px solid rgba(255,255,255,0.2); }}"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setMinimumWidth(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(2)

        # Icon
        self._icon_label = QLabel(self)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setFixedSize(icon_size, icon_size)
        if icon is not None:
            scaled = icon.scaled(
                icon_size,
                icon_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._icon_label.setPixmap(scaled)
        else:
            self._icon_label.setStyleSheet(
                "background-color: rgba(255,255,255,0.15); border-radius: 4px;"
            )
        layout.addWidget(
            self._icon_label, 0, Qt.AlignmentFlag.AlignHCenter,
        )

        # Name (optionally hidden)
        self._name_label = QLabel(name, self)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setWordWrap(True)
        font = QFont()
        font.setPixelSize(font_size)
        self._name_label.setFont(font)
        self._name_label.setStyleSheet(f"color: {text_color}; background: transparent;")
        self._name_label.setMinimumWidth(0)
        if not show_text:
            self._name_label.hide()
        layout.addWidget(self._name_label)

    @property
    def tile_name(self) -> str:
        return self._name

    @property
    def tile_data(self) -> object:
        return self._tile_data

    def set_icon(self, icon: QPixmap, icon_size: int = 48) -> None:
        """Update the tile icon."""
        scaled = icon.scaled(
            icon_size,
            icon_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._icon_label.setPixmap(scaled)

    def set_highlighted(self, highlighted: bool) -> None:
        """Apply or remove a visual highlight (bright border) on this tile."""
        self._highlighted = highlighted
        border = "3px solid #FFFFFF" if highlighted else "1px solid rgba(255,255,255,0.2)"
        self.setStyleSheet(
            f"TileWidget {{ background-color: {self._bg_color}; border: {border}; }}"
        )

    def mousePressEvent(self, event: object) -> None:
        """Emit clicked signal on mouse press."""
        self.clicked.emit()
