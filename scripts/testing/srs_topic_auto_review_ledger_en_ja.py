#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_promotion_overlay_en_ja import (  # noqa: E402
    AUTO_REVIEW_ACCEPT_DECISIONS,
    AUTO_REVIEW_REJECT_DECISIONS,
    AUTO_REVIEW_REVIEW_ONLY_DECISIONS,
    DEFAULT_AUTO_REVIEW_LABELS_JSON,
    DEFAULT_CANDIDATES_CSV,
    DEFAULT_DUMP_EVIDENCE_JSON,
    DEFAULT_WIKIDATA_EVIDENCE_JSON,
    _as_mapping,
    _autotag_promotion_rule,
    _lookup_auto_review_label,
    _mapping_rows,
    _promotion_topic,
    _runtime_blockers,
    _safe_float,
    _string_list,
)


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_auto_review_ledger_en_ja_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_auto_review_ledger_en_ja_latest.md"
LANGUAGE_PAIR = "en-ja"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a full review ledger for strict auto en-ja SRS topic candidates. "
            "The ledger is diagnostic only; promotion decisions live in the review labels JSON."
        )
    )
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES_CSV)
    parser.add_argument("--dump-evidence-json", type=Path, default=DEFAULT_DUMP_EVIDENCE_JSON)
    parser.add_argument(
        "--wikidata-evidence-json", type=Path, default=DEFAULT_WIKIDATA_EVIDENCE_JSON
    )
    parser.add_argument(
        "--auto-review-labels-json", type=Path, default=DEFAULT_AUTO_REVIEW_LABELS_JSON
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        candidates_csv=resolve_path(args.candidates_csv),
        dump_evidence_json=resolve_path(args.dump_evidence_json),
        wikidata_evidence_json=resolve_path(args.wikidata_evidence_json),
        auto_review_labels_json=resolve_path(args.auto_review_labels_json),
    )
    json_out = resolve_path(args.json_out)
    markdown_out = resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    candidates_csv: Path = DEFAULT_CANDIDATES_CSV,
    dump_evidence_json: Path = DEFAULT_DUMP_EVIDENCE_JSON,
    wikidata_evidence_json: Path = DEFAULT_WIKIDATA_EVIDENCE_JSON,
    auto_review_labels_json: Path = DEFAULT_AUTO_REVIEW_LABELS_JSON,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    candidates = load_candidate_index(candidates_csv)
    dump_evidence = load_json_or_empty(dump_evidence_json)
    wikidata_evidence = load_json_or_empty(wikidata_evidence_json)
    labels_payload = load_json_or_empty(auto_review_labels_json)
    label_index = auto_review_label_index(labels_payload)
    rows = []
    for source_path, payload in [
        (dump_evidence_json, dump_evidence),
        (wikidata_evidence_json, wikidata_evidence),
    ]:
        for row in _mapping_rows(payload.get("evidence_rows")):
            promotion_rule = _autotag_promotion_rule(row)
            if not promotion_rule or promotion_rule == "product_owned_manual_semantic_lexicon":
                continue
            rows.append(
                ledger_row(
                    row,
                    promotion_rule=promotion_rule,
                    source_path=source_path,
                    candidates=candidates,
                    label_index=label_index,
                )
            )
    rows = dedupe_rows(rows)
    rows.sort(
        key=lambda row: (
            str(row.get("topic") or ""),
            review_sort_rank(row),
            _safe_float(row.get("corrected_difficulty"), default=9.0),
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
        )
    )
    counts_by_topic = Counter(str(row.get("topic") or "") for row in rows)
    counts_by_rule = Counter(str(row.get("promotion_rule") or "") for row in rows)
    counts_by_decision = Counter(str(row.get("review_decision") or "") for row in rows)
    counts_by_source = Counter(str(row.get("source") or "") for row in rows)
    return {
        "schema_version": 1,
        "status": "ok",
        "decision": "srs_topic_auto_review_ledger_ready",
        "generated_at": generated_at,
        "language_pair": LANGUAGE_PAIR,
        "inputs": {
            "candidates_csv": repo_path(candidates_csv),
            "dump_evidence_json": repo_path(dump_evidence_json),
            "wikidata_evidence_json": repo_path(wikidata_evidence_json),
            "auto_review_labels_json": repo_path(auto_review_labels_json),
            "auto_review_labels_state": str(labels_payload.get("state") or ""),
        },
        "method": {
            "scope": "strict non-manual auto topic candidates from dump and Wikidata evidence",
            "decision_contract": (
                "Rows are review-only unless labeled accept_runtime; reject labels remove rows from the promotion overlay."
            ),
            "identity_guard": (
                "A reviewed accept can still remain runtime-blocked when the current runtime lemma-only overlay "
                "would be ambiguous for multiple readings."
            ),
        },
        "summary": {
            "row_count": len(rows),
            "counts_by_topic": dict(sorted(counts_by_topic.items())),
            "counts_by_promotion_rule": dict(sorted(counts_by_rule.items())),
            "counts_by_source": dict(sorted(counts_by_source.items())),
            "counts_by_review_decision": dict(sorted(counts_by_decision.items())),
        },
        "rows": rows,
    }


def ledger_row(
    row: Mapping[str, object],
    *,
    promotion_rule: str,
    source_path: Path,
    candidates: Mapping[str, Mapping[str, object]],
    label_index: Mapping[tuple[str, str, str], Mapping[str, object]],
) -> dict[str, object]:
    lemma = str(row.get("lemma") or "")
    reading = str(row.get("reading") or "")
    topic = _promotion_topic(row)
    candidate_info = candidates.get(lemma, {})
    label = _lookup_auto_review_label(row, topic=topic, labels=label_index)
    decision = str(label.get("decision") or "unreviewed")
    extra = _as_mapping(row.get("extra"))
    blockers = _runtime_blockers(row, candidate_info=candidate_info)
    if decision not in AUTO_REVIEW_ACCEPT_DECISIONS:
        blockers = sorted(
            set(blockers) | {"unreviewed_auto_topic_evidence_requires_manual_acceptance"}
        )
    candidate_match = candidate_row_match(candidate_info, reading)
    return {
        "topic": topic,
        "lemma": lemma,
        "reading": reading,
        "candidate_readings": _string_list(candidate_info.get("readings")),
        "corrected_difficulty": candidate_match.get("score", row.get("score")),
        "corrected_rank": candidate_match.get("rank", row.get("rank")),
        "candidate_state": row.get("candidate_state"),
        "topic_stretch_allowed": row.get("topic_stretch_allowed"),
        "promotion_rule": promotion_rule,
        "source": row.get("source"),
        "source_label": row.get("source_label"),
        "source_labels": [row.get("source_label")] if row.get("source_label") else [],
        "evidence_label": row.get("evidence_label"),
        "match_mode": row.get("match_mode"),
        "confidence": row.get("confidence"),
        "membership": row.get("membership"),
        "review_decision": decision,
        "review_reason": str(label.get("reason") or label.get("notes") or ""),
        "runtime_blockers": blockers,
        "evidence_source_path": repo_path(source_path),
        "kaikki_sense_index": extra.get("kaikki_sense_index"),
        "kaikki_glosses": _string_list(extra.get("kaikki_glosses") or row.get("glosses"))[:5],
        "kaikki_categories": _string_list(extra.get("kaikki_categories"))[:8],
        "wikipedia_title": str(extra.get("wikipedia_title") or ""),
        "wikipedia_resolved_title": str(extra.get("wikipedia_resolved_title") or ""),
        "wikipedia_categories": _string_list(extra.get("wikipedia_categories"))[:10],
        "wikidata_label": str(extra.get("wikidata_label") or ""),
        "wikidata_description": str(extra.get("wikidata_description") or ""),
        "wikidata_root_label": str(extra.get("wikidata_root_label") or ""),
        "reading_identity": str(extra.get("reading_identity") or ""),
    }


def dedupe_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    best: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    for row in rows:
        key = (
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
            str(row.get("topic") or ""),
            str(row.get("promotion_rule") or ""),
            str(row.get("source_label") or ""),
        )
        existing = best.get(key)
        if existing is None:
            best[key] = dict(row)
            continue
        existing["kaikki_glosses"] = sorted(
            set(_string_list(existing.get("kaikki_glosses")))
            | set(_string_list(row.get("kaikki_glosses")))
        )[:5]
        existing["wikipedia_categories"] = sorted(
            set(_string_list(existing.get("wikipedia_categories")))
            | set(_string_list(row.get("wikipedia_categories")))
        )[:10]
    return list(best.values())


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    rows = _mapping_rows(report.get("rows"))
    lines = [
        "# en-ja SRS Topic Auto Review Ledger",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        "",
        "## Counts By Topic",
        "",
    ]
    for topic, count in _as_mapping(summary.get("counts_by_topic")).items():
        lines.append(f"- `{topic}`: `{count}`")
    lines.extend(["", "## Counts By Review Decision", ""])
    for decision, count in _as_mapping(summary.get("counts_by_review_decision")).items():
        lines.append(f"- `{decision}`: `{count}`")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Topic | Lemma | Reading | Difficulty | Decision | Source | Label | Evidence | Blockers |",
            "| --- | --- | --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        evidence = evidence_hint(row)
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | `{row.get('reading', '')}` | "
            f"{row.get('corrected_difficulty', '')} | `{row.get('review_decision', '')}` | "
            f"`{row.get('source', '')}` | `{row.get('source_label', '')}` | {evidence} | "
            f"`{', '.join(_string_list(row.get('runtime_blockers'))[:3])}` |"
        )
    return "\n".join(lines) + "\n"


def evidence_hint(row: Mapping[str, object]) -> str:
    glosses = _string_list(row.get("kaikki_glosses"))
    if glosses:
        return "; ".join(glosses[:2])
    categories = _string_list(row.get("wikipedia_categories"))
    if categories:
        return ", ".join(categories[:4])
    description = str(row.get("wikidata_description") or "")
    if description:
        return description
    return str(row.get("evidence_label") or "")


def review_sort_rank(row: Mapping[str, object]) -> int:
    decision = str(row.get("review_decision") or "")
    if decision in AUTO_REVIEW_REJECT_DECISIONS:
        return 0
    if decision == "unreviewed":
        return 1
    if decision in AUTO_REVIEW_REVIEW_ONLY_DECISIONS:
        return 2
    if decision in AUTO_REVIEW_ACCEPT_DECISIONS:
        return 3
    return 4


def load_candidate_index(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    rows_by_lemma: dict[str, dict[str, object]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lemma = str(row.get("lemma") or "").strip()
            reading = str(row.get("reading") or "").strip()
            if not lemma:
                continue
            info = rows_by_lemma.setdefault(
                lemma,
                {
                    "rows_by_reading": {},
                    "readings": [],
                    "candidate_states": [],
                    "topic_stretch_allowed_values": [],
                },
            )
            if reading:
                info["readings"].append(reading)
                info["rows_by_reading"][reading] = {
                    "rank": row.get("rank"),
                    "score": row.get("score") or row.get("current"),
                }
            state = str(row.get("candidate_state") or "").strip()
            if state:
                info["candidate_states"].append(state)
            stretch = str(row.get("topic_stretch_allowed") or "").strip()
            if stretch:
                info["topic_stretch_allowed_values"].append(stretch)
    return {
        lemma: {
            "rows_by_reading": dict(_as_mapping(info.get("rows_by_reading"))),
            "readings": sorted(set(_string_list(info.get("readings")))),
            "candidate_states": sorted(set(_string_list(info.get("candidate_states")))),
            "topic_stretch_allowed_values": sorted(
                set(_string_list(info.get("topic_stretch_allowed_values")))
            ),
        }
        for lemma, info in rows_by_lemma.items()
    }


def candidate_row_match(candidate_info: Mapping[str, object], reading: str) -> Mapping[str, object]:
    rows_by_reading = _as_mapping(candidate_info.get("rows_by_reading"))
    row = rows_by_reading.get(reading)
    return row if isinstance(row, Mapping) else {}


def auto_review_label_index(
    labels_payload: Mapping[str, object],
) -> dict[tuple[str, str, str], Mapping[str, object]]:
    labels: dict[tuple[str, str, str], Mapping[str, object]] = {}
    for row in _mapping_rows(labels_payload.get("labels")):
        lemma = str(row.get("lemma") or "").strip()
        reading = str(row.get("reading") or "").strip()
        topic = str(row.get("topic") or row.get("family_id") or row.get("family") or "").strip()
        if lemma and topic:
            labels[(lemma, reading, topic)] = row
    return labels


def load_json_or_empty(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
