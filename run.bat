@echo off
setlocal
cd /d "%~dp0"
title EMS Reporter - Majestic GTA V RP

:: 1. Check if virtual environment python already exists
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0run.py"
    goto :end
)

:: 2. Search for system Python
set "PY_CMD="
where python >nul 2>nul
if %errorlevel% equ 0 set "PY_CMD=python"
if not defined PY_CMD (
    where py >nul 2>nul
    if %errorlevel% equ 0 set "PY_CMD=py -3"
)

if not defined PY_CMD (
    echo [ERROR] Python не найден в системе.
    echo Пожалуйста, установите Python 3.10+ с официального сайта: https://www.python.org/
    echo ВАЖНО: При установке обязательно отметьте галочку "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

:: 3. Create virtual environment
echo [INFO] Создание виртуального окружения (.venv)...
%PY_CMD% -m venv "%~dp0.venv"
if errorlevel 1 (
    echo [ERROR] Не удалось создать виртуальное окружение в %~dp0.venv
    pause
    exit /b 1
)

:: 4. Install dependencies
echo [INFO] Установка зависимостей...
"%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip
"%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [ERROR] Не удалось установить пакеты из requirements.txt
    pause
    exit /b 1
)

:: 5. Launch application
echo [INFO] Запуск EMS Reporter...
"%~dp0.venv\Scripts\python.exe" "%~dp0run.py"

:end
if errorlevel 1 (
    echo.
    echo [ERROR] Программа завершилась с ошибкой %errorlevel%.
    pause
)
