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
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_llm_prompt_downstream_en_es import _load_json  # noqa: E402


DEFAULT_RUN_JSON = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_generation_run_latest.json"
DEFAULT_CONTRACT_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_generation_contract_latest.json"
)
DEFAULT_PROTOTYPE_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_llm_example_frame_generation_prototype_admission_probe_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_generation_quality_gate_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_generation_quality_gate_latest.md"
)
DEFAULT_MIN_DECISION_ACCURACY = 0.8
DEFAULT_MIN_REPLACE_RECALL = 0.625
DEFAULT_MAX_HARMFUL_REPLACE = 0
DEFAULT_MAX_FALSE_ABSTAIN = 8


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gate a live/generated example-frame batch after structural contract and "
            "prototype-admission evaluation."
        )
    )
    parser.add_argument("--run-json", type=Path, default=DEFAULT_RUN_JSON)
    parser.add_argument("--contract-json", type=Path, default=DEFAULT_CONTRACT_JSON)
    parser.add_argument("--prototype-json", type=Path, default=DEFAULT_PROTOTYPE_JSON)
    parser.add_argument(
        "--min-decision-accuracy", type=float, default=DEFAULT_MIN_DECISION_ACCURACY
    )
    parser.add_argument("--min-replace-recall", type=float, default=DEFAULT_MIN_REPLACE_RECALL)
    parser.add_argument("--max-harmful-replace", type=int, default=DEFAULT_MAX_HARMFUL_REPLACE)
    parser.add_argument("--max-false-abstain", type=int, default=DEFAULT_MAX_FALSE_ABSTAIN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_example_frame_generation_quality_gate_report(
    *,
    run_payload: Mapping[str, object],
    contract_payload: Mapping[str, object],
    prototype_payload: Mapping[str, object],
    min_decision_accuracy: float = DEFAULT_MIN_DECISION_ACCURACY,
    min_replace_recall: float = DEFAULT_MIN_REPLACE_RECALL,
    max_harmful_replace: int = DEFAULT_MAX_HARMFUL_REPLACE,
    max_false_abstain: int = DEFAULT_MAX_FALSE_ABSTAIN,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    contract_ok = str(contract_payload.get("status") or "").strip() == "ok"
    run_summary = _coerce_mapping(run_payload.get("summary"))
    run_ok = str(run_payload.get("status") or "").strip() == "ok" and int(
        run_summary.get("selected_request_count") or 0
    ) == int(run_summary.get("accepted_item_count") or -1)
    config_rows = _config_rows(prototype_payload)
    evaluated_rows = _apply_thresholds(
        [_evaluate_config(row) for row in config_rows],
        min_decision_accuracy=min_decision_accuracy,
        min_replace_recall=min_replace_recall,
        max_harmful_replace=max_harmful_replace,
        max_false_abstain=max_false_abstain,
    )
    best_row = _best_config_row(evaluated_rows)
    quality_ok = bool(best_row.get("quality_gate_pass"))
    status = "ok" if contract_ok and run_ok and quality_ok else "reject"
    diagnostics = _build_diagnostics(config_rows)
    report = {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": status,
        "decision": "promotion_candidate" if status == "ok" else "analysis_only",
        "thresholds": {
            "min_decision_accuracy": float(min_decision_accuracy),
            "min_replace_recall": float(min_replace_recall),
            "max_harmful_replace": int(max_harmful_replace),
            "max_false_abstain": int(max_false_abstain),
        },
        "run_summary": {
            "status": str(run_payload.get("status") or "").strip(),
            "batch_id": str(run_payload.get("batch_id") or "").strip(),
            "selected_request_count": int(run_summary.get("selected_request_count") or 0),
            "accepted_item_count": int(run_summary.get("accepted_item_count") or 0),
            "input_tokens": int(run_summary.get("input_tokens") or 0),
            "output_tokens": int(run_summary.get("output_tokens") or 0),
        },
        "contract_summary": {
            "status": str(contract_payload.get("status") or "").strip(),
            "batch_id": str(contract_payload.get("batch_id") or "").strip(),
            "complete_families": int(
                _coerce_mapping(contract_payload.get("summary")).get(
                    "contract_complete_family_count"
                )
                or 0
            ),
            "families_total": int(
                _coerce_mapping(contract_payload.get("summary")).get("families_total") or 0
            ),
        },
        "prototype_config_rows": evaluated_rows,
        "best_config": best_row,
        "diagnostics": diagnostics,
        "recommendation": _build_recommendation(status, best_row, diagnostics),
    }
    return report


def render_example_frame_generation_quality_gate_markdown(report: Mapping[str, object]) -> str:
    run_summary = _coerce_mapping(report.get("run_summary"))
    contract_summary = _coerce_mapping(report.get("contract_summary"))
    best = _coerce_mapping(report.get("best_config"))
    diagnostics = _coerce_mapping(report.get("diagnostics"))
    lines = [
        "# en-es Example-Frame Generation Quality Gate",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Run batch: `{run_summary.get('batch_id', '')}`",
        f"- Contract batch: `{contract_summary.get('batch_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Run accepted: `{run_summary.get('accepted_item_count', 0)}` / `{run_summary.get('selected_request_count', 0)}`",
        f"- Contract complete: `{contract_summary.get('complete_families', 0)}` / `{contract_summary.get('families_total', 0)}`",
        f"- Best config: `{best.get('config_id', '')}`",
        f"- Best metrics: `{_pct(best.get('decision_accuracy'))}` accuracy / `{_pct(best.get('replace_recall'))}` recall / `{best.get('harmful_replace_count', 0)}` harmful / `{best.get('false_abstain_count', 0)}` false abstains",
        "",
        "## Prototype Configs",
        "",
        "| Config | Mode | Gate | Accuracy | Recall | Harmful | False Abstain |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in report.get("prototype_config_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('config_id', '')}`",
                    f"`{row.get('phrase_control_evidence_mode', '')}`",
                    "`pass`" if bool(row.get("quality_gate_pass")) else "`fail`",
                    _pct(row.get("decision_accuracy")),
                    _pct(row.get("replace_recall")),
                    str(row.get("harmful_replace_count", 0)),
                    str(row.get("false_abstain_count", 0)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Diagnostics",
            "",
            f"- Phrase-overreach pressure false-abstains: `{diagnostics.get('phrase_overreach_false_abstain_count', 0)}`",
            f"- Incremental phrase-prototype false-abstains: `{diagnostics.get('phrase_incremental_false_abstain_count', 0)}`",
            f"- Containment false-abstains: `{diagnostics.get('containment_false_abstain_count', 0)}`",
            f"- Incremental containment false-abstains: `{diagnostics.get('containment_incremental_false_abstain_count', 0)}`",
            f"- Containment overreach reduction: `{diagnostics.get('containment_overreach_reduction_count', 0)}`",
            f"- Phrase containment hits: `{diagnostics.get('phrase_containment_hit_count', 0)}`",
            f"- Harmful replace residuals: `{diagnostics.get('harmful_replace_count', 0)}`",
            "",
            "### Phrase Overreach Samples",
            "",
            "| Case | Phrase Prototype | Active Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for row in diagnostics.get("phrase_overreach_samples", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    _cell(row.get("phrase_control_evidence_text")),
                    _cell(row.get("active_evidence_text")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "### Incremental Phrase False-Abstain Samples",
            "",
            "| Case | Phrase Prototype | Active Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for row in diagnostics.get("phrase_incremental_false_abstain_samples", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    _cell(row.get("phrase_control_evidence_text")),
                    _cell(row.get("active_evidence_text")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "### Harmful Replace Samples",
            "",
            "| Case | Predicted Winner | Active Evidence | Shadow Evidence |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in diagnostics.get("harmful_replace_samples", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    f"`{row.get('predicted_winner', '')}`",
                    _cell(row.get("active_evidence_text")),
                    _cell(row.get("strongest_shadow_evidence_text")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _apply_thresholds(
    rows: Sequence[Mapping[str, object]],
    *,
    min_decision_accuracy: float,
    min_replace_recall: float,
    max_harmful_replace: int,
    max_false_abstain: int,
) -> list[dict[str, object]]:
    evaluated: list[dict[str, object]] = []
    for row in rows:
        copy = dict(row)
        copy["quality_gate_pass"] = (
            float(copy.get("decision_accuracy") or 0.0) >= min_decision_accuracy
            and float(copy.get("replace_recall") or 0.0) >= min_replace_recall
            and int(copy.get("harmful_replace_count") or 0) <= max_harmful_replace
            and int(copy.get("false_abstain_count") or 0) <= max_false_abstain
        )
        evaluated.append(copy)
    return evaluated


def _evaluate_config(config: Mapping[str, object]) -> dict[str, object]:
    summary = _coerce_mapping(config.get("summary"))
    return {
        "config_id": str(config.get("config_id") or "").strip(),
        "label": str(config.get("label") or "").strip(),
        "phrase_control_evidence_mode": str(
            config.get("phrase_control_evidence_mode") or ""
        ).strip(),
        "use_phrase_prototypes": bool(config.get("use_phrase_prototypes")),
        "use_phrase_containment_gate": bool(config.get("use_phrase_containment_gate")),
        "decision_accuracy": float(summary.get("decision_accuracy") or 0.0),
        "replace_recall": float(summary.get("replace_recall") or 0.0),
        "harmful_replace_count": int(summary.get("harmful_replace_count") or 0),
        "false_abstain_count": int(summary.get("false_abstain_count") or 0),
        "phrase_containment_hit_count": int(summary.get("phrase_containment_hit_count") or 0),
    }


def _best_config_row(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    return dict(
        max(
            rows,
            key=lambda row: (
                float(row.get("decision_accuracy") or 0.0),
                float(row.get("replace_recall") or 0.0),
                -int(row.get("harmful_replace_count") or 0),
                -int(row.get("false_abstain_count") or 0),
                _config_preference(row),
            ),
        )
    )


def _config_preference(row: Mapping[str, object]) -> int:
    config_id = str(row.get("config_id") or "").strip()
    if config_id == "prototype_reviewed_examples_phrase_containment_guard":
        return 3
    if config_id == "prototype_reviewed_examples_active_guard":
        return 2
    if config_id == "prototype_reviewed_examples_family_guard":
        return 1
    if config_id == "prototype_reviewed_examples_phrase_prototype_guard":
        return 0
    return 0


def _build_diagnostics(config_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    phrase_config = _config_by_id(config_rows, "prototype_reviewed_examples_phrase_prototype_guard")
    containment_config = _config_by_id(
        config_rows,
        "prototype_reviewed_examples_phrase_containment_guard",
    )
    active_config = _config_by_id(config_rows, "prototype_reviewed_examples_active_guard")
    active_false_abstain_ids = _false_abstain_case_ids(active_config)
    phrase_overreach = [
        _case_sample(row)
        for row in _row_results(phrase_config)
        if str(row.get("gold_decision") or "").strip() == "replace"
        and str(row.get("predicted_decision") or "").strip() == "abstain"
        and (
            str(row.get("predicted_winner") or "").strip() == "phrase_control"
            or float(row.get("phrase_control_score") or 0.0)
            >= float(row.get("active_score") or 0.0)
        )
    ]
    phrase_incremental_false_abstains = [
        _case_sample(row)
        for row in _row_results(phrase_config)
        if str(row.get("gold_decision") or "").strip() == "replace"
        and str(row.get("predicted_decision") or "").strip() == "abstain"
        and str(row.get("case_id") or "").strip() not in active_false_abstain_ids
    ]
    containment_false_abstains = [
        _case_sample(row)
        for row in _row_results(containment_config)
        if str(row.get("gold_decision") or "").strip() == "replace"
        and str(row.get("predicted_decision") or "").strip() == "abstain"
        and (
            bool(row.get("phrase_containment_hit"))
            or str(row.get("predicted_winner") or "").strip() == "phrase_control"
        )
    ]
    containment_incremental_false_abstains = [
        _case_sample(row)
        for row in _row_results(containment_config)
        if str(row.get("gold_decision") or "").strip() == "replace"
        and str(row.get("predicted_decision") or "").strip() == "abstain"
        and str(row.get("case_id") or "").strip() not in active_false_abstain_ids
    ]
    harmful = [
        _case_sample(row)
        for row in _row_results(active_config)
        if str(row.get("gold_decision") or "").strip() == "abstain"
        and str(row.get("predicted_decision") or "").strip() == "replace"
    ]
    return {
        "phrase_overreach_false_abstain_count": len(phrase_overreach),
        "phrase_incremental_false_abstain_count": len(phrase_incremental_false_abstains),
        "containment_false_abstain_count": len(containment_false_abstains),
        "containment_incremental_false_abstain_count": len(containment_incremental_false_abstains),
        "containment_overreach_reduction_count": max(
            0,
            len(phrase_incremental_false_abstains) - len(containment_incremental_false_abstains),
        ),
        "phrase_containment_hit_count": _summary_count(
            containment_config,
            "phrase_containment_hit_count",
        ),
        "phrase_overreach_samples": phrase_overreach[:8],
        "phrase_incremental_false_abstain_samples": phrase_incremental_false_abstains[:8],
        "harmful_replace_count": len(harmful),
        "harmful_replace_samples": harmful[:8],
    }


def _build_recommendation(
    status: str,
    best_row: Mapping[str, object],
    diagnostics: Mapping[str, object],
) -> str:
    if status == "ok":
        return (
            "This generated batch clears the structural contract and the prototype-quality gate; "
            "it can proceed to the next no-spend source/insertion checks before any runtime claim."
        )
    phrase_overreach = int(diagnostics.get("phrase_overreach_false_abstain_count") or 0)
    phrase_incremental = int(diagnostics.get("phrase_incremental_false_abstain_count") or 0)
    containment_false_abstains = int(diagnostics.get("containment_false_abstain_count") or 0)
    containment_incremental = int(
        diagnostics.get("containment_incremental_false_abstain_count") or 0
    )
    containment_reduction = int(diagnostics.get("containment_overreach_reduction_count") or 0)
    harmful = int(diagnostics.get("harmful_replace_count") or 0)
    return (
        "Keep this generated batch analysis-only. It clears the row contract but fails the "
        f"prototype-quality gate: best config `{best_row.get('config_id', '')}` is "
        f"`{_pct(best_row.get('decision_accuracy'))}` accuracy / "
        f"`{_pct(best_row.get('replace_recall'))}` recall / "
        f"`{best_row.get('harmful_replace_count', 0)}` harmful / "
        f"`{best_row.get('false_abstain_count', 0)}` false abstains. Diagnostics show "
        f"`{phrase_overreach}` broad phrase-prototype pressure rows, "
        f"`{phrase_incremental}` incremental broad-phrase false abstains, "
        f"`{containment_false_abstains}` containment-gated phrase false abstains, "
        f"`{containment_incremental}` incremental containment false abstains "
        f"(`{containment_reduction}` incremental overreach avoided), and `{harmful}` harmful "
        "active wins. "
        "The next source pass should not merely fill missing rows; it should generate balanced "
        "active/shadow exemplars while keeping phrase-control rows as containment patterns or "
        "separately gated abstain evidence, not broad semantic competitors."
    )


def _config_rows(payload: Mapping[str, object]) -> list[dict[str, object]]:
    rows = payload.get("configurations")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _config_by_id(rows: Sequence[Mapping[str, object]], config_id: str) -> Mapping[str, object]:
    for row in rows:
        if str(row.get("config_id") or "").strip() == config_id:
            return row
    return {}


def _row_results(config: Mapping[str, object]) -> list[dict[str, object]]:
    rows = config.get("row_results")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _false_abstain_case_ids(config: Mapping[str, object]) -> set[str]:
    return {
        str(row.get("case_id") or "").strip()
        for row in _row_results(config)
        if str(row.get("case_id") or "").strip()
        and str(row.get("gold_decision") or "").strip() == "replace"
        and str(row.get("predicted_decision") or "").strip() == "abstain"
    }


def _summary_count(config: Mapping[str, object], key: str) -> int:
    summary = _coerce_mapping(config.get("summary"))
    return int(summary.get(key) or 0)


def _case_sample(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "case_id": str(row.get("case_id") or "").strip(),
        "gold_decision": str(row.get("gold_decision") or "").strip(),
        "predicted_decision": str(row.get("predicted_decision") or "").strip(),
        "predicted_winner": str(row.get("predicted_winner") or "").strip(),
        "active_score": _round_float(row.get("active_score")),
        "strongest_shadow_score": _round_float(row.get("strongest_shadow_score")),
        "phrase_control_score": _round_float(row.get("phrase_control_score")),
        "phrase_containment_hit": bool(row.get("phrase_containment_hit")),
        "phrase_containment_pattern": str(row.get("phrase_containment_pattern") or "").strip(),
        "active_evidence_text": str(row.get("active_evidence_text") or "").strip(),
        "strongest_shadow_evidence_text": str(
            row.get("strongest_shadow_evidence_text") or ""
        ).strip(),
        "phrase_control_evidence_text": str(row.get("phrase_control_evidence_text") or "").strip(),
    }


def _coerce_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


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


def _cell(value: object, *, limit: int = 90) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > limit:
        text = text[: limit - 3].rstrip() + "..."
    return text.replace("|", "\\|") or "n/a"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    report = build_example_frame_generation_quality_gate_report(
        run_payload=_load_json(args.run_json),
        contract_payload=_load_json(args.contract_json),
        prototype_payload=_load_json(args.prototype_json),
        min_decision_accuracy=args.min_decision_accuracy,
        min_replace_recall=args.min_replace_recall,
        max_harmful_replace=args.max_harmful_replace,
        max_false_abstain=args.max_false_abstain,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_example_frame_generation_quality_gate_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote quality gate JSON to {args.json_out}")
    print(f"Wrote quality gate Markdown to {args.markdown_out}")
    print(f"Quality gate status: {report['status']}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
