"""Shared test fixtures for MRCI tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mrci.config.defaults import default_config
from mrci.config.schema import AppConfig


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Provide a temporary config directory."""
    config_dir = tmp_path / ".mrci"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def tmp_config_file(tmp_config_dir: Path) -> Path:
    """Provide a path to a temporary config file (not yet created)."""
    return tmp_config_dir / "config.json"


@pytest.fixture
def sample_config() -> AppConfig:
    """Provide a default AppConfig instance."""
    return default_config()


@pytest.fixture
def sample_config_dict() -> dict[str, Any]:
    """Provide a sample config as a raw dictionary."""
    return {
        "version": 1,
        "triggers": [
            {
                "name": "Phone Portrait",
                "aspect_ratio_min": 0.4,
                "aspect_ratio_max": 0.65,
                "top_region_percent": 40,
                "tile_background_color": "#0078D4",
                "tile_text_color": "#FFFFFF",
                "tile_columns": 3,
                "tile_rows": 4,
                "max_app_tiles": 4,
                "max_shortcut_tiles": 4,
                "custom_tiles": [
                    {"name": "Copy", "icon_path": "", "key_sequence": "ctrl+c"},
                    {"name": "Paste", "icon_path": "", "key_sequence": "ctrl+v"},
                ],
            }
        ],
        "general": {
            "config_hotkey": "ctrl+shift+f12",
            "nav_button_size": 60,
            "tile_padding": 4,
            "icon_size": 48,
            "font_size": 12,
            "show_tile_text": False,
            "restore_windows_on_hide": True,
        },
    }


@pytest.fixture
def written_config_file(tmp_config_file: Path, sample_config_dict: dict[str, Any]) -> Path:
    """Write sample config to a temp file and return the path."""
    tmp_config_file.write_text(json.dumps(sample_config_dict, indent=2), encoding="utf-8")
    return tmp_config_file
