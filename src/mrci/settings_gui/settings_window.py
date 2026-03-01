"""Full-screen settings dialog with tabs for MRCI configuration."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from mrci.config.manager import ConfigManager
from mrci.config.schema import TriggerConfig
from mrci.settings_gui.tile_editor import TileEditor
from mrci.settings_gui.trigger_editor import TriggerEditor

logger = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    """Full-screen settings dialog for MRCI."""

    config_saved = Signal()

    def __init__(
        self,
        config_manager: ConfigManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config_manager = config_manager
        self.setWindowTitle("MRCI Settings")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.showMaximized()

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Triggers tab
        triggers_tab = self._create_triggers_tab()
        tabs.addTab(triggers_tab, "Triggers")

        # General tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(120)
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(120)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        main_layout.addLayout(button_layout)

    def _create_triggers_tab(self) -> QWidget:
        """Create the triggers configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self._triggers_layout = QVBoxLayout(scroll_widget)

        self._trigger_editors: list[TriggerEditor] = []
        self._tile_editors: list[TileEditor] = []

        for trigger in self._config_manager.config.triggers:
            self._add_trigger_editor(trigger)

        self._triggers_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Add trigger button
        add_btn = QPushButton("+ Add Trigger")
        add_btn.clicked.connect(self._add_new_trigger)
        layout.addWidget(add_btn)

        return widget

    def _add_trigger_editor(self, trigger: TriggerConfig) -> None:
        """Add a trigger editor + tile editor pair."""
        editor = TriggerEditor(trigger)
        editor.remove_requested.connect(lambda e=editor: self._remove_trigger(e))
        self._triggers_layout.addWidget(editor)
        self._trigger_editors.append(editor)

        tile_editor = TileEditor(trigger.custom_tiles)
        self._triggers_layout.addWidget(tile_editor)
        self._tile_editors.append(tile_editor)

    def _add_new_trigger(self) -> None:
        """Add a new blank trigger."""
        trigger = TriggerConfig(
            name="New Trigger",
            aspect_ratio_min=0.4,
            aspect_ratio_max=0.65,
        )
        self._add_trigger_editor(trigger)

    def _remove_trigger(self, editor: TriggerEditor) -> None:
        """Remove a trigger editor and its tile editor."""
        idx = self._trigger_editors.index(editor)

        self._triggers_layout.removeWidget(editor)
        editor.deleteLater()
        self._trigger_editors.pop(idx)

        tile_editor = self._tile_editors.pop(idx)
        self._triggers_layout.removeWidget(tile_editor)
        tile_editor.deleteLater()

    def _create_general_tab(self) -> QWidget:
        """Create the general settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        general = self._config_manager.config.general

        self._hotkey_edit = QLineEdit(general.config_hotkey)
        layout.addRow("Config Hotkey:", self._hotkey_edit)

        self._nav_size = QSpinBox()
        self._nav_size.setRange(20, 200)
        self._nav_size.setValue(general.nav_button_size)
        layout.addRow("Nav Button Size:", self._nav_size)

        self._tile_padding = QSpinBox()
        self._tile_padding.setRange(0, 20)
        self._tile_padding.setValue(general.tile_padding)
        layout.addRow("Tile Padding:", self._tile_padding)

        self._icon_size = QSpinBox()
        self._icon_size.setRange(16, 128)
        self._icon_size.setValue(general.icon_size)
        layout.addRow("Icon Size:", self._icon_size)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 32)
        self._font_size.setValue(general.font_size)
        layout.addRow("Font Size:", self._font_size)

        self._show_tile_text = QCheckBox("Show text labels on tiles")
        self._show_tile_text.setChecked(general.show_tile_text)
        layout.addRow("", self._show_tile_text)

        self._restore_windows = QCheckBox("Restore windows when overlay hides")
        self._restore_windows.setChecked(general.restore_windows_on_hide)
        layout.addRow("", self._restore_windows)

        return widget

    def _save(self) -> None:
        """Save settings and emit signal."""
        config = self._config_manager.config

        # Update triggers
        config.triggers.clear()
        for i, editor in enumerate(self._trigger_editors):
            trigger = editor.get_trigger()
            # Merge custom tiles from tile editor
            if i < len(self._tile_editors):
                trigger.custom_tiles = self._tile_editors[i].get_tiles()
            config.triggers.append(trigger)

        # Update general settings
        config.general.config_hotkey = self._hotkey_edit.text()
        config.general.nav_button_size = self._nav_size.value()
        config.general.tile_padding = self._tile_padding.value()
        config.general.icon_size = self._icon_size.value()
        config.general.font_size = self._font_size.value()
        config.general.show_tile_text = self._show_tile_text.isChecked()
        config.general.restore_windows_on_hide = self._restore_windows.isChecked()

        self._config_manager.save(config)
        self.config_saved.emit()
        logger.info("Settings saved")
        self.accept()
