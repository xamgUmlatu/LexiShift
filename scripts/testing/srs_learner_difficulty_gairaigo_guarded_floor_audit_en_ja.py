#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
sys.path.insert(0, str(SCRIPT_DIR))

from artifact_provenance import build_artifact_provenance  # noqa: E402
from srs_learner_difficulty_acceptance_review_pack_en_ja import (  # noqa: E402
    DEFAULT_VALIDATION_EVAL_JSON,
)
from srs_learner_difficulty_piecewise_search_en_ja import (  # noqa: E402
    _difficulty_band,
    _difficulty_metrics,
    _escape,
    _mapping,
    _repo_or_home_path,
    _resolve_path,
    _rounded,
    _summary_metrics,
    _utc_now,
)
from srs_learner_difficulty_qualitative_failure_hypotheses_en_ja import (  # noqa: E402
    MatrixView,
)
from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    DEFAULT_COMPONENT_MATRIX,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_gairaigo_guarded_floor_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_gairaigo_guarded_floor_audit_en_ja_latest.md"
)
ANCHOR_MODEL = "ordinary_cap"
POLICY_ID = "protected_gairaigo_tail_floor_v1"
ROW_SIGNALS = (
    "frequency",
    "frequency_tail80",
    "frequency_unranked_risk",
    "bccwj_domain_rank_coverage",
    "jlpt_vocab_difficulty",
    "jlpt_vocab_beginner_core",
    "lesson_vocab_beginner_core",
    "jmdict_priority",
    "jmdict_loanword_source_risk",
    "jmdict_foreign_priority_risk",
    "wtype_gairaigo_risk",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit a protected gairaigo floor policy against fresh en-ja "
            "validation rows, comparing failures and successes."
        )
    )
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--validation-eval-json", type=Path, default=DEFAULT_VALIDATION_EVAL_JSON)
    parser.add_argument("--anchor-model", default=ANCHOR_MODEL)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        component_matrix_path=_resolve_path(args.component_matrix),
        validation_eval_json_path=_resolve_path(args.validation_eval_json),
        anchor_model=str(args.anchor_model),
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
    component_matrix_path: Path,
    validation_eval_json_path: Path,
    anchor_model: str,
) -> dict[str, object]:
    matrix = MatrixView.from_npz(np.load(component_matrix_path))
    validation_eval = _load_json(validation_eval_json_path)
    rows = validation_rows(validation_eval, matrix=matrix, anchor_model=anchor_model)
    adjusted_rows = [row | guarded_gairaigo_floor(row) for row in rows]
    gairaigo_rows = [row for row in adjusted_rows if row.get("is_gairaigo")]
    changed_rows = [row for row in adjusted_rows if row.get("changed")]
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "language_pair": "en-ja",
        "runtime_behavior_changed": False,
        "sweeps_run": False,
        "policy_id": POLICY_ID,
        "purpose": (
            "Compare rare/domain gairaigo failures against gairaigo successes "
            "and audit a protected floor correction before any model promotion."
        ),
        "inputs": {
            "component_matrix": _repo_or_home_path(component_matrix_path),
            "validation_eval_json": _repo_or_home_path(validation_eval_json_path),
            "anchor_model": anchor_model,
        },
        "policy": policy_description(),
        "summary": {
            "all_validation": metrics_for_rows(adjusted_rows),
            "gairaigo_subset": metrics_for_rows(gairaigo_rows),
            "changed_subset": metrics_for_rows(changed_rows),
            "counts": {
                "validation_rows": len(adjusted_rows),
                "gairaigo_rows": len(gairaigo_rows),
                "changed_rows": len(changed_rows),
                "protected_gairaigo_rows": len(
                    [
                        row
                        for row in gairaigo_rows
                        if row.get("policy_reason") == "protected_common_loanword"
                    ]
                ),
                "changed_success_or_near_success_rows": len(
                    [
                        row
                        for row in changed_rows
                        if _optional_float(row.get("anchor_abs_error")) <= 0.08
                    ]
                ),
                "changed_regressions": len(
                    [
                        row
                        for row in changed_rows
                        if _optional_float(row.get("adjusted_abs_error"))
                        > _optional_float(row.get("anchor_abs_error"))
                    ]
                ),
            },
        },
        "changed_rows": changed_rows,
        "gairaigo_failures": [
            row for row in gairaigo_rows if _optional_float(row.get("anchor_abs_error")) >= 0.15
        ],
        "gairaigo_successes": [
            row for row in gairaigo_rows if _optional_float(row.get("anchor_abs_error")) <= 0.08
        ],
        "protected_common_examples": [
            row for row in gairaigo_rows if row.get("policy_reason") == "protected_common_loanword"
        ],
        "provenance": build_artifact_provenance(
            producer_script=Path(__file__),
            input_paths={
                "component_matrix": component_matrix_path,
                "validation_eval_json": validation_eval_json_path,
            },
            code_paths={
                "artifact_provenance": SCRIPT_DIR / "artifact_provenance.py",
                "gairaigo_guarded_floor_audit": Path(__file__),
                "qualitative_failure_hypotheses": SCRIPT_DIR
                / "srs_learner_difficulty_qualitative_failure_hypotheses_en_ja.py",
                "piecewise_helpers": SCRIPT_DIR
                / "srs_learner_difficulty_piecewise_search_en_ja.py",
            },
            argv=sys.argv,
        ),
    }


def validation_rows(
    validation_eval: Mapping[str, object],
    *,
    matrix: MatrixView,
    anchor_model: str,
) -> list[dict[str, object]]:
    pair_to_index = matrix.row_index_by_pair()
    rows: list[dict[str, object]] = []
    for row in _rows(_mapping(validation_eval.get("row_comparison")).get("all_rows")):
        label = str(row.get("label", ""))
        if "/" not in label:
            continue
        lemma, reading = label.split("/", 1)
        matrix_index = pair_to_index.get((lemma, reading))
        if matrix_index is None:
            continue
        model = _mapping(_mapping(row.get("models")).get(anchor_model))
        observed = _optional_float(model.get("observed"))
        expected = _optional_float(row.get("expected"))
        if not np.isfinite(observed) or not np.isfinite(expected):
            continue
        signals = signal_snapshot(matrix_index, matrix=matrix)
        rows.append(
            {
                "label": label,
                "lemma": lemma,
                "reading": reading,
                "expected": _rounded(expected),
                "expected_band": _difficulty_band(expected),
                "anchor_observed": _rounded(observed),
                "anchor_abs_error": _rounded(abs(expected - observed)),
                "anchor_direction": "too_low" if observed < expected else "too_high",
                "candidate_state": matrix.candidate_states[matrix_index],
                "problem_class": matrix.problem_classes[matrix_index],
                "core_rank": _rounded(float(matrix.core_ranks[matrix_index])),
                "is_gairaigo": _float_signal(signals, "wtype_gairaigo_risk") >= 0.75,
                "signals": signals,
            }
        )
    return rows


def guarded_gairaigo_floor(row: Mapping[str, object]) -> dict[str, object]:
    expected = _optional_float(row.get("expected"))
    observed = _optional_float(row.get("anchor_observed"))
    if not bool(row.get("is_gairaigo")):
        return adjusted_payload(
            observed=observed,
            expected=expected,
            changed=False,
            floor=None,
            policy_reason="not_gairaigo",
        )
    signals = _mapping(row.get("signals"))
    frequency = _float_signal(signals, "frequency")
    tail80 = _float_signal(signals, "frequency_tail80")
    unranked = _float_signal(signals, "frequency_unranked_risk")
    domain_coverage = _float_signal(signals, "bccwj_domain_rank_coverage")
    jlpt = _float_signal(signals, "jlpt_vocab_difficulty")
    jlpt_core = _float_signal(signals, "jlpt_vocab_beginner_core")
    lesson_core = _float_signal(signals, "lesson_vocab_beginner_core")
    rank = _optional_float(row.get("core_rank"))
    unranked_low_coverage = unranked >= 0.5 and domain_coverage <= 0.45
    protected = (
        frequency <= 0.75
        or (np.isfinite(rank) and rank <= 10000)
        or jlpt_core >= 0.1
        or lesson_core >= 0.1
        or (jlpt >= 0.65 and not unranked_low_coverage)
    )
    if protected:
        return adjusted_payload(
            observed=observed,
            expected=expected,
            changed=False,
            floor=None,
            policy_reason="protected_common_loanword",
        )
    if unranked_low_coverage:
        floor = 0.52
        reason = "unranked_low_domain_coverage_floor"
    elif unranked >= 0.5:
        floor = 0.40
        reason = "unranked_general_floor"
    else:
        floor = min(0.48, 0.34 + 0.28 * tail80)
        reason = "ranked_tail80_floor"
    adjusted = max(observed, floor)
    return adjusted_payload(
        observed=adjusted,
        expected=expected,
        changed=adjusted > observed + 1e-9,
        floor=floor,
        policy_reason=reason,
    )


def adjusted_payload(
    *,
    observed: float,
    expected: float,
    changed: bool,
    floor: float | None,
    policy_reason: str,
) -> dict[str, object]:
    return {
        "adjusted_observed": _rounded(observed),
        "adjusted_abs_error": _rounded(abs(expected - observed)),
        "adjusted_band": _difficulty_band(observed),
        "changed": changed,
        "policy_floor": _rounded(floor) if floor is not None else None,
        "policy_reason": policy_reason,
    }


def metrics_for_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        return {}
    expected = np.asarray([_optional_float(row.get("expected")) for row in rows], dtype=np.float32)
    anchor = np.asarray(
        [_optional_float(row.get("anchor_observed")) for row in rows], dtype=np.float32
    )
    adjusted = np.asarray(
        [_optional_float(row.get("adjusted_observed")) for row in rows], dtype=np.float32
    )
    labels = [str(row.get("label")) for row in rows]
    expected_bands = [str(row.get("expected_band")) for row in rows]
    anchor_metrics = _difficulty_metrics(
        expected_values=expected,
        observed_values=anchor,
        expected_bands=expected_bands,
        labels=labels,
    )
    adjusted_metrics = _difficulty_metrics(
        expected_values=expected,
        observed_values=adjusted,
        expected_bands=expected_bands,
        labels=labels,
    )
    anchor_summary = _summary_metrics(anchor_metrics)
    adjusted_summary = _summary_metrics(adjusted_metrics)
    return {
        "count": len(rows),
        "anchor": anchor_summary,
        "adjusted": adjusted_summary,
        "delta": {
            "mae_reduction": _rounded(
                _optional_float(anchor_summary.get("mae"))
                - _optional_float(adjusted_summary.get("mae"))
            ),
            "bucket_delta": _rounded(
                _optional_float(adjusted_summary.get("bucket_accuracy"))
                - _optional_float(anchor_summary.get("bucket_accuracy"))
            ),
            "pairwise_delta": _rounded(
                _optional_float(adjusted_summary.get("pairwise_accuracy"))
                - _optional_float(anchor_summary.get("pairwise_accuracy"))
            ),
        },
    }


def signal_snapshot(index: int, *, matrix: MatrixView) -> dict[str, object]:
    component_index = matrix.component_index()
    snapshot: dict[str, object] = {}
    for signal in ROW_SIGNALS:
        column = component_index.get(signal)
        snapshot[signal] = (
            None if column is None else _rounded(float(matrix.component_values[index, column]))
        )
    return snapshot


def policy_description() -> dict[str, object]:
    return {
        "summary": (
            "A protected floor for gairaigo rows. It never adds a penalty to rows "
            "already above the floor and protects common learner loanwords before "
            "applying any floor."
        ),
        "predicate": {
            "gairaigo_gate": "wtype_gairaigo_risk >= 0.75",
            "common_protection": (
                "frequency <= 0.75 OR core_rank <= 10000 OR "
                "jlpt_vocab_beginner_core >= 0.1 OR lesson_vocab_beginner_core >= 0.1 "
                "OR jlpt_vocab_difficulty >= 0.65 unless unranked with low domain coverage"
            ),
            "unranked_low_domain_floor": (
                "if frequency_unranked_risk >= 0.5 and "
                "bccwj_domain_rank_coverage <= 0.45, floor = 0.52"
            ),
            "unranked_general_floor": ("else if frequency_unranked_risk >= 0.5, floor = 0.40"),
            "ranked_tail_floor": ("else floor = min(0.48, 0.34 + 0.28 * frequency_tail80)"),
        },
        "why_floor_not_additive": (
            "The labeled gairaigo successes are often already near the right band; "
            "an additive penalty would regress them, while a floor only affects "
            "implausibly low placements."
        ),
        "promotion_status": "diagnostic candidate only; not runtime behavior",
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    counts = _mapping(summary.get("counts"))
    lines = [
        "# en-ja Gairaigo Guarded Floor Audit",
        "",
        f"- Generated: `{_escape(report.get('generated_at'))}`",
        f"- Runtime behavior changed: `{_escape(report.get('runtime_behavior_changed'))}`",
        f"- Sweeps run: `{_escape(report.get('sweeps_run'))}`",
        f"- Policy: `{_escape(report.get('policy_id'))}`",
        "",
        "## Policy",
        "",
        _escape(_mapping(report.get("policy")).get("summary")),
        "",
        "This is diagnostic only. It is designed to be reviewed before any broader holdout run.",
        "",
        "## Counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key, value in counts.items():
        lines.append(f"| `{_escape(key)}` | {_escape(value)} |")
    lines.extend(["", "## Metric Impact", ""])
    lines.extend(_metrics_table(_mapping(summary.get("all_validation")), "All validation"))
    lines.append("")
    lines.extend(_metrics_table(_mapping(summary.get("gairaigo_subset")), "Gairaigo subset"))
    lines.append("")
    lines.extend(_metrics_table(_mapping(summary.get("changed_subset")), "Changed subset"))
    lines.extend(["", "## Changed Rows", ""])
    lines.extend(_row_table(_rows(report.get("changed_rows")), include_policy=True))
    lines.extend(["", "## Gairaigo Failures Before Policy", ""])
    lines.extend(_row_table(_rows(report.get("gairaigo_failures")), include_policy=True))
    lines.extend(["", "## Gairaigo Successes / Near Successes", ""])
    lines.extend(_row_table(_rows(report.get("gairaigo_successes")), include_policy=True))
    lines.extend(["", "## Protected Common Examples", ""])
    lines.extend(_row_table(_rows(report.get("protected_common_examples")), include_policy=True))
    return "\n".join(lines).rstrip() + "\n"


def _metrics_table(metrics: Mapping[str, object], title: str) -> list[str]:
    anchor = _mapping(metrics.get("anchor"))
    adjusted = _mapping(metrics.get("adjusted"))
    delta = _mapping(metrics.get("delta"))
    return [
        f"### {title}",
        "",
        "| Scope | Count | MAE | Bucket | Pairwise | MAE reduction | Bucket delta | Pairwise delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        "| Anchor | "
        + " | ".join(
            [
                _escape(metrics.get("count")),
                _escape(anchor.get("mae")),
                _escape(anchor.get("bucket_accuracy")),
                _escape(anchor.get("pairwise_accuracy")),
                "",
                "",
                "",
            ]
        )
        + " |",
        "| Adjusted | "
        + " | ".join(
            [
                _escape(metrics.get("count")),
                _escape(adjusted.get("mae")),
                _escape(adjusted.get("bucket_accuracy")),
                _escape(adjusted.get("pairwise_accuracy")),
                _escape(delta.get("mae_reduction")),
                _escape(delta.get("bucket_delta")),
                _escape(delta.get("pairwise_delta")),
            ]
        )
        + " |",
    ]


def _row_table(
    rows: Sequence[Mapping[str, object]],
    *,
    include_policy: bool,
) -> list[str]:
    headers = [
        "Label",
        "Expected",
        "Anchor",
        "Adjusted",
        "Anchor Err",
        "Adj Err",
        "Dir",
        "Rank",
        "Freq",
        "Tail80",
        "Unranked",
        "DomainCov",
        "JLPT",
        "JLPTCore",
    ]
    if include_policy:
        headers.extend(["Reason", "Floor", "Changed"])
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        signals = _mapping(row.get("signals"))
        values = [
            _escape(row.get("label")),
            _escape(row.get("expected")),
            _escape(row.get("anchor_observed")),
            _escape(row.get("adjusted_observed")),
            _escape(row.get("anchor_abs_error")),
            _escape(row.get("adjusted_abs_error")),
            f"`{_escape(row.get('anchor_direction'))}`",
            _escape(row.get("core_rank")),
            _escape(signals.get("frequency")),
            _escape(signals.get("frequency_tail80")),
            _escape(signals.get("frequency_unranked_risk")),
            _escape(signals.get("bccwj_domain_rank_coverage")),
            _escape(signals.get("jlpt_vocab_difficulty")),
            _escape(signals.get("jlpt_vocab_beginner_core")),
        ]
        if include_policy:
            values.extend(
                [
                    f"`{_escape(row.get('policy_reason'))}`",
                    _escape(row.get("policy_floor")),
                    f"`{_escape(row.get('changed'))}`",
                ]
            )
        lines.append("| " + " | ".join(str(value) for value in values) + " |")
    return lines


def _float_signal(signals: Mapping[str, object], signal: str) -> float:
    value = signals.get(signal)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _optional_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float("nan")


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
