#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${HOME}/Library/Application Support/LexiShift/LexiShift"
LAUNCH_AGENT="${HOME}/Library/LaunchAgents/com.lexishift.helper.plist"
TRAY_LOG="${DATA_ROOT}/helper_tray.log"
STATUS_JSON="${DATA_ROOT}/srs/srs_status.json"
CHROME_MANIFEST="${HOME}/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.lexishift.helper.json"
APP_BIN="/Applications/LexiShift.app/Contents/MacOS/LexiShift"

START_TRAY=0
for arg in "$@"; do
  if [[ "$arg" == "--start-tray" ]]; then
    START_TRAY=1
  fi
done

if [[ "${START_TRAY}" -eq 1 ]]; then
  echo "Starting helper tray (background)..."
  if [[ -x "${APP_BIN}" ]]; then
    nohup "${APP_BIN}" --helper-tray >/tmp/lexishift_tray.out 2>&1 &
    sleep 1
  else
    echo "App binary not found: ${APP_BIN}"
  fi
fi

echo "=== LaunchAgent ==="
if [[ -f "${LAUNCH_AGENT}" ]]; then
  echo "LaunchAgent exists: ${LAUNCH_AGENT}"
else
  echo "LaunchAgent missing: ${LAUNCH_AGENT}"
fi

echo
echo "=== launchctl list | grep com.lexishift.helper ==="
launchctl list | grep com.lexishift.helper || echo "Not loaded"

echo
echo "=== Processes ==="
pgrep -fl "/Applications/LexiShift.app/Contents/MacOS/LexiShift" || echo "No LexiShift process"
pgrep -fl "helper_tray" || echo "No helper_tray process"
pgrep -fl "lexishift_native_host.py" || echo "No native host process"

echo
echo "=== Data Root ==="
if [[ -d "${DATA_ROOT}" ]]; then
  ls -la "${DATA_ROOT}"
else
  echo "Data root missing: ${DATA_ROOT}"
fi

echo
echo "=== Helper Tray Log ==="
if [[ -f "${TRAY_LOG}" ]]; then
  tail -n 50 "${TRAY_LOG}"
else
  echo "Tray log missing: ${TRAY_LOG}"
fi

echo
echo "=== SRS Status ==="
if [[ -f "${STATUS_JSON}" ]]; then
  cat "${STATUS_JSON}"
else
  echo "Status missing: ${STATUS_JSON}"
fi

echo
echo "=== Chrome Native Messaging Manifest ==="
if [[ -f "${CHROME_MANIFEST}" ]]; then
  cat "${CHROME_MANIFEST}"
else
  echo "Manifest missing: ${CHROME_MANIFEST}"
fi

echo
echo "=== Notes ==="
echo "Tray icon visibility cannot be directly detected in shell."
echo "If tray log reports 'System tray available: False' or icon null, the UI icon will not show."
echo "Tip: run with --start-tray to launch the tray helper before checks."
