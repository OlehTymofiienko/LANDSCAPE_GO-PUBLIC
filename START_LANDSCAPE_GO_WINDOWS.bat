@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 LANDSCAPE_GO.py
) else (
    python LANDSCAPE_GO.py
)
if errorlevel 1 pause
