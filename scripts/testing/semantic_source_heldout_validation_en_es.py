#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXAMPLE_FRAME_BATCH_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
for candidate in (str(SCRIPT_ROOT), str(PROJECT_ROOT / "core")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
)
from semantic_llm_prompt_downstream_en_es import DEFAULT_DATASET_PATH  # noqa: E402
from semantic_llm_prototype_ablation_matrix_en_es import (  # noqa: E402
    build_prototype_ablation_matrix_report,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_HELDOUT_CASES = (
    DOCS_ROOT / "test_inputs" / "semantic_routing_cases" / "en_es_source_heldout_cases_v2.json"
)
DEFAULT_PROMOTION_CANDIDATE_EVIDENCE = EXAMPLE_FRAME_BATCH_ROOT / (
    "en-es-wordnet-active-related-plant-cell-depth3-heldout-v2-policy-v1-20260425a_cycle_sense_admitted_normalized_evidence.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_source_heldout_validation_v2_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_source_heldout_validation_v2_latest.md"
DEFAULT_SOURCE_MODE = "promotion_candidate_composite"
DEFAULT_SCORER = "sentence_transformer_cosine"
DEFAULT_CONTEXT_VIEW = "masked_sentence"
DEFAULT_DECISION_SHAPE = "active_shadow_containment_surface_pos"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the current en-es source-admission promotion-candidate lane on a "
            "small non-benchmark active/shadow held-out slice."
        )
    )
    parser.add_argument("--base-dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--heldout-cases", type=Path, default=DEFAULT_HELDOUT_CASES)
    parser.add_argument(
        "--evidence-batch-json",
        type=Path,
        default=DEFAULT_PROMOTION_CANDIDATE_EVIDENCE,
    )
    parser.add_argument("--scorer-id", default=DEFAULT_SCORER)
    parser.add_argument("--context-view", default=DEFAULT_CONTEXT_VIEW)
    parser.add_argument("--min-active-score", type=float, default=0.0)
    parser.add_argument("--min-margin", type=float, default=0.0)
    parser.add_argument("--decision-shape", default=DEFAULT_DECISION_SHAPE)
    parser.add_argument("--max-harmful", type=int, default=0)
    parser.add_argument("--max-false-abstain", type=int, default=0)
    parser.add_argument(
        "--window-tokens",
        type=int,
        default=DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    )
    parser.add_argument("--mask-token", default=DEFAULT_SENTENCE_VETO_MASK_TOKEN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Exit non-zero when the configured held-out row misses the thresholds.",
    )
    return parser.parse_args()


def build_source_heldout_validation_report(
    *,
    base_dataset_payload: Mapping[str, object],
    heldout_case_payload: Mapping[str, object],
    evidence_batch_payload: Mapping[str, object],
    scorer_id: str = DEFAULT_SCORER,
    context_view: str = DEFAULT_CONTEXT_VIEW,
    min_active_score: float = 0.0,
    min_margin: float = 0.0,
    decision_shape: str = DEFAULT_DECISION_SHAPE,
    max_harmful: int = 0,
    max_false_abstain: int = 0,
    window_tokens: int = DEFAULT_SENTENCE_VETO_CONTEXT_WINDOW_TOKENS,
    mask_token: str = DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    heldout_dataset = build_heldout_sentence_dataset(
        base_dataset_payload=base_dataset_payload,
        heldout_case_payload=heldout_case_payload,
    )
    queue_payload = _all_family_queue_payload(heldout_dataset, generated_at=generated_at)
    matrix_report = build_prototype_ablation_matrix_report(
        queue_payload=queue_payload,
        dataset_payload=heldout_dataset,
        source_modes=("empty_batch", DEFAULT_SOURCE_MODE),
        scopes=("all_dataset_families",),
        scorers=(scorer_id,),
        context_views=(context_view,),
        min_active_scores=(float(min_active_score),),
        min_margins=(float(min_margin),),
        source_payload_overrides={DEFAULT_SOURCE_MODE: evidence_batch_payload},
        window_tokens=window_tokens,
        mask_token=mask_token,
        generated_at=generated_at,
    )
    rows = [row for row in matrix_report.get("rows", ()) if isinstance(row, Mapping)]
    configured_row = _find_matrix_row(
        rows,
        source_mode=DEFAULT_SOURCE_MODE,
        scorer_id=scorer_id,
        context_view=context_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        decision_shape=decision_shape,
    )
    empty_baseline_row = _find_matrix_row(
        rows,
        source_mode="empty_batch",
        scorer_id=scorer_id,
        context_view=context_view,
        min_active_score=min_active_score,
        min_margin=min_margin,
        decision_shape=decision_shape,
    )
    summary = _build_validation_summary(
        heldout_dataset=heldout_dataset,
        configured_row=configured_row,
        empty_baseline_row=empty_baseline_row,
        max_harmful=max_harmful,
        max_false_abstain=max_false_abstain,
    )
    return {
        "schema_version": 1,
        "status": summary["status"],
        "decision": summary["decision"],
        "generated_at": generated_at,
        "pair": str(heldout_dataset.get("pair") or "").strip() or "en-es",
        "base_dataset_id": str(base_dataset_payload.get("dataset_id") or "").strip(),
        "heldout_dataset_id": str(heldout_dataset.get("dataset_id") or "").strip(),
        "heldout_case_scope": str(heldout_case_payload.get("case_scope") or "").strip(),
        "evidence_source_id": str(evidence_batch_payload.get("source_id") or "").strip(),
        "evidence_batch_id": str(evidence_batch_payload.get("batch_id") or "").strip(),
        "configured_lane": {
            "source_mode": DEFAULT_SOURCE_MODE,
            "scorer_id": str(scorer_id or "").strip(),
            "context_view": str(context_view or "").strip(),
            "min_active_score": float(min_active_score),
            "min_margin": float(min_margin),
            "decision_shape": str(decision_shape or "").strip(),
            "max_harmful": int(max_harmful),
            "max_false_abstain": int(max_false_abstain),
        },
        "summary": summary,
        "heldout_families": _heldout_family_rows(heldout_dataset),
        "configured_row": dict(configured_row) if isinstance(configured_row, Mapping) else None,
        "empty_baseline_row": (
            dict(empty_baseline_row) if isinstance(empty_baseline_row, Mapping) else None
        ),
        "matrix_report": matrix_report,
        "limitations": [
            "bounded_non_benchmark_slice_not_full_en_es_proof",
            "semantic_active_shadow_only_phrase_policy_excluded",
            "does_not_audit_runtime_packaging_or_latency",
        ],
        "next_steps": _next_steps_for_case_scope(
            str(heldout_case_payload.get("case_scope") or "").strip(),
            summary=summary,
        ),
    }


def build_heldout_sentence_dataset(
    *,
    base_dataset_payload: Mapping[str, object],
    heldout_case_payload: Mapping[str, object],
) -> dict[str, object]:
    _validate_heldout_case_payload(heldout_case_payload)
    base_by_family = {
        str(family.get("family_id") or "").strip(): family
        for family in base_dataset_payload.get("families", ())
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }
    families: list[dict[str, object]] = []
    for heldout_family in heldout_case_payload.get("families", ()):
        if not isinstance(heldout_family, Mapping):
            continue
        family_id = str(heldout_family.get("family_id") or "").strip()
        base_family = base_by_family.get(family_id)
        if not isinstance(base_family, Mapping):
            raise ValueError(f"Held-out family {family_id!r} is not present in the base dataset.")
        family = _copy_base_family_without_cases(base_family)
        cases = [
            dict(case) for case in heldout_family.get("cases", ()) if isinstance(case, Mapping)
        ]
        _validate_cases_against_family(family, cases)
        family["cases"] = cases
        families.append(family)
    if not families:
        raise ValueError("Held-out case payload did not resolve any dataset families.")
    return {
        "schema_version": 1,
        "pair": str(
            heldout_case_payload.get("pair") or base_dataset_payload.get("pair") or "en-es"
        ),
        "dataset_id": str(heldout_case_payload.get("dataset_id") or "source_heldout_cases"),
        "description": str(heldout_case_payload.get("description") or "").strip(),
        "families": families,
    }


def render_source_heldout_validation_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    configured = _as_mapping(report.get("configured_row"))
    baseline = _as_mapping(report.get("empty_baseline_row"))
    lines = [
        "# en-es Semantic Source Held-out Validation",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Base dataset: `{report.get('base_dataset_id', '')}`",
        f"- Held-out dataset: `{report.get('heldout_dataset_id', '')}`",
        f"- Case scope: `{report.get('heldout_case_scope', '')}`",
        f"- Evidence batch: `{report.get('evidence_batch_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Cases: `{summary.get('case_count', 0)}`",
        f"- Gold replacements: `{summary.get('gold_replace_cases', 0)}`",
        f"- Gold abstains: `{summary.get('gold_abstain_cases', 0)}`",
        f"- Harmful replacements: `{summary.get('harmful_replace_count', 0)}` / max `{summary.get('max_harmful', 0)}`",
        f"- False abstains: `{summary.get('false_abstain_count', 0)}` / max `{summary.get('max_false_abstain', 0)}`",
        f"- Replace recall: `{_pct(summary.get('replace_recall'))}`",
        f"- Decision accuracy: `{_pct(summary.get('decision_accuracy'))}`",
        "",
        "## Configured Row",
        "",
        _row_table([configured], empty_label="Configured row was not found."),
        "",
        "## Empty Baseline Comparator",
        "",
        _row_table([baseline], empty_label="Empty baseline row was not found."),
        "",
        "## Family Coverage",
        "",
        _family_table(report.get("heldout_families", ())),
        "",
        "## Failure Cases",
        "",
        f"- Harmful replace cases: `{', '.join(summary.get('harmful_replace_case_ids', ())) or 'none'}`",
        f"- False abstain cases: `{', '.join(summary.get('false_abstain_case_ids', ())) or 'none'}`",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _next_steps_for_case_scope(
    case_scope: str,
    *,
    summary: Mapping[str, object] | None = None,
) -> list[str]:
    if str(case_scope or "").strip() == "phrase_no_winner_only":
        resolved_summary = _as_mapping(summary)
        if (
            int(resolved_summary.get("harmful_replace_count") or 0) <= 0
            and int(resolved_summary.get("false_abstain_count") or 0) <= 0
        ):
            return [
                "stress the passing phrase policy on fresh no-winner and non-v10 rows",
                "keep phrase-source or pattern provenance separate from active/shadow semantic scoring",
                "rerun phrase held-out, phrase challenge, active/shadow v2, and margin sweep before accepting a phrase-policy change",
            ]
        return [
            "diagnose phrase/no-winner misses without tuning the active/shadow v2 reference",
            "test phrase-source rows or a general verb-frame no-winner policy on this slice",
            "rerun both phrase held-out and active/shadow v2 held-out before accepting a phrase-policy change",
        ]
    return [
        "expand held-out families and cases without tuning on this v2 result",
        "add phrase-sensitive held-out rows under a separate phrase-source policy harness",
        "freeze the promotion-candidate evidence manifest before broad source scaling",
    ]


def _validate_heldout_case_payload(payload: Mapping[str, object]) -> None:
    if int(payload.get("schema_version") or 0) != 1:
        raise ValueError("Held-out case payload must declare schema_version=1.")
    if not str(payload.get("pair") or "").strip():
        raise ValueError("Held-out case payload is missing `pair`.")
    if not str(payload.get("dataset_id") or "").strip():
        raise ValueError("Held-out case payload is missing `dataset_id`.")
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)) or not families:
        raise ValueError("Held-out case payload must include a non-empty `families` list.")


def _validate_cases_against_family(
    family: Mapping[str, object],
    cases: Sequence[Mapping[str, object]],
) -> None:
    family_id = str(family.get("family_id") or "").strip()
    active = _as_mapping(family.get("active"))
    active_sense_id = str(active.get("sense_id") or "").strip()
    shadow_ids = {
        str(shadow.get("sense_id") or "").strip()
        for shadow in family.get("shadows", ())
        if isinstance(shadow, Mapping) and str(shadow.get("sense_id") or "").strip()
    }
    if not cases:
        raise ValueError(f"Held-out family {family_id!r} has no cases.")
    for case in cases:
        case_id = str(case.get("case_id") or "").strip()
        sentence = str(case.get("sentence") or "").strip()
        source_phrase = str(case.get("source_phrase") or "").strip()
        gold_winner = str(case.get("gold_winner") or "").strip()
        gold_decision = str(case.get("gold_decision") or "").strip()
        if not case_id or not sentence or not source_phrase or not gold_winner:
            raise ValueError(f"Held-out family {family_id!r} has a case missing required fields.")
        if gold_decision not in {"replace", "abstain"}:
            raise ValueError(
                f"Held-out case {case_id!r} has unsupported gold_decision {gold_decision!r}."
            )
        if gold_winner not in {"none", active_sense_id} and gold_winner not in shadow_ids:
            raise ValueError(
                f"Held-out case {case_id!r} gold_winner {gold_winner!r} does not match "
                f"family {family_id!r}."
            )


def _copy_base_family_without_cases(family: Mapping[str, object]) -> dict[str, object]:
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active": dict(_as_mapping(family.get("active"))),
        "shadows": [
            dict(shadow) for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)
        ],
        "cases": [],
    }


def _all_family_queue_payload(
    dataset_payload: Mapping[str, object],
    *,
    generated_at: str,
) -> dict[str, object]:
    dataset_id = str(dataset_payload.get("dataset_id") or "").strip() or "source_heldout_cases"
    return {
        "schema_version": 1,
        "queue_id": f"{dataset_id}_source_heldout_validation",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "generated_at": generated_at,
        "dataset_id": dataset_id,
        "families": [
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "role": "target",
                "likely_bucket": "source_heldout_validation",
            }
            for family in dataset_payload.get("families", ())
            if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
        ],
    }


def _find_matrix_row(
    rows: Sequence[Mapping[str, object]],
    *,
    source_mode: str,
    scorer_id: str,
    context_view: str,
    min_active_score: float,
    min_margin: float,
    decision_shape: str,
) -> Mapping[str, object] | None:
    for row in rows:
        if str(row.get("source_mode") or "") != source_mode:
            continue
        if str(row.get("scorer_id") or "") != scorer_id:
            continue
        if str(row.get("context_view") or "") != context_view:
            continue
        if abs(float(row.get("min_active_score") or 0.0) - float(min_active_score)) > 1e-9:
            continue
        if abs(float(row.get("min_margin") or 0.0) - float(min_margin)) > 1e-9:
            continue
        if str(row.get("decision_shape") or "") != decision_shape:
            continue
        return row
    return None


def _build_validation_summary(
    *,
    heldout_dataset: Mapping[str, object],
    configured_row: Mapping[str, object] | None,
    empty_baseline_row: Mapping[str, object] | None,
    max_harmful: int,
    max_false_abstain: int,
) -> dict[str, object]:
    case_count = sum(
        len([case for case in family.get("cases", ()) if isinstance(case, Mapping)])
        for family in heldout_dataset.get("families", ())
        if isinstance(family, Mapping)
    )
    gold_replace_cases = sum(
        1
        for family in heldout_dataset.get("families", ())
        if isinstance(family, Mapping)
        for case in family.get("cases", ())
        if isinstance(case, Mapping) and str(case.get("gold_decision") or "") == "replace"
    )
    gold_abstain_cases = case_count - gold_replace_cases
    if not isinstance(configured_row, Mapping):
        return {
            "status": "review",
            "decision": "analysis_only",
            "reason": "configured_row_missing",
            "family_count": len(_heldout_family_rows(heldout_dataset)),
            "case_count": case_count,
            "gold_replace_cases": gold_replace_cases,
            "gold_abstain_cases": gold_abstain_cases,
            "max_harmful": int(max_harmful),
            "max_false_abstain": int(max_false_abstain),
            "harmful_replace_count": 0,
            "false_abstain_count": 0,
            "harmful_replace_case_ids": [],
            "false_abstain_case_ids": [],
            "replace_recall": 0.0,
            "decision_accuracy": 0.0,
            "delta_vs_empty_baseline": {},
        }
    harmful = int(configured_row.get("harmful_replace_count") or 0)
    false_abstain = int(configured_row.get("false_abstain_count") or 0)
    passes = harmful <= int(max_harmful) and false_abstain <= int(max_false_abstain)
    return {
        "status": "ok" if passes else "review",
        "decision": "heldout_pass" if passes else "heldout_review",
        "reason": "thresholds_passed" if passes else "thresholds_missed",
        "family_count": len(_heldout_family_rows(heldout_dataset)),
        "case_count": case_count,
        "gold_replace_cases": gold_replace_cases,
        "gold_abstain_cases": gold_abstain_cases,
        "max_harmful": int(max_harmful),
        "max_false_abstain": int(max_false_abstain),
        "harmful_replace_count": harmful,
        "false_abstain_count": false_abstain,
        "harmful_replace_case_ids": list(configured_row.get("harmful_replace_case_ids") or ()),
        "false_abstain_case_ids": list(configured_row.get("false_abstain_case_ids") or ()),
        "replace_recall": float(configured_row.get("replace_recall") or 0.0),
        "decision_accuracy": float(configured_row.get("decision_accuracy") or 0.0),
        "delta_vs_empty_baseline": _delta_vs_empty(configured_row, empty_baseline_row),
    }


def _delta_vs_empty(
    configured_row: Mapping[str, object],
    empty_baseline_row: Mapping[str, object] | None,
) -> dict[str, object]:
    if not isinstance(empty_baseline_row, Mapping):
        return {}
    return {
        "replace_recall_delta": _round_float(
            float(configured_row.get("replace_recall") or 0.0)
            - float(empty_baseline_row.get("replace_recall") or 0.0)
        ),
        "decision_accuracy_delta": _round_float(
            float(configured_row.get("decision_accuracy") or 0.0)
            - float(empty_baseline_row.get("decision_accuracy") or 0.0)
        ),
        "harmful_replace_delta": int(configured_row.get("harmful_replace_count") or 0)
        - int(empty_baseline_row.get("harmful_replace_count") or 0),
        "false_abstain_delta": int(configured_row.get("false_abstain_count") or 0)
        - int(empty_baseline_row.get("false_abstain_count") or 0),
    }


def _heldout_family_rows(dataset_payload: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        cases = [case for case in family.get("cases", ()) if isinstance(case, Mapping)]
        rows.append(
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "case_count": len(cases),
                "replace_cases": sum(
                    1 for case in cases if str(case.get("gold_decision") or "") == "replace"
                ),
                "abstain_cases": sum(
                    1 for case in cases if str(case.get("gold_decision") or "") == "abstain"
                ),
                "case_ids": [str(case.get("case_id") or "").strip() for case in cases],
            }
        )
    return rows


def _row_table(rows: Sequence[object], *, empty_label: str) -> str:
    materialized = [row for row in rows if isinstance(row, Mapping) and row]
    if not materialized:
        return empty_label
    lines = [
        "| Source | Scorer | Context | Shape | Cases | Harmful | False Abstain | Recall | Accuracy |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('source_mode', '')}`",
                    f"`{row.get('scorer_id', '')}`",
                    f"`{row.get('context_view', '')}`",
                    f"`{row.get('decision_shape', '')}`",
                    str(row.get("cases_total", 0)),
                    str(row.get("harmful_replace_count", 0)),
                    str(row.get("false_abstain_count", 0)),
                    _pct(row.get("replace_recall")),
                    _pct(row.get("decision_accuracy")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _family_table(rows: object) -> str:
    materialized = [row for row in rows if isinstance(row, Mapping)]
    if not materialized:
        return "No held-out family rows."
    lines = [
        "| Family | Trigger | Cases | Replace | Abstain |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('trigger', '')}`",
                    str(row.get("case_count", 0)),
                    str(row.get("replace_cases", 0)),
                    str(row.get("abstain_cases", 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _round_float(value: object) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    base_dataset = load_sentence_veto_dataset(args.base_dataset)
    heldout_cases = _load_json(args.heldout_cases)
    evidence_batch = _load_json(args.evidence_batch_json)
    report = build_source_heldout_validation_report(
        base_dataset_payload=base_dataset,
        heldout_case_payload=heldout_cases,
        evidence_batch_payload=evidence_batch,
        scorer_id=args.scorer_id,
        context_view=args.context_view,
        min_active_score=args.min_active_score,
        min_margin=args.min_margin,
        decision_shape=args.decision_shape,
        max_harmful=max(0, int(args.max_harmful)),
        max_false_abstain=max(0, int(args.max_false_abstain)),
        window_tokens=max(0, int(args.window_tokens)),
        mask_token=str(args.mask_token or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    )
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_source_heldout_validation_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
