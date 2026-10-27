#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ -f ".venv/bin/python3" ]; then
    exec .venv/bin/python3 run.py "$@"
fi

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 не установлен."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[INFO] Создание виртуального окружения (.venv)..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

exec .venv/bin/python3 run.py "$@"
