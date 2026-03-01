# Mobile Remote Control Interface (MRCI)

A mobile-friendly overlay for Windows Remote Desktop. When the screen switches to a portrait aspect ratio (as happens with mobile RDP clients), MRCI shows a Windows 8 Mobile-style tile grid for switching between running apps and executing keyboard shortcuts.

## Requirements

- Windows 11
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Quick Start

```batch
start.bat
```

## Development

Run tests:
```batch
tools\tests.bat
```

## Configuration

Settings are stored in `~/.mrci/config.json`. Use the built-in settings GUI (accessible via system tray icon) to configure triggers, tile colors, custom shortcut tiles, and more.
