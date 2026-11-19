@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "ARCHIVES=%USERPROFILE%\Downloads"
set "REPORT=%USERPROFILE%\Downloads\LANDSCAPE_GO_FULL_CATALOG_IMPORT_REPORT.json"
if not exist "%USERPROFILE%\Downloads\" set "REPORT=%TEMP%\LANDSCAPE_GO_FULL_CATALOG_IMPORT_REPORT.json"
where py >nul 2>nul
if errorlevel 1 (
  python TOOLS\import_full_catalogs.py --archive-dir "%ARCHIVES%" --report "%REPORT%"
) else (
  py -3 TOOLS\import_full_catalogs.py --archive-dir "%ARCHIVES%" --report "%REPORT%"
)
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (echo FULL CATALOG IMPORT VERIFIED.) else (echo Import NOT verified. Read the report.)
echo Report: %REPORT%
pause
exit /b %RC%
