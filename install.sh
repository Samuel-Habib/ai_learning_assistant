#!/usr/bin/env bash
# ==============================================================================
# Adaptive Study Assistant - Zero-Dependency Universal Kickstart
# Works from absolute scratch on macOS and Linux (NO Homebrew required).
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
OS="$(uname -s)"

echo "======================================================================"
echo "  🚀 Adaptive Study Assistant — Scratch Kickstart"
echo "======================================================================"
echo "Detected OS: $OS"
echo ""

# 1. Detect or verify Python 3
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null && python --version 2>&1 | grep -q "Python 3"; then
    PYTHON_BIN="python"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "⚠️ Python 3 was not found on your system."
    if [ "$OS" = "Darwin" ]; then
        echo "🍎 Triggering Apple Command Line Tools installation (includes Python 3, zero Homebrew needed)..."
        xcode-select --install || true
        echo "Please complete the Apple installation prompt on your screen, then re-run ./install.sh."
        exit 1
    else
        echo "🐧 Please install Python 3 using your system package manager:"
        echo "   Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-venv"
        echo "   Fedora:        sudo dnf install -y python3"
        echo "   Arch:          sudo pacman -S python"
        exit 1
    fi
fi

echo "✓ Using Python: $($PYTHON_BIN --version 2>&1) ($($PYTHON_BIN -c 'import sys; print(sys.executable)'))"

# 2. Setup isolated virtual environment (.venv) - zero sudo, zero Homebrew needed
VENV_DIR="$DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating self-contained environment in .venv..."
    $PYTHON_BIN -m venv "$VENV_DIR" 2>/dev/null || true
fi

# Determine virtualenv Python
if [ -f "$VENV_DIR/bin/pip" ]; then
    VENV_PY="$VENV_DIR/bin/python3"
    echo "✓ Isolated virtual environment ready."
    echo "📦 Installing pypdf for PDF extraction (no system packages required)..."
    "$VENV_DIR/bin/pip" install --quiet --disable-pip-version-check pypdf 2>/dev/null || true
else
    # If venv creation was incomplete (e.g. minimal Ubuntu without python3-venv), clean up
    [ -d "$VENV_DIR" ] && rm -rf "$VENV_DIR"
    VENV_PY="$PYTHON_BIN"
    echo "ℹ️ Using system Python ($VENV_PY)."
    $PYTHON_BIN -m pip install --quiet --user pypdf 2>/dev/null || true
fi

# 3. Interactive API Key setup (.env)
ENV_FILE="$DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$DIR/.env.example" "$ENV_FILE"
fi

# Check if an API key is present
HAS_KEY=false
if grep -q -E "^(GEMINI_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|GROQ_API_KEY)=[a-zA-Z0-9_-]+" "$ENV_FILE" 2>/dev/null; then
    HAS_KEY=true
fi

if [ "$HAS_KEY" = false ] && [ -t 0 ]; then
    echo ""
    echo "----------------------------------------------------------------------"
    echo "🔑 AI Setup: Powering Dynamic Questions & Adaptive Tutoring"
    echo "----------------------------------------------------------------------"
    echo "To dynamically generate questions and tutor you from your textbooks,"
    echo "the assistant uses an AI model. A free Gemini key works instantly."
    echo "👉 Get a free key here: https://aistudio.google.com/app/apikey"
    echo ""
    read -r -p "Enter your Gemini API key (or press Enter to skip for now): " USER_KEY
    if [ -n "$USER_KEY" ]; then
        USER_KEY="$(echo "$USER_KEY" | tr -d ' "\r\n')"
        if grep -q "^GEMINI_API_KEY=" "$ENV_FILE" 2>/dev/null; then
            sed -i.bak "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=\"$USER_KEY\"|" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
        elif grep -q "^# GEMINI_API_KEY=" "$ENV_FILE" 2>/dev/null; then
            sed -i.bak "s|^# GEMINI_API_KEY=.*|GEMINI_API_KEY=\"$USER_KEY\"|" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
        else
            echo "GEMINI_API_KEY=\"$USER_KEY\"" >> "$ENV_FILE"
        fi
        echo "✓ Saved API key to .env"
    else
        echo "ℹ️ Running in offline mode for now. (You can add a key anytime in .env)"
    fi
    echo "----------------------------------------------------------------------"
    echo ""
fi

# 4. Make scripts executable
chmod +x "$DIR/learn" "$DIR/start.sh" "$DIR/install.sh" "$DIR/scripts/"*.sh 2>/dev/null || true

# 5. Run health check
echo "🩺 Running system health check..."
echo ""
"$VENV_PY" "$DIR/learn" doctor

# 6. Prompt to launch
echo "======================================================================"
echo "🎉 Setup complete! You're ready to start studying."
echo "======================================================================"
echo ""
read -r -p "Launch study assistant now? [Y/n]: " LAUNCH_CHOICE
case "$LAUNCH_CHOICE" in
    [nN]*)
        echo "To start later, run: ./learn  or  ./start.sh"
        ;;
    *)
        exec "$VENV_PY" "$DIR/learn"
        ;;
esac
