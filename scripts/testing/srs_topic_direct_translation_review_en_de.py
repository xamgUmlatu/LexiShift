#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_CANDIDATE_JSON = (
    TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_overlay_en_de_strong_latest.json"
)
DEFAULT_REVIEW_JSON = TEST_INPUTS_ROOT / "srs_topic_direct_translation_review_en_de.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_reviewed_en_de_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_reviewed_en_de_latest.md"
LANGUAGE_PAIR = "en-de"
OVERLAY_ID = "srs_topic_direct_translation_reviewed_en_de_v1"
SOURCE_CHANNEL = "product_reviewed_direct_translation_topic_overlay"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply product review decisions to en-de direct-translation topic candidates. "
            "Accepted rows become runtime-effective overlay candidates; rejected rows stay audited."
        )
    )
    parser.add_argument("--candidate-json", type=Path, default=DEFAULT_CANDIDATE_JSON)
    parser.add_argument("--review-json", type=Path, default=DEFAULT_REVIEW_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        candidate_json=args.candidate_json,
        review_json=args.review_json,
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
    candidate_json: Path = DEFAULT_CANDIDATE_JSON,
    review_json: Path = DEFAULT_REVIEW_JSON,
    generated_at: str | None = None,
) -> dict[str, object]:
    candidate_payload = _load_json(candidate_json)
    review_payload = _load_json(review_json)
    if str(candidate_payload.get("status") or "") != "ok":
        raise ValueError(f"Candidate artifact is not ok: {candidate_json}")
    if str(review_payload.get("status") or "") != "ok":
        raise ValueError(f"Review artifact is not ok: {review_json}")

    reject_decisions = _reject_decisions_by_key(review_payload)
    accepted_rows: list[dict[str, object]] = []
    rejected_rows: list[dict[str, object]] = []
    missing_decisions: list[dict[str, object]] = []
    duplicate_candidate_count = 0
    seen_candidate_keys: set[tuple[str, str]] = set()

    acceptance_policy = _as_mapping(review_payload.get("acceptance_policy"))
    accepted_membership = _safe_float(acceptance_policy.get("accepted_membership"), default=1.0)
    accepted_confidence_label = str(acceptance_policy.get("accepted_confidence_label") or "strong")

    for candidate in _mapping_rows(candidate_payload.get("rows")):
        pair = str(candidate.get("language_pair") or "").strip()
        lemma = str(candidate.get("lemma") or "").strip()
        topic = str(candidate.get("topic") or "").strip()
        if pair != LANGUAGE_PAIR or not lemma or not topic:
            continue
        key = (topic, lemma)
        if key in seen_candidate_keys:
            duplicate_candidate_count += 1
            continue
        seen_candidate_keys.add(key)
        rejection = reject_decisions.get(key)
        if rejection is not None:
            rejected_rows.append(_rejected_row(candidate, rejection))
            continue
        accepted_rows.append(
            _accepted_row(
                candidate,
                accepted_membership=accepted_membership,
                accepted_confidence_label=accepted_confidence_label,
            )
        )

    candidate_keys = {
        (str(row.get("topic") or "").strip(), str(row.get("lemma") or "").strip())
        for row in _mapping_rows(candidate_payload.get("rows"))
    }
    for key, rejection in sorted(reject_decisions.items()):
        if key not in candidate_keys:
            missing_decisions.append(
                {
                    "topic": key[0],
                    "lemma": key[1],
                    "decision": rejection.get("decision", ""),
                    "reason": rejection.get("reason", ""),
                }
            )

    accepted_rows = sorted(
        accepted_rows,
        key=lambda row: (
            str(row.get("topic") or ""),
            _safe_float(row.get("corpus_rank"), default=999999.0),
            str(row.get("lemma") or ""),
        ),
    )
    rejected_rows = sorted(
        rejected_rows,
        key=lambda row: (
            str(row.get("topic") or ""),
            str(row.get("lemma") or ""),
        ),
    )
    summary = _summary(
        accepted_rows,
        rejected_rows=rejected_rows,
        missing_decisions=missing_decisions,
        duplicate_candidate_count=duplicate_candidate_count,
    )
    status = "ok" if accepted_rows and not missing_decisions else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_direct_translation_reviewed_en_de_ready"
            if status == "ok"
            else "srs_topic_direct_translation_reviewed_en_de_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "overlay_id": OVERLAY_ID,
        "overlay_policy": {
            "promotion_state": "product_reviewed_overlay_candidate_not_default",
            "runtime_policy_change": "none",
            "source_download": "none",
            "candidate_source_overlay_id": str(candidate_payload.get("overlay_id") or ""),
            "review_id": str(review_payload.get("review_id") or ""),
            "acceptance_policy": dict(acceptance_policy),
        },
        "inputs": {
            "candidate_json": _repo_path(candidate_json),
            "review_json": _repo_path(review_json),
        },
        "summary": summary,
        "rows": accepted_rows,
        "rejected_rows": rejected_rows,
        "missing_decisions": missing_decisions,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Reviewed Direct Translation Topic Overlay",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Accepted rows: `{summary.get('accepted_row_count', 0)}`",
        f"- Rejected rows: `{summary.get('rejected_row_count', 0)}`",
        f"- Missing review decisions: `{summary.get('missing_decision_count', 0)}`",
        "",
        "## Accepted Counts",
        "",
        "| Topic | Rows |",
        "| --- | ---: |",
    ]
    for topic, count in sorted(_as_mapping(summary.get("accepted_counts_by_topic")).items()):
        lines.append(f"| `{topic}` | {int(count)} |")
    lines.extend(["", "## Rejected Counts", "", "| Topic | Rows |", "| --- | ---: |"])
    for topic, count in sorted(_as_mapping(summary.get("rejected_counts_by_topic")).items()):
        lines.append(f"| `{topic}` | {int(count)} |")

    rejected = _mapping_rows(report.get("rejected_rows"))
    if rejected:
        lines.extend(["", "## Rejected Rows", ""])
        for row in rejected:
            lines.append(
                f"- `{row.get('topic', '')}` / `{row.get('lemma', '')}`: "
                f"{row.get('review_state', '')} - {row.get('review_note', '')}"
            )
    return "\n".join(lines) + "\n"


def _accepted_row(
    candidate: Mapping[str, object],
    *,
    accepted_membership: float,
    accepted_confidence_label: str,
) -> dict[str, object]:
    row = dict(candidate)
    provenance = dict(_as_mapping(row.get("provenance")))
    provenance["source_overlay_ids"] = _append_unique(
        _string_list(provenance.get("source_overlay_ids")),
        str(row.get("source_label") or ""),
        OVERLAY_ID,
    )
    provenance["reviewed_overlay_id"] = OVERLAY_ID
    provenance["review_policy"] = "manual_accept_from_strong_direct_translation_candidates"
    provenance["promotion_state"] = "product_reviewed_overlay_candidate_not_default"
    row["membership"] = accepted_membership
    row["confidence_label"] = accepted_confidence_label
    row["evidence_score"] = max(_safe_float(row.get("evidence_score")), 0.9)
    row["review_state"] = "product_reviewed_direct_translation"
    row["source_channel"] = SOURCE_CHANNEL
    row["source_label"] = "en_de_reviewed_direct_translation_topic"
    row["provenance"] = provenance
    return row


def _rejected_row(
    candidate: Mapping[str, object],
    rejection: Mapping[str, object],
) -> dict[str, object]:
    row = dict(candidate)
    row["membership"] = 0.0
    row["evidence_score"] = 0.0
    row["review_state"] = str(rejection.get("decision") or "rejected")
    row["review_note"] = str(rejection.get("reason") or "")
    row["source_channel"] = SOURCE_CHANNEL
    return row


def _reject_decisions_by_key(
    payload: Mapping[str, object],
) -> dict[tuple[str, str], Mapping[str, object]]:
    out: dict[tuple[str, str], Mapping[str, object]] = {}
    for row in _mapping_rows(payload.get("reject_decisions")):
        topic = str(row.get("topic") or "").strip()
        lemma = str(row.get("lemma") or "").strip()
        if not topic or not lemma:
            continue
        out[(topic, lemma)] = row
    return out


def _summary(
    accepted_rows: Sequence[Mapping[str, object]],
    *,
    rejected_rows: Sequence[Mapping[str, object]],
    missing_decisions: Sequence[Mapping[str, object]],
    duplicate_candidate_count: int,
) -> dict[str, object]:
    accepted_counts = Counter(str(row.get("topic") or "") for row in accepted_rows)
    rejected_counts = Counter(str(row.get("topic") or "") for row in rejected_rows)
    return {
        "accepted_row_count": len(accepted_rows),
        "accepted_unique_lemma_count": len({str(row.get("lemma") or "") for row in accepted_rows}),
        "accepted_topic_count": len(accepted_counts),
        "accepted_counts_by_topic": dict(sorted(accepted_counts.items())),
        "rejected_row_count": len(rejected_rows),
        "rejected_counts_by_topic": dict(sorted(rejected_counts.items())),
        "missing_decision_count": len(missing_decisions),
        "duplicate_candidate_count": duplicate_candidate_count,
    }


def _load_json(path: Path) -> Mapping[str, object]:
    resolved = Path(path).expanduser()
    if not resolved.exists():
        raise FileNotFoundError(f"Missing JSON input: {path}")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected object JSON: {path}")
    return payload


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item)]


def _append_unique(values: Sequence[str], *more_values: str) -> list[str]:
    out: list[str] = []
    for value in [*values, *more_values]:
        if value and value not in out:
            out.append(value)
    return out


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT))
    except (OSError, ValueError):
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
