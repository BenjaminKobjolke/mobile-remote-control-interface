"""Tests for ConfigManager."""

from __future__ import annotations

import json
from pathlib import Path

from mrci.config.manager import ConfigManager
from mrci.config.schema import AppConfig, CustomTile, TriggerConfig


class TestConfigManagerLoad:
    def test_load_returns_defaults_when_no_file(self, tmp_config_file: Path) -> None:
        mgr = ConfigManager(config_path=tmp_config_file)
        config = mgr.load()
        assert config.version == 1
        assert len(config.triggers) == 1
        assert config.triggers[0].name == "Phone Portrait"

    def test_load_from_file(self, written_config_file: Path) -> None:
        mgr = ConfigManager(config_path=written_config_file)
        config = mgr.load()
        assert config.version == 1
        assert len(config.triggers) == 1
        assert config.triggers[0].name == "Phone Portrait"
        assert len(config.triggers[0].custom_tiles) == 2
        assert config.triggers[0].custom_tiles[0].name == "Copy"

    def test_load_invalid_json_returns_defaults(self, tmp_config_file: Path) -> None:
        tmp_config_file.write_text("not valid json {{{", encoding="utf-8")
        mgr = ConfigManager(config_path=tmp_config_file)
        config = mgr.load()
        assert config.version == 1
        assert len(config.triggers) == 1

    def test_load_partial_config_fills_defaults(self, tmp_config_file: Path) -> None:
        partial = {
            "version": 1,
            "triggers": [
                {
                    "name": "Custom",
                    "aspect_ratio_min": 0.3,
                    "aspect_ratio_max": 0.7,
                }
            ],
        }
        tmp_config_file.write_text(json.dumps(partial), encoding="utf-8")
        mgr = ConfigManager(config_path=tmp_config_file)
        config = mgr.load()
        assert config.triggers[0].name == "Custom"
        assert config.triggers[0].top_region_percent == 40
        assert config.triggers[0].max_app_tiles == 4
        assert config.triggers[0].max_shortcut_tiles == 4
        assert config.general.config_hotkey == "ctrl+shift+f12"
        assert config.general.show_tile_text is False


class TestConfigManagerSave:
    def test_save_creates_file(self, tmp_config_file: Path) -> None:
        mgr = ConfigManager(config_path=tmp_config_file)
        mgr.load()
        mgr.save()
        assert tmp_config_file.exists()
        data = json.loads(tmp_config_file.read_text(encoding="utf-8"))
        assert data["version"] == 1

    def test_save_with_explicit_config(self, tmp_config_file: Path) -> None:
        mgr = ConfigManager(config_path=tmp_config_file)
        custom_config = AppConfig(
            version=1,
            triggers=[
                TriggerConfig(
                    name="Tablet",
                    aspect_ratio_min=0.6,
                    aspect_ratio_max=0.8,
                    custom_tiles=[CustomTile(name="Undo", key_sequence="ctrl+z")],
                )
            ],
        )
        mgr.save(custom_config)
        assert mgr.config.triggers[0].name == "Tablet"

        # Verify file content
        data = json.loads(tmp_config_file.read_text(encoding="utf-8"))
        assert data["triggers"][0]["name"] == "Tablet"
        assert data["triggers"][0]["custom_tiles"][0]["key_sequence"] == "ctrl+z"

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        config_path = tmp_path / "nested" / "deep" / "config.json"
        mgr = ConfigManager(config_path=config_path)
        mgr.save()
        assert config_path.exists()

    def test_round_trip(self, tmp_config_file: Path) -> None:
        mgr = ConfigManager(config_path=tmp_config_file)
        mgr.load()
        mgr.save()

        mgr2 = ConfigManager(config_path=tmp_config_file)
        config2 = mgr2.load()
        assert config2.version == mgr.config.version
        assert len(config2.triggers) == len(mgr.config.triggers)
        assert config2.triggers[0].name == mgr.config.triggers[0].name
        assert config2.general.config_hotkey == mgr.config.general.config_hotkey
