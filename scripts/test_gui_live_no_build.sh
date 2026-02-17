#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -n "${PYTHONPATH:-}" ]; then
  export PYTHONPATH="$ROOT_DIR/apps/gui/src:$ROOT_DIR/core:$PYTHONPATH"
else
  export PYTHONPATH="$ROOT_DIR/apps/gui/src:$ROOT_DIR/core"
fi

exec python3 "$ROOT_DIR/apps/gui/src/main.py" "$@"
