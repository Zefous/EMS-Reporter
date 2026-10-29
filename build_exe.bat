@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Build EMS Reporter Standalone EXE

echo ========================================================
echo        BUILD EMS REPORTER STANDALONE EXE
echo ========================================================
echo.

:: 1. Locate Python
set "PY_CMD="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 set "PY_CMD=python"
    if not defined PY_CMD (
        where py >nul 2>nul
        if %errorlevel% equ 0 set "PY_CMD=py -3"
    )
)

if not defined PY_CMD (
    echo [ERROR] Python not found in system PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo IMPORTANT: Make sure to check "Add python.exe to PATH".
    pause
    exit /b 1
)

:: 2. Create virtual environment if missing
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment (.venv)...
    %PY_CMD% -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv
        pause
        exit /b 1
    )
)

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

:: 3. Verify and install dependencies
echo [1/3] Checking and installing dependencies...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 4. Clean previous builds
echo [2/3] Cleaning previous build artifacts (build, dist)...
if exist "%~dp0build" rd /s /q "%~dp0build"
if exist "%~dp0dist" rd /s /q "%~dp0dist"

:: 5. Compile standalone executable
echo [3/3] Compiling application into standalone executable...
"%VENV_PY%" -m PyInstaller --clean "%~dp0EMS_Reporter.spec"

if not exist "%~dp0dist\EMS_Reporter.exe" (
    echo.
    echo [ERROR] Build failed. EMS_Reporter.exe was not created.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  [SUCCESS] Build finished successfully!
echo.
echo  Standalone output file:
echo  dist\EMS_Reporter.exe
echo.
echo  This file runs independently on any Windows PC:
echo  - Other users do NOT need Python installed.
echo  - All libraries and icons are bundled into .exe!
echo ========================================================
echo.

explorer "%~dp0dist"
pause
