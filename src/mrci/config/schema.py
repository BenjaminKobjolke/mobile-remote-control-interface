"""Configuration dataclasses for MRCI."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CustomTile:
    """A user-defined shortcut tile."""

    name: str
    key_sequence: str
    icon_path: str = ""


@dataclass
class TriggerConfig:
    """Configuration for a display aspect-ratio trigger."""

    name: str
    aspect_ratio_min: float
    aspect_ratio_max: float
    top_region_percent: int = 40
    app_area_percent: int = 30
    tile_background_color: str = "#0078D4"
    tile_text_color: str = "#FFFFFF"
    tile_columns: int = 3
    tile_rows: int = 4
    max_app_tiles: int = 4
    max_shortcut_tiles: int = 4
    custom_tiles: list[CustomTile] = field(default_factory=list)


@dataclass
class GeneralConfig:
    """General application settings."""

    config_hotkey: str = "ctrl+shift+f12"
    nav_button_size: int = 60
    tile_padding: int = 4
    icon_size: int = 48
    font_size: int = 12
    max_title_length: int = 10
    show_tile_text: bool = False
    restore_windows_on_hide: bool = True


@dataclass
class AppConfig:
    """Root configuration object."""

    version: int = 1
    triggers: list[TriggerConfig] = field(default_factory=list)
    general: GeneralConfig = field(default_factory=GeneralConfig)


@dataclass
class WindowInfo:
    """Runtime DTO for an enumerated window."""

    hwnd: int
    title: str
    process_name: str
    process_id: int
    icon: object | None = None  # QPixmap at runtime
    last_active_time: float = 0.0


@dataclass
class ScreenGeometry:
    """Runtime DTO for current screen dimensions."""

    width: int
    height: int

    @property
    def aspect_ratio(self) -> float:
        if self.height == 0:
            return 0.0
        return self.width / self.height
