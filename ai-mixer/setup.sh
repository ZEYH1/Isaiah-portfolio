#!/usr/bin/env bash
# One-command setup for the AI Mixer on macOS.
# Installs Homebrew (if missing), Python 3.11, ffmpeg, and the Python libraries.
# Re-running it is safe.

set -e

cd "$(dirname "$0")"

echo "==> Step 1/4: Checking Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Installing..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if [[ "$(uname -m)" == "arm64" ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  else
    eval "$(/usr/local/bin/brew shellenv)"
  fi
else
  echo "Homebrew already installed."
fi

echo "==> Step 2/4: Installing Python 3.11 and ffmpeg"
brew install python@3.11 ffmpeg

PY=$(brew --prefix python@3.11)/bin/python3.11

echo "==> Step 3/4: Creating virtual environment in .venv"
if [ ! -d ".venv" ]; then
  "$PY" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip

echo "==> Step 4/4: Installing Python libraries"
pip install -r requirements.txt

echo ""
echo "Setup complete."
echo "To use the project from a new terminal:"
echo "    cd $(pwd)"
echo "    source .venv/bin/activate"
echo "    streamlit run src/app.py"
