#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
GUI_SRC = PROJECT_ROOT / "apps" / "gui" / "src"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (CORE_ROOT, GUI_SRC):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from language_packs_catalog import build_pack_catalogs  # noqa: E402
from lexishift_core.helper.installed_packs import (  # noqa: E402
    installed_pack_root,
    load_installed_pack_manifest,
    resolve_installed_pack_artifact,
)


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_manual_backfill_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_manual_backfill_latest.md"
SETTINGS_FILENAME = "settings.json"


@dataclass(frozen=True)
class ManagedPackRef:
    pack_id: str
    family: str
    pack_root: Path
    artifact_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill saved manual resource settings that already point at "
            "app-managed SQLite pack roots. Dry-run by default."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("~/.local/share/LexiShift/LexiShift"),
        help="LexiShift data root containing settings.json.",
    )
    parser.add_argument(
        "--settings-path",
        type=Path,
        default=None,
        help="Explicit settings.json path. Overrides --data-root when provided.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the migrated settings.json. Omit for a dry-run report.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a settings.json.bak copy before --apply writes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings_path = args.settings_path or Path(args.data_root) / SETTINGS_FILENAME
    report = backfill_manual_resource_settings(
        settings_path,
        apply_changes=args.apply,
        backup=not args.no_backup,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_backfill_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if report["status"] == "error":
        return 1
    return 0


def backfill_manual_resource_settings(
    settings_path: Path,
    *,
    apply_changes: bool = False,
    backup: bool = True,
    generated_at: str | None = None,
) -> dict[str, object]:
    resolved_settings = Path(settings_path).expanduser().resolve(strict=False)
    data_root = resolved_settings.parent
    payload, errors = _load_json_object(resolved_settings)
    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": generated_at or _utc_now(),
        "settings_path": str(resolved_settings),
        "settings_exists": resolved_settings.exists(),
        "mode": "apply" if apply_changes else "dry_run",
        "status": "ok",
        "changed": False,
        "backup_path": "",
        "changes": [],
        "skipped": [],
    }
    if errors:
        report["status"] = "error"
        report["settings_errors"] = errors
        return report
    if not payload:
        report["status"] = "no_settings"
        return report

    updated = deepcopy(payload)
    changes: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    synonyms = updated.get("synonyms")
    if not isinstance(synonyms, dict):
        report["status"] = "no_synonym_settings"
        return report

    _backfill_pack_path_map(
        synonyms,
        data_root=data_root,
        family="language",
        path_field="language_pack_paths",
        managed_id_field="managed_language_pack_ids",
        changes=changes,
    )
    _backfill_pack_path_map(
        synonyms,
        data_root=data_root,
        family="frequency",
        path_field="frequency_pack_paths",
        managed_id_field="managed_frequency_pack_ids",
        changes=changes,
    )
    embedding_pair_key_by_pack_id = _embedding_pair_key_by_pack_id()
    _backfill_embedding_pack_paths(
        synonyms,
        data_root=data_root,
        embedding_pair_key_by_pack_id=embedding_pair_key_by_pack_id,
        changes=changes,
        skipped=skipped,
    )
    _backfill_embedding_pair_paths(
        synonyms,
        data_root=data_root,
        embedding_pair_key_by_pack_id=embedding_pair_key_by_pack_id,
        changes=changes,
        skipped=skipped,
    )

    report["changes"] = changes
    report["skipped"] = skipped
    report["changed"] = bool(changes)
    report["status"] = (
        "applied" if apply_changes and changes else ("would_update" if changes else "ok")
    )
    if apply_changes and changes:
        if backup:
            backup_path = resolved_settings.with_name(f"{resolved_settings.name}.bak")
            shutil.copy2(resolved_settings, backup_path)
            report["backup_path"] = str(backup_path)
        _write_json_object(resolved_settings, updated)
    return report


def render_backfill_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# Pack Lifecycle Manual Backfill",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Settings: `{report.get('settings_path')}`",
        f"- Mode: `{report.get('mode')}`",
        f"- Status: `{report.get('status')}`",
        f"- Changed: `{report.get('changed')}`",
        "",
    ]
    backup_path = str(report.get("backup_path") or "").strip()
    if backup_path:
        lines.extend([f"- Backup: `{backup_path}`", ""])
    changes = [row for row in _sequence(report.get("changes")) if isinstance(row, Mapping)]
    skipped = [row for row in _sequence(report.get("skipped")) if isinstance(row, Mapping)]
    if changes:
        lines.extend(
            [
                "## Changes",
                "",
                "| Action | From field | Pack id | Pair | Path |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in changes:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(row.get("action")),
                        _cell(row.get("from_field")),
                        _cell(row.get("pack_id")),
                        _cell(row.get("pair_key")),
                        _cell(row.get("path")),
                    ]
                )
                + " |"
            )
        lines.append("")
    else:
        lines.extend(["## Changes", "", "No settings backfill changes were found.", ""])
    if skipped:
        lines.extend(
            [
                "## Skipped",
                "",
                "| Reason | Field | Pack id | Pair | Path |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in skipped:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(row.get("reason")),
                        _cell(row.get("field_name")),
                        _cell(row.get("pack_id")),
                        _cell(row.get("pair_key")),
                        _cell(row.get("path")),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _backfill_pack_path_map(
    synonyms: dict[str, object],
    *,
    data_root: Path,
    family: str,
    path_field: str,
    managed_id_field: str,
    changes: list[dict[str, object]],
) -> None:
    raw_paths = synonyms.get(path_field)
    if not isinstance(raw_paths, Mapping):
        return
    managed_ids = _text_list(synonyms.get(managed_id_field))
    kept_paths: dict[object, object] = {}
    changed = False
    for raw_key, raw_path in raw_paths.items():
        key = str(raw_key or "").strip()
        path_text = str(raw_path or "").strip()
        managed_ref = _managed_pack_ref_for_path(path_text, data_root=data_root, family=family)
        if key and path_text and managed_ref is not None:
            managed_ids = _append_unique(managed_ids, managed_ref.pack_id)
            changes.append(
                {
                    "action": "migrate_manual_path_to_managed_id",
                    "from_field": path_field,
                    "to_field": managed_id_field,
                    "key": key,
                    "pack_id": managed_ref.pack_id,
                    "pair_key": "",
                    "path": path_text,
                    "artifact_path": str(managed_ref.artifact_path),
                    "pack_root": str(managed_ref.pack_root),
                }
            )
            changed = True
            continue
        kept_paths[raw_key] = raw_path
    if changed:
        synonyms[managed_id_field] = sorted(managed_ids)
        _set_or_drop_mapping(synonyms, path_field, kept_paths)


def _backfill_embedding_pack_paths(
    synonyms: dict[str, object],
    *,
    data_root: Path,
    embedding_pair_key_by_pack_id: Mapping[str, str],
    changes: list[dict[str, object]],
    skipped: list[dict[str, object]],
) -> None:
    raw_paths = synonyms.get("embedding_pack_paths")
    if not isinstance(raw_paths, Mapping):
        return
    kept_paths: dict[object, object] = {}
    changed = False
    for raw_key, raw_path in raw_paths.items():
        pack_key = str(raw_key or "").strip()
        path_text = str(raw_path or "").strip()
        managed_ref = _managed_pack_ref_for_path(
            path_text,
            data_root=data_root,
            family="embedding",
        )
        if not pack_key or not path_text or managed_ref is None:
            kept_paths[raw_key] = raw_path
            continue
        pair_key = embedding_pair_key_by_pack_id.get(managed_ref.pack_id)
        if not pair_key:
            kept_paths[raw_key] = raw_path
            skipped.append(
                _skipped_row(
                    reason="managed_embedding_pack_without_catalog_pair",
                    field_name="embedding_pack_paths",
                    pack_id=managed_ref.pack_id,
                    pair_key="",
                    path=path_text,
                )
            )
            continue
        _promote_embedding_pair_pack_id(synonyms, pair_key=pair_key, pack_id=managed_ref.pack_id)
        changes.append(
            {
                "action": "migrate_manual_embedding_path_to_pair_pack_id",
                "from_field": "embedding_pack_paths",
                "to_field": "embedding_pair_pack_ids",
                "key": pack_key,
                "pack_id": managed_ref.pack_id,
                "pair_key": pair_key,
                "path": path_text,
                "artifact_path": str(managed_ref.artifact_path),
                "pack_root": str(managed_ref.pack_root),
            }
        )
        changed = True
    if changed:
        _set_or_drop_mapping(synonyms, "embedding_pack_paths", kept_paths)


def _backfill_embedding_pair_paths(
    synonyms: dict[str, object],
    *,
    data_root: Path,
    embedding_pair_key_by_pack_id: Mapping[str, str],
    changes: list[dict[str, object]],
    skipped: list[dict[str, object]],
) -> None:
    raw_pair_paths = synonyms.get("embedding_pair_paths")
    if not isinstance(raw_pair_paths, Mapping):
        return
    changed = False
    kept_pair_paths: dict[object, object] = {}
    for raw_pair_key, raw_values in raw_pair_paths.items():
        pair_key = str(raw_pair_key or "").strip()
        if not pair_key or not isinstance(raw_values, Sequence) or isinstance(raw_values, str):
            kept_pair_paths[raw_pair_key] = raw_values
            continue
        kept_values: list[object] = []
        for raw_path in raw_values:
            path_text = str(raw_path or "").strip()
            managed_ref = _managed_pack_ref_for_path(
                path_text,
                data_root=data_root,
                family="embedding",
            )
            if not path_text or managed_ref is None:
                kept_values.append(raw_path)
                continue
            catalog_pair_key = embedding_pair_key_by_pack_id.get(managed_ref.pack_id)
            if catalog_pair_key != pair_key:
                kept_values.append(raw_path)
                skipped.append(
                    _skipped_row(
                        reason="managed_embedding_pair_mismatch",
                        field_name="embedding_pair_paths",
                        pack_id=managed_ref.pack_id,
                        pair_key=pair_key,
                        path=path_text,
                    )
                )
                continue
            _promote_embedding_pair_pack_id(
                synonyms, pair_key=pair_key, pack_id=managed_ref.pack_id
            )
            changes.append(
                {
                    "action": "migrate_manual_pair_path_to_pair_pack_id",
                    "from_field": "embedding_pair_paths",
                    "to_field": "embedding_pair_pack_ids",
                    "key": pair_key,
                    "pack_id": managed_ref.pack_id,
                    "pair_key": pair_key,
                    "path": path_text,
                    "artifact_path": str(managed_ref.artifact_path),
                    "pack_root": str(managed_ref.pack_root),
                }
            )
            changed = True
        if kept_values:
            kept_pair_paths[raw_pair_key] = kept_values
    if changed:
        _set_or_drop_mapping(synonyms, "embedding_pair_paths", kept_pair_paths)


def _promote_embedding_pair_pack_id(
    synonyms: dict[str, object],
    *,
    pair_key: str,
    pack_id: str,
) -> None:
    pair_pack_ids = synonyms.get("embedding_pair_pack_ids")
    if not isinstance(pair_pack_ids, dict):
        pair_pack_ids = {}
        synonyms["embedding_pair_pack_ids"] = pair_pack_ids
    existing = _text_list(pair_pack_ids.get(pair_key))
    pair_pack_ids[pair_key] = _append_unique(existing, pack_id)

    pair_enabled = synonyms.get("embedding_pair_enabled")
    if not isinstance(pair_enabled, dict):
        pair_enabled = {}
        synonyms["embedding_pair_enabled"] = pair_enabled
    pair_enabled.setdefault(pair_key, True)


def _managed_pack_ref_for_path(
    raw_path: str,
    *,
    data_root: Path,
    family: str,
) -> ManagedPackRef | None:
    if not raw_path:
        return None
    base_dir = {
        "language": data_root / "language_packs",
        "frequency": data_root / "frequency_packs",
        "embedding": data_root / "embedding_packs",
    }.get(family)
    if base_dir is None:
        return None
    resolved_base = base_dir.resolve(strict=False)
    candidate = Path(raw_path).expanduser().resolve(strict=False)
    try:
        relpath = candidate.relative_to(resolved_base)
    except ValueError:
        return None
    if not relpath.parts:
        return None
    pack_id = str(relpath.parts[0] or "").strip()
    if not pack_id:
        return None
    try:
        manifest = load_installed_pack_manifest(resolved_base, pack_id)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    if manifest is None:
        return None
    if str(manifest.pack_kind or "").strip().lower() != family:
        return None
    if str(manifest.artifact_kind or "").strip().lower() != "sqlite":
        return None
    artifact_path = resolve_installed_pack_artifact(resolved_base, pack_id)
    if artifact_path is None:
        return None
    try:
        resolved_artifact = artifact_path.resolve(strict=False)
        resolved_pack_root = installed_pack_root(resolved_base, pack_id).resolve(strict=False)
    except OSError:
        return None
    if (
        candidate != resolved_artifact
        and candidate != resolved_pack_root
        and resolved_pack_root not in candidate.parents
    ):
        return None
    return ManagedPackRef(
        pack_id=pack_id,
        family=family,
        pack_root=resolved_pack_root,
        artifact_path=resolved_artifact,
    )


def _embedding_pair_key_by_pack_id() -> dict[str, str]:
    catalogs = build_pack_catalogs()
    rows = (*catalogs.embedding_packs, *catalogs.cross_embedding_packs)
    return {
        str(pack.pack_id).strip(): str(pack.pair_key).strip()
        for pack in rows
        if str(getattr(pack, "pack_id", "")).strip() and str(getattr(pack, "pair_key", "")).strip()
    }


def _load_json_object(path: Path) -> tuple[dict[str, object], list[str]]:
    if not path.exists() or not path.is_file():
        return {}, []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"invalid_json:{exc}"]
    if not isinstance(payload, Mapping):
        return {}, ["not_json_object"]
    return dict(payload), []


def _write_json_object(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _text_list(value: object) -> list[str]:
    return [str(item).strip() for item in _sequence(value) if str(item).strip()]


def _append_unique(values: list[str], value: str) -> list[str]:
    normalized = str(value or "").strip()
    if normalized and normalized not in values:
        values.append(normalized)
    return values


def _set_or_drop_mapping(
    target: dict[str, object],
    field_name: str,
    values: Mapping[object, object],
) -> None:
    if values:
        target[field_name] = dict(values)
    else:
        target.pop(field_name, None)


def _skipped_row(
    *,
    reason: str,
    field_name: str,
    pack_id: str,
    pair_key: str,
    path: str,
) -> dict[str, object]:
    return {
        "reason": reason,
        "field_name": field_name,
        "pack_id": pack_id,
        "pair_key": pair_key,
        "path": path,
    }


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _cell(value: object) -> str:
    text = str(value or "").replace("|", "\\|").replace("\n", " ").strip()
    return f"`{text}`" if text else ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
