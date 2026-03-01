@echo off
cd /d "%~dp0.."
uv run pytest tests/ -x -q %*
