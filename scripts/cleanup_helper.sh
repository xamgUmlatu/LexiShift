#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${HOME}/Library/Application Support/LexiShift/LexiShift"
LAUNCH_AGENT="${HOME}/Library/LaunchAgents/com.lexishift.helper.plist"
CHROME_MANIFEST="${HOME}/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.lexishift.helper.json"
BRAVE_MANIFEST="${HOME}/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts/com.lexishift.helper.json"
CHROMIUM_MANIFEST="${HOME}/Library/Application Support/Chromium/NativeMessagingHosts/com.lexishift.helper.json"

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

echo "Stopping LexiShift processes..."
PIDS=$(pgrep -f "/Applications/LexiShift.app/Contents/MacOS/LexiShift" || true)
if [[ -n "${PIDS}" ]]; then
  echo "Killing LexiShift PIDs: ${PIDS}"
  kill ${PIDS} 2>/dev/null || true
  sleep 0.5
  kill -9 ${PIDS} 2>/dev/null || true
fi

PIDS=$(pgrep -f "lexishift_native_host.py" || true)
if [[ -n "${PIDS}" ]]; then
  echo "Killing native host PIDs: ${PIDS}"
  kill ${PIDS} 2>/dev/null || true
  sleep 0.5
  kill -9 ${PIDS} 2>/dev/null || true
fi

PIDS=$(pgrep -f "helper_tray" || true)
if [[ -n "${PIDS}" ]]; then
  echo "Killing helper tray PIDs: ${PIDS}"
  kill ${PIDS} 2>/dev/null || true
  sleep 0.5
  kill -9 ${PIDS} 2>/dev/null || true
fi

echo "Unloading LaunchAgent..."
launchctl bootout "gui/${UID}" "${LAUNCH_AGENT}" 2>/dev/null || true
rm -f "${LAUNCH_AGENT}"

echo "Removing native messaging manifests..."
rm -f "${CHROME_MANIFEST}" "${BRAVE_MANIFEST}" "${CHROMIUM_MANIFEST}"

if [[ "${FULL_CLEAN}" -eq 1 ]]; then
  echo "Removing helper data root: ${DATA_ROOT}"
  rm -rf "${DATA_ROOT}"
else
  echo "Keeping helper data root. Use --all to delete: ${DATA_ROOT}"
fi

if [[ "${START_TRAY}" -eq 1 ]]; then
  APP_BIN="/Applications/LexiShift.app/Contents/MacOS/LexiShift"
  echo "Starting helper tray..."
  if [[ -x "${APP_BIN}" ]]; then
    nohup "${APP_BIN}" --helper-tray >/tmp/lexishift_tray.out 2>&1 &
  else
    echo "App binary not found: ${APP_BIN}"
  fi
fi

echo "Done."
