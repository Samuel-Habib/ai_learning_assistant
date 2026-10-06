#!/usr/bin/env bash
# ==============================================================================
# Adaptive Study Assistant - Universal Installer
# Auto-detects macOS vs Linux vs Windows (WSL/Git Bash) and runs the right setup.
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
OS="$(uname -s)"

echo "======================================================================"
echo "  Adaptive Study Assistant Setup"
echo "======================================================================"

case "$OS" in
    Darwin*)
        echo "Detected Platform: macOS"
        echo ""
        bash "$DIR/scripts/install_mac.sh"
        ;;
    Linux*)
        echo "Detected Platform: Linux"
        echo ""
        bash "$DIR/scripts/install_linux.sh"
        ;;
    CYGWIN*|MINGW*|MSYS*)
        echo "Detected Platform: Windows (POSIX shell)"
        echo ""
        bash "$DIR/scripts/install_linux.sh"
        ;;
    *)
        echo "Unknown platform: $OS. Running Linux/POSIX setup..."
        echo ""
        bash "$DIR/scripts/install_linux.sh"
        ;;
esac
