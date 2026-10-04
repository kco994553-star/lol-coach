@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\collect_local.py
  goto finished
)
where python >nul 2>nul
if not errorlevel 1 (
  python scripts\collect_local.py
  goto finished
)
echo Python 3.10+ is required. Install Python from python.org, then run this file again.
:finished
pause
