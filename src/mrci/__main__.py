"""Entry point for MRCI — Mobile Remote Control Interface."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def main() -> int:
    """Launch the MRCI application."""
    parser = argparse.ArgumentParser(description="Mobile Remote Control Interface")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config JSON file (default: config.json in app folder)",
    )
    parser.add_argument(
        "--force-overlay",
        action="store_true",
        default=False,
        help="Show overlay immediately, bypassing aspect ratio detection",
    )
    args = parser.parse_args()

    from mrci.logging_setup import setup_logging

    setup_logging()

    logger.info("Importing modules...")
    from mrci.app import MrciApplication
    from mrci.controller import Controller

    logger.info("Creating QApplication...")
    app = MrciApplication(sys.argv)
    logger.info("Creating Controller...")
    controller = Controller(app, config_path=args.config, force_overlay=args.force_overlay)

    logger.info("Entering event loop...")
    exit_code = app.exec()
    controller.cleanup()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
