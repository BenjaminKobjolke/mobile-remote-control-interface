"""Enumerate visible GUI windows (same logic as Windows taskbar)."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import logging

from mrci.config.schema import WindowInfo
from mrci.constants import (
    GW_OWNER,
    PROCESS_QUERY_INFORMATION,
    PROCESS_VM_READ,
    WS_EX_APPWINDOW,
    WS_EX_TOOLWINDOW,
)
from mrci.win32.types import WNDENUMPROC

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi


def _get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _get_process_name(pid: int) -> str:
    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(260)
        psapi.GetModuleBaseNameW(handle, None, buf, 260)
        return buf.value
    finally:
        kernel32.CloseHandle(handle)


def _is_taskbar_window(hwnd: int) -> bool:
    """Check if a window should appear in the taskbar (same heuristic as Windows)."""
    if not user32.IsWindowVisible(hwnd):
        return False

    title = _get_window_text(hwnd)
    if not title:
        return False

    ex_style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE

    # Skip tool windows
    if ex_style & WS_EX_TOOLWINDOW:
        return False

    # If it has WS_EX_APPWINDOW, it's a taskbar window
    if ex_style & WS_EX_APPWINDOW:
        return True

    # Otherwise, only show if it has no owner
    owner: int = user32.GetWindow(hwnd, GW_OWNER)
    return owner == 0


def enumerate_windows(
    exclude_hwnds: set[int] | None = None,
) -> list[WindowInfo]:
    """Enumerate all visible GUI windows suitable for the taskbar.

    Args:
        exclude_hwnds: Set of window handles to exclude (e.g., our own overlay).

    Returns:
        List of WindowInfo DTOs for matching windows.
    """
    if exclude_hwnds is None:
        exclude_hwnds = set()

    results: list[WindowInfo] = []

    def callback(hwnd: int, _lparam: int) -> bool:
        if hwnd in exclude_hwnds:
            return True

        if not _is_taskbar_window(hwnd):
            return True

        title = _get_window_text(hwnd)
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_name = _get_process_name(pid.value)

        results.append(
            WindowInfo(
                hwnd=hwnd,
                title=title,
                process_name=process_name,
                process_id=pid.value,
            )
        )
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return results
