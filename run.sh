#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ -f ".venv_linux/bin/python3" ]; then
    exec .venv_linux/bin/python3 run.py "$@"
elif [ -f ".venv/bin/python3" ]; then
    exec .venv/bin/python3 run.py "$@"
fi

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 не установлен."
    exit 1
fi

if [ ! -d ".venv_linux" ] && [ ! -d ".venv" ]; then
    echo "[INFO] Создание виртуального окружения (.venv_linux)..."
    python3 -m venv .venv_linux
    .venv_linux/bin/pip install --upgrade pip
    .venv_linux/bin/pip install -r requirements.txt
fi

if [ -f ".venv_linux/bin/python3" ]; then
    exec .venv_linux/bin/python3 run.py "$@"
else
    exec .venv/bin/python3 run.py "$@"
fi
