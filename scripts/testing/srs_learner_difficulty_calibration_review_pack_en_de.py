#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Callable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_signal_palette_en_de import (  # noqa: E402
    build_report as build_signal_palette_report,
)


PAIR = "en-de"
DEFAULT_TOP_N = 70000
DEFAULT_TARGET_COUNT = 150
DEFAULT_BAND_SAMPLE_COUNT = 8
DEFAULT_ROWS_JSONL = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_calibration_review_pack_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_calibration_review_pack_en_de_latest.md"
)
LABEL_FLAGS = (
    "grammar_or_function_word",
    "bad_standalone_srs_item",
    "transparent_or_cognate_easy_for_english_speaker",
    "false_friend_or_translation_noise",
    "compound_or_long_form",
    "domain_or_register_specific",
    "topic_documented",
    "proper_name_or_entity",
    "needs_display_or_rule_restriction",
)
TREATMENTS = ("vocab", "restrict_admission", "display_only", "exclude", "unsure")
CONTENT_BUCKETS = frozenset(("noun", "verb", "adjective", "adverb"))


@dataclass(frozen=True)
class SelectionSpec:
    spec_id: str
    label: str
    quota: int
    selector: Callable[[Sequence[Mapping[str, object]]], list[Mapping[str, object]]]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic en-de learner-difficulty calibration review pack. "
            "The output is for human labels and does not change runtime ranking."
        )
    )
    parser.add_argument("--rows-jsonl", type=Path, default=DEFAULT_ROWS_JSONL)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT)
    parser.add_argument("--band-sample-count", type=int, default=DEFAULT_BAND_SAMPLE_COUNT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--force-rebuild-palette",
        action="store_true",
        help="Ignore row-level JSONL and rebuild the en-de signal palette in memory.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    rows = load_or_build_signal_rows(
        rows_jsonl=Path(args.rows_jsonl).expanduser(),
        top_n=max(1, int(args.top_n)),
        force_rebuild=bool(args.force_rebuild_palette),
    )
    report = build_report(
        signal_rows=rows,
        target_count=max(1, int(args.target_count)),
        band_sample_count=max(1, int(args.band_sample_count)),
    )
    json_out = Path(args.json_out).expanduser().resolve(strict=False)
    markdown_out = Path(args.markdown_out).expanduser().resolve(strict=False)
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


def load_or_build_signal_rows(
    *,
    rows_jsonl: Path,
    top_n: int,
    force_rebuild: bool = False,
) -> list[Mapping[str, object]]:
    if not force_rebuild and rows_jsonl.is_file():
        rows: list[Mapping[str, object]] = []
        with rows_jsonl.open(encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                raw = json.loads(stripped)
                if isinstance(raw, Mapping):
                    rows.append(raw)
        if rows:
            return rows
    report = build_signal_palette_report(
        top_n=top_n,
        sample_limit=8,
        include_rows=True,
    )
    return [row for row in _as_sequence(report.get("signal_rows")) if isinstance(row, Mapping)]


def build_report(
    *,
    signal_rows: Sequence[Mapping[str, object]],
    target_count: int = DEFAULT_TARGET_COUNT,
    band_sample_count: int = DEFAULT_BAND_SAMPLE_COUNT,
    generated_at: str | None = None,
) -> dict[str, object]:
    rows = [dict(row) for row in signal_rows if str(row.get("lemma") or "").strip()]
    if not rows:
        raise ValueError("signal_rows must contain at least one row")
    selected = _select_review_rows(
        rows,
        target_count=target_count,
        band_sample_count=band_sample_count,
    )
    review_rows = [_review_row(index=index, row=row) for index, row in enumerate(selected, start=1)]
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_de_learner_difficulty_calibration_review_pack_ready",
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": False,
        "manual_labels_added": False,
        "production_ranking_changed": False,
        "method": {
            "purpose": (
                "Create the first en-de learner-difficulty target set so later formula "
                "sweeps can be graded numerically instead of selected by qualitative samples."
            ),
            "selection_policy": (
                "Rows are selected from the en-de signal palette across frequency bands "
                "plus stress families: early content/function anchors, reviewed topic rows, "
                "transparent/cognate-looking rows, translation-gloss ambiguity, long compounds, "
                "tail/no-gloss rows, and boundary rows."
            ),
            "split_policy": (
                "Rows are assigned before tuning: every third row is recommended holdout; "
                "the rest are recommended calibration. Do not move holdout rows after review."
            ),
            "topic_policy": (
                "topic_documented is included as a review stress signal only. It should remain "
                "optional and weak in later sweeps, not a broad global difficulty lowerer."
            ),
        },
        "inputs": {
            "source": "srs_learner_difficulty_signal_palette_en_de_rows_latest.jsonl",
            "signal_row_count": len(rows),
            "target_count": int(target_count),
            "band_sample_count": int(band_sample_count),
        },
        "label_schema": _label_schema(),
        "summary": _summary(review_rows),
        "review_rows": review_rows,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines: list[str] = [
        "# en-de Learner Difficulty Calibration Review Pack",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Manual labels added: `{report.get('manual_labels_added')}`",
        "",
        "## Label Format",
        "",
        "Use `expected_learner_difficulty` as the numeric target: `0.00` is first-lesson German; `1.00` is recondite or effectively unusable vocabulary.",
        "",
        "Treatments:",
        "",
    ]
    for treatment in TREATMENTS:
        lines.append(f"- `{treatment}`")
    lines.extend(["", "Common flags:", ""])
    for flag in LABEL_FLAGS:
        lines.append(f"- `{flag}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Rows: `{summary.get('row_count', 0)}`",
            f"- Calibration rows: `{summary.get('calibration_count', 0)}`",
            f"- Holdout rows: `{summary.get('holdout_count', 0)}`",
            "",
            "Selection reasons:",
            "",
            "| Reason | Rows |",
            "| --- | ---: |",
        ]
    )
    for reason, count in _as_mapping(summary.get("selection_reason_counts")).items():
        lines.append(f"| `{reason}` | {count} |")
    lines.extend(
        [
            "",
            "## Review Rows",
            "",
            "| # | Split | Lemma | POS | Base | Rank | PMW | Reasons | Translations |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for raw in _as_sequence(report.get("review_rows")):
        row = _as_mapping(raw)
        signals = _as_mapping(row.get("signal_snapshot"))
        lines.append(
            f"| {row.get('review_number')} | `{row.get('recommended_split')}` | "
            f"`{_escape(row.get('lemma'))}` | `{_escape(row.get('pos_bucket'))}` | "
            f"{_fmt_float(signals.get('frequency_blend'))} | "
            f"{_fmt_rank(row.get('core_rank'))} | "
            f"{_fmt_float(row.get('pmw'))} | "
            f"{', '.join(f'`{_escape(reason)}`' for reason in _as_sequence(row.get('selection_reasons')))} | "
            f"{_escape('; '.join(str(item) for item in _as_sequence(row.get('translations'))[:3])) or '-'} |"
        )
    lines.extend(
        [
            "",
            "## JSON Label Stub",
            "",
            "Each row contains this editable label object:",
            "",
            "```json",
            json.dumps(_label_template(), ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _select_review_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    target_count: int,
    band_sample_count: int,
) -> list[Mapping[str, object]]:
    selected: dict[str, dict[str, object]] = {}

    def add(reason: str, candidates: Sequence[Mapping[str, object]], quota: int) -> None:
        _add_selected(selected, reason, candidates, quota, target_count=target_count)

    for low, high in _bands():
        add(
            f"base_band_{low:.1f}_{high:.1f}",
            _band_candidates(rows, low=low, high=high),
            band_sample_count,
        )

    specs = (
        SelectionSpec(
            "early_content_anchor",
            "early_content_frequency_anchors",
            10,
            lambda source: sorted([row for row in source if _is_content_vocab(row)], key=_rank),
        ),
        SelectionSpec(
            "early_other_anchor",
            "early_function_or_noncontent_anchors",
            8,
            lambda source: sorted(
                [row for row in source if _safe_float(row.get("other_pos_risk")) > 0.0],
                key=_rank,
            ),
        ),
        SelectionSpec(
            "topic_documented",
            "reviewed_topic_overlay_rows",
            8,
            lambda source: sorted(
                [row for row in source if _safe_float(row.get("topic_documented")) > 0.0],
                key=_rank,
            ),
        ),
        SelectionSpec(
            "cognate_or_transparent",
            "english_transparency_candidates",
            8,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if _safe_float(row.get("english_translation_similarity_ease")) >= 0.58
                ],
                key=lambda row: (
                    -_safe_float(row.get("english_translation_similarity_ease")),
                    _rank(row),
                ),
            ),
        ),
        SelectionSpec(
            "common_english_gloss",
            "common_english_translation_candidates",
            6,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if _safe_float(row.get("english_translation_frequency_ease")) >= 0.80
                    and _is_content_vocab(row)
                ],
                key=lambda row: (
                    -_safe_float(row.get("english_translation_frequency_ease")),
                    _rank(row),
                ),
            ),
        ),
        SelectionSpec(
            "translation_ambiguity",
            "high_translation_count_rows",
            6,
            lambda source: sorted(
                [row for row in source if int(row.get("translation_count") or 0) >= 8],
                key=lambda row: (
                    -int(row.get("translation_count") or 0),
                    _rank(row),
                ),
            ),
        ),
        SelectionSpec(
            "long_or_compound",
            "long_or_compound_like_rows",
            8,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if _safe_float(row.get("length_risk")) >= 0.25
                    or _safe_float(row.get("compound_like")) > 0.0
                ],
                key=lambda row: (
                    -_safe_float(row.get("length_risk")),
                    _rank(row),
                ),
            ),
        ),
        SelectionSpec(
            "tail_no_translation",
            "tail_rows_without_translation_glosses",
            8,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if not _as_sequence(row.get("translations"))
                    and _safe_float(row.get("frequency_blend")) >= 0.60
                ],
                key=lambda row: (_safe_float(row.get("frequency_blend")), _rank(row)),
                reverse=True,
            ),
        ),
        SelectionSpec(
            "boundary",
            "near_decision_boundaries",
            8,
            lambda source: _boundary_rows(source),
        ),
    )
    for spec in specs:
        add(spec.spec_id, spec.selector(rows), spec.quota)

    if len(selected) < target_count:
        add(
            "deterministic_fill",
            _exclude_selected(_evenly_spaced_by_score(rows, count=target_count * 2), selected),
            target_count - len(selected),
        )
    if len(selected) < target_count:
        add(
            "deterministic_tail_fill",
            _exclude_selected(
                sorted(rows, key=lambda row: (_safe_float(row.get("frequency_blend")), _rank(row))),
                selected,
            ),
            target_count - len(selected),
        )
    return list(selected.values())[:target_count]


def _add_selected(
    selected: dict[str, dict[str, object]],
    reason: str,
    candidates: Sequence[Mapping[str, object]],
    quota: int,
    *,
    target_count: int,
) -> None:
    for raw in candidates:
        if len(selected) >= target_count:
            return
        lemma = str(raw.get("lemma") or "").strip()
        if not lemma:
            continue
        row = selected.setdefault(lemma, dict(raw))
        reasons = list(_as_sequence(row.get("selection_reasons")))
        if reason not in reasons:
            reasons.append(reason)
        row["selection_reasons"] = reasons
        quota -= 1
        if quota <= 0:
            return


def _review_row(
    *,
    index: int,
    row: Mapping[str, object],
) -> dict[str, object]:
    return {
        "review_id": f"en-de-diff-review-{index:04d}",
        "review_number": index,
        "recommended_split": "holdout" if index % 3 == 0 else "calibration",
        "lemma": row.get("lemma"),
        "core_rank": _round(row.get("core_rank")),
        "pmw": _round(row.get("pmw")),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "translations": list(_as_sequence(row.get("translations")))[:8],
        "english_translation_tokens": list(_as_sequence(row.get("english_translation_tokens")))[:8],
        "reverse_support_terms": list(_as_sequence(row.get("reverse_support_terms")))[:8],
        "topics": list(_as_sequence(row.get("topics"))),
        "selection_reasons": list(_as_sequence(row.get("selection_reasons"))),
        "signal_snapshot": {
            key: _round(row.get(key))
            for key in (
                "frequency_blend",
                "rank_base",
                "pmw_base",
                "content_pos_gate",
                "other_pos_risk",
                "length_risk",
                "compound_like",
                "topic_documented",
                "translation_count_score",
                "english_translation_frequency_ease",
                "english_translation_similarity_ease",
                "reverse_support_score",
            )
        },
        "raw_counts": {
            "translation_count": int(row.get("translation_count") or 0),
            "reverse_support_count": int(row.get("reverse_support_count") or 0),
        },
        "label": _label_template(),
        "labeling_notes": {
            "scale": "0.00 first-lesson German; 1.00 recondite / effectively unusable for ordinary learners.",
            "instruction": (
                "Fill expected_learner_difficulty only after deciding treatment. "
                "Use null for excluded/non-vocab rows unless they still need numeric calibration."
            ),
        },
    }


def _label_schema() -> dict[str, object]:
    return {
        "target_scale": (
            "expected_learner_difficulty is a reviewed continuous 0.00-1.00 "
            "English-speaker German-learning target. It is presentation priority, "
            "not pure native rarity."
        ),
        "recommended_numeric_rows": (
            "Rows with treatment vocab and confidence >= 0.5 should become numeric calibration/holdout labels."
        ),
        "fields": {
            "treatment": list(TREATMENTS),
            "expected_learner_difficulty": "float 0.00-1.00 or null",
            "expected_difficulty_band": "beginner|core|intermediate|advanced|tail|recondite|null",
            "confidence": "float 0.00-1.00 or null",
            "flags": list(LABEL_FLAGS),
            "rationale": "short reviewer note",
        },
    }


def _label_template() -> dict[str, object]:
    return {
        "treatment": None,
        "expected_learner_difficulty": None,
        "expected_difficulty_band": None,
        "confidence": None,
        "flags": [],
        "rationale": "",
    }


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    reason_counts: dict[str, int] = {}
    for row in rows:
        for reason in _as_sequence(row.get("selection_reasons")):
            key = str(reason)
            reason_counts[key] = reason_counts.get(key, 0) + 1
    holdout_count = sum(1 for row in rows if row.get("recommended_split") == "holdout")
    return {
        "row_count": len(rows),
        "calibration_count": len(rows) - holdout_count,
        "holdout_count": holdout_count,
        "selection_reason_counts": dict(sorted(reason_counts.items())),
    }


def _band_candidates(
    rows: Sequence[Mapping[str, object]],
    *,
    low: float,
    high: float,
) -> list[Mapping[str, object]]:
    center = (low + high) / 2.0
    last_band = high >= 1.0
    candidates = [
        row
        for row in rows
        if _safe_float(row.get("frequency_blend")) >= low
        and (
            _safe_float(row.get("frequency_blend")) < high
            or (last_band and _safe_float(row.get("frequency_blend")) <= high)
        )
    ]
    return sorted(
        candidates,
        key=lambda row: (abs(_safe_float(row.get("frequency_blend")) - center), _rank(row)),
    )


def _boundary_rows(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    boundaries = (0.20, 0.40, 0.60, 0.80)
    return sorted(
        rows,
        key=lambda row: (
            min(abs(_safe_float(row.get("frequency_blend")) - boundary) for boundary in boundaries),
            _rank(row),
        ),
    )


def _evenly_spaced_by_score(
    rows: Sequence[Mapping[str, object]],
    *,
    count: int,
) -> list[Mapping[str, object]]:
    ordered = sorted(rows, key=lambda row: (_safe_float(row.get("frequency_blend")), _rank(row)))
    if count <= 0 or not ordered:
        return []
    if count >= len(ordered):
        return ordered
    return [ordered[round(index * (len(ordered) - 1) / (count - 1))] for index in range(count)]


def _exclude_selected(
    rows: Sequence[Mapping[str, object]],
    selected: Mapping[str, Mapping[str, object]],
) -> list[Mapping[str, object]]:
    return [row for row in rows if str(row.get("lemma") or "").strip() not in selected]


def _bands() -> tuple[tuple[float, float], ...]:
    return tuple((index / 10.0, (index + 1) / 10.0) for index in range(10))


def _is_content_vocab(row: Mapping[str, object]) -> bool:
    return str(row.get("pos_bucket") or "").strip().lower() in CONTENT_BUCKETS


def _rank(row: Mapping[str, object]) -> float:
    return _safe_float(row.get("core_rank"))


def _safe_float(value: object) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _round(value: object, digits: int = 6) -> float | None:
    try:
        if value is None or value == "":
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _fmt_float(value: object) -> str:
    numeric = _round(value, digits=3)
    return "" if numeric is None else f"{numeric:.3f}"


def _fmt_rank(value: object) -> str:
    numeric = _round(value, digits=0)
    return "" if numeric is None else f"{int(numeric)}"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
