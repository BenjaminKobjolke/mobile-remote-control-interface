"""Default configuration values for MRCI."""

from __future__ import annotations

from mrci.config.schema import AppConfig, CustomTile, GeneralConfig, TriggerConfig
from mrci.constants import (
    CONFIG_VERSION,
    DEFAULT_CONFIG_HOTKEY,
    DEFAULT_FONT_SIZE,
    DEFAULT_ICON_SIZE,
    DEFAULT_MAX_APP_TILES,
    DEFAULT_MAX_SHORTCUT_TILES,
    DEFAULT_NAV_BUTTON_SIZE,
    DEFAULT_TILE_BG_COLOR,
    DEFAULT_TILE_COLUMNS,
    DEFAULT_TILE_PADDING,
    DEFAULT_TILE_ROWS,
    DEFAULT_TILE_TEXT_COLOR,
    DEFAULT_TOP_REGION_PERCENT,
)


def default_trigger() -> TriggerConfig:
    """Create the default 'Phone Portrait' trigger."""
    return TriggerConfig(
        name="Phone Portrait",
        aspect_ratio_min=0.4,
        aspect_ratio_max=0.65,
        top_region_percent=DEFAULT_TOP_REGION_PERCENT,
        tile_background_color=DEFAULT_TILE_BG_COLOR,
        tile_text_color=DEFAULT_TILE_TEXT_COLOR,
        tile_columns=DEFAULT_TILE_COLUMNS,
        tile_rows=DEFAULT_TILE_ROWS,
        max_app_tiles=DEFAULT_MAX_APP_TILES,
        max_shortcut_tiles=DEFAULT_MAX_SHORTCUT_TILES,
        custom_tiles=[
            CustomTile(name="Copy", key_sequence="ctrl+c"),
            CustomTile(name="Paste", key_sequence="ctrl+v"),
        ],
    )


def default_general() -> GeneralConfig:
    """Create the default general config."""
    return GeneralConfig(
        config_hotkey=DEFAULT_CONFIG_HOTKEY,
        nav_button_size=DEFAULT_NAV_BUTTON_SIZE,
        tile_padding=DEFAULT_TILE_PADDING,
        icon_size=DEFAULT_ICON_SIZE,
        font_size=DEFAULT_FONT_SIZE,
        show_tile_text=False,
        restore_windows_on_hide=True,
    )


def default_config() -> AppConfig:
    """Create a complete default AppConfig."""
    return AppConfig(
        version=CONFIG_VERSION,
        triggers=[default_trigger()],
        general=default_general(),
    )
