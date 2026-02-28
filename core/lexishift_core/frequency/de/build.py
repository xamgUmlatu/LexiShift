#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Callable, Optional

try:
    from .build_support import (
        build_pos_inventory,
        discover_dictionary_paths,
        default_language_packs_dir,
        is_proper_noun_tag,
        load_freedict_headwords,
        load_odenet_lemmas,
        load_openthesaurus_lemmas,
        normalize_pos_tag,
        normalize_token,
        parse_args,
    )
except Exception:  # noqa: BLE001
    from build_support import (  # type: ignore[no-redef]
        build_pos_inventory,
        discover_dictionary_paths,
        default_language_packs_dir,
        is_proper_noun_tag,
        load_freedict_headwords,
        load_odenet_lemmas,
        load_openthesaurus_lemmas,
        normalize_pos_tag,
        normalize_token,
        parse_args,
    )

@dataclass(frozen=True)
class BuildStats:
    input_rows: int
    malformed_rows: int
    dropped_non_numeric: int
    dropped_non_positive: int
    dropped_invalid_surface: int
    kept_rows: int
    unique_surfaces: int
    unique_lemmas: int
    total_tokens_pre_filter: int
    dropped_min_lemma_count: int
    dropped_not_in_whitelist: int
    dropped_proper_noun: int
    kept_lemmas: int
    total_tokens_post_filter: int


@dataclass(frozen=True)
class LexiconStats:
    freedict_headwords: int
    odenet_lemmas: int
    openthesaurus_lemmas: int
    whitelist_lemmas: int


@dataclass(frozen=True)
class FilterConfig:
    min_lemma_count: int
    whitelist_enabled: bool
    whitelist_min_count: int
    drop_proper_nouns: bool


@dataclass(frozen=True)
class BuildResult:
    output_path: Path
    language_packs_dir: Path
    stats: BuildStats
    lexicon_stats: LexiconStats
    filter_config: FilterConfig
    discovered_paths: dict[str, Optional[str]]
    pos_lexicon_path: Optional[Path]
    requested_whitelist_enabled: bool
    pos_inventory: dict[str, object]
    ranked: list[tuple[str, int]]
    row_count: int
    total_pmw: float


def build_lemmatizer(*, enabled: bool, lang: str) -> Callable[[str], str]:
    if not enabled:
        return lambda token: token

    try:
        import simplemma
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "simplemma is required for lemmatization. Install it with: pip install simplemma"
        ) from exc

    cache: dict[str, str] = {}

    def lemmatize(token: str) -> str:
        if token in cache:
            return cache[token]
        lemma_raw = str(simplemma.lemmatize(token, lang=lang) or "").strip()
        lemma = normalize_token(lemma_raw) or token
        cache[token] = lemma
        return lemma

    return lemmatize


def parse_leipzig_words(
    path: Path,
    *,
    min_count: int,
    max_rows: int,
) -> tuple[dict[str, int], int, int, int, int, int, int]:
    surface_counts: dict[str, int] = defaultdict(int)
    input_rows = 0
    malformed_rows = 0
    dropped_non_numeric = 0
    dropped_non_positive = 0
    dropped_invalid_surface = 0
    kept_rows = 0

    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            if max_rows > 0 and input_rows >= max_rows:
                break
            input_rows += 1

            if len(row) < 3:
                malformed_rows += 1
                continue

            surface_raw = row[1]
            count_raw = row[2]
            try:
                count = int(str(count_raw).strip())
            except ValueError:
                dropped_non_numeric += 1
                continue

            if count < min_count or count <= 0:
                dropped_non_positive += 1
                continue

            surface = normalize_token(surface_raw)
            if not surface:
                dropped_invalid_surface += 1
                continue

            surface_counts[surface] += count
            kept_rows += 1

    return (
        dict(surface_counts),
        input_rows,
        malformed_rows,
        dropped_non_numeric,
        dropped_non_positive,
        dropped_invalid_surface,
        kept_rows,
    )


def aggregate_lemmas(
    surface_counts: dict[str, int],
    *,
    lemmatize: Callable[[str], str],
    min_lemma_length: int,
) -> dict[str, int]:
    lemma_counts: dict[str, int] = defaultdict(int)
    for surface, count in surface_counts.items():
        lemma = normalize_token(lemmatize(surface))
        if not lemma:
            continue
        if len(lemma) < min_lemma_length:
            continue
        lemma_counts[lemma] += count
    return dict(lemma_counts)


def build_lexicon_whitelist(
    *,
    language_packs_dir: Path,
    freedict_de_en_path: Optional[Path],
    odenet_path: Optional[Path],
    openthesaurus_path: Optional[Path],
) -> tuple[set[str], LexiconStats, dict[str, Optional[str]]]:
    resolved_freedict, resolved_odenet, resolved_open = discover_dictionary_paths(
        language_packs_dir=language_packs_dir,
        freedict_de_en_path=freedict_de_en_path,
        odenet_path=odenet_path,
        openthesaurus_path=openthesaurus_path,
    )

    freedict_lemmas = load_freedict_headwords(resolved_freedict) if resolved_freedict else set()
    odenet_lemmas = load_odenet_lemmas(resolved_odenet) if resolved_odenet else set()
    open_lemmas = load_openthesaurus_lemmas(resolved_open) if resolved_open else set()

    whitelist = set()
    whitelist.update(freedict_lemmas)
    whitelist.update(odenet_lemmas)
    whitelist.update(open_lemmas)

    stats = LexiconStats(
        freedict_headwords=len(freedict_lemmas),
        odenet_lemmas=len(odenet_lemmas),
        openthesaurus_lemmas=len(open_lemmas),
        whitelist_lemmas=len(whitelist),
    )
    discovered = {
        "freedict_de_en_path": str(resolved_freedict) if resolved_freedict else None,
        "odenet_path": str(resolved_odenet) if resolved_odenet else None,
        "openthesaurus_path": str(resolved_open) if resolved_open else None,
    }
    return whitelist, stats, discovered


def _resolve_delimiter(sample_line: str, mode: str) -> str:
    explicit = {
        "tab": "\t",
        "comma": ",",
        "semicolon": ";",
        "pipe": "|",
    }
    if mode in explicit:
        return explicit[mode]
    # Auto mode: prefer tab strongly because our compact POS format is
    # lemma<TAB>tag1|tag2|... and tag payload often contains many pipes.
    if "\t" in sample_line:
        return "\t"
    candidates = [";", ",", "|"]
    counts = [(char, sample_line.count(char)) for char in candidates]
    counts.sort(key=lambda item: item[1], reverse=True)
    if counts and counts[0][1] > 0:
        return counts[0][0]
    return "\t"


def _strip_inline_comment(line: str) -> str:
    if " -- " in line:
        return line.split(" -- ", 1)[0].rstrip()
    return line


def _looks_like_plain_comment(line: str, delimiter: str) -> bool:
    if not line.startswith("#"):
        return False
    # german-pos-dict can have real data rows that start with '#<surface>'
    return delimiter not in line


def _resolve_pos_columns(
    *,
    parts: list[str],
    pos_format: str,
    default_lemma_col: int,
    default_tag_col: int,
) -> tuple[int, int]:
    if pos_format == "german_pos_dict":
        return 1, 2
    if pos_format == "generic_compact":
        return 0, 1
    # auto mode: prefer german-pos-dict signature when present
    if len(parts) >= 3 and ":" in parts[2]:
        return 1, 2
    return default_lemma_col, default_tag_col


def load_pos_lexicon(
    path: Path,
    *,
    delimiter_mode: str,
    pos_format: str,
    lemma_col: int,
    tag_col: int,
) -> dict[str, str]:
    tags_by_lemma: dict[str, str] = {}
    if not path.exists() or not path.is_file():
        return tags_by_lemma

    sample = ""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for raw in handle:
                candidate = _strip_inline_comment(raw.strip())
                if not candidate:
                    continue
                sample = candidate
                break
    except OSError:
        return {}

    delimiter = _resolve_delimiter(sample, delimiter_mode)

    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for raw in handle:
                line = _strip_inline_comment(raw.strip())
                if not line:
                    continue
                if _looks_like_plain_comment(line, delimiter):
                    continue

                parts = [part.strip() for part in line.split(delimiter)]
                if len(parts) < 2:
                    continue

                resolved_lemma_col, resolved_tag_col = _resolve_pos_columns(
                    parts=parts,
                    pos_format=pos_format,
                    default_lemma_col=lemma_col,
                    default_tag_col=tag_col,
                )
                max_index = max(resolved_lemma_col, resolved_tag_col)
                if len(parts) <= max_index:
                    continue

                lemma = normalize_token(parts[resolved_lemma_col])
                tag = normalize_pos_tag(parts[resolved_tag_col])
                if not lemma or not tag:
                    continue

                existing = tags_by_lemma.get(lemma)
                if existing:
                    merged = sorted(set(existing.split("|")) | {tag})
                    tags_by_lemma[lemma] = "|".join(merged)
                else:
                    tags_by_lemma[lemma] = tag
    except OSError:
        return {}

    return tags_by_lemma


def filter_lemma_counts(
    lemma_counts: dict[str, int],
    *,
    whitelist: set[str],
    pos_tags: dict[str, str],
    config: FilterConfig,
) -> tuple[dict[str, int], dict[str, Optional[str]], int, int, int]:
    filtered_counts: dict[str, int] = {}
    pos_by_lemma: dict[str, Optional[str]] = {}

    dropped_min_count = 0
    dropped_not_in_whitelist = 0
    dropped_proper_noun = 0

    for lemma, count in lemma_counts.items():
        if count < config.min_lemma_count:
            dropped_min_count += 1
            continue

        in_whitelist = lemma in whitelist
        if config.whitelist_enabled and not in_whitelist and count < config.whitelist_min_count:
            dropped_not_in_whitelist += 1
            continue

        pos_tag = pos_tags.get(lemma)
        if config.drop_proper_nouns and pos_tag and is_proper_noun_tag(pos_tag):
            dropped_proper_noun += 1
            continue

        filtered_counts[lemma] = count
        pos_by_lemma[lemma] = pos_tag

    return (
        filtered_counts,
        pos_by_lemma,
        dropped_min_count,
        dropped_not_in_whitelist,
        dropped_proper_noun,
    )


def write_frequency_db(
    output_path: Path,
    *,
    lemma_counts: dict[str, int],
    pos_by_lemma: dict[str, Optional[str]],
    pos_inventory: dict[str, object],
    stats: BuildStats,
    source_path: Path,
    lemmatized: bool,
    lang: str,
    overwrite: bool,
    lexicon_stats: LexiconStats,
    filter_config: FilterConfig,
    discovered_paths: dict[str, Optional[str]],
    pos_lexicon_path: Optional[Path],
) -> list[tuple[str, int]]:
    if output_path.exists():
        if not overwrite:
            raise FileExistsError(f"Output already exists: {output_path}")
        output_path.unlink()

    total_tokens = sum(lemma_counts.values())
    if total_tokens <= 0:
        raise ValueError("No lemma counts available after filtering.")

    ranked = sorted(lemma_counts.items(), key=lambda item: (-item[1], item[0]))

    with sqlite3.connect(str(output_path)) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("DROP TABLE IF EXISTS frequency;")
        conn.execute("DROP TABLE IF EXISTS meta;")
        conn.execute(
            "CREATE TABLE frequency (lemma TEXT NOT NULL, core_rank REAL, pmw REAL, pos TEXT);"
        )

        batch: list[tuple[str, int, float, Optional[str]]] = []
        for rank, (lemma, count) in enumerate(ranked, start=1):
            pmw = (float(count) / float(total_tokens)) * 1_000_000.0
            batch.append((lemma, rank, pmw, pos_by_lemma.get(lemma)))
            if len(batch) >= 5000:
                conn.executemany(
                    "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?);",
                    batch,
                )
                batch.clear()
        if batch:
            conn.executemany(
                "INSERT INTO frequency (lemma, core_rank, pmw, pos) VALUES (?, ?, ?, ?);",
                batch,
            )

        conn.execute("CREATE INDEX idx_frequency_lemma ON frequency (lemma);")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);")
        meta = {
            "source_file": str(source_path),
            "generated_at_utc": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "language": lang,
            "lemmatized": lemmatized,
            "table": "frequency",
            "schema": {
                "lemma": "TEXT",
                "core_rank": "REAL",
                "pmw": "REAL",
                "pos": "TEXT",
            },
            "filter_config": {
                "min_lemma_count": filter_config.min_lemma_count,
                "whitelist_enabled": filter_config.whitelist_enabled,
                "whitelist_min_count": filter_config.whitelist_min_count,
                "drop_proper_nouns": filter_config.drop_proper_nouns,
            },
            "lexicon_stats": {
                "freedict_headwords": lexicon_stats.freedict_headwords,
                "odenet_lemmas": lexicon_stats.odenet_lemmas,
                "openthesaurus_lemmas": lexicon_stats.openthesaurus_lemmas,
                "whitelist_lemmas": lexicon_stats.whitelist_lemmas,
            },
            "discovered_paths": discovered_paths,
            "pos_lexicon_path": str(pos_lexicon_path) if pos_lexicon_path else None,
            "pos_inventory": pos_inventory,
            "build_stats": {
                "input_rows": stats.input_rows,
                "malformed_rows": stats.malformed_rows,
                "dropped_non_numeric": stats.dropped_non_numeric,
                "dropped_non_positive": stats.dropped_non_positive,
                "dropped_invalid_surface": stats.dropped_invalid_surface,
                "kept_rows": stats.kept_rows,
                "unique_surfaces": stats.unique_surfaces,
                "unique_lemmas": stats.unique_lemmas,
                "total_tokens_pre_filter": stats.total_tokens_pre_filter,
                "dropped_min_lemma_count": stats.dropped_min_lemma_count,
                "dropped_not_in_whitelist": stats.dropped_not_in_whitelist,
                "dropped_proper_noun": stats.dropped_proper_noun,
                "kept_lemmas": stats.kept_lemmas,
                "total_tokens_post_filter": stats.total_tokens_post_filter,
            },
        }
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?);",
            ("metadata", json.dumps(meta, ensure_ascii=True)),
        )
        conn.commit()

    return ranked


def sanity_check_db(path: Path) -> tuple[int, float]:
    with sqlite3.connect(str(path)) as conn:
        row_count = int(conn.execute("SELECT COUNT(*) FROM frequency;").fetchone()[0])
        if row_count <= 0:
            raise ValueError("frequency table is empty.")

        min_rank = conn.execute("SELECT MIN(core_rank) FROM frequency;").fetchone()[0]
        if min_rank is None or float(min_rank) < 1:
            raise ValueError("core_rank validation failed (expected minimum >= 1).")

        total_pmw = float(conn.execute("SELECT SUM(pmw) FROM frequency;").fetchone()[0] or 0.0)
        if not (999_000.0 <= total_pmw <= 1_001_000.0):
            raise ValueError(
                f"pmw sum validation failed (expected around 1,000,000; got {total_pmw:.2f})."
            )
    return row_count, total_pmw


def _to_int(value: object, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed


def build_de_frequency_sqlite(
    *,
    input_path: Path,
    output_path: Path,
    lang: str = "de",
    min_count: int = 1,
    min_lemma_length: int = 2,
    min_lemma_count: int = 2,
    whitelist_min_count: int = 20,
    disable_lexicon_whitelist: bool = False,
    language_packs_dir: Optional[Path] = None,
    freedict_de_en_path: Optional[Path] = None,
    odenet_path: Optional[Path] = None,
    openthesaurus_path: Optional[Path] = None,
    pos_lexicon_path: Optional[Path] = None,
    pos_delimiter: str = "auto",
    pos_format: str = "auto",
    pos_lemma_col: int = 0,
    pos_tag_col: int = 1,
    drop_proper_nouns: bool = False,
    no_lemmatize: bool = False,
    overwrite: bool = False,
    max_rows: int = 0,
) -> BuildResult:
    input_path = input_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"Input path must be a file: {input_path}")

    resolved_language_packs_dir = (
        language_packs_dir.expanduser().resolve()
        if language_packs_dir is not None
        else default_language_packs_dir()
    )

    (
        surface_counts,
        input_rows,
        malformed_rows,
        dropped_non_numeric,
        dropped_non_positive,
        dropped_invalid_surface,
        kept_rows,
    ) = parse_leipzig_words(
        input_path,
        min_count=max(1, int(min_count)),
        max_rows=max(0, int(max_rows)),
    )

    lemmatizer = build_lemmatizer(enabled=not no_lemmatize, lang=str(lang))
    lemma_counts = aggregate_lemmas(
        surface_counts,
        lemmatize=lemmatizer,
        min_lemma_length=max(1, int(min_lemma_length)),
    )

    requested_whitelist_enabled = not bool(disable_lexicon_whitelist)
    whitelist, lexicon_stats, discovered_paths = build_lexicon_whitelist(
        language_packs_dir=resolved_language_packs_dir,
        freedict_de_en_path=freedict_de_en_path,
        odenet_path=odenet_path,
        openthesaurus_path=openthesaurus_path,
    )
    whitelist_enabled = requested_whitelist_enabled and bool(whitelist)

    resolved_pos_lexicon_path = (
        pos_lexicon_path.expanduser().resolve() if pos_lexicon_path else None
    )
    pos_tags = (
        load_pos_lexicon(
            resolved_pos_lexicon_path,
            delimiter_mode=pos_delimiter,
            pos_format=pos_format,
            lemma_col=max(0, int(pos_lemma_col)),
            tag_col=max(0, int(pos_tag_col)),
        )
        if resolved_pos_lexicon_path
        else {}
    )

    filter_config = FilterConfig(
        min_lemma_count=max(1, int(min_lemma_count)),
        whitelist_enabled=whitelist_enabled,
        whitelist_min_count=max(1, int(whitelist_min_count)),
        drop_proper_nouns=bool(drop_proper_nouns),
    )

    (
        filtered_lemma_counts,
        pos_by_lemma,
        dropped_min_count,
        dropped_not_in_whitelist,
        dropped_proper_noun,
    ) = filter_lemma_counts(
        lemma_counts,
        whitelist=whitelist,
        pos_tags=pos_tags,
        config=filter_config,
    )
    pos_inventory = build_pos_inventory(pos_by_lemma)

    stats = BuildStats(
        input_rows=input_rows,
        malformed_rows=malformed_rows,
        dropped_non_numeric=dropped_non_numeric,
        dropped_non_positive=dropped_non_positive,
        dropped_invalid_surface=dropped_invalid_surface,
        kept_rows=kept_rows,
        unique_surfaces=len(surface_counts),
        unique_lemmas=len(lemma_counts),
        total_tokens_pre_filter=sum(lemma_counts.values()),
        dropped_min_lemma_count=dropped_min_count,
        dropped_not_in_whitelist=dropped_not_in_whitelist,
        dropped_proper_noun=dropped_proper_noun,
        kept_lemmas=len(filtered_lemma_counts),
        total_tokens_post_filter=sum(filtered_lemma_counts.values()),
    )

    ranked = write_frequency_db(
        output_path,
        lemma_counts=filtered_lemma_counts,
        pos_by_lemma=pos_by_lemma,
        pos_inventory=pos_inventory,
        stats=stats,
        source_path=input_path,
        lemmatized=not no_lemmatize,
        lang=str(lang),
        overwrite=bool(overwrite),
        lexicon_stats=lexicon_stats,
        filter_config=filter_config,
        discovered_paths=discovered_paths,
        pos_lexicon_path=resolved_pos_lexicon_path,
    )
    row_count, total_pmw = sanity_check_db(output_path)

    return BuildResult(
        output_path=output_path,
        language_packs_dir=resolved_language_packs_dir,
        stats=stats,
        lexicon_stats=lexicon_stats,
        filter_config=filter_config,
        discovered_paths=discovered_paths,
        pos_lexicon_path=resolved_pos_lexicon_path,
        requested_whitelist_enabled=requested_whitelist_enabled,
        pos_inventory=pos_inventory,
        ranked=ranked,
        row_count=row_count,
        total_pmw=total_pmw,
    )


def main() -> None:
    args = parse_args()
    result = build_de_frequency_sqlite(
        input_path=args.input,
        output_path=args.output,
        lang=str(args.lang),
        min_count=max(1, int(args.min_count)),
        min_lemma_length=max(1, int(args.min_lemma_length)),
        min_lemma_count=max(1, int(args.min_lemma_count)),
        whitelist_min_count=max(1, int(args.whitelist_min_count)),
        disable_lexicon_whitelist=bool(args.disable_lexicon_whitelist),
        language_packs_dir=args.language_packs_dir,
        freedict_de_en_path=args.freedict_de_en_path,
        odenet_path=args.odenet_path,
        openthesaurus_path=args.openthesaurus_path,
        pos_lexicon_path=args.pos_lexicon,
        pos_delimiter=args.pos_delimiter,
        pos_format=args.pos_format,
        pos_lemma_col=max(0, int(args.pos_lemma_col)),
        pos_tag_col=max(0, int(args.pos_tag_col)),
        drop_proper_nouns=bool(args.drop_proper_nouns),
        no_lemmatize=bool(args.no_lemmatize),
        overwrite=bool(args.overwrite),
        max_rows=max(0, int(args.max_rows)),
    )

    print(f"Built: {result.output_path}")
    print(
        "Parse stats:"
        f" input_rows={result.stats.input_rows:,}, malformed_rows={result.stats.malformed_rows:,},"
        f" dropped_non_numeric={result.stats.dropped_non_numeric:,},"
        f" dropped_non_positive={result.stats.dropped_non_positive:,},"
        f" dropped_invalid_surface={result.stats.dropped_invalid_surface:,},"
        f" kept_rows={result.stats.kept_rows:,}"
    )
    print(
        "Lexicon stats:"
        f" freedict_headwords={result.lexicon_stats.freedict_headwords:,},"
        f" odenet_lemmas={result.lexicon_stats.odenet_lemmas:,},"
        f" openthesaurus_lemmas={result.lexicon_stats.openthesaurus_lemmas:,},"
        f" whitelist_lemmas={result.lexicon_stats.whitelist_lemmas:,},"
        f" whitelist_enabled={result.filter_config.whitelist_enabled}"
    )
    if result.requested_whitelist_enabled and not result.filter_config.whitelist_enabled:
        print("Note: whitelist filtering was requested but no whitelist lemmas were available; disabled.")
    print(
        "Filter stats:"
        f" dropped_min_lemma_count={result.stats.dropped_min_lemma_count:,},"
        f" dropped_not_in_whitelist={result.stats.dropped_not_in_whitelist:,},"
        f" dropped_proper_noun={result.stats.dropped_proper_noun:,},"
        f" kept_lemmas={result.stats.kept_lemmas:,}"
    )
    print(
        "Shape:"
        f" unique_surfaces={result.stats.unique_surfaces:,},"
        f" unique_lemmas_pre_filter={result.stats.unique_lemmas:,},"
        f" total_tokens_pre_filter={result.stats.total_tokens_pre_filter:,},"
        f" db_rows={result.row_count:,},"
        f" total_tokens_post_filter={result.stats.total_tokens_post_filter:,},"
        f" total_pmw={result.total_pmw:.2f}"
    )
    print(
        "POS inventory:"
        f" rows_with_pos={_to_int(result.pos_inventory.get('rows_with_pos', 0)):,},"
        f" rows_without_pos={_to_int(result.pos_inventory.get('rows_without_pos', 0)):,},"
        f" pos_inventory_size={_to_int(result.pos_inventory.get('pos_inventory_size', 0)):,},"
        f" unknown_pos_inventory_size={_to_int(result.pos_inventory.get('unknown_pos_inventory_size', 0)):,}"
    )
    print(
        "Paths:"
        f" language_packs_dir={result.language_packs_dir},"
        f" freedict_de_en_path={result.discovered_paths['freedict_de_en_path']},"
        f" odenet_path={result.discovered_paths['odenet_path']},"
        f" openthesaurus_path={result.discovered_paths['openthesaurus_path']},"
        f" pos_lexicon_path={str(result.pos_lexicon_path) if result.pos_lexicon_path else None}"
    )
    print(f"Top {max(0, int(args.report_top))} lemmas:")
    for lemma, count in result.ranked[: max(0, int(args.report_top))]:
        print(f"  {lemma}\t{count}")


if __name__ == "__main__":
    main()
