"""JSON config file load/save/validate for MRCI."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mrci.config.defaults import default_config
from mrci.config.schema import AppConfig, CustomTile, GeneralConfig, TriggerConfig
from mrci.constants import CONFIG_VERSION, DEFAULT_CONFIG_FILE

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages loading, saving, and validating MRCI configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        if config_path is None:
            # Default: config.json next to the package (i.e. project root)
            config_path = Path(__file__).resolve().parent.parent.parent.parent / DEFAULT_CONFIG_FILE
        self._config_path = config_path
        self._config_dir = config_path.parent
        self._config: AppConfig = default_config()

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> AppConfig:
        """Load config from disk. Returns default config if file doesn't exist or is invalid."""
        if not self._config_path.exists():
            logger.info("No config file found at %s, using defaults", self._config_path)
            self._config = default_config()
            return self._config

        try:
            raw = json.loads(self._config_path.read_text(encoding="utf-8"))
            self._config = self._parse(raw)
            logger.info("Loaded config from %s", self._config_path)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning("Invalid config file at %s: %s — using defaults", self._config_path, e)
            self._config = default_config()

        return self._config

    def save(self, config: AppConfig | None = None) -> None:
        """Save config to disk."""
        if config is not None:
            self._config = config

        self._config_dir.mkdir(parents=True, exist_ok=True)
        data = asdict(self._config)
        self._config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Saved config to %s", self._config_path)

    def _parse(self, raw: dict[str, Any]) -> AppConfig:
        """Parse a raw dictionary into an AppConfig, applying defaults for missing fields."""
        version = raw.get("version", CONFIG_VERSION)

        triggers: list[TriggerConfig] = []
        for t in raw.get("triggers", []):
            custom_tiles = [
                CustomTile(
                    name=ct["name"],
                    key_sequence=ct["key_sequence"],
                    icon_path=ct.get("icon_path", ""),
                )
                for ct in t.get("custom_tiles", [])
            ]
            triggers.append(
                TriggerConfig(
                    name=t["name"],
                    aspect_ratio_min=float(t["aspect_ratio_min"]),
                    aspect_ratio_max=float(t["aspect_ratio_max"]),
                    top_region_percent=int(t.get("top_region_percent", 40)),
                    tile_background_color=t.get("tile_background_color", "#0078D4"),
                    tile_text_color=t.get("tile_text_color", "#FFFFFF"),
                    tile_columns=int(t.get("tile_columns", 3)),
                    tile_rows=int(t.get("tile_rows", 4)),
                    max_app_tiles=int(t.get("max_app_tiles", 4)),
                    max_shortcut_tiles=int(t.get("max_shortcut_tiles", 4)),
                    custom_tiles=custom_tiles,
                )
            )

        g = raw.get("general", {})
        general = GeneralConfig(
            config_hotkey=g.get("config_hotkey", "ctrl+shift+f12"),
            nav_button_size=int(g.get("nav_button_size", 60)),
            tile_padding=int(g.get("tile_padding", 4)),
            icon_size=int(g.get("icon_size", 48)),
            font_size=int(g.get("font_size", 12)),
            show_tile_text=bool(g.get("show_tile_text", False)),
            restore_windows_on_hide=bool(g.get("restore_windows_on_hide", True)),
        )

        return AppConfig(version=version, triggers=triggers, general=general)
