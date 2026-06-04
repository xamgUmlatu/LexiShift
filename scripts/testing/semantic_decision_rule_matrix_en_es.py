#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from semantic_decision_rule_matrix_common import (
    DEFAULT_DATASET,
    DEFAULT_JSON_OUT,
    DEFAULT_MANIFEST,
    DEFAULT_MARKDOWN_OUT,
    _load_json,
    _resolve_project_path,
)
from semantic_decision_rule_matrix_data import (
    _build_input_fingerprint,
    _load_matrix_dataset,
    _manifest_rows,
    _matrix_dataset_for_config,
    _merge_defaults,
    _source_evidence_scope_id,
    _source_evidence_scope_rows,
)
from semantic_decision_rule_matrix_eval import (
    _build_source_dropout_rows,
    _build_threshold_sensitivity_rows,
    _evaluate_config,
)
from semantic_decision_rule_matrix_metrics import _rank_key, _select_incumbent
from semantic_decision_rule_matrix_rendering import render_decision_rule_matrix_markdown
from semantic_decision_rule_matrix_summary import (
    _build_best_by_constraint,
    _build_decision_signature_summary,
    _build_family_bakeoff_summary,
    _build_incumbent_delta_summary,
    _build_metric_tie_summary,
    _build_negative_control_summary,
    _build_overfitting_checks,
    _build_recommendation,
    _build_selection_validation_summary,
)


def build_decision_rule_matrix_report(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> dict[str, object]:
    manifest = _load_json(manifest_path)
    dataset_path = _resolve_project_path(manifest.get("dataset_path"), default=DEFAULT_DATASET)
    base_dataset = _load_matrix_dataset(
        manifest,
        default_dataset_path=dataset_path,
        apply_source_evidence=False,
    )
    dataset_cache: dict[tuple[tuple[str, ...], str, int], dict[str, object]] = {}
    dataset = _matrix_dataset_for_config(
        base_dataset=base_dataset,
        manifest=manifest,
        config={},
        cache=dataset_cache,
    )
    defaults = manifest.get("defaults") if isinstance(manifest.get("defaults"), Mapping) else {}
    rows = _manifest_rows(manifest)
    include_case_results = bool(manifest.get("include_case_results", True))
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    config_rows: list[dict[str, object]] = []
    case_results: list[dict[str, object]] = []
    threshold_sensitivity: list[dict[str, object]] = []
    source_dropout: list[dict[str, object]] = []

    for manifest_index, raw_config in enumerate(rows):
        config = _merge_defaults(defaults, raw_config)
        config["manifest_index"] = manifest_index
        config_dataset = _matrix_dataset_for_config(
            base_dataset=base_dataset,
            manifest=manifest,
            config=config,
            cache=dataset_cache,
        )
        config["source_evidence_scope_id"] = _source_evidence_scope_id(
            manifest=manifest,
            config=config,
        )
        config["source_evidence_batches"] = list(
            config_dataset.get("source_evidence_batches") or ()
        )
        config_row, config_cases = _evaluate_config(dataset=config_dataset, config=config)
        config_rows.append(config_row)
        case_results.extend(config_cases)

        if bool(config.get("threshold_sensitivity")):
            threshold_sensitivity.extend(
                _build_threshold_sensitivity_rows(dataset=config_dataset, config=config)
            )
        if bool(config.get("source_dropout")):
            source_dropout.extend(_build_source_dropout_rows(dataset=config_dataset, config=config))

    config_rows.sort(key=_rank_key)
    incumbent = _select_incumbent(config_rows)
    report = {
        "schema_version": 1,
        "status": "ok",
        "matrix_id": str(manifest.get("matrix_id") or "semantic_decision_rule_matrix_en_es"),
        "generated_at": generated_at,
        "manifest_path": str(manifest_path),
        "dataset_path": str(dataset_path),
        "evaluation_suites": list(dataset.get("evaluation_suites") or ()),
        "source_evidence_batches": list(dataset.get("source_evidence_batches") or ()),
        "source_evidence_scopes": _source_evidence_scope_rows(dataset_cache),
        "pair": str(dataset.get("pair") or "").strip(),
        "dataset_id": str(dataset.get("dataset_id") or "").strip(),
        "input_fingerprint": _build_input_fingerprint(
            manifest_path=manifest_path,
            dataset_path=dataset_path,
            dataset=dataset,
            source_evidence_scopes=_source_evidence_scope_rows(dataset_cache),
        ),
        "row_count": len(config_rows),
        "case_result_count": len(case_results),
        "case_results_omitted": not include_case_results,
        "config_rows": config_rows,
        "case_results": case_results if include_case_results else [],
        "best_by_constraint": _build_best_by_constraint(config_rows, incumbent=incumbent),
        "family_bakeoff_summary": _build_family_bakeoff_summary(
            config_rows,
            incumbent=incumbent,
        ),
        "decision_signature_summary": _build_decision_signature_summary(config_rows),
        "metric_tie_summary": _build_metric_tie_summary(config_rows),
        "selection_validation_summary": _build_selection_validation_summary(
            config_rows,
            incumbent=incumbent,
        ),
        "incumbent_delta_summary": _build_incumbent_delta_summary(
            config_rows,
            case_results,
            incumbent=incumbent,
        ),
        "negative_control_summary": _build_negative_control_summary(
            config_rows,
            incumbent=incumbent,
        ),
        "overfitting_checks": _build_overfitting_checks(
            config_rows,
            case_results,
            defaults=defaults,
        ),
        "threshold_sensitivity": threshold_sensitivity,
        "source_dropout": source_dropout,
    }
    report["recommendation"] = _build_recommendation(report)
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare decomposed en-es semantic decision-rule configurations offline.",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_decision_rule_matrix_report(manifest_path=args.manifest)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_decision_rule_matrix_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
