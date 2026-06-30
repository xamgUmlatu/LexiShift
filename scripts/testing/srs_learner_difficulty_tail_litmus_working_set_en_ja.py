#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


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
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    _view_with_target_curve_override as _source_arbitration_view_with_target_curve_override,
    family_parts,
    generate_candidates,
    normalized_scores_for_candidate,
)


PAIR = "en-ja"
DEFAULT_SOURCE_ARBITRATION_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_source_arbitration_ordinary_cap_corrected_data_refine_warp_p60_g155_en_ja_latest.json"
)
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_ja.json"
)
DEFAULT_VALIDATION_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_stitch_validation_labels_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_litmus_working_set_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_tail_litmus_working_set_en_ja_latest.md"
)

WORKING_SET_ROWS = (
    ("no_cap_regression", "饗する", "きょうする"),
    ("no_cap_regression", "饐える", "すえる"),
    ("no_cap_regression", "齲蝕", "うしょく"),
    ("no_cap_regression", "翻って", "ひるがえって"),
    ("no_cap_regression", "歳神", "としがみ"),
    ("no_cap_regression", "龍舟", "りゅうしゅう"),
    ("no_cap_regression", "殯", "あがり"),
    ("no_cap_regression", "云為", "うんい"),
    ("no_cap_regression", "井蛙", "せいあ"),
    ("no_cap_improvement", "セル画", "せるが"),
    ("no_cap_improvement", "歯齦", "しぎん"),
    ("no_cap_improvement", "完黙", "かんもく"),
    ("no_cap_improvement", "ゲバ棒", "げばぼう"),
    ("no_cap_improvement", "鬚鯨", "ひげくじら"),
    ("no_cap_improvement", "邏卒", "らそつ"),
    ("no_cap_improvement", "仄めく", "ほのめく"),
    ("no_cap_improvement", "サビ残", "さびざん"),
    ("gairaigo_shifted_easier", "デバッグ", "でばっぐ"),
    ("gairaigo_shifted_easier", "ジェラート", "じぇらーと"),
    ("gairaigo_shifted_easier", "キュイジーヌ", "きゅいじーぬ"),
    ("gairaigo_shifted_easier", "ワンピ", "わんぴ"),
)

RARITY_SIGNAL_NAMES = (
    "frequency",
    "tubelex_count_difficulty",
    "tubelex_channels_difficulty",
    "tubelex_dispersion_difficulty",
    "tubelex_rank_difficulty",
)
MARKED_SIGNAL_NAMES = (
    "jmdict_reading_form_marked_risk",
    "jmdict_kanji_form_marked_risk",
    "jmdict_marked_usage_risk",
    "jmdict_register_marked_risk",
    "jmdict_search_only_form_risk",
    "jmdict_kana_preferred_risk",
    "jmdict_pair_marked_form_not_safe_risk",
    "rare_non_standard_reading_risk",
    "non_standard_reading_risk",
    "rare_wago_risk",
)
DOMAIN_SIGNAL_NAMES = (
    "jmdict_field_marked_risk",
    "jmdict_register_domain_risk",
    "jmdict_sense_info_risk",
    "bccwj_domain_profile_risk",
    "tubelex_written_only_risk",
    "common_register_domain_risk",
    "common_kango_register_domain_risk",
)
LEAK_SIGNAL_NAMES = (
    "jmdict_pair_priority_leak_risk",
    "jmdict_pair_surface_only_multi_reading_risk",
    "common_jmdict_ambiguity_risk",
)
LOAN_SIGNAL_NAMES = (
    "wtype_gairaigo_risk",
    "jmdict_loanword_source_risk",
    "gairaigo_non_english_source_risk",
    "jmdict_non_english_loan_source_flag",
)
ENGLISH_SIGNAL_NAMES = (
    "jmdict_english_source_frequency_ease",
    "gairaigo_english_source_ease",
    "gairaigo_english_gloss_frequency_ease",
)
PEDAGOGICAL_SIGNAL_NAMES = (
    "jlpt_vocab_effective_exact_known",
    "jlpt_vocab_exact_known",
    "lesson_vocab_known",
    "pedagogical_source_known",
)
EXACT_PEDAGOGICAL_SIGNAL_NAMES = (
    "jlpt_vocab_effective_exact_known",
    "jlpt_vocab_exact_known",
    "lesson_vocab_known",
)
BURDEN_SIGNAL_NAMES = (
    "max_written_form_burden",
    "max_kanji_burden",
    "kanji_burden",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the en-ja upper-tail cap/no-cap litmus working set with every "
            "current component-matrix signal."
        )
    )
    parser.add_argument(
        "--component-matrix",
        type=Path,
        default=None,
        help=(
            "Optional override. Defaults to the component_matrix recorded in "
            "--source-arbitration-json so row scores and signals stay aligned."
        ),
    )
    parser.add_argument(
        "--source-arbitration-json",
        type=Path,
        default=DEFAULT_SOURCE_ARBITRATION_JSON,
    )
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=(
            _resolve_repo_path(args.component_matrix) if args.component_matrix else None
        ),
        source_arbitration_json_path=_resolve_repo_path(args.source_arbitration_json),
        calibration_json_path=_resolve_repo_path(args.calibration_json),
        holdout_json_path=_resolve_repo_path(args.holdout_json),
        validation_json_path=_resolve_repo_path(args.validation_json),
    )
    json_out = _resolve_repo_path(args.json_out)
    markdown_out = _resolve_repo_path(args.markdown_out)
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
    component_matrix_path: Path | None,
    source_arbitration_json_path: Path,
    calibration_json_path: Path,
    holdout_json_path: Path,
    validation_json_path: Path,
) -> dict[str, object]:
    source_payload = json.loads(source_arbitration_json_path.read_text(encoding="utf-8"))
    resolved_component_matrix_path = component_matrix_path or _resolve_repo_path(
        Path(str(_mapping(source_payload.get("inputs")).get("component_matrix")))
    )
    component = np.load(resolved_component_matrix_path)
    view = _source_arbitration_view_with_target_curve_override(
        ComponentView.from_npz(component),
        target_curve_override="warp_p60_g155",
    )
    parts = family_parts(view)
    candidates = list(generate_candidates(candidate_family="ordinary_cap_corrected_data_refine"))
    current_candidate = _matched_candidate(
        candidates,
        {
            "ordinary_cap": 0.58,
            "ordinary_cap_mode": "hard",
            "ordinary_cap_strength": 1.0,
            "ordinary_gate_mode": "mean",
            "ordinary_gate_curve": "linear",
            "ordinary_exception_mode": "current",
            "ordinary_exception_curve": "linear",
        },
    )
    no_cap_candidate = _matched_candidate(
        candidates,
        {
            "ordinary_cap": 0.0,
            "ordinary_cap_mode": "none",
            "ordinary_cap_strength": 0.0,
            "ordinary_gate_mode": "mean",
            "ordinary_gate_curve": "linear",
            "ordinary_exception_mode": "current",
            "ordinary_exception_curve": "linear",
        },
    )
    best_candidate_id = str(source_payload["summary"]["best_holdout_balanced"]["candidate_id"])
    best_candidate = {candidate.candidate_id: candidate for candidate in candidates}[
        best_candidate_id
    ]
    score_arrays = {
        "current_hard_cap": np.asarray(
            normalized_scores_for_candidate(current_candidate, view, parts=parts),
            dtype=np.float32,
        ),
        "no_cap": np.asarray(
            normalized_scores_for_candidate(no_cap_candidate, view, parts=parts),
            dtype=np.float32,
        ),
        "best_soft_cap": np.asarray(
            normalized_scores_for_candidate(best_candidate, view, parts=parts),
            dtype=np.float32,
        ),
    }
    labels = _labels_by_row(
        calibration_json_path=calibration_json_path,
        holdout_json_path=holdout_json_path,
        validation_json_path=validation_json_path,
    )
    row_payloads = [
        _row_payload(
            group=group,
            lemma=lemma,
            reading=reading,
            view=view,
            score_arrays=score_arrays,
            labels=labels,
        )
        for group, lemma, reading in WORKING_SET_ROWS
    ]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "method": {
            "purpose": (
                "Fixed qualitative working set for upper-tail cap/no-cap model "
                "shape discussion. JSON rows include every component-matrix signal "
                "so proposed rules can be checked before another broad sweep."
            ),
            "target_curve_override": "warp_p60_g155",
            "naive_litmus": (
                "First-pass diagnostic only: tail probability rises with rarity, "
                "marked/register/domain signals, same-surface priority leak, and "
                "written burden; it falls with exact pedagogical evidence, safe "
                "pair commonness, and English gairaigo ease."
            ),
        },
        "inputs": {
            "component_matrix": _repo_or_home_path(resolved_component_matrix_path),
            "source_arbitration_json": _repo_or_home_path(source_arbitration_json_path),
            "calibration_json": _repo_or_home_path(calibration_json_path),
            "holdout_json": _repo_or_home_path(holdout_json_path),
            "validation_json": _repo_or_home_path(validation_json_path),
            "component_count": int(len(view.frequency)),
            "signal_count": int(len(view.names)),
        },
        "candidate_ids": {
            "current_hard_cap": current_candidate.candidate_id,
            "no_cap": no_cap_candidate.candidate_id,
            "best_soft_cap": best_candidate.candidate_id,
        },
        "working_set": row_payloads,
        "pattern_summary": _pattern_summary(row_payloads),
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": resolved_component_matrix_path,
                "source_arbitration_json": source_arbitration_json_path,
                "calibration_json": calibration_json_path,
                "holdout_json": holdout_json_path,
                "validation_json": validation_json_path,
            },
            code_paths={
                **_srs_difficulty_code_paths(),
                "tail_litmus_working_set": Path(__file__),
                "source_arbitration": (
                    SCRIPT_DIR / "srs_learner_difficulty_source_arbitration_en_ja.py"
                ),
                "piecewise_search": (
                    SCRIPT_DIR / "srs_learner_difficulty_piecewise_search_en_ja.py"
                ),
            },
        ),
    }


def _row_payload(
    *,
    group: str,
    lemma: str,
    reading: str,
    view: ComponentView,
    score_arrays: Mapping[str, object],
    labels: Mapping[tuple[str, str], Mapping[str, object]],
) -> dict[str, object]:
    row_index = _row_index(view, lemma=lemma, reading=reading)
    if row_index is None:
        return {
            "group": group,
            "lemma": lemma,
            "reading": reading,
            "found": False,
        }
    key = (lemma, reading)
    signal_values = _all_signals(view, row_index)
    score_summary = {
        name: _rounded(float(np.asarray(scores, dtype=np.float32)[row_index]))
        for name, scores in score_arrays.items()
    }
    litmus = _naive_tail_litmus(view, row_index)
    expected = labels.get(key, {})
    return {
        "group": group,
        "lemma": lemma,
        "reading": reading,
        "found": True,
        "row_index": int(row_index),
        "identity_key": str(view.identities[row_index]),
        "candidate_state": str(view.candidate_states[row_index]),
        "core_rank": _finite_or_none(float(view.core_ranks[row_index])),
        "expected_label": dict(expected),
        "scores": score_summary,
        "score_deltas": {
            "no_cap_minus_current": _rounded(
                float(score_summary["no_cap"]) - float(score_summary["current_hard_cap"])
            ),
            "best_soft_cap_minus_current": _rounded(
                float(score_summary["best_soft_cap"]) - float(score_summary["current_hard_cap"])
            ),
        },
        "key_signal_summary": litmus["key_signal_summary"],
        "naive_tail_litmus": litmus["naive_tail_litmus"],
        "all_component_signals": signal_values,
    }


def _naive_tail_litmus(view: ComponentView, row_index: int) -> dict[str, object]:
    rarity = _mean_signal(view, row_index, RARITY_SIGNAL_NAMES)
    marked = _max_signal(view, row_index, MARKED_SIGNAL_NAMES)
    domain = _max_signal(view, row_index, DOMAIN_SIGNAL_NAMES)
    leak = _max_signal(view, row_index, LEAK_SIGNAL_NAMES)
    burden = _max_signal(view, row_index, BURDEN_SIGNAL_NAMES)
    pedagogical = _max_signal(view, row_index, PEDAGOGICAL_SIGNAL_NAMES)
    exact_pedagogical = _max_signal(view, row_index, EXACT_PEDAGOGICAL_SIGNAL_NAMES)
    safe_pair_commonness = _value(view, row_index, "jmdict_pair_safe_commonness", fill=0.0)
    safe_pair_priority = _value(view, row_index, "jmdict_pair_safe_priority", fill=1.0)
    direct_priority = _value(view, row_index, "jmdict_direct_priority", fill=1.0)
    gairaigo = _max_signal(view, row_index, LOAN_SIGNAL_NAMES)
    english_ease = _max_signal(view, row_index, ENGLISH_SIGNAL_NAMES)
    hard_evidence = max(marked, domain, leak, _clamp01((burden - 0.72) / 0.28))
    rarity_pressure = _clamp01((rarity - 0.82) / 0.18)
    normalizer = max(
        exact_pedagogical,
        safe_pair_commonness,
        0.65 * english_ease if gairaigo > 0.2 else 0.0,
    )
    probability = _clamp01(0.55 * rarity_pressure + 0.45 * hard_evidence - 0.65 * normalizer)
    if probability >= 0.65:
        verdict = "tail_yes"
    elif probability >= 0.35:
        verdict = "tail_maybe"
    else:
        verdict = "tail_no_or_mid"
    return {
        "key_signal_summary": {
            "rarity_mean": _rounded(rarity),
            "marked_or_form_risk": _rounded(marked),
            "domain_or_register_risk": _rounded(domain),
            "same_surface_or_priority_leak_risk": _rounded(leak),
            "written_or_kanji_burden": _rounded(burden),
            "pedagogical_known": _rounded(pedagogical),
            "exact_pedagogical_known": _rounded(exact_pedagogical),
            "safe_pair_commonness": _rounded(safe_pair_commonness),
            "safe_pair_priority": _rounded(safe_pair_priority),
            "direct_priority": _rounded(direct_priority),
            "gairaigo_or_loan_risk": _rounded(gairaigo),
            "english_gairaigo_ease": _rounded(english_ease),
        },
        "naive_tail_litmus": {
            "rarity_pressure": _rounded(rarity_pressure),
            "hard_evidence": _rounded(hard_evidence),
            "normalizer": _rounded(normalizer),
            "probability": _rounded(probability),
            "verdict": verdict,
        },
    }


def _all_signals(view: ComponentView, row_index: int) -> dict[str, object]:
    values = {}
    matrix = np.asarray(view.values)
    present = np.asarray(view.present)
    for signal_index, name in enumerate(view.names):
        is_present = bool(present[row_index, signal_index])
        value = float(matrix[row_index, signal_index]) if is_present else math.nan
        values[str(name)] = {
            "present": is_present,
            "value": _finite_or_none(value),
        }
    return values


def _pattern_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    found_rows = [row for row in rows if row.get("found")]
    by_group: dict[str, dict[str, int]] = {}
    verdict_counts: dict[str, int] = {}
    for row in found_rows:
        group = str(row.get("group") or "")
        verdict = str(_mapping(row.get("naive_tail_litmus")).get("verdict") or "unknown")
        by_group.setdefault(group, {})
        by_group[group][verdict] = by_group[group].get(verdict, 0) + 1
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
    return {
        "row_count": len(rows),
        "found_count": len(found_rows),
        "verdict_counts": verdict_counts,
        "verdict_counts_by_group": by_group,
        "first_pass_failure": (
            "The naive eligibility rule over-accepts tail placement: several "
            "reviewed no-cap regressions have high rarity plus burden/marked "
            "signals and therefore receive tail_yes even when expected labels are "
            "only 0.60-0.85. The next rule must distinguish rare-normal, "
            "rare-domain, marked-reading, and true extreme-tail destinations."
        ),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    rows = [_mapping(row) for row in _rows(report.get("working_set"))]
    lines = [
        "# en-ja Tail Litmus Working Set",
        "",
        f"- Generated: `{_escape(str(report.get('generated_at')))}`",
        f"- Component signals per row: `{_escape(str(_mapping(report.get('inputs')).get('signal_count')))}`",
        "- JSON contains every component signal under `all_component_signals`; this Markdown is a compact review surface.",
        "",
        "## Why This Exists",
        "",
        (
            "This working set freezes the cap/no-cap rows we are using to reason "
            "about upper-tail eligibility before doing another broad sweep."
        ),
        "",
        "The first-pass litmus is intentionally diagnostic, not a promoted model. "
        "It fails when rarity plus burden/marked evidence says `tail_yes` for "
        "rows whose reviewed labels suggest a lower advanced band.",
        "",
        "## Compact Rows",
        "",
        "| Group | Row | Expected | Current | No cap | Best soft | Rarity | Marked | Domain | Leak | Burden | English/Gairaigo | Litmus | Verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        if not row.get("found"):
            lines.append(
                f"| {_escape(str(row.get('group')))} | "
                f"`{_escape(str(row.get('lemma')))}/{_escape(str(row.get('reading')))}` | "
                "missing |  |  |  |  |  |  |  |  |  |  |  |"
            )
            continue
        expected = _mapping(row.get("expected_label")).get("expected_learner_difficulty")
        scores = _mapping(row.get("scores"))
        key = _mapping(row.get("key_signal_summary"))
        litmus = _mapping(row.get("naive_tail_litmus"))
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape(str(row.get("group"))),
                    f"`{_escape(str(row.get('lemma')))}/{_escape(str(row.get('reading')))}`",
                    _format_float(expected),
                    _format_float(scores.get("current_hard_cap")),
                    _format_float(scores.get("no_cap")),
                    _format_float(scores.get("best_soft_cap")),
                    _format_float(key.get("rarity_mean")),
                    _format_float(key.get("marked_or_form_risk")),
                    _format_float(key.get("domain_or_register_risk")),
                    _format_float(key.get("same_surface_or_priority_leak_risk")),
                    _format_float(key.get("written_or_kanji_burden")),
                    (
                        f"{_format_float(key.get('english_gairaigo_ease'))}/"
                        f"{_format_float(key.get('gairaigo_or_loan_risk'))}"
                    ),
                    _format_float(litmus.get("probability")),
                    _escape(str(litmus.get("verdict"))),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Immediate Lesson",
            "",
            str(_mapping(report.get("pattern_summary")).get("first_pass_failure")),
            "",
            "The weakness is specific: rarity, marked-form risk, and written burden "
            "are good evidence for advanced difficulty, but they are not enough to "
            "decide that a word belongs near `1.00`. The next rule should produce "
            "graded tail destinations rather than binary tail admission.",
            "",
        ]
    )
    return "\n".join(lines)


def _matched_candidate(candidates: Sequence[object], expected: Mapping[str, object]) -> object:
    for candidate in candidates:
        if all(getattr(candidate, key) == value for key, value in expected.items()):
            return candidate
    raise ValueError(f"Could not find candidate matching {expected!r}")


def _labels_by_row(
    *,
    calibration_json_path: Path,
    holdout_json_path: Path,
    validation_json_path: Path,
) -> dict[tuple[str, str], dict[str, object]]:
    labels: dict[tuple[str, str], dict[str, object]] = {}
    for dataset, path in (
        ("calibration", calibration_json_path),
        ("holdout", holdout_json_path),
        ("stitch_validation", validation_json_path),
    ):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in _label_rows(payload):
            lemma = str(row.get("lemma") or row.get("surface") or "")
            reading = str(row.get("expected_reading") or row.get("reading") or "")
            expected = row.get("expected_learner_difficulty")
            if expected is None:
                expected = row.get("expected_score") or row.get("expected")
            if not lemma or not reading or expected is None:
                continue
            labels[(lemma, reading)] = {
                "dataset": dataset,
                "expected_learner_difficulty": _rounded(float(expected)),
                "expected_difficulty_band": row.get("expected_difficulty_band"),
                "expected_candidate_state": row.get("expected_candidate_state"),
                "expected_problem_class": row.get("expected_problem_class"),
                "rationale": row.get("rationale") or "",
            }
    return labels


def _label_rows(payload: object) -> list[Mapping[str, object]]:
    if isinstance(payload, list):
        return [_mapping(row) for row in payload]
    data = _mapping(payload)
    for key in ("labels", "rows", "items"):
        rows = data.get(key)
        if isinstance(rows, list):
            return [_mapping(row) for row in rows]
    return []


def _row_index(view: ComponentView, *, lemma: str, reading: str) -> int | None:
    lemmas = np.asarray(view.lemmas).astype(str)
    readings = np.asarray(view.readings).astype(str)
    matches = np.where((lemmas == lemma) & (readings == reading))[0]
    if len(matches) == 0:
        return None
    return int(matches[0])


def _max_signal(view: ComponentView, row_index: int, names: Sequence[str]) -> float:
    return max(_value(view, row_index, name, fill=0.0) for name in names)


def _mean_signal(view: ComponentView, row_index: int, names: Sequence[str]) -> float:
    values = [_value(view, row_index, name, fill=math.nan, require_present=True) for name in names]
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else 0.0


def _value(
    view: ComponentView,
    row_index: int,
    name: str,
    *,
    fill: float,
    require_present: bool = False,
) -> float:
    signal_index = view.name_to_index.get(name)
    if signal_index is None:
        return fill
    if require_present and not bool(np.asarray(view.present)[row_index, signal_index]):
        return fill
    if not bool(np.asarray(view.present)[row_index, signal_index]):
        return fill
    value = float(np.asarray(view.values)[row_index, signal_index])
    return value if math.isfinite(value) else fill


def _resolve_repo_path(path: Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _finite_or_none(value: float) -> float | None:
    return _rounded(value) if math.isfinite(value) else None


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def _format_float(value: object) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
