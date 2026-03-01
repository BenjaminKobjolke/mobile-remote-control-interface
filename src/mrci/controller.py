"""Main orchestrator that connects all MRCI components."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from mrci.config.manager import ConfigManager
from mrci.config.schema import TriggerConfig, WindowInfo
from mrci.display.monitor import DisplayMonitor
from mrci.overlay.overlay_window import OverlayWindow
from mrci.win32.icon_extractor import extract_icon
from mrci.win32.keyboard import send_key_sequence
from mrci.win32.mouse_hook import MouseHook
from mrci.win32.window_enum import enumerate_windows
from mrci.win32.window_manager import WindowManager

if TYPE_CHECKING:
    from mrci.app import MrciApplication

logger = logging.getLogger(__name__)

logger.info("Loading builtin shortcut icon mapping...")
_BUILTIN_SHORTCUT_ICONS: dict[str, QStyle.StandardPixmap] = {}
for _key, _attr in [
    ("up", "SP_ArrowUp"),
    ("down", "SP_ArrowDown"),
    ("left", "SP_ArrowLeft"),
    ("right", "SP_ArrowRight"),
    ("escape", "SP_BrowserStop"),
    ("enter", "SP_DialogApplyButton"),
    ("delete", "SP_TrashIcon"),
    ("backspace", "SP_ArrowBack"),
    ("home", "SP_DirHomeIcon"),
    ("tab", "SP_ArrowForward"),
]:
    sp = getattr(QStyle.StandardPixmap, _attr, None)
    if sp is not None:
        _BUILTIN_SHORTCUT_ICONS[_key] = sp
    else:
        logger.warning("QStyle.StandardPixmap.%s not available", _attr)
logger.info("Loaded %d builtin icons", len(_BUILTIN_SHORTCUT_ICONS))


def _get_shortcut_icon(key_sequence: str, icon_path: str, size: int) -> QPixmap | None:
    """Resolve a shortcut icon from custom path or built-in Qt icon."""
    if icon_path:
        px = QPixmap(icon_path)
        if not px.isNull():
            return px
    sp = _BUILTIN_SHORTCUT_ICONS.get(key_sequence)
    if sp is not None:
        style = QApplication.style()
        if style is not None:
            return style.standardIcon(sp).pixmap(size, size)
    return None


def _wrap_title(title: str, max_length: int) -> str:
    """Truncate a title to at most `max_length` characters with ellipsis."""
    if max_length <= 0 or len(title) <= max_length:
        return title
    return title[:max_length] + "..."


class Controller(QObject):
    """Main orchestrator connecting display detection, overlay, and window management."""

    def __init__(
        self,
        app: MrciApplication,
        config_path: Path | None = None,
        force_overlay: bool = False,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._app = app
        logger.info("Controller.__init__ start")

        # Config
        logger.info("Loading config...")
        self._config_manager = ConfigManager(config_path=config_path)
        self._config_manager.load()
        logger.info("Config loaded")

        # Window management
        self._window_manager = WindowManager()
        self._window_list: list[WindowInfo] = []
        self._current_window_index: int = 0
        self._active_trigger: TriggerConfig | None = None
        self._last_focused_hwnd: int = 0
        self._icon_cache: dict[int, QPixmap | None] = {}

        # Display monitor
        logger.info("Creating display monitor...")
        self._display_monitor = DisplayMonitor(
            triggers=self._config_manager.config.triggers,
            sentinel=app.sentinel,
        )
        self._display_monitor.trigger_activated.connect(self._on_trigger_activated)
        self._display_monitor.trigger_deactivated.connect(self._on_trigger_deactivated)

        # Overlay (created on first trigger activation)
        self._overlay: OverlayWindow | None = None
        self._overlay_visible = False

        # Mouse hook for long-press
        logger.info("Installing mouse hook...")
        self._mouse_hook = MouseHook(parent=self)
        self._mouse_hook.long_press_detected.connect(self._on_long_press)
        self._mouse_hook.install()
        logger.info("Mouse hook installed")

        # Periodic refresh timer (active while overlay is visible)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self._poll_windows)

        # System tray
        self._tray = self._create_tray_icon()

        # Do an initial check
        logger.info("Running initial display check...")
        self._display_monitor.check_now()
        logger.info("Display check done")

        # Force overlay mode: bypass aspect ratio detection
        if force_overlay:
            triggers = self._config_manager.config.triggers
            trigger = triggers[0] if triggers else TriggerConfig(
                name="default", aspect_ratio_min=0.0, aspect_ratio_max=99.0,
            )
            logger.info("Force overlay mode: showing overlay with trigger '%s'", trigger.name)
            self._active_trigger = trigger
            logger.info("Creating overlay...")
            self._overlay = self._create_overlay(trigger)
            logger.info("Showing overlay...")
            self._overlay.show_overlay()
            self._overlay_visible = True
            logger.info("Refreshing tiles...")
            self._refresh_tiles()
            logger.info("Starting refresh timer...")
            self._refresh_timer.start()
            logger.info("Force overlay init complete")

    def _create_tray_icon(self) -> QSystemTrayIcon:
        """Create the system tray icon with context menu."""
        # Create a simple colored icon
        pixmap = QPixmap(32, 32)
        pixmap.fill()  # white
        icon = QIcon(pixmap)

        tray = QSystemTrayIcon(icon, self)
        tray.setToolTip("MRCI - Mobile Remote Control Interface")

        menu = QMenu()
        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self._quit)
        menu.addAction(exit_action)

        tray.setContextMenu(menu)
        tray.show()
        return tray

    def _create_overlay(self, trigger: TriggerConfig) -> OverlayWindow:
        """Create a new OverlayWindow configured for the given trigger."""
        general = self._config_manager.config.general
        overlay = OverlayWindow(
            top_region_percent=trigger.top_region_percent,
            app_area_percent=trigger.app_area_percent,
            tile_columns=trigger.tile_columns,
            tile_rows=trigger.tile_rows,
            tile_bg_color=trigger.tile_background_color,
            tile_text_color=trigger.tile_text_color,
            icon_size=general.icon_size,
            font_size=general.font_size,
            tile_padding=general.tile_padding,
            nav_button_size=general.nav_button_size,
            max_app_tiles=trigger.max_app_tiles,
            max_shortcut_tiles=trigger.max_shortcut_tiles,
            show_tile_text=general.show_tile_text,
        )
        overlay.app_tile_activated.connect(self._on_app_tile_activated)
        overlay.shortcut_tile_activated.connect(self._on_shortcut_tile_activated)
        overlay.previous_window_requested.connect(self._on_previous_window)
        overlay.next_window_requested.connect(self._on_next_window)
        overlay.apps_collapsed.connect(self._on_apps_collapsed)
        return overlay

    @Slot(object)
    def _on_trigger_activated(self, trigger: TriggerConfig) -> None:
        """Handle display trigger activation — show overlay and resize windows."""
        logger.info("Trigger activated: %s", trigger.name)
        self._active_trigger = trigger
        self._overlay_visible = True

        # Create or reconfigure overlay
        if self._overlay is None:
            self._overlay = self._create_overlay(trigger)
        else:
            general = self._config_manager.config.general
            self._overlay.update_config(
                top_region_percent=trigger.top_region_percent,
                app_area_percent=trigger.app_area_percent,
                tile_columns=trigger.tile_columns,
                tile_bg_color=trigger.tile_background_color,
                tile_text_color=trigger.tile_text_color,
                icon_size=general.icon_size,
                font_size=general.font_size,
                tile_padding=general.tile_padding,
                nav_button_size=general.nav_button_size,
                max_app_tiles=trigger.max_app_tiles,
                max_shortcut_tiles=trigger.max_shortcut_tiles,
                show_tile_text=general.show_tile_text,
            )

        # Show overlay FIRST so it has a valid HWND for exclusion
        self._overlay.show_overlay()
        self._refresh_tiles()
        self._refresh_timer.start()

        # Resize active window to top region
        self._resize_active_window_to_top()

    @Slot()
    def _on_trigger_deactivated(self) -> None:
        """Handle display trigger deactivation — hide overlay and restore windows."""
        logger.info("Trigger deactivated")
        self._active_trigger = None
        self._overlay_visible = False
        self._refresh_timer.stop()

        if self._overlay is not None:
            self._overlay.hide_overlay()

        if self._config_manager.config.general.restore_windows_on_hide:
            self._window_manager.restore_all()

    def _refresh_tiles(self) -> None:
        """Enumerate windows and populate overlay tiles."""
        if self._overlay is None or self._active_trigger is None:
            return
        self._current_window_index = 0
        logger.debug("Enumerating windows...")

        # Get our own window handles to exclude
        exclude: set[int] = set()
        if self._overlay is not None:
            wid = int(self._overlay.winId())
            if wid:
                exclude.add(wid)
        sentinel_wid = int(self._app.sentinel.winId())
        if sentinel_wid:
            exclude.add(sentinel_wid)

        self._window_list = enumerate_windows(exclude_hwnds=exclude)
        logger.debug("Found %d windows", len(self._window_list))

        # Extract icons (use cache for known windows)
        icon_size = self._config_manager.config.general.icon_size
        for i, info in enumerate(self._window_list):
            if info.hwnd in self._icon_cache:
                info.icon = self._icon_cache[info.hwnd]
            else:
                n = len(self._window_list)
                logger.debug("Extracting icon %d/%d '%s'", i + 1, n, info.title)
                info.icon = extract_icon(info.hwnd, icon_size, info.process_id)
                self._icon_cache[info.hwnd] = info.icon
        logger.debug("Icon extraction complete")

        # Prune stale cache entries
        current_hwnds = {info.hwnd for info in self._window_list}
        self._icon_cache = {
            h: v for h, v in self._icon_cache.items() if h in current_hwnds
        }

        # Build app tile data: (title, icon, hwnd)
        max_len = self._config_manager.config.general.max_title_length
        app_items: list[tuple[str, QPixmap | None, int]] = []
        for info in self._window_list:
            icon = info.icon if isinstance(info.icon, QPixmap) else None
            title = _wrap_title(info.title, max_len)
            app_items.append((title, icon, info.hwnd))

        self._overlay.set_app_tiles(app_items)
        logger.debug("App tiles set")

        # Build shortcut tile data: (name, icon, key_sequence)
        icon_size = self._config_manager.config.general.icon_size
        shortcut_items: list[tuple[str, QPixmap | None, str]] = []
        for custom in self._active_trigger.custom_tiles:
            logger.debug("Loading shortcut icon for '%s'", custom.key_sequence)
            icon = _get_shortcut_icon(custom.key_sequence, custom.icon_path, icon_size)
            shortcut_items.append((custom.name, icon, custom.key_sequence))

        self._overlay.set_shortcut_tiles(shortcut_items)
        self._apply_highlight()
        logger.debug("Tile refresh complete")

    def _poll_windows(self) -> None:
        """Lightweight check — only full-refresh when the window set changes."""
        logger.debug("Polling windows...")
        if self._overlay is None or self._active_trigger is None:
            return

        exclude: set[int] = set()
        wid = int(self._overlay.winId())
        if wid:
            exclude.add(wid)
        sentinel_wid = int(self._app.sentinel.winId())
        if sentinel_wid:
            exclude.add(sentinel_wid)

        new_windows = enumerate_windows(exclude_hwnds=exclude)
        new_hwnds = {info.hwnd for info in new_windows}
        old_hwnds = {info.hwnd for info in self._window_list}

        if new_hwnds != old_hwnds:
            self._refresh_tiles()

    @Slot(int)
    def _on_app_tile_activated(self, hwnd: int) -> None:
        """Handle app tile click — focus window by hwnd and apply MRU reordering."""
        self._focus_and_resize(hwnd)

        # MRU: move this window to front of _window_list
        for i, info in enumerate(self._window_list):
            if info.hwnd == hwnd:
                self._window_list.insert(0, self._window_list.pop(i))
                self._current_window_index = 0
                break

        # Refresh tiles to reflect new MRU order
        if self._overlay is not None and self._active_trigger is not None:
            max_len = self._config_manager.config.general.max_title_length
            app_items: list[tuple[str, QPixmap | None, int]] = []
            for info in self._window_list:
                icon = info.icon if isinstance(info.icon, QPixmap) else None
                title = _wrap_title(info.title, max_len)
                app_items.append((title, icon, info.hwnd))
            self._overlay.set_app_tiles(app_items)
            self._apply_highlight()

    @Slot(str)
    def _on_shortcut_tile_activated(self, key_sequence: str) -> None:
        """Handle shortcut tile click — refocus last target window, then send key sequence."""
        target = self._last_focused_hwnd
        if target and self._window_manager.is_window_valid(target):
            self._window_manager.focus_window(target)
        QTimer.singleShot(200, lambda: self._send_shortcut_delayed(key_sequence))

    def _send_shortcut_delayed(self, key_sequence: str) -> None:
        """Send the shortcut after the OS has completed the focus switch."""
        try:
            send_key_sequence(key_sequence)
            logger.info("Sent shortcut: %s", key_sequence)
        except ValueError as e:
            logger.error("Failed to send shortcut %s: %s", key_sequence, e)
        if self._overlay is not None:
            self._overlay.raise_()

    @Slot()
    def _on_previous_window(self) -> None:
        """Focus the previous window in the list (wrap around)."""
        if not self._window_list:
            return
        self._current_window_index = (self._current_window_index - 1) % len(self._window_list)
        hwnd = self._window_list[self._current_window_index].hwnd
        self._focus_and_resize(hwnd)
        self._navigate_to_current_window_page()

    @Slot()
    def _on_next_window(self) -> None:
        """Focus the next window in the list (wrap around)."""
        if not self._window_list:
            return
        self._current_window_index = (self._current_window_index + 1) % len(self._window_list)
        hwnd = self._window_list[self._current_window_index].hwnd
        self._focus_and_resize(hwnd)
        self._navigate_to_current_window_page()

    def _navigate_to_current_window_page(self) -> None:
        """Navigate the app tile section to the page containing the current window."""
        if self._overlay is None:
            return
        items_per_page = self._overlay.app_section._items_per_page
        if items_per_page <= 0:
            return
        page = self._current_window_index // items_per_page
        self._overlay.app_section.go_to_page(page)
        self._apply_highlight()

    def _apply_highlight(self) -> None:
        """Highlight the app section tile for the current window."""
        if self._overlay is None or not self._window_list:
            return
        hwnd = self._window_list[self._current_window_index].hwnd
        self._overlay.app_section.highlight_tile_by_data(hwnd)

    def _focus_and_resize(self, hwnd: int) -> None:
        """Bring window to foreground and resize to top region."""
        if not self._window_manager.is_window_valid(hwnd):
            self._refresh_tiles()
            return

        self._last_focused_hwnd = hwnd
        self._window_manager.save_position(hwnd)
        self._window_manager.focus_window(hwnd)

        if self._active_trigger is not None:
            screen = QApplication.primaryScreen()
            if screen is not None:
                avail = screen.availableGeometry()
                self._window_manager.resize_to_top_region(
                    hwnd,
                    avail.width(),
                    avail.height(),
                    self._active_trigger.top_region_percent,
                    screen_x=avail.x(),
                    screen_y=avail.y(),
                )

        if self._overlay is not None:
            self._overlay.position_on_screen()
            self._overlay.raise_()

    def _resize_active_window_to_top(self) -> None:
        """Resize the currently active window to the top region."""
        hwnd = self._window_manager.get_foreground_window()
        if hwnd and self._active_trigger is not None:
            self._focus_and_resize(hwnd)

    @Slot()
    def _on_long_press(self) -> None:
        """Toggle overlay visibility on 3-second long-press."""
        if self._overlay is None:
            return

        if self._overlay_visible:
            # Hide overlay, maximize active window
            self._overlay.hide_overlay()
            self._overlay_visible = False
            hwnd = self._window_manager.get_foreground_window()
            if hwnd:
                self._window_manager.maximize(hwnd)
            logger.info("Long-press: overlay hidden, window maximized")
        else:
            # Show overlay, resize active window back to top region
            self._overlay.show_overlay()
            self._overlay_visible = True
            self._refresh_tiles()
            self._resize_active_window_to_top()
            logger.info("Long-press: overlay restored")

    @Slot(bool)
    def _on_apps_collapsed(self, collapsed: bool) -> None:
        """Resize the active window when the app section is collapsed/expanded."""
        if self._overlay is not None:
            self._overlay.position_on_screen()
            self._overlay.raise_()
        hwnd = self._window_manager.get_foreground_window()
        if hwnd and self._active_trigger is not None:
            screen = QApplication.primaryScreen()
            if screen is not None:
                avail = screen.availableGeometry()
                if self._overlay:
                    top_pct = self._overlay.effective_top_percent
                else:
                    top_pct = self._active_trigger.top_region_percent
                self._window_manager.resize_to_top_region(
                    hwnd,
                    avail.width(),
                    avail.height(),
                    top_pct,
                    screen_x=avail.x(),
                    screen_y=avail.y(),
                )

    def _open_settings(self) -> None:
        """Open the settings GUI."""
        from mrci.settings_gui.settings_window import SettingsWindow

        settings = SettingsWindow(self._config_manager)
        settings.config_saved.connect(self._on_config_saved)
        settings.exec()

    @Slot()
    def _on_config_saved(self) -> None:
        """Handle config changes from settings GUI."""
        self._display_monitor.update_triggers(self._config_manager.config.triggers)
        if self._overlay is not None and self._active_trigger is not None:
            general = self._config_manager.config.general
            self._overlay.update_config(
                top_region_percent=self._active_trigger.top_region_percent,
                app_area_percent=self._active_trigger.app_area_percent,
                tile_columns=self._active_trigger.tile_columns,
                tile_bg_color=self._active_trigger.tile_background_color,
                tile_text_color=self._active_trigger.tile_text_color,
                icon_size=general.icon_size,
                font_size=general.font_size,
                tile_padding=general.tile_padding,
                nav_button_size=general.nav_button_size,
                max_app_tiles=self._active_trigger.max_app_tiles,
                max_shortcut_tiles=self._active_trigger.max_shortcut_tiles,
                show_tile_text=general.show_tile_text,
            )

    def _quit(self) -> None:
        """Clean up and quit the application."""
        self._refresh_timer.stop()
        self._mouse_hook.uninstall()
        if self._overlay is not None:
            self._overlay.hide_overlay()
        self._window_manager.restore_all()
        self._tray.hide()
        QApplication.quit()

    def cleanup(self) -> None:
        """Clean up resources."""
        self._mouse_hook.uninstall()
        if self._overlay is not None:
            self._overlay.hide()
        self._tray.hide()
