#!/usr/bin/env bash
# ==============================================================================
# Adaptive Study Assistant - macOS Scratch Kickstart (NO Homebrew required)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
exec bash "$DIR/install.sh" "$@"
