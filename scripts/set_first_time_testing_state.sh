#!/usr/bin/env bash
set -euo pipefail

APP_DATA="${LEXISHIFT_APP_DATA:-$HOME/Library/Application Support/LexiShift/LexiShift}"
SETTINGS="$APP_DATA/settings.json"
BACKUP_ROOT="$APP_DATA/backups"
STAMP="$(date +%Y%m%d_%H%M%S)"
PRETEST_BACKUP="$BACKUP_ROOT/settings.pre_test_$STAMP.json"

if [ ! -f "$SETTINGS" ]; then
  echo "settings.json not found: $SETTINGS" >&2
  exit 1
fi

mkdir -p "$BACKUP_ROOT"
cp "$SETTINGS" "$PRETEST_BACKUP"

python3 - "$SETTINGS" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
data = json.loads(settings_path.read_text(encoding="utf-8"))
data["profiles"] = []
data["active_profile_id"] = ""
settings_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
print(str(settings_path))
PY

echo "Testing state enabled (profiles emptied)."
echo "Pre-test settings backup: $PRETEST_BACKUP"
