"""Tests for TileWidget and PaginatedTileSection."""

from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtGui import QPixmap

from mrci.overlay.paginated_section import PaginatedTileSection
from mrci.overlay.tile_widget import TileWidget


class TestTileWidget:
    def test_create_tile(self, qtbot: object) -> None:
        tile = TileWidget(name="Test App")
        assert tile.tile_name == "Test App"
        assert tile.tile_data is None

    def test_tile_data_hwnd(self, qtbot: object) -> None:
        tile = TileWidget(name="App", tile_data=12345)
        assert tile.tile_data == 12345

    def test_tile_data_key_sequence(self, qtbot: object) -> None:
        tile = TileWidget(name="Shortcut", tile_data="ctrl+c")
        assert tile.tile_data == "ctrl+c"

    def test_click_emits_signal(self, qtbot: object) -> None:
        tile = TileWidget(name="Test")
        callback = MagicMock()
        tile.clicked.connect(callback)
        tile.mousePressEvent(None)
        callback.assert_called_once()

    def test_tile_with_custom_colors(self, qtbot: object) -> None:
        tile = TileWidget(
            name="Custom",
            bg_color="#FF0000",
            text_color="#00FF00",
        )
        assert tile.tile_name == "Custom"

    def test_show_text_false_hides_label(self, qtbot: object) -> None:
        tile = TileWidget(name="Hidden", show_text=False)
        assert tile._name_label.isHidden()

    def test_show_text_true_shows_label(self, qtbot: object) -> None:
        tile = TileWidget(name="Visible", show_text=True)
        assert not tile._name_label.isHidden()

    def test_set_icon(self, qtbot: object) -> None:
        tile = TileWidget(name="Test")
        pixmap = QPixmap(48, 48)
        tile.set_icon(pixmap)


class TestPaginatedTileSection:
    def test_set_items(self, qtbot: object) -> None:
        section = PaginatedTileSection(label="Apps", items_per_page=4)
        section.set_items([
            ("App 1", None, 100),
            ("App 2", None, 200),
        ])
        assert len(section.tiles) == 2
        assert section.page_index == 0
        assert section.total_pages == 1

    def test_pagination(self, qtbot: object) -> None:
        section = PaginatedTileSection(label="Apps", items_per_page=2)
        section.set_items([
            ("App 1", None, 1),
            ("App 2", None, 2),
            ("App 3", None, 3),
            ("App 4", None, 4),
            ("App 5", None, 5),
        ])
        assert section.total_pages == 3
        assert section.page_index == 0
        assert len(section.tiles) == 2

        # Go to next page
        section._go_next()
        assert section.page_index == 1
        assert len(section.tiles) == 2

        # Go to last page (1 item)
        section._go_next()
        assert section.page_index == 2
        assert len(section.tiles) == 1

        # Wrap around
        section._go_next()
        assert section.page_index == 0

    def test_prev_wraps(self, qtbot: object) -> None:
        section = PaginatedTileSection(label="Apps", items_per_page=2)
        section.set_items([
            ("App 1", None, 1),
            ("App 2", None, 2),
            ("App 3", None, 3),
        ])
        assert section.page_index == 0
        # Go prev from first page wraps to last
        section._go_prev()
        assert section.page_index == 1

    def test_tile_activated_signal(self, qtbot: object) -> None:
        section = PaginatedTileSection(label="Apps", items_per_page=4)
        section.set_items([
            ("App 1", None, 100),
            ("App 2", None, 200),
        ])
        callback = MagicMock()
        section.tile_activated.connect(callback)
        # Click second tile
        section.tiles[1].mousePressEvent(None)
        callback.assert_called_once_with(200)

    def test_empty_items(self, qtbot: object) -> None:
        section = PaginatedTileSection(label="Empty", items_per_page=4)
        section.set_items([])
        assert len(section.tiles) == 0
        assert section.total_pages == 1

    def test_set_items_resets_page(self, qtbot: object) -> None:
        section = PaginatedTileSection(label="Apps", items_per_page=2)
        section.set_items([
            ("App 1", None, 1),
            ("App 2", None, 2),
            ("App 3", None, 3),
        ])
        section._go_next()
        assert section.page_index == 1

        # Setting new items resets to page 0
        section.set_items([("New", None, 99)])
        assert section.page_index == 0
