"""Parse and send keyboard shortcuts via SendInput."""

from __future__ import annotations

import ctypes
import logging

from mrci.constants import INPUT_KEYBOARD, KEYEVENTF_KEYUP, VK_CODES
from mrci.win32.types import INPUT

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32


def parse_key_sequence(sequence: str) -> list[int]:
    """Parse a key sequence string like 'ctrl+c' into a list of VK codes.

    Raises ValueError if any key name is unrecognized.
    """
    keys = [k.strip().lower() for k in sequence.split("+")]
    vk_codes: list[int] = []

    for key in keys:
        if key in VK_CODES:
            vk_codes.append(VK_CODES[key])
        elif len(key) == 1 and key.isascii():
            # Single character — use VkKeyScanW
            vk = user32.VkKeyScanW(ord(key)) & 0xFF
            if vk == 0xFF:
                raise ValueError(f"Unknown key: {key!r}")
            vk_codes.append(vk)
        else:
            raise ValueError(f"Unknown key: {key!r}")

    return vk_codes


def send_key_sequence(sequence: str) -> None:
    """Send a keyboard shortcut.

    Parses the sequence, presses all keys in order, then releases in reverse order.
    """
    vk_codes = parse_key_sequence(sequence)
    if not vk_codes:
        return

    inputs: list[INPUT] = []

    # Key down events
    for vk in vk_codes:
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = vk
        inp.union.ki.dwFlags = 0
        inputs.append(inp)

    # Key up events (reverse order)
    for vk in reversed(vk_codes):
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = vk
        inp.union.ki.dwFlags = KEYEVENTF_KEYUP
        inputs.append(inp)

    n = len(inputs)
    array = (INPUT * n)(*inputs)
    sent = user32.SendInput(n, ctypes.byref(array), ctypes.sizeof(INPUT))
    if sent != n:
        logger.warning("SendInput sent %d of %d events", sent, n)
