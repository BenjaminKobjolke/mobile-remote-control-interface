"""Trigger configuration editor widget."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from mrci.config.schema import TriggerConfig
from mrci.settings_gui.color_picker import pick_color


class TriggerEditor(QGroupBox):
    """Editor widget for a single TriggerConfig."""

    changed = Signal()
    remove_requested = Signal()

    def __init__(
        self,
        trigger: TriggerConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(trigger.name, parent)
        self._trigger = trigger
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        # Name
        self._name_edit = QLineEdit(self._trigger.name)
        self._name_edit.textChanged.connect(self._on_changed)
        layout.addRow("Name:", self._name_edit)

        # Aspect ratio range
        ratio_layout = QHBoxLayout()
        self._ratio_min = QDoubleSpinBox()
        self._ratio_min.setRange(0.1, 3.0)
        self._ratio_min.setSingleStep(0.05)
        self._ratio_min.setValue(self._trigger.aspect_ratio_min)
        self._ratio_min.valueChanged.connect(self._on_changed)
        ratio_layout.addWidget(QLabel("Min:"))
        ratio_layout.addWidget(self._ratio_min)

        self._ratio_max = QDoubleSpinBox()
        self._ratio_max.setRange(0.1, 3.0)
        self._ratio_max.setSingleStep(0.05)
        self._ratio_max.setValue(self._trigger.aspect_ratio_max)
        self._ratio_max.valueChanged.connect(self._on_changed)
        ratio_layout.addWidget(QLabel("Max:"))
        ratio_layout.addWidget(self._ratio_max)
        layout.addRow("Aspect Ratio:", ratio_layout)

        # Top region percent
        self._top_percent = QSpinBox()
        self._top_percent.setRange(10, 90)
        self._top_percent.setValue(self._trigger.top_region_percent)
        self._top_percent.valueChanged.connect(self._on_changed)
        layout.addRow("Top Region %:", self._top_percent)

        # Grid dimensions
        grid_layout = QHBoxLayout()
        self._columns = QSpinBox()
        self._columns.setRange(1, 10)
        self._columns.setValue(self._trigger.tile_columns)
        self._columns.valueChanged.connect(self._on_changed)
        grid_layout.addWidget(QLabel("Columns:"))
        grid_layout.addWidget(self._columns)

        self._rows = QSpinBox()
        self._rows.setRange(1, 20)
        self._rows.setValue(self._trigger.tile_rows)
        self._rows.valueChanged.connect(self._on_changed)
        grid_layout.addWidget(QLabel("Rows:"))
        grid_layout.addWidget(self._rows)
        layout.addRow("Grid:", grid_layout)

        # Max tiles per page
        tiles_layout = QHBoxLayout()
        self._max_app_tiles = QSpinBox()
        self._max_app_tiles.setRange(1, 20)
        self._max_app_tiles.setValue(self._trigger.max_app_tiles)
        self._max_app_tiles.valueChanged.connect(self._on_changed)
        tiles_layout.addWidget(QLabel("App Tiles:"))
        tiles_layout.addWidget(self._max_app_tiles)

        self._max_shortcut_tiles = QSpinBox()
        self._max_shortcut_tiles.setRange(1, 20)
        self._max_shortcut_tiles.setValue(self._trigger.max_shortcut_tiles)
        self._max_shortcut_tiles.valueChanged.connect(self._on_changed)
        tiles_layout.addWidget(QLabel("Shortcut Tiles:"))
        tiles_layout.addWidget(self._max_shortcut_tiles)
        layout.addRow("Max per page:", tiles_layout)

        # Colors
        color_layout = QHBoxLayout()
        self._bg_color_btn = QPushButton(self._trigger.tile_background_color)
        self._bg_color_btn.setStyleSheet(
            f"background-color: {self._trigger.tile_background_color}; color: white;"
        )
        self._bg_color_btn.clicked.connect(self._pick_bg_color)
        color_layout.addWidget(QLabel("Background:"))
        color_layout.addWidget(self._bg_color_btn)

        self._text_color_btn = QPushButton(self._trigger.tile_text_color)
        self._text_color_btn.setStyleSheet(
            f"background-color: {self._trigger.tile_text_color}; color: black;"
        )
        self._text_color_btn.clicked.connect(self._pick_text_color)
        color_layout.addWidget(QLabel("Text:"))
        color_layout.addWidget(self._text_color_btn)
        layout.addRow("Colors:", color_layout)

        # Remove button
        self._remove_btn = QPushButton("Remove Trigger")
        self._remove_btn.setStyleSheet("color: red;")
        self._remove_btn.clicked.connect(self.remove_requested.emit)
        layout.addRow("", self._remove_btn)

    def get_trigger(self) -> TriggerConfig:
        """Get the current trigger config from the editor."""
        return TriggerConfig(
            name=self._name_edit.text(),
            aspect_ratio_min=self._ratio_min.value(),
            aspect_ratio_max=self._ratio_max.value(),
            top_region_percent=self._top_percent.value(),
            tile_background_color=self._bg_color_btn.text(),
            tile_text_color=self._text_color_btn.text(),
            tile_columns=self._columns.value(),
            tile_rows=self._rows.value(),
            max_app_tiles=self._max_app_tiles.value(),
            max_shortcut_tiles=self._max_shortcut_tiles.value(),
            custom_tiles=self._trigger.custom_tiles,  # managed by tile editor
        )

    def _pick_bg_color(self) -> None:
        color = pick_color(self._bg_color_btn.text(), self)
        if color:
            self._bg_color_btn.setText(color)
            self._bg_color_btn.setStyleSheet(f"background-color: {color}; color: white;")
            self._on_changed()

    def _pick_text_color(self) -> None:
        color = pick_color(self._text_color_btn.text(), self)
        if color:
            self._text_color_btn.setText(color)
            self._text_color_btn.setStyleSheet(f"background-color: {color}; color: black;")
            self._on_changed()

    def _on_changed(self) -> None:
        self.setTitle(self._name_edit.text())
        self.changed.emit()
