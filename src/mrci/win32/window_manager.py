"""Window resize, move, focus, and position save/restore."""

from __future__ import annotations

import ctypes
import logging

from mrci.constants import (
    HWND_TOP,
    SW_MAXIMIZE,
    SW_RESTORE,
    SWP_SHOWWINDOW,
)
from mrci.win32.types import RECT

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class WindowManager:
    """Manages window positioning, focus, and state save/restore."""

    def __init__(self) -> None:
        self._saved_positions: dict[int, tuple[int, int, int, int]] = {}

    def save_position(self, hwnd: int) -> None:
        """Save the current window position and size."""
        rect = RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            self._saved_positions[hwnd] = (
                rect.left,
                rect.top,
                rect.right - rect.left,
                rect.bottom - rect.top,
            )

    def restore_position(self, hwnd: int) -> bool:
        """Restore a previously saved window position. Returns True if restored."""
        pos = self._saved_positions.pop(hwnd, None)
        if pos is None:
            return False
        x, y, w, h = pos
        user32.SetWindowPos(hwnd, HWND_TOP, x, y, w, h, SWP_SHOWWINDOW)
        return True

    def restore_all(self) -> None:
        """Restore all saved window positions."""
        for hwnd in list(self._saved_positions.keys()):
            self.restore_position(hwnd)

    def resize_to_top_region(
        self,
        hwnd: int,
        screen_width: int,
        screen_height: int,
        top_percent: int,
        screen_x: int = 0,
        screen_y: int = 0,
    ) -> None:
        """Resize a window to fill the top N% of the available screen area."""
        target_height = int(screen_height * top_percent / 100)
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetWindowPos(
            hwnd, HWND_TOP, screen_x, screen_y, screen_width, target_height, SWP_SHOWWINDOW
        )

    def maximize(self, hwnd: int) -> None:
        """Maximize a window."""
        user32.ShowWindow(hwnd, SW_MAXIMIZE)

    def focus_window(self, hwnd: int) -> None:
        """Bring a window to the foreground using AttachThreadInput trick."""
        foreground_hwnd = user32.GetForegroundWindow()
        if foreground_hwnd == hwnd:
            return

        current_thread = kernel32.GetCurrentThreadId()
        foreground_thread = user32.GetWindowThreadProcessId(foreground_hwnd, None)

        if current_thread != foreground_thread:
            user32.AttachThreadInput(foreground_thread, current_thread, True)

        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)

        if current_thread != foreground_thread:
            user32.AttachThreadInput(foreground_thread, current_thread, False)

    def get_foreground_window(self) -> int:
        """Get the currently focused window handle."""
        return user32.GetForegroundWindow()  # type: ignore[no-any-return]

    def is_window_valid(self, hwnd: int) -> bool:
        """Check if a window handle is still valid."""
        return bool(user32.IsWindow(hwnd))

    @property
    def saved_positions(self) -> dict[int, tuple[int, int, int, int]]:
        return self._saved_positions
