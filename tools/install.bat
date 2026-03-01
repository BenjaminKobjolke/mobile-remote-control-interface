@echo off
cd /d "%~dp0.."
echo Installing MRCI dependencies...
uv sync
echo.
echo Done. Run start.bat to launch MRCI.
echo.
echo Usage:
echo   start.bat                          (uses config.json in app folder)
echo   start.bat --config path\to\config.json  (uses custom config)
