@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Сборка EMS Reporter в .EXE

echo ========================================================
echo        СБОРКА EMS REPORTER В АВТОНОМНЫЙ .EXE
echo ========================================================
echo.

:: 1. Ищем Python
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
    echo [ОШИБКА] Python не найден в системе.
    echo Пожалуйста, установите Python 3.10+ с сайта https://www.python.org/
    echo Обязательно отметьте "Add python.exe to PATH".
    pause
    exit /b 1
)

:: 2. Создаём .venv если его ещё нет
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [ИНФО] Создание виртуального окружения (.venv)...
    %PY_CMD% -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать .venv
        pause
        exit /b 1
    )
)

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

:: 3. Проверяем и устанавливаем зависимости
echo [1/3] Проверка и установка зависимостей...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)

:: 4. Очищаем старые сборки
echo [2/3] Очистка предыдущих сборок (build, dist)...
if exist "%~dp0build" rd /s /q "%~dp0build"
if exist "%~dp0dist" rd /s /q "%~dp0dist"

:: 5. Компилируем .exe
echo [3/3] Компиляция приложения в один исполняемый файл...
"%VENV_PY%" -m PyInstaller --clean "%~dp0EMS_Reporter.spec"

if not exist "%~dp0dist\EMS_Reporter.exe" (
    echo.
    echo [ОШИБКА] Сборка не удалась.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  [УСПЕХ] Сборка успешно завершена!
echo.
echo  Готовый файл для отправки:
echo  dist\EMS_Reporter.exe
echo.
echo  Этот файл работает самостоятельно на любом Windows ПК:
echo  - Python устанавливать другим людям НЕ нужно!
echo  - Все библиотеки и иконка уже зашиты внутрь .exe!
echo ========================================================
echo.

explorer "%~dp0dist"
pause
