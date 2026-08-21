#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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
from srs_learner_difficulty_formula_sweep_en_es import (  # noqa: E402
    DEFAULT_JSON_OUT as DEFAULT_FORMULA_SWEEP_JSON,
    _candidate_by_id,
    _score_formula,
    generate_candidates,
)


PAIR = "en-es"
DEFAULT_TOP_N = 45000
DEFAULT_TARGET_COUNT = 120
BASE_VARIANT_ID = "spalex_blend_frequency"
BASELINE_VARIANT_ID = "learner_source_zipf_medium"
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_es.json"
)
DEFAULT_HOLDOUT_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_holdout_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_assumption_review_pack_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_assumption_review_pack_en_es_latest.md"
)


@dataclass(frozen=True)
class AssumptionSpec:
    family_id: str
    label: str
    assumption: str
    why_unproven: str
    review_question: str
    quota: int
    selector: Callable[[Sequence[Mapping[str, object]]], list[Mapping[str, object]]]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an adversarial en-es learner-difficulty assumption review pack. "
            "This is a sidecar diagnostic: it chooses rows that stress unproven data, "
            "join, or formula assumptions without changing production ranking."
        )
    )
    parser.add_argument("--formula-probe-json", type=Path, default=DEFAULT_FORMULA_PROBE_JSON)
    parser.add_argument("--formula-sweep-json", type=Path, default=DEFAULT_FORMULA_SWEEP_JSON)
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--holdout-json", type=Path, default=DEFAULT_HOLDOUT_JSON)
    parser.add_argument("--candidate-id")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--target-count", type=int, default=DEFAULT_TARGET_COUNT)
    parser.add_argument("--force-rebuild-probe", action="store_true")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
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
        sweep_payload=_load_optional_json(Path(args.formula_sweep_json).expanduser()),
        calibration_payload=_load_optional_json(Path(args.calibration_json).expanduser()),
        holdout_payload=_load_optional_json(Path(args.holdout_json).expanduser()),
        candidate_id=args.candidate_id,
        target_count=max(1, int(args.target_count)),
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


def load_or_build_formula_report(
    *,
    formula_probe_json: Path,
    top_n: int,
    force_rebuild: bool = False,
) -> dict[str, object]:
    if not force_rebuild and formula_probe_json.is_file():
        payload = _load_json(formula_probe_json)
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
    sweep_payload: Mapping[str, object] | None = None,
    calibration_payload: Mapping[str, object] | None = None,
    holdout_payload: Mapping[str, object] | None = None,
    candidate_id: str | None = None,
    target_count: int = DEFAULT_TARGET_COUNT,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    formula_rows = [_as_mapping(row) for row in _as_sequence(formula_report.get("rows"))]
    if not formula_rows:
        raise ValueError("formula report must contain rows; rebuild with include_rows=True")

    selected_candidate_id = candidate_id or _selected_candidate_id(sweep_payload)
    candidate = _candidate_by_id(generate_candidates(), selected_candidate_id)
    if candidate is None:
        raise ValueError(f"unknown formula candidate: {selected_candidate_id}")

    labels_by_lemma = _labels_by_lemma(
        calibration_payload=calibration_payload or {},
        holdout_payload=holdout_payload or {},
    )
    assumption_specs = _assumption_specs()
    selected = _select_rows(
        formula_rows,
        assumption_specs=assumption_specs,
        target_count=target_count,
    )
    review_rows = [
        _review_row(
            index=index,
            row=row,
            assumption_specs_by_id={spec.family_id: spec for spec in assumption_specs},
            candidate=candidate,
            selected_candidate_id=selected_candidate_id,
            label=_as_mapping(labels_by_lemma.get(_lemma_key(row))),
        )
        for index, row in enumerate(selected, start=1)
    ]
    return {
        "schema_version": 1,
        "language_pair": PAIR,
        "decision": "en_es_learner_difficulty_assumption_review_pack_ready",
        "generated_at": generated_at,
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "manual_labels_added": False,
        "method": {
            "purpose": (
                "Stress-test unproven assumptions in the en-es learner-difficulty "
                "pipeline from source data and joins through formula effects and "
                "product-readiness expectations."
            ),
            "selection_policy": (
                "Rows are selected by assumption family, not by being known errors. "
                "A row can appear once with multiple assumption families attached."
            ),
            "base_variant_id": BASE_VARIANT_ID,
            "baseline_variant_id": BASELINE_VARIANT_ID,
            "candidate_id": selected_candidate_id,
        },
        "inputs": {
            "formula_probe_decision": formula_report.get("decision"),
            "formula_probe_generated_at": formula_report.get("generated_at"),
            "formula_probe_top_n": _as_mapping(formula_report.get("inputs")).get("top_n"),
            "formula_sweep_decision": _as_mapping(sweep_payload).get("decision"),
            "formula_sweep_generated_at": _as_mapping(sweep_payload).get("generated_at"),
            "calibration_count": len(_as_sequence(_as_mapping(calibration_payload).get("labels"))),
            "holdout_count": len(_as_sequence(_as_mapping(holdout_payload).get("labels"))),
            "target_count": int(target_count),
        },
        "assumption_families": [_assumption_family(spec) for spec in assumption_specs],
        "summary": _summary(review_rows),
        "review_rows": review_rows,
        "limitations": [
            "This pack is adversarial by design; it over-samples suspicious rows and should not be read as a random quality sample.",
            "Existing calibration/holdout labels are included when available, but unlabeled rows still require human judgment before becoming model evidence.",
            "The pack tests assumptions qualitatively; it does not prove that a candidate is production-ready by itself.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    method = _as_mapping(report.get("method"))
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Learner Difficulty Assumption Review Pack",
        "",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        f"- Candidate: `{method.get('candidate_id')}`",
        f"- Rows: `{summary.get('row_count')}`",
        f"- Labeled rows already covered: `{summary.get('known_label_count')}`",
        "",
        "## Assumption Families",
        "",
        "| Family | Rows | Assumption | Review question |",
        "| --- | ---: | --- | --- |",
    ]
    family_counts = _as_mapping(summary.get("assumption_family_counts"))
    for raw in _as_sequence(report.get("assumption_families")):
        family = _as_mapping(raw)
        family_id = str(family.get("family_id") or "")
        lines.append(
            f"| `{_escape(family_id)}` | {family_counts.get(family_id, 0)} | "
            f"{_escape(family.get('assumption'))} | {_escape(family.get('review_question'))} |"
        )

    lines.extend(
        [
            "",
            "## Review Rows",
            "",
            "| # | Lemma | POS | Base | Candidate | Delta | Rank | Families | Label | Translations |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for raw in _as_sequence(report.get("review_rows")):
        row = _as_mapping(raw)
        scores = _as_mapping(row.get("scores"))
        label = _as_mapping(row.get("existing_label"))
        label_text = "-"
        if label:
            label_text = (
                f"{_fmt(label.get('expected_learner_difficulty'))} `{_escape(label.get('split'))}`"
            )
        lines.append(
            f"| {row.get('review_number')} | `{_escape(row.get('lemma'))}` | "
            f"`{_escape(row.get('pos'))}` | {_fmt(scores.get('base'))} | "
            f"{_fmt(scores.get('candidate'))} | {_fmt(scores.get('candidate_delta_vs_base'))} | "
            f"{_fmt_rank(row.get('spalex_rank'))} | "
            f"{', '.join(f'`{_escape(item)}`' for item in _as_sequence(row.get('assumption_family_ids')))} | "
            f"{label_text} | "
            f"{_escape('; '.join(str(item) for item in _as_sequence(row.get('translations'))[:3])) or '-'} |"
        )

    lines.extend(["", "## Family Details", ""])
    rows_by_family: dict[str, list[Mapping[str, object]]] = {}
    for raw in _as_sequence(report.get("review_rows")):
        row = _as_mapping(raw)
        for family_id in _as_sequence(row.get("assumption_family_ids")):
            rows_by_family.setdefault(str(family_id), []).append(row)
    for raw in _as_sequence(report.get("assumption_families")):
        family = _as_mapping(raw)
        family_id = str(family.get("family_id") or "")
        rows = rows_by_family.get(family_id, [])
        if not rows:
            continue
        lines.extend(
            [
                f"### `{family_id}`",
                "",
                f"Assumption: {_escape(family.get('assumption'))}",
                "",
                f"Why unproven: {_escape(family.get('why_unproven'))}",
                "",
                "| Lemma | Base | Candidate | Signals |",
                "| --- | ---: | ---: | --- |",
            ]
        )
        for row in rows[:12]:
            scores = _as_mapping(row.get("scores"))
            lines.append(
                f"| `{_escape(row.get('lemma'))}` | {_fmt(scores.get('base'))} | "
                f"{_fmt(scores.get('candidate'))} | {_escape(_signal_text(row))} |"
            )
        lines.append("")

    limitations = _as_sequence(report.get("limitations"))
    if limitations:
        lines.extend(["## Limitations", ""])
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def _assumption_specs() -> tuple[AssumptionSpec, ...]:
    return (
        AssumptionSpec(
            "frequency_backbone_tail",
            "Frequency backbone tail",
            "SPALEX/native frequency can order advanced normal vocabulary once learner sources thin out.",
            "Sparse tail ranks can reflect corpus coverage, genre, or tokenization rather than product difficulty.",
            "Does the frequency-only score place this advanced word roughly where an English-speaking learner should see it?",
            10,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _is_content(row)
                    and _base_score(row) >= 0.72
                    and _component(row, "dict_marked_usage_risk") <= 0.0
                    and _component(row, "lexcom_known") <= 0.0
                ],
                key=lambda row: (_base_score(row), -_rank(row)),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "wordfreq_spalex_disagreement",
            "wordfreq / SPALEX disagreement",
            "External wordfreq commonness can safely rescue rows SPALEX places too late.",
            "wordfreq mixes sources and may reflect names, inflected forms, or cross-domain usage differently from SPALEX.",
            "When wordfreq says this is common, does it actually deserve to move earlier?",
            10,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _component(row, "wordfreq_source_rescue") >= 0.025
                    or _component(row, "wordfreq_tail_rescue") >= 0.025
                ],
                key=lambda row: (
                    _component(row, "wordfreq_tail_rescue")
                    + _component(row, "wordfreq_source_rescue"),
                    _base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "lexcom_rescue",
            "LexCom direct learner rescue",
            "LexComSpaL2 token complexity can lower words that learners find easy.",
            "LexCom is token-level, domain-limited, and not specifically English-speaker en-es.",
            "Is the LexCom-easy row really easy enough to lower, or is the context/domain misleading?",
            10,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _component(row, "lexcom_known") > 0.0
                    and (
                        _component(row, "lexcom_learner_rescue") > 0.0
                        or _component(row, "lexcom_rescue_after030") > 0.0
                        or _component(row, "lexcom_rescue_after040") > 0.0
                    )
                ],
                key=lambda row: (
                    _component(row, "lexcom_learner_rescue")
                    + _component(row, "lexcom_rescue_after030")
                    + _component(row, "lexcom_rescue_after040"),
                    _base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "lexcom_caution",
            "LexCom direct learner caution",
            "LexComSpaL2 can also flag words that should resist being too easy.",
            "A hard LexCom item may be hard only in its sentence or annotation context.",
            "Does LexCom hardness correspond to presentation difficulty for this standalone vocab item?",
            8,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _component(row, "lexcom_known") > 0.0
                    and _component(row, "lexcom_learner_caution") > 0.0
                ],
                key=lambda row: (
                    _component(row, "lexcom_learner_caution"),
                    -_base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "learner_source_rescue",
            "Learner-source rescue",
            "Open learner/core lists can pull useful words earlier than native frequency alone.",
            "Small public lists can be incomplete, inconsistent, or source-biased.",
            "Is this source-backed word truly early enough to justify the rescue amount?",
            10,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _component(row, "learner_core_gap_zipf_confident") > 0.0
                    or _component(row, "learner_core_gap_blend_confident") > 0.0
                ],
                key=lambda row: (
                    _component(row, "learner_core_gap_zipf_confident")
                    + _component(row, "learner_core_gap_blend_confident"),
                    -_base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "learner_absence_easy_zone",
            "Learner-source absence in easy zone",
            "Absence from broad learner sources should not be treated as a blanket penalty.",
            "Some absent rows are genuinely too advanced for the easy zone; others are just missing from shallow lists.",
            "Should this learner-source-absent row be allowed to stay this early?",
            10,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _base_score(row) <= 0.50
                    and _component(row, "learner_broad_source_absent") > 0.5
                    and (
                        _component(row, "unsupported_ease_suspicion") > 0.0
                        or _component(row, "unsupported_ease_content") > 0.0
                    )
                ],
                key=lambda row: (
                    _component(row, "unsupported_ease_content")
                    + _component(row, "unsupported_ease_suspicion"),
                    -_base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "cognate_rescue",
            "Cognate rescue",
            "English-Spanish transparency should make some words easier for English speakers.",
            "Translation joins, false friends, abstractness, and morphology can make apparent cognates misleading.",
            "Is this actually easy for an English speaker, or is the cognate rescue over-pulling it?",
            12,
            lambda rows: _sorted(
                [row for row in rows if _component(row, "cognate_rescue") >= 0.20],
                key=lambda row: (
                    _component(row, "cognate_rescue"),
                    _component(row, "false_friend_caution"),
                    _base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "short_polysemy_sense_join",
            "Short/polysemous sense join",
            "A single lemma/POS row is specific enough even for short, highly polysemous words.",
            "Dictionary senses and translations can merge multiple learner experiences into one score.",
            "Does the row represent one teachable vocab item, or is it hiding multiple senses/difficulties?",
            10,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if len(str(row.get("lemma") or "")) <= 6
                    and _component(row, "common_dict_ambiguity") >= 0.40
                    and _base_score(row) <= 0.45
                ],
                key=lambda row: (
                    _component(row, "common_dict_ambiguity"),
                    -_base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "function_or_grammar_vocab",
            "Function/grammar vocab",
            "Highly frequent function words can live on the same scalar as normal vocabulary.",
            "They may be grammar prerequisites rather than ordinary SRS vocabulary items.",
            "Should this be taught as vocabulary at this score, or handled through grammar/rule policy?",
            8,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _component(row, "pos_function_risk") > 0.5 and _base_score(row) <= 0.40
                ],
                key=lambda row: (_rank(row), _base_score(row)),
            ),
        ),
        AssumptionSpec(
            "marked_low_or_mid",
            "Marked/register row in low-mid band",
            "Dictionary markedness should only raise difficulty when it reflects learner-facing rarity.",
            "Marked tags can be attached to one sense while the main word is ordinary.",
            "Is this low/mid placement acceptable despite marked dictionary evidence?",
            10,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _base_score(row) <= 0.65
                    and (
                        _component(row, "dict_marked_usage_risk") > 0.0
                        or _component(row, "gated_dict_marked_usage_risk") > 0.0
                        or _component(row, "dict_register_sensitive_score") > 0.0
                    )
                ],
                key=lambda row: (
                    _component(row, "gated_dict_marked_usage_risk")
                    + _component(row, "dict_register_sensitive_score"),
                    -_base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "regional_colloquial_policy",
            "Regional/colloquial policy",
            "Regional or colloquial common words should be ranked by usefulness, not automatically punished.",
            "Product policy, dialect coverage, and actual cross-region usefulness are not proven by the source tag alone.",
            "Should this be available as normal vocab, regional/topic-gated, or pushed later?",
            8,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _component(row, "regional_colloquial_gate") > 0.0
                    or _component(row, "dict_region_tag_count_score") > 0.0
                    or _component(row, "dict_register_colloquial_score") > 0.0
                ],
                key=lambda row: (
                    _component(row, "regional_colloquial_gate")
                    + _component(row, "dict_region_tag_count_score")
                    + _component(row, "dict_register_colloquial_score"),
                    _base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "domain_specificity",
            "Domain specificity",
            "Domain/topic dictionary evidence can identify words that are less broadly useful.",
            "A domain-tagged word can still be common/product-useful, and tags may describe only one sense.",
            "Does the domain tag justify the placement, or is this word useful enough to ignore it?",
            8,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _component(row, "dict_domain_topic_count_score") > 0.0
                    or _component(row, "tail_domain_specificity") > 0.0
                ],
                key=lambda row: (
                    _component(row, "tail_domain_specificity")
                    + _component(row, "dict_domain_topic_count_score"),
                    _base_score(row),
                ),
                reverse=True,
            ),
        ),
        AssumptionSpec(
            "form_complexity_and_multiword",
            "Form complexity / multiword",
            "Spanish form burden is weak but still sometimes relevant.",
            "Diacritics, length, punctuation, and multiword status may affect SRS suitability more than difficulty.",
            "Is this a normal vocab item at this score, or should form/display/admission policy handle it?",
            8,
            lambda rows: _sorted(
                [
                    row
                    for row in rows
                    if _component(row, "char_length_difficulty") >= 0.18
                    or _component(row, "diacritic_burden_light") > 0.0
                    or _component(row, "multiword_risk") > 0.0
                    or _component(row, "punctuation_or_digit_risk") > 0.0
                ],
                key=lambda row: (
                    _component(row, "multiword_risk")
                    + _component(row, "char_length_difficulty")
                    + _component(row, "diacritic_burden_light"),
                    _base_score(row),
                ),
                reverse=True,
            ),
        ),
    )


def _select_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    assumption_specs: Sequence[AssumptionSpec],
    target_count: int,
) -> list[Mapping[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    for spec in assumption_specs:
        for raw in spec.selector(rows)[: spec.quota]:
            if len(selected) >= target_count:
                break
            lemma = _lemma_key(raw)
            if not lemma:
                continue
            row = selected.setdefault(lemma, dict(raw))
            family_ids = list(_as_sequence(row.get("assumption_family_ids")))
            if spec.family_id not in family_ids:
                family_ids.append(spec.family_id)
            row["assumption_family_ids"] = family_ids
    if len(selected) < target_count:
        for raw in _fallback_rows(rows, target_count=target_count * 2):
            if len(selected) >= target_count:
                break
            lemma = _lemma_key(raw)
            if not lemma:
                continue
            row = selected.setdefault(lemma, dict(raw))
            family_ids = list(_as_sequence(row.get("assumption_family_ids")))
            if "fallback_band_anchor" not in family_ids:
                family_ids.append("fallback_band_anchor")
            row["assumption_family_ids"] = family_ids
    return list(selected.values())[:target_count]


def _review_row(
    *,
    index: int,
    row: Mapping[str, object],
    assumption_specs_by_id: Mapping[str, AssumptionSpec],
    candidate: object,
    selected_candidate_id: str,
    label: Mapping[str, object],
) -> dict[str, object]:
    components = _as_mapping(row.get("components"))
    base = _base_score(row)
    baseline = _score_variant(row, BASELINE_VARIANT_ID)
    candidate_score = _score_formula(candidate, row)
    family_ids = [str(item) for item in _as_sequence(row.get("assumption_family_ids"))]
    families = [
        _assumption_family(assumption_specs_by_id[family_id])
        for family_id in family_ids
        if family_id in assumption_specs_by_id
    ]
    existing_label = {}
    if label:
        existing_label = {
            "split": label.get("split"),
            "expected_learner_difficulty": label.get("expected_learner_difficulty"),
            "expected_candidate_state": label.get("expected_candidate_state"),
            "expected_problem_class": label.get("expected_problem_class"),
            "review_treatment": label.get("review_treatment"),
            "review_flags": list(_as_sequence(label.get("review_flags"))),
        }
    return {
        "review_number": index,
        "lemma": row.get("lemma"),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "candidate_state": row.get("candidate_state"),
        "spalex_rank": row.get("spalex_rank"),
        "translations": list(_as_sequence(row.get("translations")))[:8],
        "assumption_family_ids": family_ids,
        "assumption_families": families,
        "existing_label": existing_label,
        "scores": {
            "base_variant_id": BASE_VARIANT_ID,
            "base": _round_float(base),
            "baseline_variant_id": BASELINE_VARIANT_ID,
            "baseline": _round_float(baseline),
            "candidate_id": selected_candidate_id,
            "candidate": _round_float(candidate_score),
            "candidate_delta_vs_base": _round_float(candidate_score - base),
            "candidate_delta_vs_baseline": _round_float(candidate_score - baseline),
            "wordfreq_probe": _score_variant(row, "wordfreq_rescue_probe"),
            "lexcom_probe": _score_variant(row, "lexcom_complexity_probe"),
            "cognate_probe": _score_variant(row, "cognate_rescue_light"),
            "tail_guard_probe": _score_variant(row, "tail_guard_medium"),
        },
        "source_summary": {
            "learner_source_known": _component(row, "learner_source_known"),
            "learner_core_score": _component(row, "learner_core_score"),
            "learner_source_count": _component(row, "learner_source_count"),
            "broad_source_absent": _component(row, "learner_broad_source_absent"),
            "wordfreq_known": _component(row, "wordfreq_known"),
            "wordfreq_zipf": _component(row, "wordfreq_zipf"),
            "lexcom_known": _component(row, "lexcom_known"),
            "lexcom_complexity": _component(row, "lexcom_complexity"),
        },
        "dictionary_summary": _dictionary_summary(row),
        "signals": _interesting_signals(components),
        "label_stub": {
            "expected_learner_difficulty": None,
            "expected_candidate_state": None,
            "review_treatment": None,
            "review_flags": [],
            "rationale": "",
        },
    }


def _assumption_family(spec: AssumptionSpec) -> dict[str, object]:
    return {
        "family_id": spec.family_id,
        "label": spec.label,
        "assumption": spec.assumption,
        "why_unproven": spec.why_unproven,
        "review_question": spec.review_question,
    }


def _summary(review_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    family_counts = Counter(
        str(family_id)
        for row in review_rows
        for family_id in _as_sequence(row.get("assumption_family_ids"))
    )
    labeled = [row for row in review_rows if _as_mapping(row.get("existing_label"))]
    return {
        "row_count": len(review_rows),
        "known_label_count": len(labeled),
        "unlabeled_count": len(review_rows) - len(labeled),
        "assumption_family_counts": dict(sorted(family_counts.items())),
        "score_band_counts": _band_counts(review_rows),
        "top_candidate_lowers": _largest_changes(
            review_rows,
            score_key="candidate_delta_vs_base",
            reverse=False,
        ),
        "top_candidate_raises": _largest_changes(
            review_rows,
            score_key="candidate_delta_vs_base",
            reverse=True,
        ),
    }


def _labels_by_lemma(
    *,
    calibration_payload: Mapping[str, object],
    holdout_payload: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    labels: dict[str, Mapping[str, object]] = {}
    for split, payload in (("calibration", calibration_payload), ("holdout", holdout_payload)):
        for raw in _as_sequence(_as_mapping(payload).get("labels")):
            label = dict(_as_mapping(raw))
            lemma = str(label.get("lemma") or "").strip().lower()
            if not lemma:
                continue
            label["split"] = split
            labels[lemma] = label
    return labels


def _selected_candidate_id(sweep_payload: Mapping[str, object] | None) -> str:
    summary = _as_mapping(_as_mapping(sweep_payload).get("summary"))
    for key in (
        "best_stable_candidate",
        "best_holdout_guarded_candidate",
        "best_calibration_candidate",
    ):
        candidate_id = str(_as_mapping(summary.get(key)).get("candidate_id") or "")
        if candidate_id:
            return candidate_id
    return "spalex_blend__lsb_w090_c022__cog_l__no_wf__no_guard"


def _dictionary_summary(row: Mapping[str, object]) -> dict[str, object]:
    dictionary = _as_mapping(row.get("dictionary"))
    return {
        "entry_count": dictionary.get("entry_count"),
        "sense_count": dictionary.get("sense_count"),
        "translation_count": dictionary.get("translation_count"),
        "marked_terms": list(_as_sequence(dictionary.get("marked_terms")))[:8],
        "region_terms": list(_as_sequence(dictionary.get("region_terms")))[:8],
        "register_terms": list(_as_sequence(dictionary.get("register_terms")))[:8],
        "domain_terms": list(_as_sequence(dictionary.get("domain_terms")))[:8],
        "topics": list(_as_sequence(dictionary.get("topics")))[:8],
        "alt_of_count": dictionary.get("alt_of_count"),
        "form_of_count": dictionary.get("form_of_count"),
    }


def _interesting_signals(components: Mapping[str, object]) -> list[dict[str, object]]:
    keys = (
        "spalex_blend",
        "zipf_base",
        "rank_base",
        "learner_core_gap_zipf_confident",
        "learner_core_gap_blend_confident",
        "learner_core_gap_zipf_quality",
        "learner_core_gap_blend_quality",
        "learner_core_gap_zipf_strict",
        "learner_core_gap_blend_strict",
        "learner_source_reliability",
        "learner_independent_vocab_support",
        "learner_rescue_quality_gate",
        "learner_rescue_strict_gate",
        "learner_broad_source_absent",
        "unsupported_ease_content",
        "cognate_rescue",
        "false_friend_caution",
        "wordfreq_source_rescue",
        "wordfreq_tail_rescue",
        "lexcom_learner_rescue",
        "lexcom_rescue_after030",
        "lexcom_rescue_after040",
        "lexcom_learner_caution",
        "dict_marked_usage_risk",
        "gated_dict_marked_usage_risk",
        "common_dict_ambiguity",
        "tail_dict_ambiguity",
        "dict_domain_topic_count_score",
        "regional_colloquial_gate",
        "pos_function_risk",
        "pos_other_risk",
        "char_length_difficulty",
        "diacritic_burden_light",
        "multiword_risk",
    )
    result = []
    for key in keys:
        value = _safe_float(components.get(key)) or 0.0
        if value > 0.0 or key in {"spalex_blend", "zipf_base", "rank_base"}:
            result.append({"component": key, "value": _round_float(value)})
    return result


def _fallback_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    target_count: int,
) -> list[Mapping[str, object]]:
    scored = sorted(rows, key=_base_score)
    if not scored:
        return []
    if target_count <= 1:
        return [scored[0]]
    result = []
    for index in range(target_count):
        position = round(index * (len(scored) - 1) / (target_count - 1))
        result.append(scored[position])
    return result


def _largest_changes(
    rows: Sequence[Mapping[str, object]],
    *,
    score_key: str,
    reverse: bool,
    limit: int = 12,
) -> list[dict[str, object]]:
    ordered = sorted(
        rows,
        key=lambda row: _safe_float(_as_mapping(row.get("scores")).get(score_key)) or 0.0,
        reverse=reverse,
    )
    return [
        {
            "lemma": row.get("lemma"),
            score_key: _as_mapping(row.get("scores")).get(score_key),
            "base": _as_mapping(row.get("scores")).get("base"),
            "candidate": _as_mapping(row.get("scores")).get("candidate"),
            "families": list(_as_sequence(row.get("assumption_family_ids"))),
        }
        for row in ordered[:limit]
    ]


def _band_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        score = _safe_float(_as_mapping(row.get("scores")).get("candidate")) or 0.0
        low = min(9, int(score * 10)) / 10
        high = low + 0.1
        counts[f"{low:.1f}-{high:.1f}"] += 1
    return dict(sorted(counts.items()))


def _signal_text(row: Mapping[str, object]) -> str:
    signals = []
    for raw in _as_sequence(row.get("signals")):
        item = _as_mapping(raw)
        component = str(item.get("component") or "")
        if component in {"spalex_blend", "zipf_base", "rank_base"}:
            continue
        signals.append(f"{component}={_fmt(item.get('value'))}")
    return ", ".join(signals[:8]) or "-"


def _is_content(row: Mapping[str, object]) -> bool:
    return str(row.get("pos_bucket") or "") in {"noun", "verb", "adjective", "adverb"}


def _score_variant(row: Mapping[str, object], variant_id: str) -> float:
    value = _safe_float(_as_mapping(row.get("variant_scores")).get(variant_id))
    if value is not None:
        return _round_float(value)
    return _base_score(row)


def _base_score(row: Mapping[str, object]) -> float:
    value = _safe_float(_as_mapping(row.get("variant_scores")).get(BASE_VARIANT_ID))
    if value is not None:
        return _round_float(value)
    return _round_float(_component(row, "spalex_blend"))


def _component(row: Mapping[str, object], component: str) -> float:
    return _round_float(_safe_float(_as_mapping(row.get("components")).get(component)) or 0.0)


def _rank(row: Mapping[str, object]) -> float:
    return _safe_float(row.get("spalex_rank")) or 0.0


def _lemma_key(row: Mapping[str, object]) -> str:
    return str(row.get("lemma") or "").strip().lower()


def _sorted(
    rows: Sequence[Mapping[str, object]],
    *,
    key: Callable[[Mapping[str, object]], object],
    reverse: bool = False,
) -> list[Mapping[str, object]]:
    return sorted(rows, key=key, reverse=reverse)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    return _load_json(path)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_float(value: object, digits: int = 6) -> float:
    numeric = _safe_float(value)
    if numeric is None:
        return 0.0
    return round(numeric, digits)


def _fmt(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return f"{numeric:.3f}"


def _fmt_rank(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "-"
    return str(int(numeric))


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
