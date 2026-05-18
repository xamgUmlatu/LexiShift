from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Mapping, Sequence


def path_if_exists(path: Path | None) -> Path | None:
    if path is None:
        return None
    resolved = path.expanduser()
    return resolved if resolved.exists() else None


def resolve_kaikki_forward_db(pair: str, configured_path: Path | None) -> Path | None:
    explicit = path_if_exists(configured_path)
    if explicit is not None:
        return explicit
    if pair != "en-es":
        return None
    from lexishift_core.helper.paths import build_helper_paths

    candidate = build_helper_paths().language_packs_dir / "wiktionary-es-en.sqlite"
    return path_if_exists(candidate)


def prepare_lab_frequency_db(
    *,
    base_frequency_db: Path,
    pair: str,
    work_dir: Path,
    overlay_source_path: Path | None,
    augment_with_zipf_bridge: bool,
    zipf_bridge_path: Path | None,
    kaikki_forward_db: Path | None,
) -> tuple[Path, dict[str, object]]:
    bridge = path_if_exists(zipf_bridge_path)
    if not augment_with_zipf_bridge:
        return base_frequency_db, {"status": "disabled"}
    if pair != "en-es":
        return base_frequency_db, {"status": "skipped", "reason": "pair_not_supported"}
    if bridge is None:
        return base_frequency_db, {"status": "skipped", "reason": "zipf_bridge_missing"}

    output = work_dir / "srs-admission-lab-zipf-augmented.sqlite"
    summary = build_zipf_augmented_frequency_db(
        base_frequency_db=base_frequency_db,
        output_frequency_db=output,
        pair=pair,
        overlay_source_path=overlay_source_path,
        zipf_bridge_path=bridge,
        kaikki_forward_db=kaikki_forward_db,
    )
    if summary.get("status") != "applied":
        return base_frequency_db, summary
    return output, summary


def build_zipf_augmented_frequency_db(
    *,
    base_frequency_db: Path,
    output_frequency_db: Path,
    pair: str,
    overlay_source_path: Path | None,
    zipf_bridge_path: Path,
    kaikki_forward_db: Path | None,
) -> dict[str, object]:
    base_rows = _load_base_frequency_rows(base_frequency_db)
    bridge_rows = _load_zipf_bridge_targets(zipf_bridge_path)
    if not bridge_rows:
        return {"status": "skipped", "reason": "zipf_bridge_empty"}
    topic_by_lemma = _load_overlay_topics(overlay_source_path, pair=pair)
    candidate_lemmas = set(base_rows) | set(bridge_rows)
    compact_pos_by_lemma = _load_kaikki_compact_pos(
        kaikki_forward_db,
        lemmas=sorted(candidate_lemmas),
    )

    records: dict[str, dict[str, object]] = {}
    for lemma, row in base_rows.items():
        records[lemma] = {
            "lemma": lemma,
            "source_family": "freq-es-cde",
            "cde_rank": row.get("rank"),
            "cde_freq": row.get("frequency"),
            "cde_pos": row.get("pos") or "",
            "bridge_zipf": None,
            "bridge_source": "",
        }
    for lemma, row in bridge_rows.items():
        record = records.setdefault(
            lemma,
            {
                "lemma": lemma,
                "source_family": "zipf_bridge",
                "cde_rank": None,
                "cde_freq": None,
                "cde_pos": "",
            },
        )
        record["bridge_zipf"] = row.get("zipf")
        record["bridge_source"] = row.get("source") or ""
        if record.get("source_family") == "freq-es-cde":
            record["source_family"] = "freq-es-cde+zipf_bridge"
    for lemma, topics in topic_by_lemma.items():
        if lemma in records:
            records[lemma]["topics"] = ",".join(topics)

    ordered_records = sorted(records.values(), key=_augmented_frequency_sort_key)
    total = len(ordered_records)
    inserted_rows = []
    added_lemmas = []
    zipf_rank_by_lemma: dict[str, int] = {}
    for index, record in enumerate(ordered_records, start=1):
        lemma = str(record["lemma"])
        if lemma in bridge_rows:
            zipf_rank_by_lemma[lemma] = index
        if lemma not in base_rows:
            added_lemmas.append(lemma)
        topics = str(record.get("topics") or "")
        cde_pos = str(record.get("cde_pos") or "").strip()
        compact_pos = compact_pos_by_lemma.get(lemma) or cde_pos
        inserted_rows.append(
            (
                float(index),
                float(total - index + 1),
                record.get("bridge_zipf") or record.get("cde_freq"),
                lemma,
                compact_pos,
                record.get("source_family") or "",
                record.get("bridge_zipf") or record.get("cde_rank"),
                record.get("bridge_zipf") or record.get("cde_freq"),
                record.get("cde_rank"),
                record.get("cde_freq"),
                cde_pos,
                record.get("bridge_zipf"),
                record.get("bridge_source") or "",
                topics,
                "topic_overlay" if topics else "",
                _pos_source(compact_pos_by_lemma, lemma, cde_pos),
            )
        )

    _write_augmented_frequency_db(output_frequency_db, inserted_rows)
    overlay_missing_without_bridge = [
        lemma for lemma in topic_by_lemma if lemma not in base_rows and lemma not in bridge_rows
    ]
    example_lemmas = ("perro", "gato", "caballo", "ave", "pájaro", "león", "vaca", "pez")
    return {
        "status": "applied",
        "runtime_scope": "dev_lab_only",
        "output_frequency_db": str(output_frequency_db),
        "base_frequency_db": str(base_frequency_db),
        "zipf_bridge_path": str(zipf_bridge_path),
        "kaikki_forward_db": str(kaikki_forward_db) if kaikki_forward_db else None,
        "base_row_count": len(base_rows),
        "bridge_target_count": len(bridge_rows),
        "output_row_count": total,
        "added_row_count": len(added_lemmas),
        "added_lemma_sample": added_lemmas[:20],
        "overlay_topic_lemma_count": len(topic_by_lemma),
        "overlay_missing_without_bridge_count": len(overlay_missing_without_bridge),
        "overlay_missing_without_bridge_sample": overlay_missing_without_bridge[:20],
        "kaikki_pos_lemma_count": len(compact_pos_by_lemma),
        "example_zipf_ranks": {
            lemma: {
                "rank": zipf_rank_by_lemma.get(lemma),
                "zipf": bridge_rows.get(lemma, {}).get("zipf"),
            }
            for lemma in example_lemmas
            if lemma in bridge_rows
        },
    }


def _write_augmented_frequency_db(
    output_frequency_db: Path,
    inserted_rows: Sequence[tuple[object, ...]],
) -> None:
    output_frequency_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(output_frequency_db) as conn:
        conn.execute(
            """
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
                bridge_zipf REAL,
                bridge_source TEXT,
                topics TEXT,
                topic_source TEXT,
                pos_source TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (
                id, pmw, freq, lemma, pos, source_family, source_rank,
                source_frequency, cde_rank, cde_freq, cde_pos, bridge_zipf,
                bridge_source, topics, topic_source, pos_source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            inserted_rows,
        )
        conn.execute("CREATE INDEX idx_frequency_lemma ON frequency(lemma)")
        conn.execute("CREATE INDEX idx_frequency_rank ON frequency(id)")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            (
                "metadata",
                json.dumps(
                    {
                        "source_kind": "frequency",
                        "source_provider": "srs-admission-lab-zipf-augmented",
                        "source_profile": "spalex_bridge_plus_cde_lab_v1",
                        "rank_column": "id",
                        "pmw_column": "pmw",
                        "pos_policy": "kaikki_compact_else_cde_compact",
                        "topic_policy": "animals_plants_overlay_topics",
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            ),
        )
        conn.commit()


def _load_base_frequency_rows(path: Path) -> dict[str, dict[str, object]]:
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        columns = set(_column_names(conn, "frequency"))
        rank_expr = _first_existing(("id", "core_rank", "rank", "index"), columns) or "rowid"
        freq_expr = _first_existing(("pmw", "freq", "frequency", "count"), columns) or "0"
        pos_expr = _first_existing(("pos", "part_of_speech"), columns) or "''"
        rows = {}
        for row in conn.execute(
            f"""
            SELECT lemma, {rank_expr} AS rank_value, {freq_expr} AS frequency_value,
                   {pos_expr} AS pos_value
            FROM frequency
            WHERE TRIM(COALESCE(lemma, '')) != ''
            ORDER BY rank_value
            """
        ):
            lemma = str(row["lemma"] or "").strip()
            if not lemma or lemma in rows:
                continue
            rows[lemma] = {
                "rank": _safe_float(row["rank_value"]),
                "frequency": _safe_float(row["frequency_value"]),
                "pos": str(row["pos_value"] or "").strip(),
            }
    return rows


def _load_zipf_bridge_targets(path: Path) -> dict[str, dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid Zipf bridge JSON: {path}") from exc
    targets: dict[str, dict[str, object]] = {}
    for row in payload.get("full_source_target_pairs", ()):
        if not isinstance(row, Mapping):
            continue
        lemma = str(row.get("target") or "").strip()
        zipf = _safe_float(row.get("target_zipf_frequency_es"))
        if not lemma or zipf is None:
            continue
        existing = _safe_float(targets.get(lemma, {}).get("zipf"))
        if existing is not None and existing >= zipf:
            continue
        targets[lemma] = {
            "zipf": zipf,
            "source": str(row.get("source") or "").strip(),
        }
    return targets


def _load_overlay_topics(path: Path | None, *, pair: str) -> dict[str, tuple[str, ...]]:
    source = path_if_exists(path)
    if source is None:
        return {}
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid topic overlay JSON: {source}") from exc
    grouped: dict[str, list[str]] = {}
    for row in payload.get("rows", ()):
        if not isinstance(row, Mapping):
            continue
        if str(row.get("language_pair") or "").strip() != pair:
            continue
        membership = _safe_float(row.get("membership")) or 0.0
        if membership < 0.5:
            continue
        lemma = str(row.get("lemma") or "").strip()
        topic = str(row.get("topic") or "").strip()
        if not lemma or not topic:
            continue
        topics = grouped.setdefault(lemma, [])
        if topic not in topics:
            topics.append(topic)
    return {lemma: tuple(topics) for lemma, topics in grouped.items()}


def _load_kaikki_compact_pos(path: Path | None, *, lemmas: Sequence[str]) -> dict[str, str]:
    source = path_if_exists(path)
    if source is None or not lemmas:
        return {}
    result: dict[str, str] = {}
    with sqlite3.connect(source) as conn:
        for chunk in _chunks([lemma for lemma in lemmas if lemma], 500):
            placeholders = ",".join("?" for _item in chunk)
            rows = conn.execute(
                f"""
                SELECT headword_lc, pos
                FROM entry_meta
                WHERE headword_lc IN ({placeholders})
                """,
                chunk,
            ).fetchall()
            best_by_lemma: dict[str, tuple[int, str]] = {}
            for lemma, raw_pos in rows:
                compact_pos = _compact_kaikki_pos(raw_pos)
                if compact_pos is None:
                    continue
                score, tag = compact_pos
                current = best_by_lemma.get(str(lemma))
                if current is None or score < current[0]:
                    best_by_lemma[str(lemma)] = (score, tag)
            for lemma, (_score, compact_pos) in best_by_lemma.items():
                result[lemma] = compact_pos
    return result


def _compact_kaikki_pos(raw_pos: object) -> tuple[int, str] | None:
    priority = {
        "noun": (0, "n"),
        "proper noun": (0, "n"),
        "name": (0, "n"),
        "adj": (1, "j"),
        "adjective": (1, "j"),
        "verb": (2, "v"),
        "adv": (3, "r"),
        "adverb": (3, "r"),
        "pron": (4, "p"),
        "pronoun": (4, "p"),
        "det": (5, "l"),
        "determiner": (5, "l"),
        "article": (5, "l"),
        "prep": (6, "e"),
        "preposition": (6, "e"),
        "adp": (6, "e"),
        "conj": (7, "c"),
        "conjunction": (7, "c"),
        "intj": (8, "i"),
        "interjection": (8, "i"),
        "num": (9, "m"),
        "numeral": (9, "m"),
    }
    normalized_pos = str(raw_pos or "").strip().lower().replace("_", " ")
    return priority.get(normalized_pos)


def _pos_source(compact_pos_by_lemma: Mapping[str, str], lemma: str, cde_pos: str) -> str:
    if compact_pos_by_lemma.get(lemma):
        return "kaikki"
    if cde_pos:
        return "freq-es-cde"
    return ""


def _column_names(conn: sqlite3.Connection, table: str) -> tuple[str, ...]:
    return tuple(str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})"))


def _first_existing(candidates: Sequence[str], available: set[str]) -> str | None:
    for candidate in candidates:
        if candidate in available:
            return candidate
    return None


def _chunks(items: Sequence[str], size: int) -> Sequence[Sequence[str]]:
    return tuple(items[index : index + size] for index in range(0, len(items), size))


def _augmented_frequency_sort_key(record: Mapping[str, object]) -> tuple[int, float, float, str]:
    zipf = _safe_float(record.get("bridge_zipf"))
    if zipf is not None:
        return (0, -zipf, 0.0, str(record.get("lemma") or ""))
    rank = _safe_float(record.get("cde_rank"))
    return (1, 0.0, rank if rank is not None else float("inf"), str(record.get("lemma") or ""))


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None
