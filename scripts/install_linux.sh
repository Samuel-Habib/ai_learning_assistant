#!/usr/bin/env bash
# ==============================================================================
# Adaptive Study Assistant - Linux Installer (Debian/Ubuntu/Fedora/Arch)
# ==============================================================================
set -e

echo "🐧 Installing Adaptive Study Assistant for Linux..."
echo ""

# Helper to run with sudo if not root
SUDO=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo &>/dev/null; then
        SUDO="sudo"
    else
        echo "⚠️ Not running as root and 'sudo' is not installed. Package installations might fail."
    fi
fi

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "📦 Installing Python 3..."
    if command -v apt-get &>/dev/null; then
        $SUDO apt-get update && $SUDO apt-get install -y python3 python3-pip
    elif command -v dnf &>/dev/null; then
        $SUDO dnf install -y python3 python3-pip
    elif command -v pacman &>/dev/null; then
        $SUDO pacman -Sy --noconfirm python python-pip
    fi
else
    echo "✓ Python 3 is installed: $(python3 --version)"
fi

# Install poppler-utils for PDF extraction
if ! command -v pdftotext &>/dev/null; then
    echo "📦 Installing poppler-utils for PDF processing..."
    if command -v apt-get &>/dev/null; then
        $SUDO apt-get update && $SUDO apt-get install -y poppler-utils
    elif command -v dnf &>/dev/null; then
        $SUDO dnf install -y poppler-utils
    elif command -v pacman &>/dev/null; then
        $SUDO pacman -Sy --noconfirm poppler
    elif command -v zypper &>/dev/null; then
        $SUDO zypper install -y poppler-tools
    else
        echo "⚠️ Package manager not recognized. Installing pypdf via pip..."
        python3 -m pip install --quiet pypdf || true
    fi
else
    echo "✓ poppler-utils (pdftotext) is already installed."
fi

# Optional aichat check
if ! command -v aichat &>/dev/null; then
    echo "ℹ️ AIChat CLI not installed; the assistant will use its native built-in Python dialogue mode."
else
    echo "✓ aichat is installed."
fi

# Setup .env if missing
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "👉 Edit .env to add your GEMINI_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY."
else
    echo "✓ .env file already exists."
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/learn" "$SCRIPT_DIR/start.sh" "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/scripts/"*.sh 2>/dev/null || true

echo ""
echo "🎉 Linux Installation complete!"
echo "Run './learn' or './start.sh' to begin studying."
