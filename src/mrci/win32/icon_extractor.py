"""Extract window icons as QPixmap."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from mrci.constants import (
    GCLP_HICON,
    GCLP_HICONSM,
    ICON_BIG,
    ICON_SMALL,
    PROCESS_QUERY_LIMITED_INFORMATION,
    SEND_MESSAGE_TIMEOUT_MS,
    SHGFI_ICON,
    SHGFI_LARGEICON,
    SMTO_ABORTIFHUNG,
    WM_GETICON,
)

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32


class _SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HANDLE),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", ctypes.c_wchar * 260),
        ("szTypeName", ctypes.c_wchar * 80),
    ]


def _send_msg_timeout(hwnd: int, msg: int, wparam: int, lparam: int) -> int:
    """SendMessageTimeoutW wrapper — returns 0 if the window doesn't respond."""
    result = wintypes.LPARAM(0)
    ok = user32.SendMessageTimeoutW(
        hwnd, msg, wparam, lparam,
        SMTO_ABORTIFHUNG, SEND_MESSAGE_TIMEOUT_MS,
        ctypes.byref(result),
    )
    return result.value if ok else 0


def _get_icon_handle(hwnd: int) -> int:
    """Try to get an icon handle from a window via WM_GETICON, then GetClassLongPtrW."""
    # Try WM_GETICON (with timeout so hung/elevated windows don't block)
    hicon: int = _send_msg_timeout(hwnd, WM_GETICON, ICON_BIG, 0)
    if hicon:
        return hicon

    hicon = _send_msg_timeout(hwnd, WM_GETICON, ICON_SMALL, 0)
    if hicon:
        return hicon

    # Fallback to class icon (these don't send messages, so they're safe)
    hicon = user32.GetClassLongPtrW(hwnd, GCLP_HICON)
    if hicon:
        return hicon

    hicon = user32.GetClassLongPtrW(hwnd, GCLP_HICONSM)
    return hicon


def _get_exe_path(pid: int) -> str | None:
    """Get the executable path for a process ID."""
    try:
        h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h_process:
            return None
        try:
            buf = ctypes.create_unicode_buffer(1024)
            buf_size = wintypes.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(buf_size)):
                return buf.value
            return None
        finally:
            kernel32.CloseHandle(h_process)
    except Exception:
        logger.debug("Failed to get exe path for pid %d", pid, exc_info=True)
        return None


def _get_icon_from_exe(exe_path: str) -> int:
    """Extract an icon handle from an executable using SHGetFileInfo.

    The returned HICON is owned by the caller and must be destroyed with DestroyIcon.
    Returns 0 on failure.
    """
    try:
        info = _SHFILEINFO()
        result = shell32.SHGetFileInfoW(
            exe_path,
            0,
            ctypes.byref(info),
            ctypes.sizeof(info),
            SHGFI_ICON | SHGFI_LARGEICON,
        )
        if result and info.hIcon:
            return int(info.hIcon)
        return 0
    except Exception:
        logger.debug("Failed to get icon from exe %s", exe_path, exc_info=True)
        return 0


def _get_icon_via_extract_icon_ex(exe_path: str) -> int:
    """Extract an icon from an executable using ExtractIconExW.

    Reads PE icon resources directly. Works when SHGetFileInfo returns nothing.
    The returned HICON is owned by the caller and must be destroyed with DestroyIcon.
    Returns 0 on failure.
    """
    try:
        large_icon = wintypes.HICON()
        count: int = shell32.ExtractIconExW(
            exe_path, 0, ctypes.byref(large_icon), None, 1,
        )
        if count > 0 and large_icon.value:
            return int(large_icon.value)
        return 0
    except Exception:
        logger.debug(
            "ExtractIconExW failed for %s", exe_path, exc_info=True,
        )
        return 0


def _get_uwp_icon(exe_path: str, size: int) -> QPixmap | None:
    """Extract icon from a UWP app's AppxManifest.xml logo reference.

    UWP apps store logos as PNG assets referenced in AppxManifest.xml.
    Returns a QPixmap directly (bypasses the HICON pipeline).
    """
    try:
        pkg_dir = Path(exe_path).parent
        manifest = pkg_dir / "AppxManifest.xml"
        if not manifest.exists():
            return None

        tree = ET.parse(manifest)  # noqa: S314
        root = tree.getroot()

        # Namespace-agnostic search for VisualElements
        logo_path: str | None = None
        for elem in root.iter():
            tag = elem.tag.rpartition("}")[2] if "}" in elem.tag else elem.tag
            if tag == "VisualElements":
                logo_path = (
                    elem.get("Square44x44Logo")
                    or elem.get("Square150x150Logo")
                    or elem.get("Logo")
                )
                break

        if not logo_path:
            return None

        # Resolve relative path against package directory
        logo_file = pkg_dir / logo_path
        # Try exact path first, then glob for scaled variants
        candidates: list[Path] = []
        if logo_file.exists():
            candidates.append(logo_file)
        else:
            stem = logo_file.stem
            parent = logo_file.parent
            if parent.exists():
                candidates = sorted(
                    parent.glob(f"{stem}.scale-*.png"),
                    reverse=True,
                )

        for candidate in candidates:
            pixmap = QPixmap(str(candidate))
            if not pixmap.isNull():
                return pixmap.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

        return None
    except Exception:
        logger.debug(
            "UWP icon extraction failed for %s", exe_path, exc_info=True,
        )
        return None


def extract_icon(hwnd: int, size: int = 48, pid: int = 0) -> QPixmap | None:
    """Extract the icon of a window as a QPixmap.

    Falls back to extracting the icon from the process executable if the window
    doesn't expose an icon via WM_GETICON or GetClassLongPtrW.

    Returns None if no icon could be extracted.
    """
    try:
        hicon = _get_icon_handle(hwnd)
        owns_icon = False

        # Fallback: extract icon from the process executable
        if not hicon and pid:
            exe_path = _get_exe_path(pid)
            if exe_path:
                # Try SHGetFileInfo
                hicon = _get_icon_from_exe(exe_path)
                if hicon:
                    owns_icon = True

                # Try ExtractIconExW (reads PE resources directly)
                if not hicon:
                    hicon = _get_icon_via_extract_icon_ex(exe_path)
                    if hicon:
                        owns_icon = True

                # Try UWP manifest logo (returns QPixmap directly)
                if not hicon and "\\WindowsApps\\" in exe_path:
                    pixmap = _get_uwp_icon(exe_path, size)
                    if pixmap:
                        return pixmap

        if not hicon:
            return None

        # Use GetIconInfo to extract bitmap data
        class ICONINFO(ctypes.Structure):
            _fields_ = [
                ("fIcon", wintypes.BOOL),
                ("xHotspot", wintypes.DWORD),
                ("yHotspot", wintypes.DWORD),
                ("hbmMask", wintypes.HBITMAP),
                ("hbmColor", wintypes.HBITMAP),
            ]

        icon_info = ICONINFO()
        if not user32.GetIconInfo(hicon, ctypes.byref(icon_info)):
            if owns_icon:
                user32.DestroyIcon(hicon)
            return None

        gdi32 = ctypes.windll.gdi32

        # Clean up bitmaps
        if icon_info.hbmMask:
            gdi32.DeleteObject(icon_info.hbmMask)

        if icon_info.hbmColor:
            gdi32.DeleteObject(icon_info.hbmColor)
            result = _render_icon_to_pixmap(hicon, size)
            if owns_icon:
                user32.DestroyIcon(hicon)
            return result

        if owns_icon:
            user32.DestroyIcon(hicon)
        return None
    except Exception:
        logger.debug("Failed to extract icon for hwnd %d", hwnd, exc_info=True)
        return None


def _render_icon_to_pixmap(hicon: int, size: int) -> QPixmap | None:
    """Render an HICON to a QPixmap using DrawIconEx."""
    try:
        gdi32 = ctypes.windll.gdi32

        # Create a compatible DC and bitmap
        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, size, size)
        old_bmp = gdi32.SelectObject(hdc_mem, hbmp)

        # Fill with white background
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD),
                ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD),
            ]

        # Draw the icon
        DI_NORMAL = 0x0003
        user32.DrawIconEx(hdc_mem, 0, 0, hicon, size, size, 0, 0, DI_NORMAL)

        # Read pixel data
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = size
        bmi.biHeight = -size  # top-down
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0  # BI_RGB

        buf = (ctypes.c_ubyte * (size * size * 4))()
        gdi32.GetDIBits(hdc_mem, hbmp, 0, size, buf, ctypes.byref(bmi), 0)

        # Create QImage from raw data
        image = QImage(
            bytes(buf),
            size,
            size,
            size * 4,
            QImage.Format.Format_ARGB32,
        )
        pixmap = QPixmap.fromImage(image)

        # Cleanup GDI resources
        gdi32.SelectObject(hdc_mem, old_bmp)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

        return pixmap
    except Exception:
        logger.debug("Failed to render icon to pixmap", exc_info=True)
        return None
