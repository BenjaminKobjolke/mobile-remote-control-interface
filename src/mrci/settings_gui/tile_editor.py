"""Custom shortcut tile configuration editor."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mrci.config.schema import CustomTile


class TileEditorRow(QWidget):
    """Editor for a single custom tile."""

    changed = Signal()
    remove_requested = Signal()

    def __init__(self, tile: CustomTile, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._name_edit = QLineEdit(tile.name)
        self._name_edit.setPlaceholderText("Tile Name")
        self._name_edit.textChanged.connect(self.changed.emit)
        layout.addWidget(self._name_edit)

        self._key_edit = QLineEdit(tile.key_sequence)
        self._key_edit.setPlaceholderText("Key Sequence (e.g. ctrl+c)")
        self._key_edit.textChanged.connect(self.changed.emit)
        layout.addWidget(self._key_edit)

        self._icon_edit = QLineEdit(tile.icon_path)
        self._icon_edit.setPlaceholderText("Icon Path (optional)")
        self._icon_edit.textChanged.connect(self.changed.emit)
        layout.addWidget(self._icon_edit)

        remove_btn = QPushButton("X")
        remove_btn.setFixedWidth(30)
        remove_btn.setStyleSheet("color: red;")
        remove_btn.clicked.connect(self.remove_requested.emit)
        layout.addWidget(remove_btn)

    def get_tile(self) -> CustomTile:
        return CustomTile(
            name=self._name_edit.text(),
            key_sequence=self._key_edit.text(),
            icon_path=self._icon_edit.text(),
        )


class TileEditor(QGroupBox):
    """Editor for a list of custom shortcut tiles."""

    changed = Signal()

    def __init__(
        self,
        tiles: list[CustomTile],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Custom Shortcut Tiles", parent)
        self._rows: list[TileEditorRow] = []

        self._layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("Name"))
        header.addWidget(QLabel("Key Sequence"))
        header.addWidget(QLabel("Icon Path"))
        header.addWidget(QLabel(""))  # spacer for remove button
        self._layout.addLayout(header)

        # Tile rows container
        self._rows_container = QVBoxLayout()
        self._layout.addLayout(self._rows_container)

        for tile in tiles:
            self._add_row(tile)

        # Add button
        add_btn = QPushButton("+ Add Shortcut Tile")
        add_btn.clicked.connect(self._add_empty_row)
        self._layout.addWidget(add_btn)

    def _add_row(self, tile: CustomTile) -> None:
        row = TileEditorRow(tile)
        row.changed.connect(self.changed.emit)
        row.remove_requested.connect(lambda r=row: self._remove_row(r))
        self._rows_container.addWidget(row)
        self._rows.append(row)

    def _add_empty_row(self) -> None:
        self._add_row(CustomTile(name="", key_sequence=""))
        self.changed.emit()

    def _remove_row(self, row: TileEditorRow) -> None:
        self._rows_container.removeWidget(row)
        self._rows.remove(row)
        row.deleteLater()
        self.changed.emit()

    def get_tiles(self) -> list[CustomTile]:
        return [row.get_tile() for row in self._rows]
