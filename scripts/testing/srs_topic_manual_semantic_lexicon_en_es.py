#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_LEXICON_JSON = TEST_INPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_es.json"
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-es-spalex-v1" / "main.sqlite"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_es_latest.md"
LANGUAGE_PAIR = "en-es"
SOURCE_CHANNEL = "product_owned_manual_semantic_lexicon"
OVERLAY_ID = "srs_topic_manual_semantic_lexicon_en_es_v1"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a product-owned en-es topic overlay from conservative manual "
            "semantic seed lists. Entries are exact-matched to the Spanish SRS corpus."
        )
    )
    parser.add_argument("--lexicon-json", type=Path, default=DEFAULT_LEXICON_JSON)
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        lexicon_json=args.lexicon_json,
        frequency_db=args.frequency_db,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    lexicon_json: Path = DEFAULT_LEXICON_JSON,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    generated_at: str | None = None,
) -> dict[str, object]:
    lexicon = _load_json(lexicon_json)
    frequency_rows = _load_frequency_rows(frequency_db)
    rows_by_key: dict[tuple[str, str], dict[str, object]] = {}
    collection_summaries: list[dict[str, object]] = []
    unmatched_entries: list[dict[str, object]] = []
    skipped_entries: list[dict[str, object]] = []
    duplicate_row_count = 0

    for collection in _mapping_rows(lexicon.get("collections")):
        if not bool(collection.get("promotion_eligible")):
            skipped_entries.extend(_skipped_collection_entries(collection))
            continue
        topic = str(collection.get("target_family") or "").strip()
        collection_id = str(collection.get("id") or "").strip()
        if not topic or not collection_id:
            skipped_entries.extend(_skipped_collection_entries(collection))
            continue
        membership = _safe_float(collection.get("membership"), default=1.0)
        confidence = _safe_float(collection.get("confidence"), default=0.98)
        matched_count = 0
        unmatched_count = 0
        for entry in _entry_rows(collection.get("entries")):
            lemma = str(entry.get("lemma") or "").strip()
            if not lemma:
                continue
            frequency = frequency_rows.get(lemma)
            if frequency is None:
                unmatched_count += 1
                unmatched_entries.append(
                    {
                        "collection_id": collection_id,
                        "lemma": lemma,
                        "topic": topic,
                        "reason": "lemma_not_in_frequency_corpus",
                    }
                )
                continue
            matched_count += 1
            row = _overlay_row(
                collection=collection,
                entry=entry,
                frequency=frequency,
                topic=topic,
                membership=membership,
                confidence=confidence,
            )
            key = (str(row["lemma"]), str(row["topic"]))
            existing = rows_by_key.get(key)
            if existing is None:
                rows_by_key[key] = row
                continue
            duplicate_row_count += 1
            rows_by_key[key] = _merge_duplicate_rows(existing, row)
        collection_summaries.append(
            {
                "id": collection_id,
                "target_family": topic,
                "entry_count": len(_entry_rows(collection.get("entries"))),
                "matched_count": matched_count,
                "unmatched_count": unmatched_count,
                "membership": membership,
                "confidence": confidence,
            }
        )

    rows = sorted(
        rows_by_key.values(),
        key=lambda row: (
            str(row.get("topic") or ""),
            _safe_float(row.get("corpus_rank"), default=999999.0),
            str(row.get("lemma") or ""),
        ),
    )
    summary = _summary(
        rows,
        collection_summaries=collection_summaries,
        unmatched_entries=unmatched_entries,
        skipped_entries=skipped_entries,
        duplicate_row_count=duplicate_row_count,
    )
    status = "ok" if rows else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "manual_semantic_lexicon_evidence_ready"
            if status == "ok"
            else "manual_semantic_lexicon_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "overlay_id": OVERLAY_ID,
        "overlay_policy": {
            "promotion_state": "product_owned_reviewed_overlay_candidate_not_default",
            "runtime_policy_change": "none",
            "source_download": "none",
            "match_policy": "exact_lemma_in_frequency_corpus",
            "membership_policy": "promotion_eligible_collections_emit_full_membership_rows",
        },
        "inputs": {
            "lexicon_json": _repo_path(lexicon_json),
            "frequency_db": str(frequency_db),
        },
        "summary": summary,
        "collections": collection_summaries,
        "unmatched_entries": unmatched_entries[:200],
        "skipped_entries": skipped_entries[:200],
        "rows": rows,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Manual Semantic Topic Lexicon",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Runtime rows: `{summary.get('row_count', 0)}`",
        f"- Unique lemmas: `{summary.get('unique_lemma_count', 0)}`",
        f"- Unmatched entries: `{summary.get('unmatched_entry_count', 0)}`",
        f"- Duplicate rows resolved: `{summary.get('duplicate_row_count', 0)}`",
        "",
        "## Topic Counts",
        "",
        "| Topic | Rows |",
        "| --- | ---: |",
    ]
    for topic, count in sorted(_as_mapping(summary.get("counts_by_topic")).items()):
        lines.append(f"| `{topic}` | {int(count)} |")
    lines.extend(
        [
            "",
            "## Collections",
            "",
            "| Collection | Topic | Matched | Unmatched |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("collections")):
        lines.append(
            f"| `{row.get('id', '')}` | `{row.get('target_family', '')}` | "
            f"{int(row.get('matched_count') or 0)} | {int(row.get('unmatched_count') or 0)} |"
        )
    unmatched = _mapping_rows(report.get("unmatched_entries"))
    if unmatched:
        lines.extend(["", "## Unmatched Sample", ""])
        for row in unmatched[:25]:
            lines.append(
                f"- `{row.get('lemma', '')}` -> `{row.get('topic', '')}` "
                f"({row.get('collection_id', '')})"
            )
    return "\n".join(lines) + "\n"


def _overlay_row(
    *,
    collection: Mapping[str, object],
    entry: Mapping[str, object],
    frequency: Mapping[str, object],
    topic: str,
    membership: float,
    confidence: float,
) -> dict[str, object]:
    lemma = str(entry.get("lemma") or "").strip()
    collection_id = str(collection.get("id") or "").strip()
    facet_id = str(collection.get("facet_id") or "").strip()
    review_id = _review_id(collection_id, lemma, topic)
    return {
        "language_pair": LANGUAGE_PAIR,
        "lemma": lemma,
        "topic": topic,
        "membership": round(membership, 6),
        "confidence_label": "strong" if confidence >= 0.9 and membership >= 1.0 else "light",
        "review_state": "product_owned_manual_seed",
        "review_id": review_id,
        "source_channel": SOURCE_CHANNEL,
        "source_label": collection_id,
        "facet_id": facet_id,
        "evidence_score": round(confidence, 6),
        "corpus_rank": frequency.get("source_rank"),
        "pmw": frequency.get("pmw"),
        "pos": str(frequency.get("pos") or ""),
        "pos_canonical": str(frequency.get("pos_canonical") or ""),
        "provenance": {
            "lexicon_id": OVERLAY_ID,
            "collection_id": collection_id,
            "display_name": str(collection.get("display_name") or ""),
            "source_note": str(collection.get("source_note") or ""),
            "source_overlay_ids": [OVERLAY_ID],
            "promotion_state": "product_owned_reviewed_overlay_candidate_not_default",
            "license_note": "Product-owned manually curated topic seed list.",
            "match_policy": "exact_lemma_in_frequency_corpus",
        },
    }


def _merge_duplicate_rows(
    left: Mapping[str, object],
    right: Mapping[str, object],
) -> dict[str, object]:
    winner = dict(left if _row_priority(left) >= _row_priority(right) else right)
    provenance = dict(_as_mapping(winner.get("provenance")))
    collection_ids: list[str] = []
    for row in (left, right):
        collection_id = str(_as_mapping(row.get("provenance")).get("collection_id") or "").strip()
        if collection_id and collection_id not in collection_ids:
            collection_ids.append(collection_id)
    if collection_ids:
        provenance["collection_ids"] = collection_ids
    winner["provenance"] = provenance
    return winner


def _row_priority(row: Mapping[str, object]) -> tuple[float, float, float]:
    return (
        _safe_float(row.get("membership")),
        _safe_float(row.get("evidence_score")),
        -_safe_float(row.get("corpus_rank"), default=999999.0),
    )


def _summary(
    rows: Sequence[Mapping[str, object]],
    *,
    collection_summaries: Sequence[Mapping[str, object]],
    unmatched_entries: Sequence[Mapping[str, object]],
    skipped_entries: Sequence[Mapping[str, object]],
    duplicate_row_count: int,
) -> dict[str, object]:
    counts_by_topic = Counter(str(row.get("topic") or "") for row in rows)
    confidence_counts = Counter(str(row.get("confidence_label") or "unknown") for row in rows)
    unique_lemmas = {str(row.get("lemma") or "").strip() for row in rows if row.get("lemma")}
    return {
        "row_count": len(rows),
        "runtime_effective_row_count": len(rows),
        "unique_lemma_count": len(unique_lemmas),
        "topic_count": len(counts_by_topic),
        "runtime_effective_topic_count": len(counts_by_topic),
        "counts_by_topic": dict(sorted(counts_by_topic.items())),
        "runtime_effective_counts_by_topic": dict(sorted(counts_by_topic.items())),
        "counts_by_confidence": dict(sorted(confidence_counts.items())),
        "runtime_effective_counts_by_confidence": dict(sorted(confidence_counts.items())),
        "collection_count": len(collection_summaries),
        "input_entry_count": sum(int(row.get("entry_count") or 0) for row in collection_summaries),
        "matched_entry_count": sum(
            int(row.get("matched_count") or 0) for row in collection_summaries
        ),
        "unmatched_entry_count": len(unmatched_entries),
        "skipped_entry_count": len(skipped_entries),
        "duplicate_row_count": duplicate_row_count,
    }


def _load_frequency_rows(path: Path) -> dict[str, dict[str, object]]:
    db_path = Path(path).expanduser()
    if not db_path.exists():
        raise FileNotFoundError(f"Missing frequency DB: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT lemma, source_rank, pmw, pos, pos_canonical
            FROM frequency
            WHERE lemma IS NOT NULL AND TRIM(lemma) != ''
            """
        ).fetchall()
    finally:
        conn.close()
    return {
        str(row["lemma"]).strip(): {
            "source_rank": _safe_float(row["source_rank"], default=0.0),
            "pmw": _safe_float(row["pmw"], default=0.0),
            "pos": str(row["pos"] or ""),
            "pos_canonical": str(row["pos_canonical"] or ""),
        }
        for row in rows
        if str(row["lemma"]).strip()
    }


def _entry_rows(value: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return rows
    for entry in value:
        if isinstance(entry, Mapping):
            lemma = str(entry.get("lemma") or "").strip()
            if lemma:
                rows.append(dict(entry))
        else:
            lemma = str(entry or "").strip()
            if lemma:
                rows.append({"lemma": lemma})
    return rows


def _skipped_collection_entries(collection: Mapping[str, object]) -> list[dict[str, object]]:
    collection_id = str(collection.get("id") or "").strip()
    topic = str(collection.get("target_family") or "").strip()
    return [
        {
            "collection_id": collection_id,
            "lemma": str(entry.get("lemma") or "").strip(),
            "topic": topic,
            "reason": "collection_not_promotion_eligible_or_missing_topic",
        }
        for entry in _entry_rows(collection.get("entries"))
    ]


def _review_id(collection_id: str, lemma: str, topic: str) -> str:
    digest = hashlib.sha1(f"{collection_id}\\0{lemma}\\0{topic}".encode("utf-8")).hexdigest()[:12]
    return f"srs-enes-manual-topic-{digest}"


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = Path(path).expanduser()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
