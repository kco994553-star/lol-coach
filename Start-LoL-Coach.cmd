@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-LoL-Coach.ps1" -InstallPython -CreateShortcut %*
if errorlevel 1 pause
