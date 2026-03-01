# MRCI Development Guide

## Build & Run
- `start.bat` — Launch the application
- `tools\tests.bat` — Run all tests
- `uv run ruff check src/ tests/` — Lint
- `uv run mypy src/` — Type check
- `uv run pytest tests/ -x -q` — Run tests (quick)
- `uv run pytest tests/test_config/ -x -q` — Run specific test module

## Architecture
- **PySide6** for GUI, **ctypes** for all win32 calls (no pywin32)
- Entry point: `src/mrci/__main__.py`
- Config stored at `~/.mrci/config.json`
- Overlay: borderless always-on-top PySide6 window in bottom 60% of screen
- Display detection: dual path (QScreen signals + WM_DISPLAYCHANGE)

## Code Style
- Python 3.11+, strict mypy, ruff for linting
- Dataclasses for config schema, runtime DTOs
- All win32 constants in `constants.py`
- Type hints on all public functions
