"""QApplication subclass and sentinel window for WM_DISPLAYCHANGE detection."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys

from PySide6.QtCore import QByteArray, Signal
from PySide6.QtWidgets import QApplication, QWidget

from mrci.constants import WM_DISPLAYCHANGE


class SentinelWindow(QWidget):
    """Hidden window that captures WM_DISPLAYCHANGE via nativeEvent."""

    display_changed = Signal(int, int)  # width, height

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("MRCI_Sentinel")
        self.resize(1, 1)
        # Keep it hidden — never show

    def nativeEvent(self, event_type: QByteArray | bytes, message: int) -> tuple[bool, int]:  # type: ignore[override]
        """Intercept Windows native messages to detect WM_DISPLAYCHANGE."""
        if sys.platform == "win32":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == WM_DISPLAYCHANGE:
                lparam = msg.lParam
                width = lparam & 0xFFFF
                height = (lparam >> 16) & 0xFFFF
                self.display_changed.emit(width, height)
        return super().nativeEvent(event_type, message)  # type: ignore[return-value]


class MrciApplication(QApplication):
    """Main QApplication for MRCI with sentinel window."""

    def __init__(self, argv: list[str] | None = None) -> None:
        super().__init__(argv or sys.argv)
        self.setApplicationName("MRCI")
        self.setQuitOnLastWindowClosed(False)
        self._sentinel = SentinelWindow()
        # Create the native window handle without showing
        self._sentinel.winId()

    @property
    def sentinel(self) -> SentinelWindow:
        return self._sentinel
