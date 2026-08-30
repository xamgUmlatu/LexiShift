#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_CANDIDATES_JSON = (
    TEST_OUTPUTS_ROOT / "srs_wikidata_natural_taxonomy_candidates_en_de_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_wikidata_natural_taxonomy_topic_overlay_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_wikidata_natural_taxonomy_topic_overlay_en_de_latest.md"
)
DEFAULT_PAIR = "en-de"
PROMOTABLE_TOPICS = {"animals", "plants_nature"}
PROMOTABLE_CONFIDENCE_LABELS = {"strong_direct_taxonomy", "light"}
PROMOTION_EXCLUDED_LEMMAS_BY_TOPIC = {
    "animals": set(),
    "plants_nature": set(),
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Promote reviewed Wikidata natural-taxonomy source candidates into a normal "
            "en-de SRS topic overlay artifact. This consumes local candidate artifacts only; "
            "Wikidata is not a runtime dependency."
        )
    )
    parser.add_argument("--candidates-json", type=Path, default=DEFAULT_CANDIDATES_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_overlay(
        candidate_payload=_load_json(args.candidates_json),
        candidate_path=args.candidates_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_overlay(
    *,
    candidate_payload: Mapping[str, object],
    candidate_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    skipped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in _mapping_rows(candidate_payload.get("new_candidates")):
        lemma = str(candidate.get("lemma") or "").strip()
        topic = str(candidate.get("topic") or "").strip()
        confidence = str(candidate.get("confidence_label") or "").strip()
        if topic not in PROMOTABLE_TOPICS or confidence not in PROMOTABLE_CONFIDENCE_LABELS:
            skipped.append({"lemma": lemma, "topic": topic, "reason": "not_promotable"})
            continue
        if lemma in PROMOTION_EXCLUDED_LEMMAS_BY_TOPIC.get(topic, set()):
            skipped.append({"lemma": lemma, "topic": topic, "reason": "promotion_excluded"})
            continue
        if not lemma:
            skipped.append({"lemma": lemma, "topic": topic, "reason": "missing_lemma"})
            continue
        key = (lemma, topic)
        if key in seen:
            skipped.append({"lemma": lemma, "topic": topic, "reason": "duplicate"})
            continue
        seen.add(key)
        rows.append(_overlay_row(candidate, candidate_path=candidate_path))

    rows.sort(key=lambda row: (str(row["topic"]), str(row["lemma"]), str(row["review_id"])))
    counts_by_topic = Counter(str(row["topic"]) for row in rows)
    counts_by_confidence = Counter(str(row["confidence_label"]) for row in rows)
    status = "ok" if rows else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_wikidata_natural_taxonomy_topic_overlay_ready"
            if status == "ok"
            else "srs_wikidata_natural_taxonomy_topic_overlay_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "overlay_id": "srs_wikidata_natural_taxonomy_topic_overlay_en_de_v1",
        "language_pair": DEFAULT_PAIR,
        "inputs": {
            "candidates_json": _repo_path(candidate_path),
            "candidate_decision": str(candidate_payload.get("decision") or ""),
        },
        "overlay_policy": {
            "promotion_state": "reviewed_wikidata_source_candidate_not_product_default",
            "runtime_policy_change": "none",
            "source_download": "none",
            "source": "Wikidata structured data German label/alias intersection promoted from local candidate packet",
            "source_license": "Wikidata structured data CC0",
            "runtime_dependency": "none",
            "duplicate_policy": "dedupe by lemma/topic within this overlay",
        },
        "summary": {
            "row_count": len(rows),
            "runtime_effective_row_count": len(rows),
            "topic_count": len(counts_by_topic),
            "runtime_effective_topic_count": len(counts_by_topic),
            "counts_by_topic": dict(sorted(counts_by_topic.items())),
            "runtime_effective_counts_by_topic": dict(sorted(counts_by_topic.items())),
            "counts_by_confidence": dict(sorted(counts_by_confidence.items())),
            "runtime_effective_counts_by_confidence": dict(sorted(counts_by_confidence.items())),
            "skipped_count": len(skipped),
        },
        "skipped": skipped,
        "rows": rows,
        "limitations": [
            "This overlay internalizes reviewed source candidates; it does not make Wikidata a runtime dependency.",
            "Rows are useful for admission-preview/topic preference testing, but natural taxonomy coverage is intentionally incomplete.",
            "Polysemic labels are retained when the source candidate packet judged them acceptable enough for topic preference use.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Wikidata Natural Taxonomy Topic Overlay",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Skipped: `{summary.get('skipped_count', 0)}`",
        "",
        "## Topic Counts",
        "",
        "| Topic | Rows |",
        "| --- | ---: |",
    ]
    for topic, count in _as_mapping(summary.get("counts_by_topic")).items():
        lines.append(f"| `{topic}` | {count} |")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Topic | Lemma | Confidence | Membership | Roots | Match |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("rows"))[:180]:
        provenance = _as_mapping(row.get("provenance"))
        roots = ", ".join(str(item) for item in provenance.get("wikidata_roots", []))
        kinds = ", ".join(str(item) for item in provenance.get("wikidata_match_kinds", []))
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | "
            f"`{row.get('confidence_label', '')}` | {row.get('membership', '')} | "
            f"{roots} | {kinds} |"
        )
    lines.extend(["", "## Limitations", ""])
    for limitation in report.get("limitations", []):
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def _overlay_row(
    candidate: Mapping[str, object], *, candidate_path: Path | None
) -> dict[str, object]:
    lemma = str(candidate.get("lemma") or "").strip()
    topic = str(candidate.get("topic") or "").strip()
    confidence = str(candidate.get("confidence_label") or "").strip()
    membership = _safe_float(candidate.get("membership"))
    return {
        "language_pair": DEFAULT_PAIR,
        "lemma": lemma,
        "topic": topic,
        "review_id": f"srs-wikidata-natural-taxonomy:{topic}:{lemma}",
        "membership": round(membership, 6),
        "confidence_label": "strong" if membership >= 1.0 else "light",
        "source_channel": "wikidata_structured_data",
        "source_label": "wikidata_natural_taxonomy_reviewed_candidate",
        "review_state": "agent_reviewed_pending_product_approval",
        "provenance": {
            "promotion_state": "reviewed_wikidata_source_candidate_not_product_default",
            "candidate_json": _repo_path(candidate_path),
            "candidate_confidence_label": confidence,
            "wikidata_qids": list(candidate.get("wikidata_qids") or []),
            "wikidata_roots": list(candidate.get("wikidata_roots") or []),
            "wikidata_match_kinds": list(candidate.get("wikidata_match_kinds") or []),
            "source_license": "Wikidata structured data CC0",
            "runtime_dependency": "none",
        },
    }


def _load_json(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    return _as_mapping(payload)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
