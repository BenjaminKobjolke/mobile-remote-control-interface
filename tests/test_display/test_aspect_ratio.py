"""Tests for aspect ratio computation and trigger matching."""

from __future__ import annotations

from mrci.config.schema import ScreenGeometry, TriggerConfig
from mrci.display.aspect_ratio import compute_aspect_ratio, is_portrait, match_trigger


class TestComputeAspectRatio:
    def test_landscape(self) -> None:
        assert abs(compute_aspect_ratio(1920, 1080) - 1.778) < 0.01

    def test_portrait(self) -> None:
        assert abs(compute_aspect_ratio(1080, 1920) - 0.5625) < 0.01

    def test_square(self) -> None:
        assert compute_aspect_ratio(1000, 1000) == 1.0

    def test_zero_height(self) -> None:
        assert compute_aspect_ratio(1920, 0) == 0.0


class TestIsPortrait:
    def test_portrait(self) -> None:
        assert is_portrait(1080, 1920) is True

    def test_landscape(self) -> None:
        assert is_portrait(1920, 1080) is False

    def test_square_is_not_portrait(self) -> None:
        assert is_portrait(1000, 1000) is False


class TestMatchTrigger:
    def test_matches_first_trigger(self) -> None:
        triggers = [
            TriggerConfig(name="Phone", aspect_ratio_min=0.4, aspect_ratio_max=0.65),
            TriggerConfig(name="Tablet", aspect_ratio_min=0.65, aspect_ratio_max=0.85),
        ]
        geo = ScreenGeometry(width=1080, height=1920)  # ratio ≈ 0.5625
        result = match_trigger(geo, triggers)
        assert result is not None
        assert result.name == "Phone"

    def test_matches_second_trigger(self) -> None:
        triggers = [
            TriggerConfig(name="Phone", aspect_ratio_min=0.4, aspect_ratio_max=0.65),
            TriggerConfig(name="Tablet", aspect_ratio_min=0.65, aspect_ratio_max=0.85),
        ]
        geo = ScreenGeometry(width=768, height=1024)  # ratio = 0.75
        result = match_trigger(geo, triggers)
        assert result is not None
        assert result.name == "Tablet"

    def test_no_match(self) -> None:
        triggers = [
            TriggerConfig(name="Phone", aspect_ratio_min=0.4, aspect_ratio_max=0.65),
        ]
        geo = ScreenGeometry(width=1920, height=1080)  # ratio ≈ 1.778
        result = match_trigger(geo, triggers)
        assert result is None

    def test_boundary_inclusive(self) -> None:
        triggers = [
            TriggerConfig(name="Exact", aspect_ratio_min=0.5, aspect_ratio_max=0.5),
        ]
        geo = ScreenGeometry(width=500, height=1000)  # ratio = 0.5
        result = match_trigger(geo, triggers)
        assert result is not None
        assert result.name == "Exact"

    def test_empty_triggers(self) -> None:
        geo = ScreenGeometry(width=1080, height=1920)
        result = match_trigger(geo, [])
        assert result is None
