"""Tests for config schema dataclasses."""

from __future__ import annotations

from mrci.config.schema import (
    AppConfig,
    CustomTile,
    GeneralConfig,
    ScreenGeometry,
    TriggerConfig,
    WindowInfo,
)


class TestCustomTile:
    def test_defaults(self) -> None:
        tile = CustomTile(name="Copy", key_sequence="ctrl+c")
        assert tile.name == "Copy"
        assert tile.key_sequence == "ctrl+c"
        assert tile.icon_path == ""

    def test_with_icon_path(self) -> None:
        tile = CustomTile(name="Save", key_sequence="ctrl+s", icon_path="C:/icon.png")
        assert tile.icon_path == "C:/icon.png"


class TestTriggerConfig:
    def test_defaults(self) -> None:
        trigger = TriggerConfig(name="Test", aspect_ratio_min=0.4, aspect_ratio_max=0.65)
        assert trigger.top_region_percent == 40
        assert trigger.tile_background_color == "#0078D4"
        assert trigger.tile_text_color == "#FFFFFF"
        assert trigger.tile_columns == 3
        assert trigger.tile_rows == 4
        assert trigger.max_app_tiles == 4
        assert trigger.max_shortcut_tiles == 4
        assert trigger.custom_tiles == []

    def test_with_custom_tiles(self) -> None:
        tiles = [CustomTile(name="Copy", key_sequence="ctrl+c")]
        trigger = TriggerConfig(
            name="Test",
            aspect_ratio_min=0.4,
            aspect_ratio_max=0.65,
            custom_tiles=tiles,
        )
        assert len(trigger.custom_tiles) == 1
        assert trigger.custom_tiles[0].name == "Copy"


class TestGeneralConfig:
    def test_defaults(self) -> None:
        config = GeneralConfig()
        assert config.config_hotkey == "ctrl+shift+f12"
        assert config.nav_button_size == 60
        assert config.tile_padding == 4
        assert config.icon_size == 48
        assert config.font_size == 12
        assert config.show_tile_text is False
        assert config.restore_windows_on_hide is True


class TestAppConfig:
    def test_defaults(self) -> None:
        config = AppConfig()
        assert config.version == 1
        assert config.triggers == []
        assert isinstance(config.general, GeneralConfig)

    def test_with_triggers(self) -> None:
        trigger = TriggerConfig(name="Test", aspect_ratio_min=0.4, aspect_ratio_max=0.65)
        config = AppConfig(triggers=[trigger])
        assert len(config.triggers) == 1


class TestScreenGeometry:
    def test_landscape(self) -> None:
        geo = ScreenGeometry(width=1920, height=1080)
        assert abs(geo.aspect_ratio - 1920 / 1080) < 0.001

    def test_portrait(self) -> None:
        geo = ScreenGeometry(width=1080, height=1920)
        assert abs(geo.aspect_ratio - 1080 / 1920) < 0.001

    def test_zero_height(self) -> None:
        geo = ScreenGeometry(width=1920, height=0)
        assert geo.aspect_ratio == 0.0


class TestWindowInfo:
    def test_defaults(self) -> None:
        info = WindowInfo(hwnd=123, title="Test", process_name="test.exe", process_id=456)
        assert info.hwnd == 123
        assert info.icon is None
        assert info.last_active_time == 0.0
