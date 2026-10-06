#!/usr/bin/env bash
# Accuracy-First AI Learning System Launcher
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
exec python3 "$DIR/learn" "$@"
