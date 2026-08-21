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

from srs_learner_difficulty_formula_probe_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_PROBE_JSON,
    build_report as build_formula_probe_report,
)


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_TARGET_COUNT = 150
DEFAULT_BAND_SAMPLE_COUNT = 8
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_calibration_review_pack_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_calibration_review_pack_en_es_latest.md"
)
DEFAULT_BALANCED_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_calibration_review_pack_en_es_balanced_latest.json"
)
DEFAULT_BALANCED_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_calibration_review_pack_en_es_balanced_latest.md"
)
BASE_VARIANT = "spalex_blend_frequency"
REVIEW_VARIANTS = (
    BASE_VARIANT,
    "tail_guard_medium",
    "transfer_all_light",
    "cognate_rescue_light",
)
LABEL_FLAGS = (
    "grammar_or_function_word",
    "bad_standalone_srs_item",
    "cognate_easy_for_english_speaker",
    "marked_rare_or_regional",
    "domain_or_register_specific",
    "foreign_or_borrowed_form",
    "proper_name_or_entity",
    "needs_display_or_rule_restriction",
)
TREATMENTS = ("vocab", "restrict_admission", "display_only", "exclude", "unsure")
CONTENT_BUCKETS = frozenset(("noun", "verb", "adjective", "adverb"))
SELECTION_PROFILES = ("diagnostic", "balanced")


@dataclass(frozen=True)
class SelectionSpec:
    spec_id: str
    label: str
    quota: int
    selector: Callable[[Sequence[Mapping[str, object]]], list[Mapping[str, object]]]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic en-es learner-difficulty calibration review pack. "
            "The output is for human labeling; it does not add labels or change production scoring."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT)
    parser.add_argument("--band-sample-count", type=int, default=DEFAULT_BAND_SAMPLE_COUNT)
    parser.add_argument(
        "--selection-profile",
        choices=SELECTION_PROFILES,
        default="diagnostic",
        help=(
            "diagnostic keeps the first stress-test pack; balanced adds more content-word "
            "beginner/core rows and splits the tail into more label-worthy families."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--force-rebuild-probe",
        action="store_true",
        help="Ignore any probe JSON rows and rebuild the formula probe in memory.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    formula_report = load_or_build_formula_report(
        formula_probe_json=Path(args.formula_probe_json).expanduser(),
        top_n=max(1, int(args.top_n)),
        force_rebuild=bool(args.force_rebuild_probe),
    )
    report = build_report(
        formula_report=formula_report,
        target_count=max(1, int(args.target_count)),
        band_sample_count=max(1, int(args.band_sample_count)),
        selection_profile=str(args.selection_profile),
    )
    json_out_path = Path(args.json_out)
    markdown_out_path = Path(args.markdown_out)
    if args.selection_profile == "balanced" and json_out_path == DEFAULT_JSON_OUT:
        json_out_path = DEFAULT_BALANCED_JSON_OUT
    if args.selection_profile == "balanced" and markdown_out_path == DEFAULT_MARKDOWN_OUT:
        markdown_out_path = DEFAULT_BALANCED_MARKDOWN_OUT
    json_out = json_out_path.expanduser().resolve(strict=False)
    markdown_out = markdown_out_path.expanduser().resolve(strict=False)
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


def load_or_build_formula_report(
    *,
    formula_probe_json: Path,
    top_n: int,
    force_rebuild: bool = False,
) -> dict[str, object]:
    if not force_rebuild and formula_probe_json.is_file():
        payload = json.loads(formula_probe_json.read_text(encoding="utf-8"))
        if payload.get("rows"):
            return payload
    return build_formula_probe_report(
        top_n=top_n,
        sample_limit=8,
        include_rows=True,
    )


def build_report(
    *,
    formula_report: Mapping[str, object],
    target_count: int = DEFAULT_TARGET_COUNT,
    band_sample_count: int = DEFAULT_BAND_SAMPLE_COUNT,
    selection_profile: str = "diagnostic",
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")
    selection_profile = (
        selection_profile if selection_profile in SELECTION_PROFILES else "diagnostic"
    )
    selected = _select_review_rows(
        rows,
        target_count=target_count,
        band_sample_count=band_sample_count,
        selection_profile=selection_profile,
    )
    review_rows = [
        _review_row(index=index, row=row, total_count=len(selected))
        for index, row in enumerate(selected, start=1)
    ]
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": _decision_for_profile(selection_profile),
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "manual_labels_added": False,
        "production_ranking_changed": False,
        "method": {
            "purpose": (
                "Create a first reviewed en-es learner-difficulty target set so later "
                "formula sweeps can be graded numerically instead of selected by qualitative samples."
            ),
            "selection_profile": selection_profile,
            "selection_policy": _selection_policy_text(selection_profile),
            "split_policy": (
                "Rows are assigned before tuning: every third row is recommended holdout; "
                "the rest are recommended calibration. Do not move holdout rows after review."
            ),
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "target_count": int(target_count),
            "band_sample_count": int(band_sample_count),
            "selection_profile": selection_profile,
            "base_variant": BASE_VARIANT,
            "review_variants": list(REVIEW_VARIANTS),
        },
        "label_schema": _label_schema(),
        "summary": _summary(review_rows),
        "review_rows": review_rows,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    lines: list[str] = [
        "# en-es Learner Difficulty Calibration Review Pack",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Selection profile: `{method.get('selection_profile')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Manual labels added: `{report.get('manual_labels_added')}`",
        "",
        "## Label Format",
        "",
        "Use `expected_learner_difficulty` as the numeric target: `0.00` is first-lesson Spanish; `1.00` is recondite or effectively unusable vocabulary.",
        "",
        "Treatments:",
        "",
    ]
    for treatment in TREATMENTS:
        lines.append(f"- `{treatment}`")
    lines.extend(
        [
            "",
            "Common flags:",
            "",
        ]
    )
    for flag in LABEL_FLAGS:
        lines.append(f"- `{flag}`")
    summary = _as_mapping(report.get("summary"))
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
            "| # | Split | Lemma | POS | Base | Tail | Transfer | Rank | Reasons | Translations |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for raw in _as_sequence(report.get("review_rows")):
        row = _as_mapping(raw)
        scores = _as_mapping(row.get("scores"))
        lines.append(
            f"| {row.get('review_number')} | `{row.get('recommended_split')}` | "
            f"`{_escape(row.get('lemma'))}` | `{_escape(row.get('pos'))}` | "
            f"{_fmt_float(scores.get(BASE_VARIANT))} | "
            f"{_fmt_float(scores.get('tail_guard_medium'))} | "
            f"{_fmt_float(scores.get('transfer_all_light'))} | "
            f"{_fmt_rank(row.get('spalex_rank'))} | "
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
    selection_profile: str,
) -> list[Mapping[str, object]]:
    if selection_profile == "balanced":
        return _select_balanced_review_rows(
            rows,
            target_count=target_count,
            band_sample_count=band_sample_count,
        )
    return _select_diagnostic_review_rows(
        rows,
        target_count=target_count,
        band_sample_count=band_sample_count,
    )


def _select_diagnostic_review_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    target_count: int,
    band_sample_count: int,
) -> list[Mapping[str, object]]:
    selected: dict[str, dict[str, object]] = {}

    def add(reason: str, candidates: Sequence[Mapping[str, object]], quota: int) -> None:
        _add_selected(selected, reason, candidates, quota, target_count=target_count)

    for low, high in _bands():
        reason = f"base_band_{low:.1f}_{high:.1f}"
        add(
            reason,
            _band_candidates(rows, variant_id=BASE_VARIANT, low=low, high=high),
            band_sample_count,
        )

    specs = (
        SelectionSpec(
            "tail_guard_raise",
            "tail_guard_largest_raises",
            22,
            lambda source: _largest_delta(
                source,
                variant_id="tail_guard_medium",
                minimum_delta=0.025,
                descending=True,
            ),
        ),
        SelectionSpec(
            "cognate_lower",
            "cognate_largest_lowers",
            22,
            lambda source: _largest_delta(
                source,
                variant_id="cognate_rescue_light",
                maximum_delta=-0.015,
                descending=False,
            ),
        ),
        SelectionSpec(
            "pos_function_raise",
            "pos_function_largest_raises",
            18,
            lambda source: [
                row
                for row in _largest_delta(
                    source,
                    variant_id="transfer_all_light",
                    minimum_delta=0.04,
                    descending=True,
                )
                if _component(row, "pos_function_risk") > 0.5
            ],
        ),
        SelectionSpec(
            "unknown_pos_tail",
            "unknown_pos_tail_rows",
            18,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if _component(row, "pos_other_risk") > 0.5 and _score(row, BASE_VARIANT) >= 0.60
                ],
                key=lambda row: (_score(row, BASE_VARIANT), _rank(row)),
                reverse=True,
            ),
        ),
        SelectionSpec(
            "ordinary_high",
            "ordinary_looking_high_rows",
            14,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if str(row.get("pos_bucket") or "") in {"noun", "verb", "adjective", "adverb"}
                    and _score(row, BASE_VARIANT) >= 0.68
                    and _component(row, "dict_marked_usage_risk") <= 0.0
                    and _component(row, "pos_other_risk") <= 0.0
                ],
                key=lambda row: (_score(row, BASE_VARIANT), _rank(row)),
                reverse=True,
            ),
        ),
        SelectionSpec(
            "rare_low",
            "rare_or_marked_low_rows",
            12,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if _score(row, BASE_VARIANT) <= 0.45
                    and (
                        _component(row, "dict_marked_usage_risk") > 0.0
                        or _component(row, "pos_other_risk") > 0.5
                    )
                ],
                key=lambda row: (_score(row, BASE_VARIANT), -_rank(row)),
            ),
        ),
        SelectionSpec(
            "boundary",
            "near_decision_boundaries",
            24,
            lambda source: _boundary_rows(source, variant_id="tail_guard_medium"),
        ),
    )
    for spec in specs:
        add(spec.spec_id, spec.selector(rows), spec.quota)

    if len(selected) < target_count:
        add(
            "deterministic_fill",
            _evenly_spaced_by_score(rows, variant_id=BASE_VARIANT, count=target_count * 2),
            target_count - len(selected),
        )
    return list(selected.values())[:target_count]


def _select_balanced_review_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    target_count: int,
    band_sample_count: int,
) -> list[Mapping[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    content_rows = [row for row in rows if _is_content_vocab(row)]
    translated_content_rows = [row for row in content_rows if _as_sequence(row.get("translations"))]

    def add(reason: str, candidates: Sequence[Mapping[str, object]], quota: int) -> None:
        _add_selected(selected, reason, candidates, quota, target_count=target_count)

    add(
        "function_anchor",
        sorted(
            [
                row
                for row in rows
                if _component(row, "pos_function_risk") > 0.5 and _score(row, BASE_VARIANT) <= 0.35
            ],
            key=lambda row: _rank(row),
        ),
        12,
    )
    add(
        "core_content_low_rank",
        sorted(translated_content_rows or content_rows, key=lambda row: _rank(row)),
        24,
    )

    for low, high in _bands():
        reason = f"content_band_{low:.1f}_{high:.1f}"
        candidates = _band_candidates(
            translated_content_rows or content_rows,
            variant_id=BASE_VARIANT,
            low=low,
            high=high,
        )
        if not candidates:
            candidates = _band_candidates(
                content_rows,
                variant_id=BASE_VARIANT,
                low=low,
                high=high,
            )
        add(reason, candidates, max(3, min(band_sample_count, 6)))

    specs = (
        SelectionSpec(
            "cognate_lower_content",
            "content_cognate_largest_lowers",
            18,
            lambda source: [
                row
                for row in _largest_delta(
                    source,
                    variant_id="cognate_rescue_light",
                    maximum_delta=-0.015,
                    descending=False,
                )
                if _is_content_vocab(row)
            ],
        ),
        SelectionSpec(
            "tail_guard_raise_marked",
            "tail_guard_largest_marked_or_other_raises",
            18,
            lambda source: [
                row
                for row in _largest_delta(
                    source,
                    variant_id="tail_guard_medium",
                    minimum_delta=0.025,
                    descending=True,
                )
                if _component(row, "dict_marked_usage_risk") > 0.0
                or _component(row, "pos_other_risk") > 0.5
            ],
        ),
        SelectionSpec(
            "ordinary_content_high",
            "ordinary_looking_high_content_rows",
            14,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if _is_content_vocab(row)
                    and _score(row, BASE_VARIANT) >= 0.68
                    and _component(row, "dict_marked_usage_risk") <= 0.0
                ],
                key=lambda row: (_score(row, BASE_VARIANT), _rank(row)),
                reverse=True,
            ),
        ),
        SelectionSpec(
            "technical_or_long_tail_content",
            "technical_or_long_tail_content_rows",
            14,
            lambda source: sorted(
                [
                    row
                    for row in source
                    if _is_content_vocab(row)
                    and _score(row, BASE_VARIANT) >= 0.70
                    and (
                        _component(row, "char_length_difficulty") >= 0.22
                        or _component(row, "diacritic_burden_light") > 0.0
                        or _component(row, "cognate_rescue") > 0.0
                    )
                ],
                key=lambda row: (_score(row, BASE_VARIANT), -_rank(row)),
                reverse=True,
            ),
        ),
        SelectionSpec(
            "absolute_tail_anchor",
            "absolute_spalex_tail_rows",
            12,
            lambda source: sorted(source, key=lambda row: _rank(row), reverse=True),
        ),
        SelectionSpec(
            "content_boundary",
            "content_near_decision_boundaries",
            20,
            lambda source: _boundary_rows(content_rows, variant_id="tail_guard_medium"),
        ),
    )
    for spec in specs:
        add(spec.spec_id, spec.selector(rows), spec.quota)

    if len(selected) < target_count:
        add(
            "balanced_deterministic_fill",
            _evenly_spaced_by_score(
                content_rows or rows, variant_id=BASE_VARIANT, count=target_count * 2
            ),
            target_count - len(selected),
        )
    if len(selected) < target_count:
        add(
            "balanced_any_fill",
            _evenly_spaced_by_score(rows, variant_id=BASE_VARIANT, count=target_count * 2),
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
        lemma = str(raw.get("lemma") or "")
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
    total_count: int,
) -> dict[str, object]:
    components = _as_mapping(row.get("components"))
    scores = _as_mapping(row.get("variant_scores"))
    base_score = _score(row, BASE_VARIANT)
    compact_scores = {
        variant: _round(_safe_float(scores.get(variant))) for variant in REVIEW_VARIANTS
    }
    return {
        "review_id": f"en-es-diff-review-{index:04d}",
        "review_number": index,
        "recommended_split": "holdout" if index % 3 == 0 else "calibration",
        "lemma": row.get("lemma"),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "candidate_state": row.get("candidate_state"),
        "spalex_rank": _round(row.get("spalex_rank")),
        "translations": list(_as_sequence(row.get("translations")))[:8],
        "selection_reasons": list(_as_sequence(row.get("selection_reasons"))),
        "scores": compact_scores,
        "deltas_from_base": {
            variant: _round((_safe_float(scores.get(variant)) or 0.0) - base_score)
            for variant in REVIEW_VARIANTS
            if variant != BASE_VARIANT
        },
        "component_snapshot": {
            key: _round(components.get(key))
            for key in (
                "pos_function_risk",
                "pos_other_risk",
                "dict_marked_usage_risk",
                "gated_dict_marked_usage_risk",
                "dict_ambiguity",
                "tail_dict_ambiguity",
                "weak_form_risk",
                "cognate_rescue",
                "false_friend_caution",
            )
        },
        "label": _label_template(),
        "labeling_notes": {
            "scale": "0.00 first-lesson Spanish; 1.00 recondite / effectively unusable for ordinary learners.",
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
            "English-speaker Spanish-learning target. It is presentation priority, "
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
    variant_id: str,
    low: float,
    high: float,
) -> list[Mapping[str, object]]:
    center = (low + high) / 2.0
    last_band = high >= 1.0
    candidates = [
        row
        for row in rows
        if _score(row, variant_id) >= low
        and (_score(row, variant_id) < high or (last_band and _score(row, variant_id) <= high))
    ]
    return sorted(
        candidates,
        key=lambda row: (abs(_score(row, variant_id) - center), _rank(row)),
    )


def _largest_delta(
    rows: Sequence[Mapping[str, object]],
    *,
    variant_id: str,
    minimum_delta: float | None = None,
    maximum_delta: float | None = None,
    descending: bool,
) -> list[Mapping[str, object]]:
    candidates = []
    for row in rows:
        delta = _score(row, variant_id) - _score(row, BASE_VARIANT)
        if minimum_delta is not None and delta < minimum_delta:
            continue
        if maximum_delta is not None and delta > maximum_delta:
            continue
        candidates.append(row)
    return sorted(
        candidates,
        key=lambda row: (_score(row, variant_id) - _score(row, BASE_VARIANT), -_rank(row)),
        reverse=descending,
    )


def _boundary_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    variant_id: str,
) -> list[Mapping[str, object]]:
    boundaries = (0.20, 0.40, 0.60, 0.80)
    candidates = sorted(
        rows,
        key=lambda row: (
            min(abs(_score(row, variant_id) - boundary) for boundary in boundaries),
            _rank(row),
        ),
    )
    return candidates


def _evenly_spaced_by_score(
    rows: Sequence[Mapping[str, object]],
    *,
    variant_id: str,
    count: int,
) -> list[Mapping[str, object]]:
    ordered = sorted(rows, key=lambda row: (_score(row, variant_id), _rank(row)))
    if count <= 0 or not ordered:
        return []
    if count >= len(ordered):
        return ordered
    return [ordered[round(index * (len(ordered) - 1) / (count - 1))] for index in range(count)]


def _bands() -> tuple[tuple[float, float], ...]:
    return tuple((index / 10.0, (index + 1) / 10.0) for index in range(10))


def _is_content_vocab(row: Mapping[str, object]) -> bool:
    pos_bucket = str(row.get("pos_bucket") or "").strip().lower()
    return (
        pos_bucket in CONTENT_BUCKETS
        and _component(row, "pos_other_risk") <= 0.0
        and _component(row, "pos_function_risk") <= 0.0
    )


def _decision_for_profile(selection_profile: str) -> str:
    if selection_profile == "balanced":
        return "en_es_learner_difficulty_balanced_calibration_review_pack_ready"
    return "en_es_learner_difficulty_calibration_review_pack_ready"


def _selection_policy_text(selection_profile: str) -> str:
    if selection_profile == "balanced":
        return (
            "Rows are selected from the en-es formula probe with a label-oriented "
            "balanced profile: limited grammar/function anchors, content-word "
            "beginner/core coverage, content samples across the full base scale, "
            "cognate lowers, marked/other tail raises, ordinary high-content rows, "
            "technical/long tail content rows, absolute SPALEX tail anchors, and "
            "content-word boundary rows."
        )
    return (
        "Rows are selected from the en-es formula probe with deliberate strata: "
        "full-band base samples, tail-guard raises, cognate lowers, POS/function "
        "raises, unknown-POS tail rows, ordinary high rows, rare-low rows, and "
        "near-boundary rows."
    )


def _score(row: Mapping[str, object], variant_id: str) -> float:
    return _safe_float(_as_mapping(row.get("variant_scores")).get(variant_id)) or 0.0


def _component(row: Mapping[str, object], component: str) -> float:
    return _safe_float(_as_mapping(row.get("components")).get(component)) or 0.0


def _rank(row: Mapping[str, object]) -> float:
    return _safe_float(row.get("spalex_rank")) or 0.0


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: object, digits: int = 6) -> float | None:
    numeric = _safe_float(value)
    return round(numeric, digits) if numeric is not None else None


def _fmt_float(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric:.3f}"


def _fmt_rank(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{int(round(numeric))}"


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
