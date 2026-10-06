#!/usr/bin/env bash
# ==============================================================================
# Adaptive Study Assistant - macOS Installer
# ==============================================================================
set -e

echo "🍏 Installing Adaptive Study Assistant for macOS..."
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "⚠️ Python 3 not found. Installing via Homebrew..."
    if command -v brew &>/dev/null; then
        brew install python
    else
        echo "❌ Homebrew is required to install Python 3. Please install Homebrew from https://brew.sh"
        exit 1
    fi
else
    echo "✓ Python 3 is installed: $(python3 --version)"
fi

# Check / Install Homebrew packages
if command -v brew &>/dev/null; then
    # Install Poppler for PDF extraction
    if ! command -v pdftotext &>/dev/null; then
        echo "📦 Installing poppler for PDF textbook extraction..."
        brew install poppler
    else
        echo "✓ poppler (pdftotext) is already installed."
    fi

    # Optional: Install aichat
    if ! command -v aichat &>/dev/null; then
        echo "📦 Installing aichat for enhanced terminal UI..."
        brew install aichat || echo "ℹ️ Note: aichat installation skipped; the assistant will use its native Python interactive mode."
    else
        echo "✓ aichat is already installed."
    fi
else
    echo "ℹ️ Homebrew not found. Installing pypdf fallback for PDF processing..."
    python3 -m pip install --quiet pypdf || true
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
echo "🎉 macOS Installation complete!"
echo "Run './learn' or './start.sh' to begin studying."
