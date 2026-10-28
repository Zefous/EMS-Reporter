@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Сборка EMS Reporter в .EXE

echo ========================================================
echo        СБОРКА EMS REPORTER В АВТОНОМНЫЙ .EXE
echo ========================================================
echo.

:: 1. Определяем Python из venv или системы
set "PY_EXE="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
    set "PIP_EXE=%~dp0.venv\Scripts\pip.exe"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_EXE=python"
        set "PIP_EXE=pip"
    )
)

if not defined PY_EXE (
    echo [ОШИБКА] Python не найден!
    echo Сначала запустите run.bat один раз, чтобы создать виртуальное окружение .venv
    pause
    exit /b 1
)

:: 2. Проверяем наличие PyInstaller
echo [1/3] Проверка установленного PyInstaller...
"%PY_EXE%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ИНФО] Установка PyInstaller в окружение...
    "%PIP_EXE%" install pyinstaller
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить PyInstaller.
        pause
        exit /b 1
    )
)

:: 3. Очищаем старые сборки
echo [2/3] Очистка предыдущих сборок (build, dist)...
if exist "%~dp0build" rd /s /q "%~dp0build"
if exist "%~dp0dist" rd /s /q "%~dp0dist"

:: 4. Запускаем сборку
echo [3/3] Компиляция приложения в один исполняемый файл...
"%PY_EXE%" -m PyInstaller --clean "%~dp0EMS_Reporter.spec"

if not exist "%~dp0dist\EMS_Reporter.exe" (
    echo.
    echo [ОШИБКА] Сборка не удалась. Исполняемый файл не найден.
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

:: Открываем папку с готовым файлом в проводнике
explorer "%~dp0dist"

pause
