#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
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
from lexishift_core.helper.pack_provenance import (  # noqa: E402
    PACK_PROVENANCE_FILENAME,
    validate_pack_provenance_file,
    write_app_managed_pack_provenance,
)
from lexishift_core.helper.pack_source_identity import (  # noqa: E402
    safe_pack_source_identity_fields,
    source_bundle_fields_for_pack,
)


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_provenance_backfill_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_provenance_backfill_latest.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill missing provenance.json sidecars for catalog-backed app-managed "
            "installed packs. Dry-run by default."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("~/.local/share/LexiShift/LexiShift"),
        help="LexiShift data root containing language_packs/frequency_packs/embedding_packs.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write missing provenance.json sidecars. Omit for a dry-run report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = backfill_installed_pack_provenance(
        data_root=args.data_root,
        apply_changes=args.apply,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_provenance_backfill_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if report["summary"]["error_count"]:
        return 1
    return 0


def backfill_installed_pack_provenance(
    *,
    data_root: Path,
    apply_changes: bool = False,
    generated_at: str | None = None,
) -> dict[str, object]:
    resolved_root = Path(data_root).expanduser().resolve(strict=False)
    rows: list[dict[str, object]] = []
    for family, base_dir, catalog in _family_catalogs(resolved_root):
        rows.extend(
            _scan_family(
                family=family,
                base_dir=base_dir,
                catalog=catalog,
                apply_changes=apply_changes,
            )
        )
    summary = _summary(rows=rows, apply_changes=apply_changes)
    return {
        "schema_version": 1,
        "generated_at": generated_at or _utc_now(),
        "data_root": str(resolved_root),
        "mode": "apply" if apply_changes else "dry_run",
        "status": summary["status"],
        "summary": summary,
        "packs": rows,
    }


def render_provenance_backfill_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# Pack Provenance Backfill",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Data root: `{report.get('data_root')}`",
        f"- Mode: `{report.get('mode')}`",
        f"- Status: `{report.get('status')}`",
        f"- Scanned packs: `{summary.get('scanned_pack_count', 0)}`",
        f"- Backfillable missing sidecars: `{summary.get('backfillable_count', 0)}`",
        f"- Written sidecars: `{summary.get('written_count', 0)}`",
        f"- Existing valid sidecars: `{summary.get('valid_existing_count', 0)}`",
        f"- Skipped packs: `{summary.get('skipped_count', 0)}`",
        f"- Error count: `{summary.get('error_count', 0)}`",
        "",
        "## Rows",
        "",
        "| Family | Pack | Action | Provenance | Issues |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in _mapping_rows(report.get("packs")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("family")),
                    _cell(row.get("pack_id")),
                    _cell(row.get("action")),
                    _cell(row.get("provenance_path")),
                    _cell(", ".join(str(item) for item in _sequence(row.get("issues")))),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _scan_family(
    *,
    family: str,
    base_dir: Path,
    catalog: Mapping[str, object],
    apply_changes: bool,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    root = Path(base_dir).expanduser().resolve(strict=False)
    if not root.exists() or not root.is_dir():
        return rows
    for pack_root in sorted(path for path in root.iterdir() if path.is_dir()):
        rows.append(
            _scan_pack_root(
                family=family,
                base_dir=root,
                pack_root=pack_root,
                catalog=catalog,
                apply_changes=apply_changes,
            )
        )
    return rows


def _scan_pack_root(
    *,
    family: str,
    base_dir: Path,
    pack_root: Path,
    catalog: Mapping[str, object],
    apply_changes: bool,
) -> dict[str, object]:
    pack_id = pack_root.name
    provenance_path = pack_root / PACK_PROVENANCE_FILENAME
    row: dict[str, object] = {
        "family": family,
        "pack_id": pack_id,
        "pack_root": str(pack_root),
        "manifest_path": str(pack_root / "manifest.json"),
        "artifact_path": "",
        "provenance_path": str(provenance_path),
        "provenance_exists": provenance_path.exists(),
        "provenance_valid": False,
        "action": "skip",
        "issues": [],
    }
    try:
        manifest = load_installed_pack_manifest(base_dir, pack_id)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        row["issues"] = [f"manifest_error:{exc}"]
        row["action"] = "error"
        return row
    if manifest is None:
        row["issues"] = ["missing_manifest"]
        return row
    manifest_pack_kind = str(manifest.pack_kind or "").strip()
    if manifest_pack_kind != family:
        row["issues"] = [f"unexpected_pack_kind:{manifest_pack_kind}"]
        return row
    catalog_pack = catalog.get(pack_id)
    if catalog_pack is None:
        row["issues"] = ["pack_not_in_catalog"]
        return row
    artifact_path = resolve_installed_pack_artifact(base_dir, pack_id)
    if artifact_path is None:
        row["issues"] = ["missing_artifact"]
        return row
    row["artifact_path"] = str(artifact_path)

    if provenance_path.exists():
        errors = list(validate_pack_provenance_file(provenance_path))
        row["provenance_valid"] = not errors
        row["issues"] = [f"provenance:{error}" for error in errors]
        row["action"] = "existing_valid" if not errors else "existing_invalid"
        return row

    write_issues = _backfill_preflight_issues(catalog_pack)
    if write_issues:
        row["issues"] = write_issues
        return row
    row["action"] = "would_write"
    if not apply_changes:
        return row

    try:
        write_app_managed_pack_provenance(
            pack_root=installed_pack_root(base_dir, pack_id),
            pack_id=pack_id,
            pack_kind=family,
            provider=_provider(manifest=manifest, catalog_pack=catalog_pack),
            source_name=_text(getattr(catalog_pack, "source", "")),
            source_url=_text(getattr(catalog_pack, "url", "")),
            wayback_url=_text(getattr(catalog_pack, "wayback_url", "")) or None,
            build_mode=_text(manifest.build_mode),
            build_command=_build_command_for_mode(_text(manifest.build_mode)),
            converter_version=_converter_version_for_mode(_text(manifest.build_mode)),
            parser_config=_parser_config_for_catalog_pack(catalog_pack),
            artifact_path=artifact_path,
            source_filename=manifest.source_filename
            or _optional_catalog_text(catalog_pack, "source_filename")
            or _optional_catalog_text(catalog_pack, "filename"),
            sqlite_filename=manifest.sqlite_filename
            or _optional_catalog_text(catalog_pack, "sqlite_filename"),
            required_files=manifest.required_files
            or tuple(getattr(catalog_pack, "required_files", ()) or ()),
            **safe_pack_source_identity_fields(catalog_pack),
            **source_bundle_fields_for_pack(catalog_pack),
        )
    except OSError as exc:
        row["action"] = "error"
        row["issues"] = [f"write_error:{exc}"]
        return row
    errors = list(validate_pack_provenance_file(provenance_path))
    row["provenance_exists"] = provenance_path.exists()
    row["provenance_valid"] = not errors
    row["issues"] = [f"provenance:{error}" for error in errors]
    row["action"] = "written" if not errors else "error"
    return row


def _family_catalogs(data_root: Path) -> tuple[tuple[str, Path, dict[str, object]], ...]:
    catalogs = build_pack_catalogs()
    language = {str(pack.pack_id): pack for pack in catalogs.language_packs}
    frequency = {str(pack.pack_id): pack for pack in catalogs.frequency_packs}
    embedding = {
        str(pack.pack_id): pack
        for pack in (*catalogs.embedding_packs, *catalogs.cross_embedding_packs)
    }
    return (
        ("language", data_root / "language_packs", language),
        ("frequency", data_root / "frequency_packs", frequency),
        ("embedding", data_root / "embedding_packs", embedding),
    )


def _backfill_preflight_issues(catalog_pack: object) -> list[str]:
    issues: list[str] = []
    if not _text(getattr(catalog_pack, "source", "")):
        issues.append("missing_catalog_source_name")
    if not _text(getattr(catalog_pack, "url", "")):
        issues.append("missing_catalog_source_url")
    return issues


def _build_command_for_mode(build_mode: str) -> str:
    commands = {
        "download_only": "download_only",
        "freedict_tei_to_sqlite": "convert_freedict_tei_to_sqlite",
        "kaikki_glosses_to_sqlite": "convert_kaikki_glosses_to_sqlite",
        "kaikki_translations_to_sqlite": "convert_kaikki_translations_to_sqlite",
        "convert_archive": "convert_frequency_to_sqlite",
        "de_frequency_pipeline": "run_de_frequency_pipeline",
        "convert_to_sqlite": "scripts/data/convert_embeddings.py",
    }
    normalized = str(build_mode or "").strip()
    return commands.get(normalized, normalized)


def _converter_version_for_mode(build_mode: str) -> str:
    converter_sources = {
        "freedict_tei_to_sqlite": (
            "lexishift_core.resources.freedict_sqlite",
            CORE_ROOT / "lexishift_core" / "resources" / "freedict_sqlite.py",
        ),
        "kaikki_glosses_to_sqlite": (
            "lexishift_core.resources.kaikki_sqlite",
            CORE_ROOT / "lexishift_core" / "resources" / "kaikki_sqlite.py",
        ),
        "kaikki_translations_to_sqlite": (
            "lexishift_core.resources.kaikki_sqlite",
            CORE_ROOT / "lexishift_core" / "resources" / "kaikki_sqlite.py",
        ),
        "convert_archive": (
            "lexishift_core.frequency.sqlite",
            CORE_ROOT / "lexishift_core" / "frequency" / "sqlite.py",
        ),
        "de_frequency_pipeline": (
            "lexishift_core.frequency.de.pipeline",
            CORE_ROOT / "lexishift_core" / "frequency" / "de" / "pipeline.py",
        ),
        "convert_to_sqlite": (
            "scripts.data.convert_embeddings",
            PROJECT_ROOT / "scripts" / "data" / "convert_embeddings.py",
        ),
    }
    label, path = converter_sources.get(str(build_mode or "").strip(), ("", Path()))
    if not label:
        return ""
    return _source_file_version(label, path)


def _source_file_version(label: str, path: Path) -> str:
    if not path.is_file():
        return ""
    digest = sha256(path.read_bytes()).hexdigest()
    return f"source_sha256:{label}:{digest}"


def _parser_config_for_catalog_pack(catalog_pack: object) -> dict[str, object]:
    build_mode = _text(getattr(catalog_pack, "build_mode", ""))
    if build_mode == "freedict_tei_to_sqlite":
        required_files = tuple(getattr(catalog_pack, "required_files", ()) or ())
        return {
            "target_lang": _text(getattr(catalog_pack, "target_lang_code", "")),
            "tei_filename": required_files[0] if required_files else "",
        }
    if build_mode == "kaikki_glosses_to_sqlite":
        return {
            "source_lang_code": _text(getattr(catalog_pack, "source_lang_code", "")).lower()
            or "es",
            "gloss_language": _text(getattr(catalog_pack, "gloss_language", "")).lower() or "en",
            "source_dump": "enwiktionary",
        }
    if build_mode == "kaikki_translations_to_sqlite":
        target_lang = _text(getattr(catalog_pack, "target_lang_code", "")).lower()
        return {
            "source_lang_code": _text(getattr(catalog_pack, "source_lang_code", "")).lower(),
            "target_lang_code": target_lang,
            "translation_language": _text(
                getattr(catalog_pack, "gloss_language", "") or target_lang
            ).lower(),
            "source_dump": "enwiktionary",
        }
    if build_mode == "de_frequency_pipeline":
        return {"drop_proper_nouns": True}
    parse_config = getattr(catalog_pack, "parse_config", None)
    if parse_config is None:
        return {}
    parser_config: dict[str, object] = {
        "delimiter": getattr(parse_config, "delimiter", ""),
        "header_starts_with": getattr(parse_config, "header_starts_with", None),
        "skip_prefixes": list(getattr(parse_config, "skip_prefixes", ()) or ()),
        "encoding": getattr(parse_config, "encoding", ""),
        "errors": getattr(parse_config, "errors", ""),
        "index_column": _text(getattr(catalog_pack, "index_column", "")),
    }
    return parser_config


def _provider(*, manifest: object, catalog_pack: object) -> str:
    return (
        _text(getattr(manifest, "provider", ""))
        or _text(getattr(catalog_pack, "source", "")).lower()
    )


def _optional_catalog_text(catalog_pack: object, field_name: str) -> str | None:
    value = _text(getattr(catalog_pack, field_name, ""))
    return value or None


def _summary(*, rows: Sequence[Mapping[str, object]], apply_changes: bool) -> dict[str, object]:
    backfillable_count = sum(1 for row in rows if row.get("action") == "would_write")
    written_count = sum(1 for row in rows if row.get("action") == "written")
    error_count = sum(1 for row in rows if row.get("action") == "error")
    skipped_count = sum(
        1
        for row in rows
        if row.get("action") in {"skip", "existing_invalid"} and bool(row.get("issues"))
    )
    status = "ok"
    if error_count:
        status = "error"
    elif apply_changes and written_count:
        status = "applied"
    elif not apply_changes and backfillable_count:
        status = "would_update"
    return {
        "status": status,
        "scanned_pack_count": len(rows),
        "backfillable_count": backfillable_count,
        "written_count": written_count,
        "valid_existing_count": sum(1 for row in rows if row.get("action") == "existing_valid"),
        "skipped_count": skipped_count,
        "error_count": error_count,
    }


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Mapping):
        iterable = value.values()
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        iterable = value
    else:
        return []
    return [item for item in iterable if isinstance(item, Mapping)]


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _cell(value: object) -> str:
    text = str(value or "").replace("|", "\\|").replace("\n", " ").strip()
    return f"`{text}`" if text else ""


def _text(value: object) -> str:
    return str(value or "").strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
