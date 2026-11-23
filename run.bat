@echo off
setlocal
cd /d "%~dp0"
title WARAQ Library Studio
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 main.py
) else (
    python main.py
)
if errorlevel 1 (
    echo.
    echo Waraq could not start. Check that Python 3.10+ is installed.
)
echo.
echo Press any key to close this window.
pause >nul
endlocal
