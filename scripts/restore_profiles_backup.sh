#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 /full/path/to/profiles_backup_<profile_ids>_<timestamp>" >&2
  exit 1
fi

BACKUP_DIR="$1"
APP_DATA="${LEXISHIFT_APP_DATA:-$HOME/Library/Application Support/LexiShift/LexiShift}"
SETTINGS="$APP_DATA/settings.json"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup dir not found: $BACKUP_DIR" >&2
  exit 1
fi
if [ ! -f "$BACKUP_DIR/manifest.json" ]; then
  echo "Missing: $BACKUP_DIR/manifest.json" >&2
  exit 1
fi
if [ ! -f "$BACKUP_DIR/selected_profiles.json" ]; then
  echo "Missing: $BACKUP_DIR/selected_profiles.json" >&2
  exit 1
fi

python3 - "$SETTINGS" "$BACKUP_DIR" <<'PY'
import json
import shutil
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
backup_dir = Path(sys.argv[2])

manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
selected_payload = json.loads((backup_dir / "selected_profiles.json").read_text(encoding="utf-8"))
backup_profiles = list(selected_payload.get("profiles") or [])
backup_ids = [p.get("profile_id") for p in backup_profiles if p.get("profile_id")]

if not backup_ids:
    raise SystemExit("Backup has no profiles to restore.")

if settings_path.exists():
    current = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    current = {"profiles": [], "active_profile_id": ""}

current_profiles = list(current.get("profiles") or [])
backup_id_set = set(backup_ids)
kept = [p for p in current_profiles if p.get("profile_id") not in backup_id_set]
merged = kept + backup_profiles
current["profiles"] = merged

all_ids = {p.get("profile_id") for p in merged if p.get("profile_id")}
candidate_active = str(manifest.get("selected_active_profile_id") or "")
if candidate_active not in all_ids:
    existing_active = str(current.get("active_profile_id") or "")
    if existing_active in all_ids:
        candidate_active = existing_active
    else:
        candidate_active = backup_ids[0]
current["active_profile_id"] = candidate_active

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")

missing_backup_files = []
for rec in manifest.get("ruleset_files", []):
    src_text = rec.get("source_path")
    rel = rec.get("backup_rel_path")
    if not src_text or not rel:
        continue
    from_path = backup_dir / rel
    to_path = Path(src_text).expanduser()
    if from_path.exists():
        to_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(from_path, to_path)
    else:
        missing_backup_files.append(str(from_path))

print("Restored profile IDs:", ", ".join(backup_ids))
if missing_backup_files:
    print("Warning: missing backed-up ruleset files:")
    for path in missing_backup_files:
        print(" -", path)
PY

echo "Restore complete from: $BACKUP_DIR"
