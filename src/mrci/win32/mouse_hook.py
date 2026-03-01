"""Global low-level mouse hook for long-press (3s) detection."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import logging
import math

from PySide6.QtCore import QObject, QTimer, Signal

from mrci.constants import (
    LONG_PRESS_DURATION_MS,
    LONG_PRESS_MOVE_THRESHOLD_PX,
    WH_MOUSE_LL,
    WM_LBUTTONDOWN,
    WM_LBUTTONUP,
    WM_MOUSEMOVE,
)
from mrci.win32.types import HOOKPROC, MSLLHOOKSTRUCT

logger = logging.getLogger(__name__)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# Set proper 64-bit return/argument types to prevent pointer truncation.
kernel32.GetModuleHandleW.restype = ctypes.c_void_p
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]

user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int, HOOKPROC, ctypes.c_void_p, wintypes.DWORD,
]

user32.CallNextHookEx.restype = ctypes.c_long
user32.CallNextHookEx.argtypes = [
    ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM,
]

user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]


class MouseHook(QObject):
    """Installs a global low-level mouse hook to detect 3-second long-press.

    Emits `long_press_detected` when the user holds the left mouse button
    for 3 seconds without moving more than 10 pixels.
    """

    long_press_detected = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._hook_handle: int = 0
        self._hook_proc: object | None = None
        self._press_start_x = 0
        self._press_start_y = 0
        self._is_pressed = False

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(LONG_PRESS_DURATION_MS)
        self._timer.timeout.connect(self._on_timer_fired)

    def install(self) -> bool:
        """Install the low-level mouse hook. Returns True on success."""
        if self._hook_handle:
            return True

        self._hook_proc = HOOKPROC(self._hook_callback)
        self._hook_handle = user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            self._hook_proc,
            kernel32.GetModuleHandleW("user32.dll"),
            0,
        )
        if self._hook_handle:
            logger.info("Mouse hook installed")
            return True
        else:
            err = ctypes.get_last_error()
            logger.warning("Failed to install mouse hook (Windows error %d)", err)
            return False

    def uninstall(self) -> None:
        """Remove the mouse hook."""
        if self._hook_handle:
            user32.UnhookWindowsHookEx(self._hook_handle)
            self._hook_handle = 0
            self._hook_proc = None
            self._timer.stop()
            self._is_pressed = False
            logger.info("Mouse hook uninstalled")

    def _hook_callback(self, n_code: int, w_param: int, l_param: int) -> int:
        """Low-level mouse hook callback."""
        if n_code >= 0:
            try:
                hook_struct = MSLLHOOKSTRUCT.from_address(l_param)
                x, y = hook_struct.pt.x, hook_struct.pt.y

                if w_param == WM_LBUTTONDOWN:
                    self._press_start_x = x
                    self._press_start_y = y
                    self._is_pressed = True
                    self._timer.start()

                elif w_param == WM_LBUTTONUP:
                    self._is_pressed = False
                    self._timer.stop()

                elif w_param == WM_MOUSEMOVE and self._is_pressed:
                    dx = x - self._press_start_x
                    dy = y - self._press_start_y
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance > LONG_PRESS_MOVE_THRESHOLD_PX:
                        self._timer.stop()
                        self._is_pressed = False
            except Exception:
                logger.debug("Error in mouse hook callback", exc_info=True)

        result: int = user32.CallNextHookEx(self._hook_handle, n_code, w_param, l_param)
        return result

    def _on_timer_fired(self) -> None:
        """Timer expired — 3-second long-press detected."""
        if self._is_pressed:
            logger.info("Long-press detected (3s)")
            self._is_pressed = False
            self.long_press_detected.emit()
