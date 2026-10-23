#!/usr/bin/env bash
# ==============================================================================
# Adaptive Study Assistant Launcher
# Automatically initializes setup if running for the first time.
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# If first-time run (no .env or no .venv), kickstart automatically!
if [ ! -f "$DIR/.env" ] || [ ! -d "$DIR/.venv" ]; then
    exec bash "$DIR/install.sh" "$@"
fi

# Use virtualenv python if available, else system python3
if [ -f "$DIR/.venv/bin/python3" ]; then
    exec "$DIR/.venv/bin/python3" "$DIR/learn" "$@"
else
    exec python3 "$DIR/learn" "$@"
fi
