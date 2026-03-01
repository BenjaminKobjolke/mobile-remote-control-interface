"""QColorDialog wrapper for picking tile colors."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QWidget


def pick_color(current_color: str, parent: QWidget | None = None) -> str | None:
    """Open a color picker dialog.

    Returns the selected color as a hex string, or None if cancelled.
    """
    color = QColorDialog.getColor(QColor(current_color), parent, "Pick a Color")
    if color.isValid():
        return color.name()
    return None
