#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

FULL_CLEAN=0
START_TRAY=0
for arg in "$@"; do
  if [[ "$arg" == "--all" ]]; then
    FULL_CLEAN=1
  fi
  if [[ "$arg" == "--start-tray" ]]; then
    START_TRAY=1
  fi
done

echo "==> Cleanup"
if [[ "${FULL_CLEAN}" -eq 1 ]]; then
  bash "${REPO_ROOT}/scripts/cleanup_helper.sh" --all
else
  bash "${REPO_ROOT}/scripts/cleanup_helper.sh"
fi

echo "==> Build + install app"
python "${REPO_ROOT}/scripts/build_gui_app.py" --install

echo "==> Install helper (manual step required)"
echo "Open LexiShift app -> LexiShift menu -> Install Helper"

if [[ "${START_TRAY}" -eq 1 ]]; then
  echo "==> Start tray helper"
  bash "${REPO_ROOT}/scripts/cleanup_helper.sh" --start-tray
fi

echo "==> Status"
bash "${REPO_ROOT}/scripts/check_helper_status.sh"
