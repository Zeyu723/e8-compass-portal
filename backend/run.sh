#!/usr/bin/env bash
# Run the E8 Compass FastAPI backend locally.
# Works on Linux/macOS and Windows (Git Bash / WSL). For plain Windows cmd,
# see the commands at the bottom of this file.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Create virtualenv if missing (python3 on Linux/macOS, python on Windows)
if [ ! -d ".venv" ]; then
  (command -v python3 >/dev/null && python3 -m venv .venv) || python -m venv .venv
fi

# Activate venv (handle both POSIX and Windows layouts)
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate
fi

pip install --upgrade pip setuptools wheel >/dev/null
pip install -r requirements.txt
pip install anthropic  # Claude provider (optional import guard in code)

# Copy example env if present and .env missing
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
fi

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

exec python -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
