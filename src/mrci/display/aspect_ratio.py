"""Pure functions for aspect ratio computation and trigger matching."""

from __future__ import annotations

from mrci.config.schema import ScreenGeometry, TriggerConfig


def compute_aspect_ratio(width: int, height: int) -> float:
    """Compute width/height aspect ratio. Returns 0.0 if height is 0."""
    if height == 0:
        return 0.0
    return width / height


def is_portrait(width: int, height: int) -> bool:
    """Return True if the aspect ratio indicates portrait orientation (< 1.0)."""
    return compute_aspect_ratio(width, height) < 1.0


def match_trigger(
    geometry: ScreenGeometry,
    triggers: list[TriggerConfig],
) -> TriggerConfig | None:
    """Find the first trigger whose aspect ratio range matches the screen geometry.

    Returns None if no trigger matches.
    """
    ratio = geometry.aspect_ratio
    for trigger in triggers:
        if trigger.aspect_ratio_min <= ratio <= trigger.aspect_ratio_max:
            return trigger
    return None
