from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Mapping, Optional, Sequence

from lexishift_core.resources.installed_packs import (
    load_installed_pack_manifest_for_artifact,
    resolve_installed_pack_artifact,
)

POS_OVERLAY_TABLE = "pos_overlay"
DEFAULT_POS_OVERLAY_PACKS_BY_TARGET = {
    "es": ("pos-es-ud-ancora-v1",),
}
DEFAULT_POS_OVERLAY_PROVIDER = "universal-dependencies-ud-ancora"
DEFAULT_POS_OVERLAY_SOURCE_PROFILE = "universal-dependencies"


@dataclass(frozen=True)
class PosOverlayRef:
    pair: str
    path: Path
    pack_id: str
    provider: str
    resolution: str


@dataclass(frozen=True)
class PosOverlayEntry:
    lemma: str
    raw_pos: str
    pos_canonical: str
    pos_bucket: str
    pos_source_profile: str
    pos_matched_rule: str
    confidence: float | None
    source_count: int | None
    total_count: int | None
    source_provider: str
    overlay_id: str


def resolve_pair_pos_overlay(
    paths: object,
    *,
    pair: str,
    pos_overlay_path: Path | None = None,
) -> Optional[PosOverlayRef]:
    resolved_pair = str(pair or "").strip().lower()
    if pos_overlay_path is not None:
        candidate = Path(pos_overlay_path).expanduser().resolve(strict=False)
        if candidate.is_file():
            return _build_pos_overlay_ref(
                pair=resolved_pair,
                path=candidate,
                resolution="explicit",
            )
        return None

    for pack_id in _default_pos_overlay_pack_ids(resolved_pair):
        for base_dir_name in ("pos_packs", "pos_overlays"):
            base_dir = getattr(paths, "data_root", None)
            if base_dir is None:
                continue
            artifact = resolve_installed_pack_artifact(Path(base_dir) / base_dir_name, pack_id)
            if artifact is not None and artifact.is_file():
                return _build_pos_overlay_ref(
                    pair=resolved_pair,
                    path=artifact,
                    resolution=f"managed:{pack_id}",
                )
        for candidate in _legacy_pos_overlay_candidates(paths, pack_id):
            if candidate.is_file():
                return _build_pos_overlay_ref(
                    pair=resolved_pair,
                    path=candidate,
                    resolution=f"legacy:{pack_id}",
                )
    return None


def pos_overlay_resource_payload(ref: PosOverlayRef | None) -> dict[str, object]:
    if ref is None:
        return {
            "pos_overlay_path": None,
            "pos_overlay_exists": False,
            "pos_overlay_id": None,
            "pos_overlay_provider": None,
            "pos_overlay_resolution": "missing",
        }
    return {
        "pos_overlay_path": str(ref.path),
        "pos_overlay_exists": ref.path.exists(),
        "pos_overlay_id": ref.pack_id,
        "pos_overlay_provider": ref.provider,
        "pos_overlay_resolution": ref.resolution,
    }


def load_pos_overlay_entries(path: Path | None) -> dict[str, PosOverlayEntry]:
    if path is None:
        return {}
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return {}
    with sqlite3.connect(candidate) as conn:
        if not _table_exists(conn, POS_OVERLAY_TABLE):
            return {}
        columns = _column_names(conn, POS_OVERLAY_TABLE)
        if "lemma" not in columns:
            return {}
        select_columns = [
            column
            for column in (
                "lemma",
                "raw_pos",
                "pos",
                "pos_canonical",
                "pos_bucket",
                "pos_source_profile",
                "pos_matched_rule",
                "confidence",
                "source_count",
                "total_count",
                "source_provider",
                "overlay_id",
            )
            if column in columns
        ]
        rows = conn.execute(
            "SELECT "
            + ", ".join(_quote_ident(column) for column in select_columns)
            + f" FROM {_quote_ident(POS_OVERLAY_TABLE)}"
        ).fetchall()
    entries: dict[str, PosOverlayEntry] = {}
    for row in rows:
        payload = dict(zip(select_columns, row))
        entry = _entry_from_row(payload)
        if entry is None:
            continue
        entries.setdefault(_lemma_key(entry.lemma), entry)
    return entries


def lookup_pos_overlay_entry(
    entries: Mapping[str, PosOverlayEntry],
    lemma: object,
) -> PosOverlayEntry | None:
    return entries.get(_lemma_key(str(lemma or "")))


def _entry_from_row(row: Mapping[str, object]) -> PosOverlayEntry | None:
    lemma = str(row.get("lemma") or "").strip()
    if not lemma:
        return None
    raw_pos = str(row.get("raw_pos") or row.get("pos") or "").strip()
    if not raw_pos:
        return None
    return PosOverlayEntry(
        lemma=lemma,
        raw_pos=raw_pos,
        pos_canonical=str(row.get("pos_canonical") or "").strip(),
        pos_bucket=str(row.get("pos_bucket") or "").strip(),
        pos_source_profile=(
            str(row.get("pos_source_profile") or "").strip() or DEFAULT_POS_OVERLAY_SOURCE_PROFILE
        ),
        pos_matched_rule=str(row.get("pos_matched_rule") or "").strip(),
        confidence=_optional_float(row.get("confidence")),
        source_count=_optional_int(row.get("source_count")),
        total_count=_optional_int(row.get("total_count")),
        source_provider=(
            str(row.get("source_provider") or "").strip() or DEFAULT_POS_OVERLAY_PROVIDER
        ),
        overlay_id=str(row.get("overlay_id") or "").strip(),
    )


def _build_pos_overlay_ref(
    *,
    pair: str,
    path: Path,
    resolution: str,
) -> PosOverlayRef:
    manifest = load_installed_pack_manifest_for_artifact(path)
    pack_id = (
        str(manifest.pack_id).strip()
        if manifest and str(manifest.pack_id).strip()
        else _infer_pack_id(path)
    )
    provider = (
        str(manifest.provider).strip()
        if manifest and str(manifest.provider).strip()
        else DEFAULT_POS_OVERLAY_PROVIDER
    )
    return PosOverlayRef(
        pair=pair,
        path=path,
        pack_id=pack_id,
        provider=provider,
        resolution=resolution,
    )


def _default_pos_overlay_pack_ids(pair: str) -> tuple[str, ...]:
    target = _target_language(pair)
    return DEFAULT_POS_OVERLAY_PACKS_BY_TARGET.get(target, ())


def _legacy_pos_overlay_candidates(paths: object, pack_id: str) -> tuple[Path, ...]:
    data_root = getattr(paths, "data_root", None)
    language_packs_dir = getattr(paths, "language_packs_dir", None)
    candidates: list[Path] = []
    if data_root is not None:
        root = Path(data_root)
        candidates.extend(
            (
                root / "pos_packs" / pack_id / "main.sqlite",
                root / "pos_overlays" / pack_id / "main.sqlite",
                root / "pos_overlays" / f"{pack_id}.sqlite",
            )
        )
    if language_packs_dir is not None:
        root = Path(language_packs_dir)
        candidates.extend((root / pack_id / "main.sqlite", root / f"{pack_id}.sqlite"))
    return _unique_paths(candidates)


def _unique_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return tuple(unique)


def _target_language(pair: str) -> str:
    _source, separator, target = str(pair or "").strip().lower().partition("-")
    return target if separator else ""


def _infer_pack_id(path: Path) -> str:
    name = path.name.strip()
    if name.endswith((".sqlite", ".sqlite3", ".db")):
        return name.rsplit(".", 1)[0]
    return path.parent.name or name


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({_quote_ident(table)})")}


def _quote_ident(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _lemma_key(value: str) -> str:
    return str(value or "").strip().casefold()


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


__all__ = [
    "PosOverlayEntry",
    "PosOverlayRef",
    "load_pos_overlay_entries",
    "lookup_pos_overlay_entry",
    "pos_overlay_resource_payload",
    "resolve_pair_pos_overlay",
]
