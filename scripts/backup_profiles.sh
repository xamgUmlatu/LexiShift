#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 PROFILE_ID [PROFILE_ID ...]" >&2
  exit 1
fi

PROFILE_SLUG="$(
  python3 - "$@" <<'PY'
import re
import sys

profile_ids = [item.strip() for item in sys.argv[1:] if item.strip()]
if not profile_ids:
    raise SystemExit("At least one non-empty profile ID is required.")


def slug_part(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return slug or "profile"


print("_".join(slug_part(profile_id) for profile_id in profile_ids))
PY
)"

APP_DATA="${LEXISHIFT_APP_DATA:-$HOME/Library/Application Support/LexiShift/LexiShift}"
SETTINGS="$APP_DATA/settings.json"
BACKUP_ROOT="$APP_DATA/backups"
STAMP="$(date +%Y%m%d_%H%M%S)"
DEST="$BACKUP_ROOT/profiles_backup_${PROFILE_SLUG}_$STAMP"

if [ ! -f "$SETTINGS" ]; then
  echo "settings.json not found: $SETTINGS" >&2
  exit 1
fi

python3 - "$SETTINGS" "$DEST" "$@" <<'PY'
import hashlib
import json
import shutil
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
backup_dir = Path(sys.argv[2])
target_ids = [item.strip() for item in sys.argv[3:] if item.strip()]
target_id_set = set(target_ids)

if not target_ids:
    raise SystemExit("At least one non-empty profile ID is required.")

data = json.loads(settings_path.read_text(encoding="utf-8"))
profiles = list(data.get("profiles") or [])

selected = [p for p in profiles if p.get("profile_id") in target_id_set]
found_ids = {p.get("profile_id") for p in selected}
missing = [pid for pid in target_ids if pid not in found_ids]
if missing:
    raise SystemExit(f"Missing profile(s): {', '.join(missing)}")

backup_dir.mkdir(parents=True, exist_ok=False)
shutil.copy2(settings_path, backup_dir / "settings.full.json")

selected_ids = [p.get("profile_id") for p in selected if p.get("profile_id")]
selected_active = str(data.get("active_profile_id") or "")
if selected_active not in selected_ids:
    selected_active = selected_ids[0] if selected_ids else ""

ruleset_paths = []
seen = set()


def add_path(path):
    if not isinstance(path, str):
        return
    path = path.strip()
    if not path or path in seen:
        return
    seen.add(path)
    ruleset_paths.append(path)


for profile in selected:
    add_path(profile.get("dataset_path"))
    add_path(profile.get("active_ruleset"))
    for path in profile.get("rulesets") or []:
        add_path(path)

manifest = {
    "created_from_settings_path": str(settings_path),
    "requested_profile_ids": target_ids,
    "selected_profile_ids": selected_ids,
    "selected_active_profile_id": selected_active,
    "ruleset_files": [],
}

(backup_dir / "selected_profiles.json").write_text(
    json.dumps({"profiles": selected}, indent=2, sort_keys=True),
    encoding="utf-8",
)

for src_text in ruleset_paths:
    src = Path(src_text).expanduser()
    rec = {
        "source_path": src_text,
        "exists_at_backup_time": src.exists(),
    }
    if src.exists():
        digest = hashlib.sha1(str(src).encode("utf-8")).hexdigest()[:12]
        rel = f"rulesets/{digest}__{src.name}"
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        rec["backup_rel_path"] = rel
    manifest["ruleset_files"].append(rec)

(backup_dir / "manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True),
    encoding="utf-8",
)

print(str(backup_dir))
PY

echo "Backup complete: $DEST"
