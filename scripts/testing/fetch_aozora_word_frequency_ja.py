#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import urllib.request


PROJECT_ROOT = Path(__file__).resolve().parents[2]


PACK_ID = "freq-ja-aozora-word"
SOURCE_SITE = "http://aozora-word.hahasoha.net"
SOURCE_NAME = "青空文庫形態素解析データ集"
METADATA_FILE = "aozora_word_list_utf8.csv.gz"
SOURCE_PAGES = ("index.html", "about.html", "download.html", "license.html")
VARIANT_FILES = {
    "all": "utf8/utf8_all.csv.gz",
    "newnew": "utf8/newnew.csv.gz",
    "newold": "utf8/newold.csv.gz",
    "oldnew": "utf8/oldnew.csv.gz",
    "oldold": "utf8/oldold.csv.gz",
    "etc": "utf8/etc.csv.gz",
}
TOKEN_COLUMNS = (
    "source_file",
    "source_line",
    "token_index",
    "surface",
    "pos_major",
    "pos_sub1",
    "pos_sub2",
    "pos_sub3",
    "conjugation_type",
    "conjugation_form",
    "base_form",
    "reading",
    "pronunciation",
)
MODERN_ORTHOGRAPHY = "新字新仮名"
CONTENT_POS_MAJOR = {"名詞", "動詞", "形容詞", "副詞", "連体詞", "感動詞"}
COMMON_RANK_MAX = 20_000
MID_RANK_MAX = 80_000
TAIL_RANK_MIN = 160_000
METADATA_COLUMNS = (
    "作品id",
    "作品名",
    "作品名読み",
    "ソート用読み",
    "副題",
    "副題読み",
    "原題",
    "初出",
    "分類番号",
    "文字遣い種別",
    "作品著作権フラグ",
    "公開日",
    "最終更新日",
    "図書カードurl",
    "人物id",
    "姓",
    "名",
    "姓読み",
    "名読み",
    "姓読みソート用",
    "名読みソート用",
    "姓ローマ字",
    "名ローマ字",
    "役割フラグ",
    "生年月日",
    "没年月日",
    "人物著作権フラグ",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch and aggregate the Aozora Bunko morphological CSV dataset as a "
            "local en-ja learner-difficulty research sidecar. This does not wire "
            "the signal into any production scorer."
        )
    )
    parser.add_argument(
        "--variant",
        choices=sorted(VARIANT_FILES),
        default="all",
        help="Aozora bulk CSV variant to fetch and aggregate. Defaults to full UTF-8 data.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory. Defaults to the local LexiShift frequency_packs/freq-ja-aozora-word."
        ),
    )
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--force-build", action="store_true")
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument(
        "--progress-every",
        type=int,
        default=1_000_000,
        help="Print one aggregation progress line per N token rows.",
    )
    parser.add_argument(
        "--probe",
        action="append",
        default=[],
        help="After building, print top Aozora rows for this surface/base term.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_dir = _resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    pages_dir = output_dir / "source_pages"
    raw_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    page_records = [
        _download(
            url=f"{SOURCE_SITE}/{page}",
            path=pages_dir / page,
            force=bool(args.force_download),
        )
        for page in SOURCE_PAGES
    ]
    metadata_record = _download(
        url=f"{SOURCE_SITE}/{METADATA_FILE}",
        path=raw_dir / METADATA_FILE,
        force=bool(args.force_download),
    )
    variant_relpath = VARIANT_FILES[str(args.variant)]
    variant_record = _download(
        url=f"{SOURCE_SITE}/{variant_relpath}",
        path=raw_dir / Path(variant_relpath).name,
        force=bool(args.force_download),
    )

    sqlite_path = output_dir / "main.sqlite"
    build_record: dict[str, object] | None = None
    if args.download_only and sqlite_path.exists():
        build_record = _existing_sqlite_record(sqlite_path)
    elif not args.download_only:
        if sqlite_path.exists() and not args.force_build:
            build_record = _existing_sqlite_record(sqlite_path)
        else:
            build_record = build_sqlite(
                metadata_path=Path(metadata_record["path"]),
                token_csv_gz_path=Path(variant_record["path"]),
                sqlite_path=sqlite_path,
                variant=str(args.variant),
                progress_every=max(1, int(args.progress_every)),
            )

    metadata = _metadata_payload(
        output_dir=output_dir,
        variant=str(args.variant),
        raw_records=[metadata_record, variant_record],
        page_records=page_records,
        build_record=build_record,
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(metadata["manifest"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "provenance.json").write_text(
        json.dumps(metadata["provenance"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote Aozora frequency sidecar to {output_dir}")
    print(f"- metadata: {metadata_record['status']} {metadata_record['sha256']}")
    print(f"- {Path(variant_relpath).name}: {variant_record['status']} {variant_record['sha256']}")
    if build_record:
        print(
            "- main.sqlite: "
            f"{build_record['status']} rows={build_record.get('frequency_rows')} "
            f"tokens={build_record.get('token_rows')} "
            f"work_profiles={build_record.get('work_profile_rows')} "
            f"context_profiles={build_record.get('context_profile_rows')}"
        )
    if args.probe and sqlite_path.exists():
        for term in args.probe:
            _print_probe(sqlite_path, term)
    return 0


def build_sqlite(
    *,
    metadata_path: Path,
    token_csv_gz_path: Path,
    sqlite_path: Path,
    variant: str,
    progress_every: int,
) -> dict[str, object]:
    work_authors, metadata_rows, work_info = _load_work_metadata(metadata_path)
    token_counts: Counter[tuple[str, ...]] = Counter()
    work_counts: Counter[tuple[str, ...]] = Counter()
    author_sets: dict[tuple[str, ...], set[str]] = defaultdict(set)
    total_tokens = 0
    skipped_rows = 0
    current_file = ""
    current_counter: Counter[tuple[str, ...]] = Counter()

    def flush_work() -> None:
        if not current_file or not current_counter:
            return
        work_id = _work_id_from_source_file(current_file)
        authors = work_authors.get(work_id) or ()
        for key, count in current_counter.items():
            token_counts[key] += count
            work_counts[key] += 1
            if authors:
                author_sets[key].update(authors)
        current_counter.clear()

    with gzip.open(token_csv_gz_path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < len(TOKEN_COLUMNS):
                skipped_rows += 1
                continue
            source_file = row[0]
            if source_file != current_file:
                flush_work()
                current_file = source_file
            key = _token_key(row)
            current_counter[key] += 1
            total_tokens += 1
            if total_tokens % progress_every == 0:
                print(
                    f"Pass 1 global frequency: {total_tokens:,} token rows; "
                    f"{len(token_counts) + len(current_counter):,} distinct rows seen",
                    flush=True,
                )
    flush_work()

    ranked_rows = sorted(token_counts.items(), key=lambda item: (-item[1], item[0]))
    rank_by_key = {key: rank for rank, (key, _count) in enumerate(ranked_rows, start=1)}
    raw_work_profiles = _build_work_profiles(
        token_csv_gz_path=token_csv_gz_path,
        work_info=work_info,
        rank_by_key=rank_by_key,
        progress_every=progress_every,
    )
    work_profiles = _assign_work_accessibility_bands(raw_work_profiles)
    context_profiles = _build_context_profiles(
        token_csv_gz_path=token_csv_gz_path,
        work_info=work_info,
        work_profiles=work_profiles,
        progress_every=progress_every,
    )

    temporary = sqlite_path.with_suffix(".sqlite.tmp")
    if temporary.exists():
        temporary.unlink()
    _write_sqlite(
        sqlite_path=temporary,
        metadata_rows=metadata_rows,
        token_counts=token_counts,
        work_counts=work_counts,
        author_sets=author_sets,
        ranked_rows=ranked_rows,
        work_profiles=work_profiles,
        context_profiles=context_profiles,
        total_tokens=total_tokens,
        skipped_rows=skipped_rows,
        variant=variant,
    )
    temporary.replace(sqlite_path)
    return {
        "status": "built",
        "path": str(sqlite_path),
        "size_bytes": sqlite_path.stat().st_size,
        "sha256": _sha256_file(sqlite_path),
        "token_rows": total_tokens,
        "skipped_rows": skipped_rows,
        "frequency_rows": len(token_counts),
        "work_metadata_rows": len(metadata_rows),
        "work_profile_rows": len(work_profiles),
        "context_profile_rows": len(context_profiles),
    }


def _write_sqlite(
    *,
    sqlite_path: Path,
    metadata_rows: list[dict[str, str]],
    token_counts: Counter[tuple[str, ...]],
    work_counts: Counter[tuple[str, ...]],
    author_sets: dict[tuple[str, ...], set[str]],
    ranked_rows: list[tuple[tuple[str, ...], int]],
    work_profiles: dict[str, dict[str, object]],
    context_profiles: dict[tuple[str, ...], dict[str, object]],
    total_tokens: int,
    skipped_rows: int,
    variant: str,
) -> None:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    try:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute(
            """
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE work_metadata (
                work_id TEXT NOT NULL,
                title TEXT NOT NULL,
                title_reading TEXT NOT NULL,
                ndc TEXT NOT NULL,
                orthography_type TEXT NOT NULL,
                work_copyright TEXT NOT NULL,
                published_on TEXT NOT NULL,
                updated_on TEXT NOT NULL,
                card_url TEXT NOT NULL,
                author_id TEXT NOT NULL,
                author_name TEXT NOT NULL,
                author_role TEXT NOT NULL,
                author_birth TEXT NOT NULL,
                author_death TEXT NOT NULL,
                author_copyright TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE token_frequency (
                surface TEXT NOT NULL,
                base_form TEXT NOT NULL,
                reading TEXT NOT NULL,
                pronunciation TEXT NOT NULL,
                pos_major TEXT NOT NULL,
                pos_sub1 TEXT NOT NULL,
                pos_sub2 TEXT NOT NULL,
                pos_sub3 TEXT NOT NULL,
                conjugation_type TEXT NOT NULL,
                conjugation_form TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                work_count INTEGER NOT NULL,
                author_count INTEGER NOT NULL,
                rank_by_token INTEGER NOT NULL,
                pmw REAL NOT NULL,
                source_variant TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE work_profile (
                work_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author_names_json TEXT NOT NULL,
                ndc TEXT NOT NULL,
                ndc_primary_classes_json TEXT NOT NULL,
                children_or_youth_ndc INTEGER NOT NULL,
                orthography_type TEXT NOT NULL,
                modern_orthography INTEGER NOT NULL,
                token_count INTEGER NOT NULL,
                content_token_count INTEGER NOT NULL,
                unique_content_count INTEGER NOT NULL,
                common_content_share REAL NOT NULL,
                mid_content_share REAL NOT NULL,
                tail_content_share REAL NOT NULL,
                rare_unique_content_share REAL NOT NULL,
                function_token_share REAL NOT NULL,
                accessibility_raw REAL NOT NULL,
                accessibility_percentile REAL NOT NULL,
                accessibility_band TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE token_context_profile (
                surface TEXT NOT NULL,
                base_form TEXT NOT NULL,
                reading TEXT NOT NULL,
                pronunciation TEXT NOT NULL,
                pos_major TEXT NOT NULL,
                pos_sub1 TEXT NOT NULL,
                pos_sub2 TEXT NOT NULL,
                pos_sub3 TEXT NOT NULL,
                conjugation_type TEXT NOT NULL,
                conjugation_form TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                work_count INTEGER NOT NULL,
                modern_token_count INTEGER NOT NULL,
                modern_work_count INTEGER NOT NULL,
                old_orthography_token_count INTEGER NOT NULL,
                old_orthography_work_count INTEGER NOT NULL,
                children_token_count INTEGER NOT NULL,
                children_work_count INTEGER NOT NULL,
                modern_children_token_count INTEGER NOT NULL,
                modern_children_work_count INTEGER NOT NULL,
                accessible_token_count INTEGER NOT NULL,
                accessible_work_count INTEGER NOT NULL,
                hard_token_count INTEGER NOT NULL,
                hard_work_count INTEGER NOT NULL,
                accessibility_weighted_mean REAL NOT NULL,
                orthography_token_counts_json TEXT NOT NULL,
                orthography_work_counts_json TEXT NOT NULL,
                ndc_class_token_counts_json TEXT NOT NULL,
                ndc_class_work_counts_json TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO work_metadata VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                (
                    row["work_id"],
                    row["title"],
                    row["title_reading"],
                    row["ndc"],
                    row["orthography_type"],
                    row["work_copyright"],
                    row["published_on"],
                    row["updated_on"],
                    row["card_url"],
                    row["author_id"],
                    row["author_name"],
                    row["author_role"],
                    row["author_birth"],
                    row["author_death"],
                    row["author_copyright"],
                )
                for row in metadata_rows
            ),
        )
        batch = []
        for rank, (key, count) in enumerate(ranked_rows, start=1):
            batch.append(
                (
                    *key,
                    count,
                    int(work_counts.get(key, 0)),
                    len(author_sets.get(key, ())),
                    rank,
                    (float(count) / float(total_tokens) * 1_000_000.0) if total_tokens else 0.0,
                    variant,
                )
            )
            if len(batch) >= 50_000:
                _insert_frequency_batch(conn, batch)
                batch.clear()
        if batch:
            _insert_frequency_batch(conn, batch)
        _insert_work_profiles(conn, work_profiles)
        _insert_context_profiles(conn, token_counts, work_counts, context_profiles)
        conn.executemany(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            [
                ("schema_version", "2"),
                ("pack_id", PACK_ID),
                ("source_name", SOURCE_NAME),
                ("source_url", SOURCE_SITE),
                ("source_variant", variant),
                ("token_rows", str(total_tokens)),
                ("skipped_rows", str(skipped_rows)),
                ("frequency_rows", str(len(token_counts))),
                ("work_metadata_rows", str(len(metadata_rows))),
                ("work_profile_rows", str(len(work_profiles))),
                ("context_profile_rows", str(len(context_profiles))),
                ("generated_at_utc", _utc_now()),
                ("token_columns", json.dumps(TOKEN_COLUMNS, ensure_ascii=False)),
                (
                    "derived_signal_notes",
                    (
                        "work_profile and token_context_profile are derived from Aozora "
                        "orthography, NDC metadata, global Aozora rank, and per-work token "
                        "mix; they are research signals, not production difficulty labels."
                    ),
                ),
            ],
        )
        conn.execute(
            "CREATE INDEX idx_token_frequency_base_reading ON token_frequency(base_form, reading)"
        )
        conn.execute(
            "CREATE INDEX idx_token_frequency_surface_reading ON token_frequency(surface, reading)"
        )
        conn.execute("CREATE INDEX idx_token_frequency_rank ON token_frequency(rank_by_token)")
        conn.execute(
            "CREATE INDEX idx_context_base_reading ON token_context_profile(base_form, reading)"
        )
        conn.execute(
            "CREATE INDEX idx_context_surface_reading ON token_context_profile(surface, reading)"
        )
        conn.execute("CREATE INDEX idx_work_profile_band ON work_profile(accessibility_band)")
        conn.execute(
            "CREATE INDEX idx_work_profile_ndc_child ON work_profile(children_or_youth_ndc)"
        )
        conn.execute("CREATE INDEX idx_work_metadata_work_id ON work_metadata(work_id)")
        conn.commit()
    finally:
        conn.close()


def _insert_frequency_batch(conn: sqlite3.Connection, batch: list[tuple[object, ...]]) -> None:
    conn.executemany(
        """
        INSERT INTO token_frequency (
            surface,
            base_form,
            reading,
            pronunciation,
            pos_major,
            pos_sub1,
            pos_sub2,
            pos_sub3,
            conjugation_type,
            conjugation_form,
            token_count,
            work_count,
            author_count,
            rank_by_token,
            pmw,
            source_variant
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        batch,
    )


def _insert_work_profiles(
    conn: sqlite3.Connection,
    work_profiles: dict[str, dict[str, object]],
) -> None:
    conn.executemany(
        """
        INSERT INTO work_profile (
            work_id,
            title,
            author_names_json,
            ndc,
            ndc_primary_classes_json,
            children_or_youth_ndc,
            orthography_type,
            modern_orthography,
            token_count,
            content_token_count,
            unique_content_count,
            common_content_share,
            mid_content_share,
            tail_content_share,
            rare_unique_content_share,
            function_token_share,
            accessibility_raw,
            accessibility_percentile,
            accessibility_band
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                work_id,
                str(profile["title"]),
                json.dumps(profile["author_names"], ensure_ascii=False, sort_keys=True),
                str(profile["ndc"]),
                json.dumps(profile["ndc_primary_classes"], ensure_ascii=False, sort_keys=True),
                int(bool(profile["children_or_youth_ndc"])),
                str(profile["orthography_type"]),
                int(bool(profile["modern_orthography"])),
                int(profile["token_count"]),
                int(profile["content_token_count"]),
                int(profile["unique_content_count"]),
                float(profile["common_content_share"]),
                float(profile["mid_content_share"]),
                float(profile["tail_content_share"]),
                float(profile["rare_unique_content_share"]),
                float(profile["function_token_share"]),
                float(profile["accessibility_raw"]),
                float(profile["accessibility_percentile"]),
                str(profile["accessibility_band"]),
            )
            for work_id, profile in sorted(work_profiles.items())
        ),
    )


def _insert_context_profiles(
    conn: sqlite3.Connection,
    token_counts: Counter[tuple[str, ...]],
    work_counts: Counter[tuple[str, ...]],
    context_profiles: dict[tuple[str, ...], dict[str, object]],
) -> None:
    batch = []
    for key, token_count in sorted(token_counts.items(), key=lambda item: (-item[1], item[0])):
        profile = context_profiles.get(key) or _empty_context_profile()
        weighted_sum = float(profile["accessibility_weighted_sum"])
        accessibility_weighted_mean = weighted_sum / float(token_count) if token_count else 0.0
        batch.append(
            (
                *key,
                int(token_count),
                int(work_counts.get(key, 0)),
                int(profile["modern_token_count"]),
                int(profile["modern_work_count"]),
                int(profile["old_orthography_token_count"]),
                int(profile["old_orthography_work_count"]),
                int(profile["children_token_count"]),
                int(profile["children_work_count"]),
                int(profile["modern_children_token_count"]),
                int(profile["modern_children_work_count"]),
                int(profile["accessible_token_count"]),
                int(profile["accessible_work_count"]),
                int(profile["hard_token_count"]),
                int(profile["hard_work_count"]),
                accessibility_weighted_mean,
                _json_counts(profile["orthography_token_counts"]),
                _json_counts(profile["orthography_work_counts"]),
                _json_counts(profile["ndc_class_token_counts"]),
                _json_counts(profile["ndc_class_work_counts"]),
            )
        )
        if len(batch) >= 50_000:
            _insert_context_batch(conn, batch)
            batch.clear()
    if batch:
        _insert_context_batch(conn, batch)


def _insert_context_batch(conn: sqlite3.Connection, batch: list[tuple[object, ...]]) -> None:
    conn.executemany(
        """
        INSERT INTO token_context_profile (
            surface,
            base_form,
            reading,
            pronunciation,
            pos_major,
            pos_sub1,
            pos_sub2,
            pos_sub3,
            conjugation_type,
            conjugation_form,
            token_count,
            work_count,
            modern_token_count,
            modern_work_count,
            old_orthography_token_count,
            old_orthography_work_count,
            children_token_count,
            children_work_count,
            modern_children_token_count,
            modern_children_work_count,
            accessible_token_count,
            accessible_work_count,
            hard_token_count,
            hard_work_count,
            accessibility_weighted_mean,
            orthography_token_counts_json,
            orthography_work_counts_json,
            ndc_class_token_counts_json,
            ndc_class_work_counts_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        batch,
    )


def _load_work_metadata(
    metadata_path: Path,
) -> tuple[dict[str, tuple[str, ...]], list[dict[str, str]], dict[str, dict[str, object]]]:
    work_authors: dict[str, set[str]] = defaultdict(set)
    work_author_names: dict[str, set[str]] = defaultdict(set)
    rows: list[dict[str, str]] = []
    with gzip.open(metadata_path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            work_id = str(raw.get("作品id") or "").strip()
            author_id = str(raw.get("人物id") or "").strip()
            author_name = "".join(
                part for part in (str(raw.get("姓") or ""), str(raw.get("名") or "")) if part
            )
            if work_id and author_id:
                work_authors[work_id].add(author_id)
            if work_id and author_name:
                work_author_names[work_id].add(author_name)
            rows.append(
                {
                    "work_id": work_id,
                    "title": str(raw.get("作品名") or ""),
                    "title_reading": str(raw.get("作品名読み") or ""),
                    "ndc": str(raw.get("分類番号") or ""),
                    "orthography_type": str(raw.get("文字遣い種別") or ""),
                    "work_copyright": str(raw.get("作品著作権フラグ") or ""),
                    "published_on": str(raw.get("公開日") or ""),
                    "updated_on": str(raw.get("最終更新日") or ""),
                    "card_url": str(raw.get("図書カードurl") or ""),
                    "author_id": author_id,
                    "author_name": author_name,
                    "author_role": str(raw.get("役割フラグ") or ""),
                    "author_birth": str(raw.get("生年月日") or ""),
                    "author_death": str(raw.get("没年月日") or ""),
                    "author_copyright": str(raw.get("人物著作権フラグ") or ""),
                }
            )
    work_info: dict[str, dict[str, object]] = {}
    for row in rows:
        work_id = row["work_id"]
        if not work_id or work_id in work_info:
            continue
        ndc = row["ndc"]
        work_info[work_id] = {
            "work_id": work_id,
            "title": row["title"],
            "ndc": ndc,
            "ndc_primary_classes": _ndc_primary_classes(ndc),
            "children_or_youth_ndc": _is_children_or_youth_ndc(ndc),
            "orthography_type": row["orthography_type"],
            "modern_orthography": row["orthography_type"] == MODERN_ORTHOGRAPHY,
            "author_ids": tuple(sorted(work_authors.get(work_id, ()))),
            "author_names": tuple(sorted(work_author_names.get(work_id, ()))),
        }
    return {key: tuple(sorted(value)) for key, value in work_authors.items()}, rows, work_info


def _build_work_profiles(
    *,
    token_csv_gz_path: Path,
    work_info: dict[str, dict[str, object]],
    rank_by_key: dict[tuple[str, ...], int],
    progress_every: int,
) -> dict[str, dict[str, object]]:
    profiles: dict[str, dict[str, object]] = {}
    for source_file, counter in _iter_work_counters(
        token_csv_gz_path=token_csv_gz_path,
        progress_every=progress_every,
        label="Pass 2 work profiles",
    ):
        work_id = _work_id_from_source_file(source_file)
        profile = _profile_work_counter(
            work_id=work_id,
            info=work_info.get(work_id) or {},
            counter=counter,
            rank_by_key=rank_by_key,
        )
        profiles[work_id] = profile
    return profiles


def _assign_work_accessibility_bands(
    profiles: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    ranked = sorted(
        profiles.items(),
        key=lambda item: (float(item[1]["accessibility_raw"]), item[0]),
    )
    denominator = max(1, len(ranked) - 1)
    for index, (_work_id, profile) in enumerate(ranked):
        percentile = float(index) / float(denominator)
        profile["accessibility_percentile"] = percentile
        if percentile >= 0.75:
            band = "accessible"
        elif percentile >= 0.40:
            band = "mixed"
        elif percentile >= 0.15:
            band = "hard"
        else:
            band = "very_hard"
        profile["accessibility_band"] = band
    return profiles


def _build_context_profiles(
    *,
    token_csv_gz_path: Path,
    work_info: dict[str, dict[str, object]],
    work_profiles: dict[str, dict[str, object]],
    progress_every: int,
) -> dict[tuple[str, ...], dict[str, object]]:
    context_profiles: dict[tuple[str, ...], dict[str, object]] = defaultdict(_empty_context_profile)
    for source_file, counter in _iter_work_counters(
        token_csv_gz_path=token_csv_gz_path,
        progress_every=progress_every,
        label="Pass 3 context profiles",
    ):
        work_id = _work_id_from_source_file(source_file)
        info = work_info.get(work_id) or {}
        work_profile = work_profiles.get(work_id) or {}
        orthography = str(info.get("orthography_type") or "")
        ndc_classes = tuple(str(value) for value in info.get("ndc_primary_classes") or ())
        modern = bool(info.get("modern_orthography"))
        children = bool(info.get("children_or_youth_ndc"))
        accessibility_band = str(work_profile.get("accessibility_band") or "")
        accessibility_percentile = float(work_profile.get("accessibility_percentile") or 0.0)
        for key, count in counter.items():
            profile = context_profiles[key]
            profile["accessibility_weighted_sum"] += float(count) * accessibility_percentile
            if modern:
                profile["modern_token_count"] += count
                profile["modern_work_count"] += 1
            else:
                profile["old_orthography_token_count"] += count
                profile["old_orthography_work_count"] += 1
            if children:
                profile["children_token_count"] += count
                profile["children_work_count"] += 1
            if modern and children:
                profile["modern_children_token_count"] += count
                profile["modern_children_work_count"] += 1
            if accessibility_band == "accessible":
                profile["accessible_token_count"] += count
                profile["accessible_work_count"] += 1
            elif accessibility_band in {"hard", "very_hard"}:
                profile["hard_token_count"] += count
                profile["hard_work_count"] += 1
            profile["orthography_token_counts"][orthography] += count
            profile["orthography_work_counts"][orthography] += 1
            for ndc_class in ndc_classes:
                profile["ndc_class_token_counts"][ndc_class] += count
                profile["ndc_class_work_counts"][ndc_class] += 1
    return dict(context_profiles)


def _iter_work_counters(
    *,
    token_csv_gz_path: Path,
    progress_every: int,
    label: str,
):
    current_file = ""
    current_counter: Counter[tuple[str, ...]] = Counter()
    total_tokens = 0
    with gzip.open(token_csv_gz_path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < len(TOKEN_COLUMNS):
                continue
            source_file = row[0]
            if current_file and source_file != current_file:
                yield current_file, current_counter
                current_counter = Counter()
            current_file = source_file
            current_counter[_token_key(row)] += 1
            total_tokens += 1
            if total_tokens % progress_every == 0:
                print(f"{label}: {total_tokens:,} token rows", flush=True)
    if current_file:
        yield current_file, current_counter


def _profile_work_counter(
    *,
    work_id: str,
    info: dict[str, object],
    counter: Counter[tuple[str, ...]],
    rank_by_key: dict[tuple[str, ...], int],
) -> dict[str, object]:
    token_count = sum(counter.values())
    content_items = [(key, count) for key, count in counter.items() if _is_content_key(key)]
    content_token_count = sum(count for _key, count in content_items)
    unique_content_count = len(content_items)
    denominator = max(1, content_token_count)
    common_count = sum(
        count
        for key, count in content_items
        if rank_by_key.get(key, sys.maxsize) <= COMMON_RANK_MAX
    )
    mid_count = sum(
        count for key, count in content_items if rank_by_key.get(key, sys.maxsize) <= MID_RANK_MAX
    )
    tail_count = sum(
        count for key, count in content_items if rank_by_key.get(key, 0) >= TAIL_RANK_MIN
    )
    rare_unique_count = sum(
        1 for key, _count in content_items if rank_by_key.get(key, 0) >= TAIL_RANK_MIN
    )
    common_share = common_count / denominator
    mid_share = mid_count / denominator
    tail_share = tail_count / denominator
    rare_unique_share = rare_unique_count / max(1, unique_content_count)
    function_share = (token_count - content_token_count) / max(1, token_count)
    orthography_type = str(info.get("orthography_type") or "")
    orthography_weight = _orthography_accessibility_weight(orthography_type)
    children_bonus = 0.06 if bool(info.get("children_or_youth_ndc")) else 0.0
    accessibility_raw = _clamp01(
        0.35 * common_share
        + 0.25 * mid_share
        + 0.25 * orthography_weight
        + 0.10 * (1.0 - tail_share)
        + children_bonus
        - 0.20 * rare_unique_share
    )
    return {
        "work_id": work_id,
        "title": str(info.get("title") or ""),
        "author_names": tuple(info.get("author_names") or ()),
        "ndc": str(info.get("ndc") or ""),
        "ndc_primary_classes": tuple(info.get("ndc_primary_classes") or ()),
        "children_or_youth_ndc": bool(info.get("children_or_youth_ndc")),
        "orthography_type": orthography_type,
        "modern_orthography": bool(info.get("modern_orthography")),
        "token_count": token_count,
        "content_token_count": content_token_count,
        "unique_content_count": unique_content_count,
        "common_content_share": common_share,
        "mid_content_share": mid_share,
        "tail_content_share": tail_share,
        "rare_unique_content_share": rare_unique_share,
        "function_token_share": function_share,
        "accessibility_raw": accessibility_raw,
        "accessibility_percentile": 0.0,
        "accessibility_band": "unassigned",
    }


def _empty_context_profile() -> dict[str, object]:
    return {
        "modern_token_count": 0,
        "modern_work_count": 0,
        "old_orthography_token_count": 0,
        "old_orthography_work_count": 0,
        "children_token_count": 0,
        "children_work_count": 0,
        "modern_children_token_count": 0,
        "modern_children_work_count": 0,
        "accessible_token_count": 0,
        "accessible_work_count": 0,
        "hard_token_count": 0,
        "hard_work_count": 0,
        "accessibility_weighted_sum": 0.0,
        "orthography_token_counts": Counter(),
        "orthography_work_counts": Counter(),
        "ndc_class_token_counts": Counter(),
        "ndc_class_work_counts": Counter(),
    }


def _token_key(row: list[str]) -> tuple[str, ...]:
    values = [str(cell or "").strip() for cell in row[: len(TOKEN_COLUMNS)]]
    surface = values[3]
    base_form = values[10] or surface
    return (
        surface,
        base_form,
        values[11],
        values[12],
        values[4],
        values[5],
        values[6],
        values[7],
        values[8],
        values[9],
    )


def _work_id_from_source_file(source_file: str) -> str:
    prefix = str(source_file).split("_", 1)[0].split(".", 1)[0]
    if prefix.isdigit():
        return prefix.zfill(6)
    return prefix


def _is_content_key(key: tuple[str, ...]) -> bool:
    return bool(key and key[4] in CONTENT_POS_MAJOR)


def _ndc_primary_classes(value: str) -> tuple[str, ...]:
    classes = []
    for token in str(value or "").replace("NDC", " ").split():
        normalized = token.strip()
        if not normalized:
            continue
        if normalized.startswith("K") and len(normalized) > 1 and normalized[1].isdigit():
            classes.append(f"K{normalized[1]}")
        elif normalized[0].isdigit():
            classes.append(normalized[0])
    return tuple(dict.fromkeys(classes))


def _is_children_or_youth_ndc(value: str) -> bool:
    return any(token.startswith("K") for token in str(value or "").replace("NDC", " ").split())


def _orthography_accessibility_weight(value: str) -> float:
    if value == "新字新仮名":
        return 1.0
    if value == "新字旧仮名":
        return 0.55
    if value == "旧字新仮名":
        return 0.45
    if value == "旧字旧仮名":
        return 0.15
    return 0.35


def _json_counts(value: object) -> str:
    if isinstance(value, Counter):
        payload = {str(key): int(count) for key, count in value.items() if str(key)}
    else:
        payload = {}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _download(*, url: str, path: Path, force: bool) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return _file_record(url=url, path=path, status="exists")
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    request = urllib.request.Request(url, headers={"User-Agent": "LexiShift research sidecar"})
    with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    temporary.replace(path)
    return _file_record(url=url, path=path, status="downloaded")


def _file_record(*, url: str, path: Path, status: str) -> dict[str, object]:
    return {
        "filename": path.name,
        "url": url,
        "path": str(path),
        "status": status,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _existing_sqlite_record(sqlite_path: Path) -> dict[str, object]:
    frequency_rows = None
    token_rows = None
    work_profile_rows = None
    context_profile_rows = None
    with sqlite3.connect(sqlite_path) as conn:
        try:
            frequency_rows = conn.execute("SELECT COUNT(*) FROM token_frequency").fetchone()[0]
            token_rows = conn.execute(
                "SELECT value FROM metadata WHERE key = 'token_rows'"
            ).fetchone()[0]
            if _sqlite_table_exists(conn, "work_profile"):
                work_profile_rows = conn.execute("SELECT COUNT(*) FROM work_profile").fetchone()[0]
            if _sqlite_table_exists(conn, "token_context_profile"):
                context_profile_rows = conn.execute(
                    "SELECT COUNT(*) FROM token_context_profile"
                ).fetchone()[0]
        except sqlite3.DatabaseError:
            pass
    return {
        "status": "exists",
        "path": str(sqlite_path),
        "size_bytes": sqlite_path.stat().st_size,
        "sha256": _sha256_file(sqlite_path),
        "frequency_rows": frequency_rows,
        "token_rows": token_rows,
        "work_profile_rows": work_profile_rows,
        "context_profile_rows": context_profile_rows,
    }


def _sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row)


def _metadata_payload(
    *,
    output_dir: Path,
    variant: str,
    raw_records: list[dict[str, object]],
    page_records: list[dict[str, object]],
    build_record: dict[str, object] | None,
) -> dict[str, object]:
    now = _utc_now()
    artifact_relpath = "main.sqlite" if build_record else f"raw/{Path(VARIANT_FILES[variant]).name}"
    return {
        "manifest": {
            "pack_id": PACK_ID,
            "pack_kind": "frequency_sidecar",
            "provider": "aozora-word.hahasoha.net",
            "local_kind": "file",
            "build_mode": "aozora_word_morphology_aggregate",
            "artifact_relpath": artifact_relpath,
            "artifact_kind": "sqlite" if build_record else "csv.gz",
            "installed_at_utc": now,
            "raw_retained": True,
            "source_variant": variant,
            "raw_artifacts": [
                {
                    "filename": record["filename"],
                    "artifact_relpath": f"raw/{record['filename']}",
                    "sha256": record["sha256"],
                    "size_bytes": record["size_bytes"],
                }
                for record in raw_records
            ],
        },
        "provenance": {
            "schema_version": 1,
            "pack_id": PACK_ID,
            "pack_kind": "frequency_sidecar",
            "provider": "aozora-word.hahasoha.net",
            "installed_at_utc": now,
            "output_dir": str(output_dir),
            "source": {
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_SITE,
                "source_version": "2012-12 bulk UTF-8 CSV files",
                "license": "CC BY-SA 2.1 JP",
                "license_url": f"{SOURCE_SITE}/license.html",
                "notes": (
                    "Aozora morphological CSV rows are local research sidecar data. "
                    "The accepted learner-difficulty scorer is not changed by this install."
                ),
            },
            "build": build_record,
            "raw_artifacts": raw_records,
            "source_pages": page_records,
        },
    }


def _print_probe(sqlite_path: Path, term: str) -> None:
    print(f"\nProbe: {term}")
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                f.surface,
                f.base_form,
                f.reading,
                f.pos_major,
                f.pos_sub1,
                f.token_count,
                f.work_count,
                f.author_count,
                f.rank_by_token,
                ROUND(f.pmw, 4) AS pmw,
                ROUND(c.accessibility_weighted_mean, 3) AS accessibility_mean,
                c.modern_work_count,
                c.children_work_count,
                c.modern_children_work_count,
                c.accessible_work_count,
                c.hard_work_count
            FROM token_frequency AS f
            LEFT JOIN token_context_profile AS c
                ON c.surface = f.surface
                AND c.base_form = f.base_form
                AND c.reading = f.reading
                AND c.pronunciation = f.pronunciation
                AND c.pos_major = f.pos_major
                AND c.pos_sub1 = f.pos_sub1
                AND c.pos_sub2 = f.pos_sub2
                AND c.pos_sub3 = f.pos_sub3
                AND c.conjugation_type = f.conjugation_type
                AND c.conjugation_form = f.conjugation_form
            WHERE f.surface = ? OR f.base_form = ?
            ORDER BY f.token_count DESC, f.work_count DESC
            LIMIT 20
            """,
            (term, term),
        ).fetchall()
    if not rows:
        print("- no rows")
        return
    for row in rows:
        print(
            "- "
            f"{row['surface']} / {row['base_form']} [{row['reading']}] "
            f"{row['pos_major']}-{row['pos_sub1']} "
            f"count={row['token_count']} works={row['work_count']} "
            f"authors={row['author_count']} rank={row['rank_by_token']} pmw={row['pmw']} "
            f"access={row['accessibility_mean']} modern_works={row['modern_work_count']} "
            f"children_works={row['children_work_count']} "
            f"modern_children_works={row['modern_children_work_count']} "
            f"accessible_works={row['accessible_work_count']} hard_works={row['hard_work_count']}"
        )


def _resolve_output_dir(value: Path | None) -> Path:
    if value is not None:
        return _resolve_path(value)
    return _resolve_data_root() / "frequency_packs" / PACK_ID


def _resolve_data_root() -> Path:
    override = os.environ.get("LEXISHIFT_DATA_DIR")
    if override:
        root = Path(override)
    else:
        home = Path.home()
        if sys.platform == "darwin":
            root = home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
        elif sys.platform.startswith("win"):
            base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
            root = Path(base) / "LexiShift" / "LexiShift"
        else:
            root = home / ".local" / "share" / "LexiShift" / "LexiShift"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
