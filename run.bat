@echo off
cd /d "%~dp0"
title EMS Reporter - Majestic GTA V RP

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0run.py"
    goto :done
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 "%~dp0run.py"
    goto :done
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python "%~dp0run.py"
    goto :done
)

echo [ERROR] Python was not found in system PATH.
echo Please install Python 3.10+ from https://www.python.org/
echo IMPORTANT: Make sure to check "Add python.exe to PATH".
echo.
pause
exit /b 1

:done
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with code %errorlevel%.
    pause
)
