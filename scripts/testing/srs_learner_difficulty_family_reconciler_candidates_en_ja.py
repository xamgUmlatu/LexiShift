#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _escape,
    _repo_or_home_path,
    _rounded,
    _utc_now,
)
from srs_learner_difficulty_signal_sweep_en_ja import (  # noqa: E402
    _srs_difficulty_code_paths,
)


PAIR = "en-ja"
DEFAULT_RANKING_CSV = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_final_ranking_corrected_en_ja_latest.csv"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_family_reconciler_candidates_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_family_reconciler_candidates_en_ja_latest.md"
)


@dataclass(frozen=True)
class Row:
    rank: int
    lemma: str
    reading: str
    score: float
    model_score: float
    candidate_state: str
    correction_types: str
    display_form: str
    admission_override: str
    topic_stretch_allowed: str
    manual_correction_active: str
    review_flags: str
    exact_commonness: float
    jlpt_exact_known: float
    jlpt_raw_exact_known: float
    jlpt_normalized_only_known: float
    lesson_known: float
    kana_preferred: float
    same_surface_risk: float
    reading_inheritance: float
    tail_guard: float
    suspicion_full: float


@dataclass(frozen=True)
class Candidate:
    row: Row
    anchor: Row
    support_gap: float
    score_gap: float
    confidence: float
    confidence_tier: str
    proposed_floor: float
    proposed_action: str
    reasons: tuple[str, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate dry-run post-ranking same-surface family reconciliation "
            "candidates from the corrected en-ja difficulty ranking."
        )
    )
    parser.add_argument("--ranking-csv", type=Path, default=DEFAULT_RANKING_CSV)
    parser.add_argument("--max-score", type=float, default=0.35)
    parser.add_argument("--support-gap-min", type=float, default=0.28)
    parser.add_argument("--confidence-min", type=float, default=0.45)
    parser.add_argument("--detail-limit", type=int, default=80)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        ranking_csv=_resolve_path(args.ranking_csv),
        max_score=float(args.max_score),
        support_gap_min=float(args.support_gap_min),
        confidence_min=float(args.confidence_min),
        detail_limit=max(1, int(args.detail_limit)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    ranking_csv: Path,
    max_score: float,
    support_gap_min: float,
    confidence_min: float,
    detail_limit: int,
) -> dict[str, Any]:
    rows = _load_rows(ranking_csv)
    by_surface: dict[str, list[Row]] = {}
    for row in rows:
        by_surface.setdefault(row.lemma, []).append(row)
    raw_candidates: list[Candidate] = []
    for family_rows in by_surface.values():
        if len(family_rows) < 2:
            continue
        anchors = _anchor_rows(family_rows)
        if not anchors:
            continue
        for row in family_rows:
            if row.score > max_score:
                continue
            anchor = _best_anchor_for(row, anchors)
            if anchor is None:
                continue
            candidate = _candidate_for_row(
                row=row,
                anchor=anchor,
                support_gap_min=support_gap_min,
            )
            if candidate and candidate.confidence >= confidence_min:
                raw_candidates.append(candidate)
    raw_candidates.sort(key=_candidate_sort_key)
    unapplied = [candidate for candidate in raw_candidates if not _is_active(candidate.row)]
    already_active = [candidate for candidate in raw_candidates if _is_active(candidate.row)]
    conservative = [
        candidate for candidate in unapplied if _is_conservative_batch_candidate(candidate)
    ]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "method": {
            "purpose": (
                "Dry-run a post-ranking family reconciler: after the current "
                "model and manual sidecar have produced scores, detect readings "
                "that appear to inherit strength from a much stronger same-surface "
                "anchor reading."
            ),
            "important_boundary": (
                "This artifact proposes correction candidates only. It does not "
                "change scores, runtime admission, or the manual correction layer."
            ),
            "candidate_filter": (
                "same written surface, candidate score <= max_score, stronger "
                "same-surface anchor, support gap above threshold, and confidence "
                "above threshold"
            ),
        },
        "inputs": {
            "ranking_csv": _repo_or_home_path(ranking_csv),
            "max_score": _rounded(max_score),
            "support_gap_min": _rounded(support_gap_min),
            "confidence_min": _rounded(confidence_min),
            "detail_limit": detail_limit,
        },
        "summary": _summary(
            rows=rows,
            families=by_surface,
            raw_candidates=raw_candidates,
            unapplied=unapplied,
            already_active=already_active,
            conservative=conservative,
        ),
        "conservative_batch_candidates": [
            _candidate_payload(candidate) for candidate in conservative[:detail_limit]
        ],
        "unapplied_candidates": [
            _candidate_payload(candidate) for candidate in unapplied[:detail_limit]
        ],
        "already_active_overlap": [
            _candidate_payload(candidate)
            for candidate in already_active[: max(20, detail_limit // 2)]
        ],
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={"ranking_csv": ranking_csv},
            code_paths={
                **_srs_difficulty_code_paths(),
                "family_reconciler_candidates": Path(__file__),
            },
            version_constants={
                "runtime_behavior_changed": False,
                "artifact_purpose": (
                    "Dry-run review artifact only; uses corrected ranking CSV "
                    "as input instead of model matrices."
                ),
            },
        ),
    }


def _load_rows(path: Path) -> list[Row]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [_row_from_mapping(row) for row in reader]


def _row_from_mapping(row: Mapping[str, str]) -> Row:
    return Row(
        rank=int(row["rank"]),
        lemma=str(row["lemma"]),
        reading=str(row["reading"]),
        score=_float(row.get("score")),
        model_score=_float(row.get("model_score")),
        candidate_state=str(row.get("candidate_state") or ""),
        correction_types=str(row.get("correction_types") or ""),
        display_form=str(row.get("display_form") or ""),
        admission_override=str(row.get("admission_override") or ""),
        topic_stretch_allowed=str(row.get("topic_stretch_allowed") or ""),
        manual_correction_active=str(row.get("manual_correction_active") or ""),
        review_flags=str(row.get("review_flags") or ""),
        exact_commonness=_float(row.get("exact_commonness")),
        jlpt_exact_known=_float(row.get("jlpt_exact_known")),
        jlpt_raw_exact_known=_float(row.get("jlpt_raw_exact_known")),
        jlpt_normalized_only_known=_float(row.get("jlpt_normalized_only_known")),
        lesson_known=_float(row.get("lesson_known")),
        kana_preferred=_float(row.get("kana_preferred")),
        same_surface_risk=_float(row.get("same_surface_risk")),
        reading_inheritance=_float(row.get("reading_inheritance")),
        tail_guard=_float(row.get("tail_guard")),
        suspicion_full=_float(row.get("suspicion_full")),
    )


def _anchor_rows(rows: Sequence[Row]) -> list[Row]:
    anchors = [
        row
        for row in rows
        if "restricted_admission" not in row.correction_types
        and "exclude_standalone_srs" not in row.correction_types
    ]
    return sorted(anchors, key=lambda row: (_support(row), -row.score), reverse=True)


def _best_anchor_for(row: Row, anchors: Sequence[Row]) -> Row | None:
    possible = [
        anchor
        for anchor in anchors
        if anchor.reading != row.reading
        and anchor.score <= row.score + 0.08
        and _support(anchor) > _support(row)
    ]
    if not possible:
        return None
    return max(possible, key=lambda anchor: (_support(anchor), -anchor.score))


def _candidate_for_row(
    *,
    row: Row,
    anchor: Row,
    support_gap_min: float,
) -> Candidate | None:
    if _protected_beginner(row):
        return None
    support_gap = _support(anchor) - _support(row)
    if support_gap < support_gap_min and row.same_surface_risk < 0.70:
        return None
    exact_gap = anchor.exact_commonness - row.exact_commonness
    if exact_gap < 0.12 and row.same_surface_risk < 0.70:
        return None
    score_gap = max(0.0, row.score - anchor.score)
    reasons = _reasons(row=row, anchor=anchor, support_gap=support_gap)
    if not reasons:
        return None
    confidence = _confidence(row=row, anchor=anchor, support_gap=support_gap)
    if confidence < 0.35:
        return None
    proposed_floor = _proposed_floor(row)
    return Candidate(
        row=row,
        anchor=anchor,
        support_gap=support_gap,
        score_gap=score_gap,
        confidence=confidence,
        confidence_tier=_confidence_tier(confidence),
        proposed_floor=proposed_floor,
        proposed_action="score_floor",
        reasons=tuple(reasons),
    )


def _support(row: Row) -> float:
    return min(
        1.5,
        row.exact_commonness
        + 0.20 * row.jlpt_raw_exact_known
        + 0.16 * row.lesson_known
        + 0.06 * row.jlpt_exact_known
        - 0.10 * row.jlpt_normalized_only_known
        - 0.08 * row.same_surface_risk,
    )


def _protected_beginner(row: Row) -> bool:
    return (
        row.lesson_known >= 1.0
        and row.jlpt_raw_exact_known >= 1.0
        and row.exact_commonness >= 0.12
        and row.score < 0.18
    )


def _reasons(*, row: Row, anchor: Row, support_gap: float) -> list[str]:
    reasons: list[str] = []
    if support_gap >= 0.45:
        reasons.append("large_support_gap")
    elif support_gap >= 0.28:
        reasons.append("moderate_support_gap")
    if anchor.exact_commonness - row.exact_commonness >= 0.25:
        reasons.append("weaker_exact_commonness")
    if row.same_surface_risk >= 0.70:
        reasons.append("same_surface_risk")
    if row.suspicion_full >= 0.70:
        reasons.append("high_suspicion")
    if row.jlpt_normalized_only_known >= 1.0 and row.jlpt_raw_exact_known <= 0.0:
        reasons.append("normalized_only_source")
    if row.exact_commonness <= 0.08:
        reasons.append("very_low_exact_commonness")
    return reasons


def _confidence(*, row: Row, anchor: Row, support_gap: float) -> float:
    exact_gap = max(0.0, anchor.exact_commonness - row.exact_commonness)
    confidence = 0.18
    confidence += min(0.34, support_gap * 0.38)
    confidence += min(0.24, exact_gap * 0.25)
    confidence += 0.16 * row.same_surface_risk
    confidence += 0.10 * row.suspicion_full
    confidence += 0.06 * row.tail_guard
    if row.jlpt_normalized_only_known >= 1.0 and row.jlpt_raw_exact_known <= 0.0:
        confidence += 0.08
    if row.lesson_known >= 1.0:
        confidence -= 0.18
    if row.exact_commonness >= 0.45:
        confidence -= 0.16
    if row.jlpt_raw_exact_known >= 1.0 and row.exact_commonness >= 0.30:
        confidence -= 0.10
    return max(0.0, min(1.0, confidence))


def _confidence_tier(confidence: float) -> str:
    if confidence >= 0.72:
        return "high"
    if confidence >= 0.56:
        return "medium"
    return "low"


def _proposed_floor(row: Row) -> float:
    if row.score < 0.20:
        return 0.35
    if row.score < 0.30:
        return 0.40
    if row.score < 0.40:
        return 0.45
    return min(0.60, _rounded(row.score + 0.10))


def _summary(
    *,
    rows: Sequence[Row],
    families: Mapping[str, Sequence[Row]],
    raw_candidates: Sequence[Candidate],
    unapplied: Sequence[Candidate],
    already_active: Sequence[Candidate],
    conservative: Sequence[Candidate],
) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "same_surface_family_count": sum(1 for values in families.values() if len(values) >= 2),
        "raw_candidate_count": len(raw_candidates),
        "unapplied_candidate_count": len(unapplied),
        "conservative_batch_candidate_count": len(conservative),
        "already_active_overlap_count": len(already_active),
        "unapplied_by_tier": _counts(candidate.confidence_tier for candidate in unapplied),
        "unapplied_by_score_band": _counts(_band(candidate.row.score) for candidate in unapplied),
        "conservative_by_score_band": _counts(
            _band(candidate.row.score) for candidate in conservative
        ),
        "already_active_by_tier": _counts(
            candidate.confidence_tier for candidate in already_active
        ),
    }


def _candidate_payload(candidate: Candidate) -> dict[str, Any]:
    row = candidate.row
    anchor = candidate.anchor
    return {
        "surface": row.lemma,
        "reading": row.reading,
        "rank": row.rank,
        "score": _rounded(row.score),
        "model_score": _rounded(row.model_score),
        "current_correction_types": row.correction_types,
        "current_admission": row.admission_override or row.candidate_state,
        "anchor_surface": anchor.lemma,
        "anchor_reading": anchor.reading,
        "anchor_rank": anchor.rank,
        "anchor_score": _rounded(anchor.score),
        "anchor_support": _rounded(_support(anchor)),
        "row_support": _rounded(_support(row)),
        "support_gap": _rounded(candidate.support_gap),
        "score_gap": _rounded(candidate.score_gap),
        "confidence": _rounded(candidate.confidence),
        "confidence_tier": candidate.confidence_tier,
        "proposed_action": candidate.proposed_action,
        "proposed_floor": _rounded(candidate.proposed_floor),
        "reasons": list(candidate.reasons),
        "signals": {
            "exact_commonness": _rounded(row.exact_commonness),
            "jlpt_raw_exact_known": _rounded(row.jlpt_raw_exact_known),
            "jlpt_normalized_only_known": _rounded(row.jlpt_normalized_only_known),
            "lesson_known": _rounded(row.lesson_known),
            "same_surface_risk": _rounded(row.same_surface_risk),
            "tail_guard": _rounded(row.tail_guard),
            "suspicion_full": _rounded(row.suspicion_full),
        },
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# en-ja Learner Difficulty Family Reconciler Candidates",
        "",
        f"Generated: `{_escape(str(report.get('generated_at') or ''))}`",
        "",
        "Purpose: dry-run a post-ranking family reconciler over the corrected ranking. "
        "This proposes rows whose written surface has a much stronger alternate reading, "
        "so the weaker reading may be inheriting too much ease from the surface.",
        "",
        "No scores or runtime behavior are changed by this artifact.",
        "",
        "## Summary",
        "",
        f"- Rows scanned: `{int(summary.get('row_count') or 0)}`",
        f"- Same-surface families: `{int(summary.get('same_surface_family_count') or 0)}`",
        f"- Raw candidates: `{int(summary.get('raw_candidate_count') or 0)}`",
        f"- Unapplied candidates: `{int(summary.get('unapplied_candidate_count') or 0)}`",
        (
            f"- Conservative batch candidates: "
            f"`{int(summary.get('conservative_batch_candidate_count') or 0)}`"
        ),
        f"- Already-active overlap: `{int(summary.get('already_active_overlap_count') or 0)}`",
        f"- Unapplied by tier: `{_escape(json.dumps(summary.get('unapplied_by_tier') or {}, ensure_ascii=False, sort_keys=True))}`",
        f"- Unapplied by score band: `{_escape(json.dumps(summary.get('unapplied_by_score_band') or {}, ensure_ascii=False, sort_keys=True))}`",
        f"- Conservative by score band: `{_escape(json.dumps(summary.get('conservative_by_score_band') or {}, ensure_ascii=False, sort_keys=True))}`",
        "",
        "## Conservative Batch Candidates",
        "",
        "These are the stricter subset: high confidence, strong same-surface risk, "
        "high suspicion, no lesson signal, low exact commonness, and a large support gap. "
        "They are still review candidates, not applied corrections.",
        "",
    ]
    lines.extend(_candidate_table(report.get("conservative_batch_candidates") or ()))
    lines.extend(
        [
            "",
            "## Unapplied Candidates",
            "",
        ]
    )
    lines.extend(_candidate_table(report.get("unapplied_candidates") or ()))
    lines.extend(
        [
            "",
            "## Already-Active Overlap",
            "",
            "Rows here were already handled by the manual correction layer, but the dry-run "
            "heuristic would have found them. This is useful as a sanity check.",
            "",
        ]
    )
    lines.extend(_candidate_table(report.get("already_active_overlap") or ()))
    return "\n".join(lines) + "\n"


def _candidate_table(candidates: object) -> list[str]:
    rows = [row for row in candidates if isinstance(row, Mapping)]
    lines = [
        "| Tier | Confidence | Rank | Score | Row | Anchor | Proposed | Reasons |",
        "| --- | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        reasons = ", ".join(str(reason) for reason in row.get("reasons") or ())
        lines.append(
            "| "
            f"`{_escape(str(row.get('confidence_tier') or ''))}` | "
            f"{_rounded(_float(row.get('confidence'))):.3f} | "
            f"{int(row.get('rank') or 0)} | "
            f"{_rounded(_float(row.get('score'))):.6f} | "
            f"`{_escape(str(row.get('surface') or ''))}` / `{_escape(str(row.get('reading') or ''))}` | "
            f"`{_escape(str(row.get('anchor_surface') or ''))}` / `{_escape(str(row.get('anchor_reading') or ''))}` "
            f"({_rounded(_float(row.get('anchor_score'))):.6f}) | "
            f"{_escape(str(row.get('proposed_action') or ''))} `{_rounded(_float(row.get('proposed_floor'))):.2f}` | "
            f"{_escape(reasons)} |"
        )
    return lines


def _candidate_sort_key(candidate: Candidate) -> tuple[float, float, float, int]:
    return (
        -candidate.confidence,
        candidate.row.score,
        -candidate.support_gap,
        candidate.row.rank,
    )


def _is_conservative_batch_candidate(candidate: Candidate) -> bool:
    row = candidate.row
    return (
        candidate.confidence >= 0.72
        and row.score <= 0.35
        and row.same_surface_risk >= 0.65
        and row.suspicion_full >= 0.65
        and row.lesson_known <= 0.0
        and row.exact_commonness <= 0.16
        and candidate.support_gap >= 0.35
    )


def _counts(values: Sequence[str] | Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _band(score: float) -> str:
    lo = int(score * 10) / 10
    hi = min(1.0, lo + 0.1)
    return f"{lo:.1f}-{hi:.1f}"


def _is_active(row: Row) -> bool:
    return row.manual_correction_active == "yes" or bool(row.correction_types)


def _float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
