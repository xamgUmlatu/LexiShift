#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.candidate_classification import (  # noqa: E402
    CANDIDATE_STATE_NORMAL_VOCAB,
    classify_srs_candidate,
)


PAIR = "en-de"
DEFAULT_ROWS_JSONL = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_candidate_classification_review_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_candidate_classification_review_en_de_latest.md"
)
DEFAULT_SAMPLE_LIMIT = 80


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Review conservative en-de SRS candidate-classification hits and richer "
            "support-gap diagnostics against the current learner-difficulty signal palette."
        )
    )
    parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        signal_rows=_load_jsonl(args.rows_jsonl),
        sample_limit=max(1, int(args.sample_limit)),
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
    return 0


def build_report(
    *,
    signal_rows: Sequence[Mapping[str, object]],
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
) -> dict[str, object]:
    runtime_hits: list[dict[str, object]] = []
    support_gap_hits: list[dict[str, object]] = []
    runtime_state_counts: Counter[str] = Counter()
    runtime_reason_counts: Counter[str] = Counter()
    support_gap_reason_counts: Counter[str] = Counter()

    for row in signal_rows:
        lemma = str(row.get("lemma") or "").strip()
        if not lemma:
            continue
        classification = classify_srs_candidate(
            language_pair=PAIR,
            lemma=lemma,
            raw_pos=row.get("pos"),
        )
        if classification.candidate_state != CANDIDATE_STATE_NORMAL_VOCAB:
            runtime_state_counts[classification.candidate_state] += 1
            for reason in classification.reasons:
                runtime_reason_counts[str(reason)] += 1
            runtime_hits.append(_review_row(row, classification=classification))

        support_gap_reasons = _support_gap_reasons(row)
        if support_gap_reasons:
            for reason in support_gap_reasons:
                support_gap_reason_counts[reason] += 1
            support_gap_hits.append(
                {
                    **_review_row(row, classification=classification),
                    "support_gap_reasons": support_gap_reasons,
                }
            )

    runtime_hits = sorted(runtime_hits, key=_review_sort_key)
    support_gap_hits = sorted(support_gap_hits, key=_review_sort_key)
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_de_candidate_classification_review_ready",
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "method": {
            "runtime_policy": (
                "Uses classify_srs_candidate with only runtime-available lemma and POS "
                "evidence. These hits can affect admission after en-de SRS resources "
                "are regenerated."
            ),
            "support_gap_policy": (
                "Uses richer signal-palette-only evidence such as translation support, "
                "reverse support, learner sources, topic hints, and Klexikon/ODenet. "
                "These rows are diagnostic only and are not runtime classifier rules."
            ),
            "sample_limit": sample_limit,
        },
        "summary": {
            "signal_row_count": len(signal_rows),
            "runtime_hit_count": len(runtime_hits),
            "runtime_state_counts": dict(sorted(runtime_state_counts.items())),
            "runtime_reason_counts": dict(sorted(runtime_reason_counts.items())),
            "support_gap_hit_count": len(support_gap_hits),
            "support_gap_reason_counts": dict(sorted(support_gap_reason_counts.items())),
        },
        "runtime_hits_sample": runtime_hits[:sample_limit],
        "support_gap_hits_sample": support_gap_hits[:sample_limit],
        "limitations": [
            "The runtime classifier cannot see translation/reverse-support evidence today.",
            "Rows with existing stored candidate_state metadata require SRS resource regeneration before classifier changes are reflected.",
            "Support-gap diagnostics should be reviewed before becoming default runtime or admission policy.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de SRS Candidate Classification Review",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Summary",
        "",
        f"- Signal rows: `{summary.get('signal_row_count')}`",
        f"- Runtime classifier hits: `{summary.get('runtime_hit_count')}`",
        f"- Support-gap diagnostic hits: `{summary.get('support_gap_hit_count')}`",
        "",
        "Runtime state counts:",
        "",
        "| State | Rows |",
        "| --- | ---: |",
    ]
    for state, count in _as_mapping(summary.get("runtime_state_counts")).items():
        lines.append(f"| `{state}` | {count} |")
    lines.extend(
        [
            "",
            "Runtime reason counts:",
            "",
            "| Reason | Rows |",
            "| --- | ---: |",
        ]
    )
    for reason, count in _as_mapping(summary.get("runtime_reason_counts")).items():
        lines.append(f"| `{reason}` | {count} |")
    lines.extend(["", "## Runtime Hits Sample", "", _row_table(report.get("runtime_hits_sample"))])
    lines.extend(
        [
            "",
            "## Support-Gap Diagnostic Hits Sample",
            "",
            _row_table(report.get("support_gap_hits_sample"), include_support_gap=True),
            "",
            "## Limitations",
            "",
        ]
    )
    for limitation in _sequence(report.get("limitations")):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def _review_row(
    row: Mapping[str, object],
    *,
    classification: object,
) -> dict[str, object]:
    translations = [
        str(item).strip() for item in _sequence(row.get("translations")) if str(item).strip()
    ]
    topics = [str(item).strip() for item in _sequence(row.get("topics")) if str(item).strip()]
    return {
        "lemma": str(row.get("lemma") or "").strip(),
        "pos": str(row.get("pos") or "").strip(),
        "pos_bucket": str(row.get("pos_bucket") or "").strip(),
        "frequency_blend": _rounded(row.get("frequency_blend")),
        "rank_base": _rounded(row.get("rank_base")),
        "pmw_base": _rounded(row.get("pmw_base")),
        "learner_source_confidence": _rounded(row.get("learner_source_confidence")),
        "translation_count_score": _rounded(row.get("translation_count_score")),
        "reverse_support_score": _rounded(row.get("reverse_support_score")),
        "klexikon_title_known": _rounded(row.get("klexikon_title_known")),
        "odenet_basis_learner_source_known": _rounded(row.get("odenet_basis_learner_source_known")),
        "classification": {
            "candidate_state": getattr(classification, "candidate_state", ""),
            "presentation_mode": getattr(classification, "presentation_mode", ""),
            "problem_class": getattr(classification, "problem_class", ""),
            "confidence": getattr(classification, "confidence", ""),
            "admission_suitability": _rounded(
                getattr(classification, "admission_suitability", None)
            ),
            "reasons": list(getattr(classification, "reasons", ()) or ()),
        },
        "translations": translations[:5],
        "topics": topics[:8],
    }


def _support_gap_reasons(row: Mapping[str, object]) -> list[str]:
    lemma = str(row.get("lemma") or "").strip()
    if not lemma:
        return []
    has_translations = any(str(item).strip() for item in _sequence(row.get("translations")))
    has_topics = any(str(item).strip() for item in _sequence(row.get("topics")))
    has_reverse_support = (_float(row.get("reverse_support_score")) or 0.0) > 0.0
    has_translation_support = (_float(row.get("translation_count_score")) or 0.0) > 0.0
    has_learner_support = (_float(row.get("learner_source_confidence")) or 0.0) > 0.0
    has_child_reference = (_float(row.get("klexikon_title_known")) or 0.0) > 0.0
    has_basis_reference = (_float(row.get("odenet_basis_learner_source_known")) or 0.0) > 0.0
    if (
        has_translations
        or has_topics
        or has_reverse_support
        or has_translation_support
        or has_learner_support
        or has_child_reference
        or has_basis_reference
    ):
        return []

    reasons = ["no_semantic_or_learner_support"]
    if "-" in lemma:
        reasons.append("hyphenated_without_support")
    if len(lemma) <= 3 and str(row.get("pos_bucket") or "").strip() in {"", "other"}:
        reasons.append("short_other_without_support")
    if not str(row.get("pos") or "").strip():
        reasons.append("missing_pos_without_support")
    return reasons


def _row_table(value: object, *, include_support_gap: bool = False) -> str:
    rows = [_as_mapping(row) for row in _sequence(value)]
    if not rows:
        return "_No rows._"
    support_header = " | support gap" if include_support_gap else ""
    lines = [
        f"| lemma | state | reason | freq | rank | pos bucket | translations{support_header} |",
        f"| --- | --- | --- | ---: | ---: | --- | ---{' | ---' if include_support_gap else ''} |",
    ]
    for row in rows:
        classification = _as_mapping(row.get("classification"))
        reasons = ", ".join(str(reason) for reason in _sequence(classification.get("reasons")))
        translations = "; ".join(str(item) for item in _sequence(row.get("translations")))
        support = ""
        if include_support_gap:
            support = " | " + ", ".join(
                str(reason) for reason in _sequence(row.get("support_gap_reasons"))
            )
        lines.append(
            f"| `{_escape(row.get('lemma'))}` | "
            f"`{_escape(classification.get('candidate_state'))}` | "
            f"{_escape(reasons)} | "
            f"{_fmt(row.get('frequency_blend'))} | "
            f"{_fmt(row.get('rank_base'))} | "
            f"`{_escape(row.get('pos_bucket'))}` | "
            f"{_escape(translations) or '-'}{support} |"
        )
    return "\n".join(lines)


def _review_sort_key(row: Mapping[str, object]) -> tuple[float, float, str]:
    return (
        _float(row.get("frequency_blend")) or 1.0,
        _float(row.get("rank_base")) or 1.0,
        str(row.get("lemma") or ""),
    )


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sequence(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _rounded(value: object) -> float | None:
    parsed = _float(value)
    if parsed is None:
        return None
    return round(parsed, 6)


def _fmt(value: object) -> str:
    parsed = _float(value)
    if parsed is None:
        return "-"
    return f"{parsed:.3f}"


def _escape(value: object) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("|", "\\|")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


if __name__ == "__main__":
    raise SystemExit(main())
