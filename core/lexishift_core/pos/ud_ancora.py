from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import unicodedata
from typing import Iterable, Mapping, Sequence
from urllib.request import urlopen

from lexishift_core.helper.installed_packs import write_installed_pack_manifest
from lexishift_core.helper.pack_provenance import write_app_managed_pack_provenance
from lexishift_core.pos.normalization import normalize_pos

DEFAULT_PACK_ID = "pos-es-ud-ancora-v1"
DEFAULT_PROVIDER = "universal-dependencies-ud-ancora"
DEFAULT_SOURCE_PROFILE = "universal-dependencies"
DEFAULT_SOURCE_NAME = "Universal Dependencies Spanish AnCora"
DEFAULT_SOURCE_URL = "https://universaldependencies.org/treebanks/es_ancora/index.html"
DEFAULT_LICENSE = "CC BY 4.0"
DEFAULT_UD_ANCORA_URLS = (
    "https://raw.githubusercontent.com/UniversalDependencies/UD_Spanish-AnCora/master/es_ancora-ud-train.conllu",
    "https://raw.githubusercontent.com/UniversalDependencies/UD_Spanish-AnCora/master/es_ancora-ud-dev.conllu",
    "https://raw.githubusercontent.com/UniversalDependencies/UD_Spanish-AnCora/master/es_ancora-ud-test.conllu",
)
POS_OVERLAY_SCHEMA_SQL = """
CREATE TABLE pos_overlay (
  lemma TEXT PRIMARY KEY,
  raw_pos TEXT NOT NULL,
  pos TEXT NOT NULL,
  pos_canonical TEXT NOT NULL,
  pos_bucket TEXT NOT NULL,
  pos_source_profile TEXT NOT NULL,
  pos_matched_rule TEXT NOT NULL,
  confidence REAL NOT NULL,
  source_count INTEGER NOT NULL,
  total_count INTEGER NOT NULL,
  pos_counts_json TEXT NOT NULL,
  lemma_variants_json TEXT NOT NULL,
  source_provider TEXT NOT NULL,
  overlay_id TEXT NOT NULL,
  source_corpus TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class UdPosRow:
    lemma: str
    raw_pos: str
    pos_canonical: str
    pos_bucket: str
    pos_matched_rule: str
    confidence: float
    source_count: int
    total_count: int
    pos_counts: Mapping[str, int]
    lemma_variants: Mapping[str, int]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Spanish POS overlay from UD Spanish AnCora .conllu files."
    )
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--download-sources", action="store_true")
    parser.add_argument("--output-sqlite", type=Path)
    parser.add_argument("--pack-root", type=Path)
    parser.add_argument("--pack-id", default=DEFAULT_PACK_ID)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--write-sidecars", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    source_paths = tuple(Path(path) for path in args.source)
    if args.download_sources:
        if args.source_dir is None:
            raise ValueError("--source-dir is required with --download-sources")
        source_paths = download_ud_ancora_sources(args.source_dir, overwrite=args.overwrite)
    elif args.source_dir is not None and not source_paths:
        source_paths = tuple(sorted(Path(args.source_dir).glob("*.conllu")))
    if not source_paths:
        raise ValueError("Provide --source files, --source-dir, or --download-sources.")

    output_sqlite = _resolve_output_sqlite(
        output_sqlite=args.output_sqlite,
        pack_root=args.pack_root,
    )
    metadata = build_ud_ancora_pos_overlay(
        source_paths=source_paths,
        output_sqlite=output_sqlite,
        pack_id=args.pack_id,
        provider=args.provider,
        overwrite=args.overwrite,
        write_sidecars=args.write_sidecars,
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def download_ud_ancora_sources(
    source_dir: Path,
    *,
    overwrite: bool = False,
    urls: Sequence[str] = DEFAULT_UD_ANCORA_URLS,
) -> tuple[Path, ...]:
    output_dir = Path(source_dir).expanduser().resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for url in urls:
        filename = Path(url).name
        if not filename:
            raise ValueError(f"Could not infer filename from URL: {url}")
        target = output_dir / filename
        if target.exists() and not overwrite:
            paths.append(target)
            continue
        with urlopen(url, timeout=60) as response:
            target.write_bytes(response.read())
        paths.append(target)
    return tuple(paths)


def build_ud_ancora_pos_overlay(
    *,
    source_paths: Sequence[Path],
    output_sqlite: Path,
    pack_id: str = DEFAULT_PACK_ID,
    provider: str = DEFAULT_PROVIDER,
    overwrite: bool = False,
    write_sidecars: bool = False,
) -> dict[str, object]:
    sources = tuple(Path(path).expanduser().resolve(strict=False) for path in source_paths)
    missing = [str(path) for path in sources if not path.exists() or not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing UD AnCora source files: {', '.join(missing)}")
    output = Path(output_sqlite).expanduser().resolve(strict=False)
    if output.exists():
        if overwrite:
            output.unlink()
        else:
            raise FileExistsError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    rows = _build_rows(sources)
    _write_sqlite(
        output,
        rows=rows,
        pack_id=pack_id,
        provider=provider,
        source_paths=sources,
    )
    metrics = _metrics(rows)
    source_bundle_sha256 = _source_bundle_sha256(sources)
    metadata: dict[str, object] = {
        "pack_id": pack_id,
        "provider": provider,
        "source_name": DEFAULT_SOURCE_NAME,
        "source_url": DEFAULT_SOURCE_URL,
        "license": DEFAULT_LICENSE,
        "output_sqlite": str(output),
        "row_count": len(rows),
        "source_files": [str(path) for path in sources],
        "source_file_sha256": {path.name: _sha256_file(path) for path in sources},
        "source_bundle_sha256": source_bundle_sha256,
        "metrics": metrics,
    }
    if write_sidecars:
        _write_sidecars(
            output,
            metadata=metadata,
            pack_id=pack_id,
            provider=provider,
            source_paths=sources,
            source_bundle_sha256=source_bundle_sha256,
            metrics=metrics,
        )
    return metadata


def _build_rows(source_paths: Sequence[Path]) -> list[UdPosRow]:
    pos_counts_by_lemma: dict[str, Counter[str]] = defaultdict(Counter)
    variants_by_lemma: dict[str, Counter[str]] = defaultdict(Counter)
    for path in source_paths:
        for lemma, upos in _iter_conllu_lemmas(path):
            normalized_lemma = _normalize_lemma(lemma)
            normalized_upos = str(upos or "").strip().upper()
            if not normalized_lemma or not normalized_upos:
                continue
            pos_counts_by_lemma[normalized_lemma][normalized_upos] += 1
            variants_by_lemma[normalized_lemma][str(lemma).strip()] += 1

    rows: list[UdPosRow] = []
    for lemma, pos_counts in sorted(pos_counts_by_lemma.items()):
        raw_pos, source_count = _select_majority_pos(pos_counts)
        total_count = sum(pos_counts.values())
        normalized = normalize_pos(
            raw_pos,
            source_provider=DEFAULT_PROVIDER,
            source_kind="pos_overlay",
            source_profile=DEFAULT_SOURCE_PROFILE,
        )
        if not normalized.mapped:
            continue
        rows.append(
            UdPosRow(
                lemma=lemma,
                raw_pos=raw_pos,
                pos_canonical=normalized.canonical,
                pos_bucket=normalized.bucket,
                pos_matched_rule=normalized.matched_rule,
                confidence=round(source_count / total_count, 6) if total_count else 0.0,
                source_count=source_count,
                total_count=total_count,
                pos_counts=dict(sorted(pos_counts.items())),
                lemma_variants=dict(sorted(variants_by_lemma[lemma].items())),
            )
        )
    return rows


def _iter_conllu_lemmas(path: Path) -> Iterable[tuple[str, str]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 4:
            continue
        token_id = fields[0].strip()
        if "-" in token_id or "." in token_id:
            continue
        form = fields[1].strip()
        upos = fields[3].strip()
        if form and form != "_" and upos and upos != "_":
            yield form, upos


def _write_sqlite(
    output: Path,
    *,
    rows: Sequence[UdPosRow],
    pack_id: str,
    provider: str,
    source_paths: Sequence[Path],
) -> None:
    with sqlite3.connect(output) as conn:
        conn.execute(POS_OVERLAY_SCHEMA_SQL)
        conn.executemany(
            """
            INSERT INTO pos_overlay (
              lemma, raw_pos, pos, pos_canonical, pos_bucket, pos_source_profile,
              pos_matched_rule, confidence, source_count, total_count,
              pos_counts_json, lemma_variants_json, source_provider, overlay_id,
              source_corpus
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.lemma,
                    row.raw_pos,
                    row.raw_pos,
                    row.pos_canonical,
                    row.pos_bucket,
                    DEFAULT_SOURCE_PROFILE,
                    row.pos_matched_rule,
                    row.confidence,
                    row.source_count,
                    row.total_count,
                    json.dumps(row.pos_counts, ensure_ascii=False, sort_keys=True),
                    json.dumps(row.lemma_variants, ensure_ascii=False, sort_keys=True),
                    provider,
                    pack_id,
                    "UD_Spanish-AnCora",
                )
                for row in rows
            ],
        )
        conn.execute("CREATE INDEX idx_pos_overlay_canonical ON pos_overlay(pos_canonical)")
        conn.execute("CREATE INDEX idx_pos_overlay_raw_pos ON pos_overlay(raw_pos)")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        metadata = {
            "pack_id": pack_id,
            "provider": provider,
            "source_name": DEFAULT_SOURCE_NAME,
            "source_url": DEFAULT_SOURCE_URL,
            "license": DEFAULT_LICENSE,
            "source_files": [path.name for path in source_paths],
            "source_file_sha256": {path.name: _sha256_file(path) for path in source_paths},
            "source_bundle_sha256": _source_bundle_sha256(source_paths),
            "built_at_utc": _utc_timestamp(),
        }
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("metadata", json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
        )
        conn.commit()


def _write_sidecars(
    output: Path,
    *,
    metadata: Mapping[str, object],
    pack_id: str,
    provider: str,
    source_paths: Sequence[Path],
    source_bundle_sha256: str,
    metrics: Mapping[str, object],
) -> None:
    pack_root = output.parent
    (pack_root / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_installed_pack_manifest(
        pack_root.parent,
        pack_id=pack_id,
        pack_kind="pos_overlay",
        provider=provider,
        local_kind="file",
        build_mode="ud_ancora_pos_overlay",
        artifact_path=output,
        source_filename="+".join(path.name for path in source_paths),
        sqlite_filename=output.name,
        required_files=tuple(path.name for path in source_paths),
        raw_retained=False,
    )
    write_app_managed_pack_provenance(
        pack_root=pack_root,
        pack_id=pack_id,
        pack_kind="pos_overlay",
        provider=provider,
        source_name=DEFAULT_SOURCE_NAME,
        source_url=DEFAULT_SOURCE_URL,
        build_mode="ud_ancora_pos_overlay",
        artifact_path=output,
        source_filename="+".join(path.name for path in source_paths),
        sqlite_filename=output.name,
        required_files=tuple(path.name for path in source_paths),
        license_status="confirmed",
        source_version=f"source_bundle_sha256:{source_bundle_sha256}",
        parser_profile=DEFAULT_SOURCE_PROFILE,
        artifact_metrics=metrics,
    )


def _resolve_output_sqlite(
    *,
    output_sqlite: Path | None,
    pack_root: Path | None,
) -> Path:
    if output_sqlite is not None:
        return Path(output_sqlite)
    if pack_root is None:
        raise ValueError("Either --output-sqlite or --pack-root is required.")
    return Path(pack_root) / "main.sqlite"


def _metrics(rows: Sequence[UdPosRow]) -> dict[str, object]:
    canonical_counts = Counter(row.pos_canonical for row in rows)
    raw_counts = Counter(row.raw_pos for row in rows)
    return {
        "distinct_lemmas": len(rows),
        "canonical_pos_counts": dict(sorted(canonical_counts.items())),
        "raw_pos_counts": dict(sorted(raw_counts.items())),
        "high_confidence_rows": sum(1 for row in rows if row.confidence >= 0.8),
        "low_confidence_rows": sum(1 for row in rows if row.confidence < 0.5),
    }


def _select_majority_pos(pos_counts: Counter[str]) -> tuple[str, int]:
    if not pos_counts:
        return "", 0
    priority = {
        "NOUN": 0,
        "PROPN": 1,
        "ADJ": 2,
        "VERB": 3,
        "ADV": 4,
        "PRON": 5,
        "DET": 6,
        "ADP": 7,
        "CCONJ": 8,
        "SCONJ": 9,
        "INTJ": 10,
        "NUM": 11,
        "AUX": 12,
        "PART": 13,
        "PUNCT": 14,
        "SYM": 15,
        "X": 16,
    }
    raw_pos, count = min(
        pos_counts.items(),
        key=lambda item: (-item[1], priority.get(item[0], 99), item[0]),
    )
    return raw_pos, count


def _normalize_lemma(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or "").strip())
    if not text:
        return ""
    return text.casefold()


def _source_bundle_sha256(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256_file(path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
