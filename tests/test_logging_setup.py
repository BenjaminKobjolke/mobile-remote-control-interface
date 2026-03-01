"""Tests for the logging setup module."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

import pytest

from mrci.logging_setup import setup_logging


@pytest.fixture()
def _clean_root_logger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect log output to tmp_path and restore root handlers after each test."""
    log_dir = tmp_path / ".mrci" / "logs"
    monkeypatch.setattr("mrci.logging_setup._LOG_DIR", log_dir)
    monkeypatch.setattr("mrci.logging_setup._LOG_FILE", log_dir / "mrci.log")

    root = logging.getLogger()
    original_handlers = root.handlers[:]
    root.handlers.clear()
    yield
    root.handlers = original_handlers


@pytest.mark.usefixtures("_clean_root_logger")
class TestSetupLogging:
    def test_creates_log_directory(self, tmp_path: Path) -> None:
        log_dir = tmp_path / ".mrci" / "logs"
        setup_logging()
        assert log_dir.exists()

    def test_adds_console_and_file_handlers(self) -> None:
        setup_logging()
        root = logging.getLogger()
        handler_types = [type(h) for h in root.handlers]
        assert logging.StreamHandler in handler_types
        assert logging.handlers.RotatingFileHandler in handler_types

    def test_idempotent(self) -> None:
        setup_logging()
        count = len(logging.getLogger().handlers)
        setup_logging()
        assert len(logging.getLogger().handlers) == count
