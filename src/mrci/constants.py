"""All win32 constants, default values, and magic numbers used throughout MRCI."""

# --- Win32 Window Styles ---
WS_VISIBLE = 0x10000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_NOACTIVATE = 0x08000000

# --- Win32 Window Messages ---
WM_DISPLAYCHANGE = 0x007E
WM_GETICON = 0x007F
WM_CLOSE = 0x0010
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200

# --- Win32 SendMessage flags ---
SMTO_ABORTIFHUNG = 0x0002
SEND_MESSAGE_TIMEOUT_MS = 100

# --- Win32 Icons ---
ICON_SMALL = 0
ICON_BIG = 1
ICON_SMALL2 = 2
GCL_HICON = -14
GCL_HICONSM = -34
GCLP_HICON = -14
GCLP_HICONSM = -34

# --- Win32 SetWindowPos flags ---
SWP_SHOWWINDOW = 0x0040
SWP_NOACTIVATE = 0x0010
SWP_NOZORDER = 0x0004
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

# --- Win32 ShowWindow commands ---
SW_SHOW = 5
SW_RESTORE = 9
SW_MAXIMIZE = 3
SW_MINIMIZE = 6
SW_SHOWNOACTIVATE = 4

# --- Win32 GetWindow commands ---
GW_OWNER = 4

# --- Win32 SendInput constants ---
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

# --- Virtual Key Codes ---
VK_CODES: dict[str, int] = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "menu": 0x12,
    "pause": 0x13,
    "capslock": 0x14,
    "escape": 0x1B,
    "esc": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "printscreen": 0x2C,
    "insert": 0x2D,
    "delete": 0x2E,
    "del": 0x2E,
    "win": 0x5B,
    "lwin": 0x5B,
    "rwin": 0x5C,
    "numpad0": 0x60,
    "numpad1": 0x61,
    "numpad2": 0x62,
    "numpad3": 0x63,
    "numpad4": 0x64,
    "numpad5": 0x65,
    "numpad6": 0x66,
    "numpad7": 0x67,
    "numpad8": 0x68,
    "numpad9": 0x69,
    "multiply": 0x6A,
    "add": 0x6B,
    "subtract": 0x6D,
    "decimal": 0x6E,
    "divide": 0x6F,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
    "numlock": 0x90,
    "scrolllock": 0x91,
}

# --- Win32 Mouse Hook ---
WH_MOUSE_LL = 14

# --- Win32 Process Access ---
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010

# --- Win32 Shell ---
SHGFI_ICON = 0x100
SHGFI_LARGEICON = 0x0

# --- MRCI Defaults ---
DEFAULT_CONFIG_FILE = "config.json"
CONFIG_VERSION = 1

LONG_PRESS_DURATION_MS = 3000
LONG_PRESS_MOVE_THRESHOLD_PX = 10

DISPLAY_CHANGE_DEBOUNCE_MS = 100

DEFAULT_TOP_REGION_PERCENT = 40
DEFAULT_APP_AREA_PERCENT = 30
DEFAULT_TILE_COLUMNS = 3
DEFAULT_TILE_ROWS = 4
DEFAULT_TILE_BG_COLOR = "#0078D4"
DEFAULT_TILE_TEXT_COLOR = "#FFFFFF"
DEFAULT_NAV_BUTTON_SIZE = 60
DEFAULT_TILE_PADDING = 4
DEFAULT_ICON_SIZE = 48
DEFAULT_FONT_SIZE = 12
DEFAULT_MAX_APP_TILES = 4
DEFAULT_MAX_SHORTCUT_TILES = 4
DEFAULT_MAX_TITLE_LENGTH = 10
DEFAULT_CONFIG_HOTKEY = "ctrl+shift+f12"
