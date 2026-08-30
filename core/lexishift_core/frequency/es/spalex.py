from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import unicodedata
from typing import Iterable, Mapping, Sequence


from lexishift_core.helper.installed_packs import write_installed_pack_manifest
from lexishift_core.helper.pack_provenance import (
    write_app_managed_pack_provenance,
)
from lexishift_core.pos.normalization import normalize_pos


DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_CURRENT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-es-cde.sqlite"
DEFAULT_KAIKKI_FORWARD_DB = (
    DEFAULT_DATA_ROOT / "language_packs" / "wiktionary-es-en" / "main.sqlite"
)
DEFAULT_PACK_ID = "freq-es-spalex-v1"
DEFAULT_PROVIDER = DEFAULT_PACK_ID
DEFAULT_SOURCE_MODE = "spalex_only"
SOURCE_MODE_SPALEX_ONLY = "spalex_only"
SOURCE_MODE_CDE_UNION = "spalex_cde_union"
SOURCE_MODES = (SOURCE_MODE_SPALEX_ONLY, SOURCE_MODE_CDE_UNION)
DEFAULT_SPALEX_SOURCE_URL = "https://figshare.com/articles/dataset/Word_information/5924794"
DEFAULT_SPALEX_DOI = "10.6084/m9.figshare.5924794.v4"
DEFAULT_SPALEX_LICENSE = "CC BY 4.0"
KAIKKI_LICENSE_POSTURE = "review_required_cc_by_sa_gfdl_obligations"
SPALEX_COLUMNS = (
    "spelling",
    "count_total",
    "percent_total",
    "prevalence_total",
    "count_nts",
    "percent_nts",
    "prevalence_nts",
    "count_ntl",
    "percent_ntl",
    "prevalence_ntl",
    "freq",
    "zipf",
)
FREQUENCY_COLUMNS_SQL = """
CREATE TABLE frequency (
  id REAL,
  pmw REAL,
  freq REAL,
  lemma TEXT,
  pos TEXT,
  source_family TEXT,
  source_rank REAL,
  source_frequency REAL,
  cde_rank REAL,
  cde_freq REAL,
  cde_pos TEXT,
  spalex_rank REAL,
  spalex_freq REAL,
  spalex_zipf REAL,
  spalex_prevalence_total REAL,
  spalex_percent_total REAL,
  pos_source TEXT,
  pos_canonical TEXT,
  topics TEXT,
  topic_source TEXT
);
"""
POS_COMPACT_BY_CANONICAL = {
    "noun": "n",
    "adjective": "j",
    "verb": "v",
    "adverb": "r",
    "pronoun": "p",
    "determiner": "d",
    "adposition": "e",
    "conjunction": "c",
    "interjection": "i",
    "numeral": "m",
    "punctuation": "-",
    "other": "u",
}
POS_PRIORITY = {
    "noun": 0,
    "adjective": 1,
    "verb": 2,
    "adverb": 3,
    "pronoun": 4,
    "determiner": 5,
    "adposition": 6,
    "conjunction": 7,
    "interjection": 8,
    "numeral": 9,
    "punctuation": 10,
    "other": 11,
}


@dataclass(frozen=True)
class CurrentFrequencyRow:
    lemma: str
    rank: float | None
    freq: float | None
    pos: str


@dataclass(frozen=True)
class SpalexRow:
    lemma: str
    rank: int
    freq: float | None
    zipf: float | None
    prevalence_total: float | None
    percent_total: float | None


@dataclass(frozen=True)
class KaikkiEnrichment:
    pos_compact: str
    pos_canonical: str
    topics: tuple[str, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a reversible en-es research frequency pack from SPALEX. "
            "The default mode is SPALEX-only so publishable candidates do not "
            "inherit the manual-supply freq-es-cde source."
        )
    )
    parser.add_argument("--spalex-csv", type=Path, required=True)
    parser.add_argument("--output-sqlite", type=Path)
    parser.add_argument("--pack-root", type=Path)
    parser.add_argument("--pack-id", default=DEFAULT_PACK_ID)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument(
        "--source-mode",
        choices=SOURCE_MODES,
        default=DEFAULT_SOURCE_MODE,
        help=(
            "spalex_only builds the publishable candidate without freq-es-cde. "
            "spalex_cde_union keeps the legacy internal comparison stack."
        ),
    )
    parser.add_argument(
        "--current-frequency-db",
        type=Path,
        default=DEFAULT_CURRENT_FREQUENCY_DB,
        help="Only used by --source-mode spalex_cde_union.",
    )
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument(
        "--no-kaikki-enrichment",
        action="store_true",
        help="Build a frequency-only SPALEX pack without Kaikki POS/topic enrichment.",
    )
    parser.add_argument("--target-size", type=int, default=0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--write-sidecars", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_sqlite = _resolve_output_sqlite(
        output_sqlite=args.output_sqlite,
        pack_root=args.pack_root,
        pack_id=args.pack_id,
    )
    metadata = build_spalex_frequency_pack(
        spalex_csv=args.spalex_csv,
        current_frequency_db=args.current_frequency_db,
        output_sqlite=output_sqlite,
        kaikki_forward_db=None if args.no_kaikki_enrichment else args.kaikki_forward_db,
        pack_id=args.pack_id,
        provider=args.provider,
        source_mode=args.source_mode,
        target_size=args.target_size,
        overwrite=args.overwrite,
        write_sidecars=args.write_sidecars,
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def build_spalex_frequency_pack(
    *,
    spalex_csv: Path,
    current_frequency_db: Path | None = DEFAULT_CURRENT_FREQUENCY_DB,
    output_sqlite: Path,
    kaikki_forward_db: Path | None = None,
    pack_id: str = DEFAULT_PACK_ID,
    provider: str = DEFAULT_PROVIDER,
    source_mode: str = DEFAULT_SOURCE_MODE,
    target_size: int = 0,
    overwrite: bool = False,
    write_sidecars: bool = False,
) -> dict[str, object]:
    normalized_source_mode = _normalize_source_mode(source_mode)
    output = Path(output_sqlite).expanduser().resolve(strict=False)
    if output.exists():
        if overwrite:
            output.unlink()
        else:
            raise FileExistsError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    resolved_kaikki_forward_db = _resolve_optional_pack_sqlite(kaikki_forward_db)
    current_rows = (
        _load_current_frequency_rows(_require_current_frequency_db(current_frequency_db))
        if normalized_source_mode == SOURCE_MODE_CDE_UNION
        else {}
    )
    spalex_rows = _load_spalex_rows(spalex_csv)
    enrichments = (
        _load_kaikki_enrichment(resolved_kaikki_forward_db) if resolved_kaikki_forward_db else {}
    )
    combined_rows = _combine_rows(
        current_rows,
        spalex_rows,
        source_mode=normalized_source_mode,
        target_size=target_size,
    )
    row_count = _write_frequency_sqlite(
        output,
        combined_rows=combined_rows,
        current_rows=current_rows,
        spalex_rows=spalex_rows,
        enrichments=enrichments,
        pack_id=pack_id,
        provider=provider,
        source_paths={
            "spalex_csv": Path(spalex_csv),
            "current_frequency_db": Path(current_frequency_db) if current_frequency_db else None,
            "kaikki_forward_db": resolved_kaikki_forward_db,
        },
        source_mode=normalized_source_mode,
    )
    metrics = _frequency_metrics(output)
    metadata = {
        "pack_id": pack_id,
        "provider": provider,
        "source_mode": normalized_source_mode,
        "output_sqlite": str(output),
        "row_count": row_count,
        "metrics": metrics,
        "source_counts": {
            "current_cde_distinct": len(current_rows),
            "spalex_clean_distinct": len(spalex_rows),
            "combined_distinct": len(combined_rows),
            "spalex_added": sum(1 for row in combined_rows if row["source_family"] == "spalex"),
            "spalex_included": sum(1 for row in combined_rows if row["source_family"] == "spalex"),
            "cde_included": sum(
                1 for row in combined_rows if row["source_family"] == "freq-es-cde"
            ),
        },
        "sidecars_written": False,
    }
    if write_sidecars:
        metadata["sidecars"] = _write_sidecars(
            output_sqlite=output,
            pack_id=pack_id,
            provider=provider,
            source_mode=normalized_source_mode,
            spalex_csv=Path(spalex_csv),
            current_frequency_db=Path(current_frequency_db) if current_frequency_db else None,
            kaikki_forward_db=resolved_kaikki_forward_db,
            metrics=metrics,
        )
        metadata["sidecars_written"] = True
    return metadata


def _load_current_frequency_rows(path: Path) -> dict[str, CurrentFrequencyRow]:
    resolved = _resolve_optional_pack_sqlite(path) or Path(path).expanduser().resolve(strict=False)
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    rows: dict[str, CurrentFrequencyRow] = {}
    with sqlite3.connect(resolved) as conn:
        columns = _column_names(conn, "frequency")
        rank_column = "id" if "id" in columns else "rank" if "rank" in columns else "rowid"
        freq_column = "freq" if "freq" in columns else "pmw" if "pmw" in columns else "NULL"
        pos_column = "pos" if "pos" in columns else "''"
        for lemma, rank, freq, pos in conn.execute(
            f"""
            SELECT lemma, {rank_column}, {freq_column}, {pos_column}
            FROM frequency
            WHERE TRIM(COALESCE(lemma, '')) != ''
            ORDER BY {rank_column}
            """
        ):
            normalized = _normalize_lemma(lemma)
            if not normalized or normalized in rows:
                continue
            rows[normalized] = CurrentFrequencyRow(
                lemma=normalized,
                rank=_to_float(rank),
                freq=_to_float(freq),
                pos=str(pos or "").strip(),
            )
    return rows


def _normalize_source_mode(value: object) -> str:
    mode = str(value or DEFAULT_SOURCE_MODE).strip().lower()
    if mode not in SOURCE_MODES:
        allowed = ", ".join(SOURCE_MODES)
        raise ValueError(f"Unsupported SPALEX source mode {mode!r}; expected one of: {allowed}")
    return mode


def _require_current_frequency_db(path: Path | None) -> Path:
    if path is None:
        raise ValueError("--current-frequency-db is required for source_mode=spalex_cde_union")
    return Path(path)


def _resolve_optional_pack_sqlite(path: Path | None) -> Path | None:
    if path is None:
        return None
    requested = Path(path).expanduser().resolve(strict=False)
    if requested.is_file():
        return requested
    if requested.suffix == ".sqlite":
        managed = requested.parent / requested.stem / "main.sqlite"
        if managed.is_file():
            return managed.expanduser().resolve(strict=False)
    if requested.is_dir():
        managed = requested / "main.sqlite"
        if managed.is_file():
            return managed.expanduser().resolve(strict=False)
    return None


def _load_spalex_rows(path: Path) -> dict[str, SpalexRow]:
    resolved = Path(path).expanduser().resolve(strict=False)
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    raw_rows: list[dict[str, object]] = []
    with resolved.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = tuple(reader.fieldnames or ())
        missing = [column for column in SPALEX_COLUMNS if column not in columns]
        if missing:
            raise ValueError(f"SPALEX CSV missing required columns: {', '.join(missing)}")
        for raw in reader:
            lemma = _normalize_lemma(raw.get("spelling"))
            if not _is_clean_surface(lemma):
                continue
            raw_rows.append(
                {
                    "lemma": lemma,
                    "freq": _to_float(raw.get("freq")),
                    "zipf": _to_float(raw.get("zipf")),
                    "prevalence_total": _to_float(raw.get("prevalence_total")),
                    "percent_total": _to_float(raw.get("percent_total")),
                }
            )
    deduped = _dedupe_spalex_rows(raw_rows)
    ranked = sorted(
        deduped,
        key=lambda row: (
            _float_or_floor(row.get("zipf")),
            _float_or_floor(row.get("prevalence_total")),
            str(row.get("lemma") or ""),
        ),
        reverse=True,
    )
    return {
        str(row["lemma"]): SpalexRow(
            lemma=str(row["lemma"]),
            rank=index,
            freq=_to_float(row.get("freq")),
            zipf=_to_float(row.get("zipf")),
            prevalence_total=_to_float(row.get("prevalence_total")),
            percent_total=_to_float(row.get("percent_total")),
        )
        for index, row in enumerate(ranked, start=1)
    }


def _load_kaikki_enrichment(path: Path) -> dict[str, KaikkiEnrichment]:
    resolved = Path(path).expanduser().resolve(strict=False)
    if not resolved.exists():
        return {}
    raw_pos_by_lemma: dict[str, list[str]] = defaultdict(list)
    topics_by_lemma: dict[str, set[str]] = defaultdict(set)
    with sqlite3.connect(resolved) as conn:
        for lemma, raw_pos in conn.execute(
            "SELECT headword_lc, pos FROM entry_meta WHERE TRIM(COALESCE(headword_lc, '')) != ''"
        ):
            raw_pos_by_lemma[_normalize_lemma(lemma)].append(str(raw_pos or "").strip())
        for lemma, topics_json in conn.execute(
            "SELECT headword_lc, topics_json FROM sense_glosses "
            "WHERE COALESCE(topics_json, '') NOT IN ('', '[]')"
        ):
            topics_by_lemma[_normalize_lemma(lemma)].update(_json_string_list(topics_json))
    enrichments: dict[str, KaikkiEnrichment] = {}
    for lemma, raw_values in raw_pos_by_lemma.items():
        canonical = _select_canonical_pos(raw_values)
        topics = tuple(sorted(topics_by_lemma.get(lemma, set())))
        enrichments[lemma] = KaikkiEnrichment(
            pos_compact=POS_COMPACT_BY_CANONICAL.get(canonical, ""),
            pos_canonical=canonical,
            topics=topics,
        )
    for lemma, topic_values in topics_by_lemma.items():
        if lemma not in enrichments:
            enrichments[lemma] = KaikkiEnrichment(
                pos_compact="",
                pos_canonical="",
                topics=tuple(sorted(topic_values)),
            )
    return enrichments


def _combine_rows(
    current_rows: Mapping[str, CurrentFrequencyRow],
    spalex_rows: Mapping[str, SpalexRow],
    *,
    source_mode: str,
    target_size: int,
) -> list[dict[str, object]]:
    normalized_source_mode = _normalize_source_mode(source_mode)
    combined: list[dict[str, object]] = []
    seen: set[str] = set()
    if normalized_source_mode == SOURCE_MODE_CDE_UNION:
        for current_row in current_rows.values():
            seen.add(current_row.lemma)
            combined.append({"lemma": current_row.lemma, "source_family": "freq-es-cde"})
    for spalex_row in sorted(spalex_rows.values(), key=lambda item: item.rank):
        if spalex_row.lemma in seen:
            continue
        seen.add(spalex_row.lemma)
        combined.append({"lemma": spalex_row.lemma, "source_family": "spalex"})
        if target_size and len(combined) >= target_size:
            break
    return combined[:target_size] if target_size else combined


def _write_frequency_sqlite(
    output: Path,
    *,
    combined_rows: Sequence[Mapping[str, object]],
    current_rows: Mapping[str, CurrentFrequencyRow],
    spalex_rows: Mapping[str, SpalexRow],
    enrichments: Mapping[str, KaikkiEnrichment],
    pack_id: str,
    provider: str,
    source_paths: Mapping[str, Path | None],
    source_mode: str,
) -> int:
    total = len(combined_rows)
    inserted_rows = []
    for index, row in enumerate(combined_rows, start=1):
        lemma = str(row["lemma"])
        source_family = str(row["source_family"])
        cde = current_rows.get(lemma)
        spalex = spalex_rows.get(lemma)
        enrichment = enrichments.get(lemma)
        pos = _resolve_compact_pos(cde, enrichment)
        topics = ",".join(enrichment.topics) if enrichment and enrichment.topics else ""
        inserted_rows.append(
            (
                float(index),
                float(total - index + 1),
                _source_frequency(source_family, cde, spalex),
                lemma,
                pos,
                source_family,
                _source_rank(source_family, cde, spalex),
                _source_frequency(source_family, cde, spalex),
                cde.rank if cde else None,
                cde.freq if cde else None,
                cde.pos if cde else "",
                float(spalex.rank) if spalex else None,
                spalex.freq if spalex else None,
                spalex.zipf if spalex else None,
                spalex.prevalence_total if spalex else None,
                spalex.percent_total if spalex else None,
                _pos_source(cde, enrichment),
                enrichment.pos_canonical if enrichment else "",
                topics,
                "wiktionary-es-en:sense_glosses.topics_json" if topics else "",
            )
        )
    with sqlite3.connect(output) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute(FREQUENCY_COLUMNS_SQL)
        conn.executemany(
            """
            INSERT INTO frequency (
              id, pmw, freq, lemma, pos, source_family, source_rank,
              source_frequency, cde_rank, cde_freq, cde_pos, spalex_rank,
              spalex_freq, spalex_zipf, spalex_prevalence_total,
              spalex_percent_total, pos_source, pos_canonical, topics, topic_source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            inserted_rows,
        )
        conn.execute("CREATE INDEX idx_frequency_lemma ON frequency(lemma);")
        conn.execute("CREATE INDEX idx_frequency_rank ON frequency(id);")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);")
        metadata = _sqlite_metadata(
            pack_id=pack_id,
            provider=provider,
            row_count=len(inserted_rows),
            source_paths=source_paths,
            source_mode=source_mode,
            has_kaikki_enrichment=bool(enrichments),
        )
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?);",
            ("metadata", json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
        )
        conn.commit()
    return len(inserted_rows)


def _write_sidecars(
    *,
    output_sqlite: Path,
    pack_id: str,
    provider: str,
    source_mode: str,
    spalex_csv: Path,
    current_frequency_db: Path | None,
    kaikki_forward_db: Path | None,
    metrics: Mapping[str, object],
) -> dict[str, str]:
    mode = _normalize_source_mode(source_mode)
    pack_root = output_sqlite.parent
    base_dir = pack_root.parent
    manifest = write_installed_pack_manifest(
        base_dir,
        pack_id=pack_id,
        pack_kind="frequency",
        provider=provider,
        local_kind="file",
        build_mode=mode,
        artifact_path=output_sqlite,
        source_filename=spalex_csv.name,
        sqlite_filename=output_sqlite.name,
        required_files=_required_source_filenames(
            source_mode=mode,
            spalex_csv=spalex_csv,
            current_frequency_db=current_frequency_db,
        ),
        raw_retained=False,
    )
    required_source_filenames = _required_source_filenames(
        source_mode=mode,
        spalex_csv=spalex_csv,
        current_frequency_db=current_frequency_db,
    )
    provenance = write_app_managed_pack_provenance(
        pack_root=pack_root,
        pack_id=pack_id,
        pack_kind="frequency",
        provider=provider,
        source_name=_source_name_for_mode(mode, kaikki_forward_db=kaikki_forward_db),
        source_url=DEFAULT_SPALEX_SOURCE_URL,
        source_filename=spalex_csv.name,
        sqlite_filename=output_sqlite.name,
        required_files=required_source_filenames,
        build_mode=mode,
        artifact_path=output_sqlite,
        build_command="python3 scripts/data/build_spalex_frequency_pack_en_es.py",
        converter_version="build_spalex_frequency_pack_en_es_v2",
        parser_profile=_parser_profile_for_mode(mode),
        parser_config=_parser_config_for_mode(mode, kaikki_forward_db=kaikki_forward_db),
        source_version=DEFAULT_SPALEX_DOI,
        source_bundle=_source_bundle(
            pack_id=pack_id,
            source_mode=mode,
            spalex_csv=spalex_csv,
            current_frequency_db=current_frequency_db,
            kaikki_forward_db=kaikki_forward_db,
        ),
        raw_artifact_sha1=_sha1_file(spalex_csv),
        raw_artifact_sha256=_sha256_file(spalex_csv),
        artifact_metrics=metrics,
        license_status=_license_status_for_stack(mode, kaikki_forward_db=kaikki_forward_db),
    )
    return {"manifest": str(manifest), "provenance": str(provenance)}


def _source_bundle(
    *,
    pack_id: str,
    source_mode: str,
    spalex_csv: Path,
    current_frequency_db: Path | None,
    kaikki_forward_db: Path | None,
) -> dict[str, object]:
    mode = _normalize_source_mode(source_mode)
    components = [
        _source_component(
            role="primary_frequency",
            source_name="SPALEX word information",
            source_url=DEFAULT_SPALEX_SOURCE_URL,
            filename=spalex_csv.name,
            path=spalex_csv,
            license=DEFAULT_SPALEX_LICENSE,
        )
    ]
    if mode == SOURCE_MODE_CDE_UNION and current_frequency_db is not None:
        components.append(
            _source_component(
                role="legacy_seed_frequency",
                source_name="freq-es-cde installed baseline",
                build_ref="freq-es-cde",
                filename=current_frequency_db.name,
                path=current_frequency_db,
                license="review_required_manual_supply",
            )
        )
    if kaikki_forward_db is not None:
        components.append(
            _source_component(
                role="pos_topic_enrichment",
                source_name="Kaikki/Wiktionary Spanish headword pack",
                build_ref="wiktionary-es-en",
                filename=kaikki_forward_db.name,
                path=kaikki_forward_db,
                license=KAIKKI_LICENSE_POSTURE,
            )
        )
    return {
        "bundle_id": f"{pack_id}:{_bundle_suffix(mode, kaikki_forward_db=kaikki_forward_db)}",
        "bundle_kind": "generated_frequency_pipeline",
        "lineage_status": "pinned_component_artifacts",
        "components": components,
    }


def _required_source_filenames(
    *,
    source_mode: str,
    spalex_csv: Path,
    current_frequency_db: Path | None,
) -> tuple[str, ...]:
    names = [spalex_csv.name]
    if _normalize_source_mode(source_mode) == SOURCE_MODE_CDE_UNION and current_frequency_db:
        names.append(current_frequency_db.name)
    return tuple(names)


def _source_name_for_mode(source_mode: str, *, kaikki_forward_db: Path | None) -> str:
    mode = _normalize_source_mode(source_mode)
    enrichment = " plus Kaikki enrichment" if kaikki_forward_db is not None else ""
    if mode == SOURCE_MODE_CDE_UNION:
        return f"SPALEX plus freq-es-cde seed{enrichment}"
    return f"SPALEX word information{enrichment}"


def _parser_profile_for_mode(source_mode: str) -> str:
    if _normalize_source_mode(source_mode) == SOURCE_MODE_CDE_UNION:
        return "spalex_cde_union_v1"
    return "spalex_only_v1"


def _parser_config_for_mode(
    source_mode: str, *, kaikki_forward_db: Path | None
) -> dict[str, object]:
    mode = _normalize_source_mode(source_mode)
    has_kaikki_enrichment = kaikki_forward_db is not None
    parser_config: dict[str, object] = {
        "primary_source": "spalex_word_info_csv",
        "rank_policy": "spalex_zipf_then_prevalence",
        "runtime_pmw": "rank_descending_commonness_score",
        "topic_policy": "kaikki_sense_topics_only" if has_kaikki_enrichment else "none",
    }
    if mode == SOURCE_MODE_CDE_UNION:
        parser_config.update(
            {
                "current_seed": "freq-es-cde",
                "rank_policy": "freq_es_cde_seed_then_spalex_zipf_prevalence",
                "pos_policy": _pos_policy_for_mode(
                    mode,
                    has_kaikki_enrichment=has_kaikki_enrichment,
                ),
            }
        )
    else:
        parser_config.update(
            {
                "current_seed": "none",
                "pos_policy": _pos_policy_for_mode(
                    mode,
                    has_kaikki_enrichment=has_kaikki_enrichment,
                ),
            }
        )
    return parser_config


def _pos_policy_for_mode(source_mode: str, *, has_kaikki_enrichment: bool) -> str:
    mode = _normalize_source_mode(source_mode)
    if mode == SOURCE_MODE_CDE_UNION:
        return (
            "freq_es_cde_pos_else_kaikki_pos_mapped_to_compact_latin"
            if has_kaikki_enrichment
            else "freq_es_cde_pos_only"
        )
    return "kaikki_pos_mapped_to_compact_latin" if has_kaikki_enrichment else "none"


def _license_status_for_stack(source_mode: str, *, kaikki_forward_db: Path | None) -> str:
    mode = _normalize_source_mode(source_mode)
    if mode == SOURCE_MODE_CDE_UNION or kaikki_forward_db is not None:
        return "requires_review"
    return "confirmed"


def _bundle_suffix(source_mode: str, *, kaikki_forward_db: Path | None) -> str:
    suffix = "spalex_cde_union" if source_mode == SOURCE_MODE_CDE_UNION else "spalex_only"
    if kaikki_forward_db is not None:
        suffix += "_kaikki"
    return f"{suffix}_v1"


def _source_component(
    *,
    role: str,
    source_name: str,
    filename: str,
    path: Path,
    license: str,
    source_url: str | None = None,
    build_ref: str | None = None,
) -> dict[str, object]:
    component: dict[str, object] = {
        "role": role,
        "source_name": source_name,
        "filename": filename,
        "sha256": _sha256_file(path) if path.exists() and path.is_file() else "",
        "license": license,
    }
    if source_url:
        component["source_url"] = source_url
    if build_ref:
        component["build_ref"] = build_ref
    return component


def _resolve_output_sqlite(
    *,
    output_sqlite: Path | None,
    pack_root: Path | None,
    pack_id: str,
) -> Path:
    if output_sqlite:
        return Path(output_sqlite).expanduser().resolve(strict=False)
    if pack_root:
        return Path(pack_root).expanduser().resolve(strict=False) / "main.sqlite"
    raise ValueError(f"Provide --output-sqlite or --pack-root for {pack_id}.")


def _dedupe_spalex_rows(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    best: dict[str, dict[str, object]] = {}
    for row in rows:
        lemma = str(row.get("lemma") or "")
        old = best.get(lemma)
        if old is None:
            best[lemma] = dict(row)
            continue
        current_key = (
            _float_or_floor(row.get("zipf")),
            _float_or_floor(row.get("prevalence_total")),
        )
        old_key = (_float_or_floor(old.get("zipf")), _float_or_floor(old.get("prevalence_total")))
        if current_key > old_key:
            best[lemma] = dict(row)
    return list(best.values())


def _select_canonical_pos(raw_values: Sequence[str]) -> str:
    normalized = [
        normalize_pos(
            raw,
            language_pair="en-es",
            source_provider="wiktionary-es-en",
            source_profile="wiktionary",
        )
        for raw in raw_values
    ]
    mapped = [row.canonical for row in normalized if row.mapped]
    if not mapped:
        return ""
    return min(mapped, key=lambda item: POS_PRIORITY.get(item, 99))


def _resolve_compact_pos(
    cde: CurrentFrequencyRow | None, enrichment: KaikkiEnrichment | None
) -> str:
    if cde and cde.pos:
        return cde.pos
    if enrichment and enrichment.pos_compact:
        return enrichment.pos_compact
    return ""


def _pos_source(cde: CurrentFrequencyRow | None, enrichment: KaikkiEnrichment | None) -> str:
    if cde and cde.pos:
        return "freq-es-cde"
    if enrichment and enrichment.pos_compact:
        return "wiktionary-es-en"
    return ""


def _source_rank(
    source_family: str,
    cde: CurrentFrequencyRow | None,
    spalex: SpalexRow | None,
) -> float | None:
    if source_family == "freq-es-cde":
        return cde.rank if cde else None
    return float(spalex.rank) if spalex else None


def _source_frequency(
    source_family: str,
    cde: CurrentFrequencyRow | None,
    spalex: SpalexRow | None,
) -> float | None:
    if source_family == "freq-es-cde":
        return cde.freq if cde else None
    return spalex.freq if spalex else None


def _sqlite_metadata(
    *,
    pack_id: str,
    provider: str,
    row_count: int,
    source_paths: Mapping[str, Path | None],
    source_mode: str,
    has_kaikki_enrichment: bool,
) -> dict[str, object]:
    mode = _normalize_source_mode(source_mode)
    return {
        "pack_id": pack_id,
        "provider": provider,
        "source_provider": provider,
        "source_kind": "frequency",
        "source_profile": _parser_profile_for_mode(mode),
        "source_mode": mode,
        "row_count": row_count,
        "column_names": [
            "id",
            "pmw",
            "freq",
            "lemma",
            "pos",
            "source_family",
            "source_rank",
            "source_frequency",
            "topics",
        ],
        "rank_column": "id",
        "pmw_column": "pmw",
        "frequency_column_semantics": {
            "pmw": "rank_descending_commonness_score",
            "freq": "original_source_frequency",
        },
        "pos_policy": _pos_policy_for_mode(
            mode,
            has_kaikki_enrichment=has_kaikki_enrichment,
        ),
        "topic_policy": "kaikki_sense_topics_csv" if has_kaikki_enrichment else "none",
        "sources": {
            key: str(path.expanduser().resolve(strict=False)) if path is not None else None
            for key, path in source_paths.items()
        },
        "generated_at_utc": _utc_timestamp(),
    }


def _frequency_metrics(path: Path) -> dict[str, int]:
    with sqlite3.connect(path) as conn:
        row_count = int(conn.execute("SELECT COUNT(*) FROM frequency").fetchone()[0])
        distinct_lemma_count = int(
            conn.execute(
                "SELECT COUNT(DISTINCT lemma) FROM frequency WHERE TRIM(COALESCE(lemma, '')) != ''"
            ).fetchone()[0]
        )
        pos_rows = int(
            conn.execute(
                "SELECT COUNT(*) FROM frequency WHERE TRIM(COALESCE(pos, '')) != ''"
            ).fetchone()[0]
        )
        topic_domain_rows = int(
            conn.execute(
                "SELECT COUNT(*) FROM frequency WHERE TRIM(COALESCE(topics, '')) != ''"
            ).fetchone()[0]
        )
    return {
        "row_count": row_count,
        "distinct_lemma_count": distinct_lemma_count,
        "pos_rows": pos_rows,
        "topic_domain_rows": topic_domain_rows,
    }


def _column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})")]


def _json_string_list(value: object) -> set[str]:
    text = str(value or "").strip()
    if not text or text == "[]":
        return set()
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        return set()
    if not isinstance(decoded, list):
        return set()
    return {_normalize_lemma(item) for item in decoded if _normalize_lemma(item)}


def _normalize_lemma(value: object) -> str:
    return unicodedata.normalize("NFC", str(value or "").strip().lower())


def _is_clean_surface(value: object) -> bool:
    text = _normalize_lemma(value)
    return bool(text) and all(character.isalpha() for character in text)


def _to_float(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _float_or_floor(value: object) -> float:
    parsed = _to_float(value)
    return parsed if parsed is not None else -999999.0


def _sha1_file(path: Path) -> str:
    return _hash_file(path, "sha1")


def _sha256_file(path: Path) -> str:
    return _hash_file(path, "sha256")


def _hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
