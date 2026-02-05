#!/bin/bash
# Automates the build-and-run cycle for development.

set -e
cd "$(dirname "$0")/.."

echo "🏗️  Building LexiShift..."
python3 scripts/build_gui_app.py

echo "🚀 Launching..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open apps/gui/dist/LexiShift.app
else
    echo "Please run the executable in apps/gui/dist/ manually."
fi