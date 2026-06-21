#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMPONENT_MATRIX = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_signal_sweep_en_ja_source_arbitration_surface_s010_component_matrix_latest.npz"
)
DEFAULT_AUDIT_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_constituent_transparency_audit_en_ja_latest.json"
)
DEFAULT_LABELS_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_learner_difficulty_constituent_transparency_review_labels_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_constituent_transparency_label_eval_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_constituent_transparency_label_eval_en_ja_latest.md"
)
SCALAR_FIELDS = (
    "guarded_transparency_score",
    "reading_compositionality",
    "domain_marked_risk",
    "tail",
    "written",
    "min_knownness",
)
ACCEPT_DECISION = "accept_auto_downshift"
OPACITY_GATE_SIGNALS = (
    "jmdict_reading_form_ambiguity",
    "common_restriction_complexity_risk",
    "jmdict_no_kanji_reading_flag",
    "jmdict_restriction_complexity_risk",
    "jmdict_restriction_count",
    "jmdict_kana_preferred_flag",
    "jmdict_field_marked_flag",
    "jmdict_register_domain_flag",
    "jmdict_marked_usage_flag",
    "jmdict_sense_info_flag",
    "jmdict_cross_reference_flag",
    "jmdict_search_only_form_flag",
    "jmdict_dialect_flag",
    "jmdict_reading_form_marked_flag",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate reviewed labels for the en-ja constituent-transparency difficulty sidecar."
        )
    )
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--labels-json", type=Path, default=DEFAULT_LABELS_JSON)
    parser.add_argument("--component-matrix", type=Path, default=DEFAULT_COMPONENT_MATRIX)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        audit_json_path=_resolve_path(args.audit_json),
        labels_json_path=_resolve_path(args.labels_json),
        component_matrix_path=_resolve_path(args.component_matrix),
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
    audit_json_path: Path,
    labels_json_path: Path,
    component_matrix_path: Path,
) -> dict[str, object]:
    audit = _load_json(audit_json_path)
    labels_payload = _load_json(labels_json_path)
    rows = joined_rows(audit=audit, labels_payload=labels_payload)
    decision_counts = Counter(str(row.get("decision") or "") for row in rows)
    allowed_count = sum(1 for row in rows if bool(row.get("automatic_downshift_allowed")))
    blocked_count = int(decision_counts.get("block_auto_downshift", 0))
    review_count = int(decision_counts.get("hold_review_lane", 0))
    accepted_count = int(decision_counts.get(ACCEPT_DECISION, 0))
    scalar_rules = [
        best_scalar_rule(rows=rows, field=field)
        for field in SCALAR_FIELDS
        if any(field in row for row in rows)
    ]
    source_contrast = source_signal_contrast(
        rows=rows,
        component_matrix_path=component_matrix_path,
    )
    opacity_gate_search = opacity_gate_search_report(
        rows=rows,
        component_matrix_path=component_matrix_path,
    )
    best_gate = _mapping(opacity_gate_search.get("best_precision_gate"))
    return {
        "schema_version": 1,
        "inputs": {
            "audit_json": _repo_path(audit_json_path),
            "labels_json": _repo_path(labels_json_path),
            "component_matrix": _repo_path(component_matrix_path),
        },
        "summary": {
            "reviewed_rows": len(rows),
            "decision_counts": dict(sorted(decision_counts.items())),
            "automatic_downshift_allowed": allowed_count,
            "automatic_downshift_held_or_blocked": len(rows) - allowed_count,
            "current_candidate_strict_precision": _rounded(accepted_count / len(rows)),
            "current_candidate_hard_false_positive_rate": _rounded(blocked_count / len(rows)),
            "current_candidate_review_lane_rate": _rounded(review_count / len(rows)),
            "simple_scalar_fields_tested": len(scalar_rules),
            "simple_scalar_perfect_separator_found": any(
                bool(rule.get("perfect_separator")) for rule in scalar_rules
            ),
            "opacity_gate_signals_tested": opacity_gate_search.get("signals_tested", 0),
            "opacity_gate_candidates_tested": opacity_gate_search.get("candidates_tested", 0),
            "best_opacity_gate_precision": best_gate.get("precision"),
            "best_opacity_gate_recall": best_gate.get("recall"),
            "best_opacity_gate_f1": best_gate.get("f1"),
            "best_opacity_gate_selected": best_gate.get("selected"),
            "best_opacity_gate_false_positives": best_gate.get("false_positives"),
            "best_opacity_gate_false_negatives": best_gate.get("false_negatives"),
            "best_opacity_gate_hard_blocks_left": best_gate.get("hard_blocks_left"),
        },
        "scalar_rules": scalar_rules,
        "source_signal_contrast": source_contrast,
        "opacity_gate_search": opacity_gate_search,
        "rows": rows,
        "interpretation": [
            (
                "The reviewed labels confirm that the guarded constituent rule "
                "has real positives, but the current candidate would still touch "
                "many rows that the review kept out of automatic promotion."
            ),
            (
                "The scalar fields overlap between accepted and held/blocked "
                "rows, so another one-dimensional threshold over the current "
                "numbers is unlikely to solve the semantic/domain opacity issue."
            ),
            (
                "The next useful model shape is a review or opacity lane for "
                "plant/species, material/object, cultural-object, idiom, and "
                "register-sensitive rows, not another broad transparency scalar."
            ),
            (
                "Source-column contrast points at candidate opacity features, "
                "but these should be tested as a narrow held-row gate rather "
                "than assumed to be globally safe."
            ),
            (
                "The best reviewed-set opacity gate improves precision, but it "
                "also loses accepted rows. That makes it promising as a search "
                "dimension, not yet a promotion-ready hard rule."
            ),
        ],
    }


def joined_rows(
    *,
    audit: Mapping[str, object],
    labels_payload: Mapping[str, object],
) -> list[dict[str, object]]:
    audit_rows = _rows(_mapping(audit.get("review_pack")).get("would_change_examples"))
    label_rows = _rows(labels_payload.get("labels"))
    labels_by_key = {
        (str(row.get("lemma") or ""), str(row.get("reading") or "")): row for row in label_rows
    }
    joined = []
    missing_labels = []
    for index, audit_row in enumerate(audit_rows, start=1):
        key = (str(audit_row.get("lemma") or ""), str(audit_row.get("reading") or ""))
        label = labels_by_key.get(key)
        if label is None:
            missing_labels.append("/".join(key))
            continue
        joined.append(
            {
                "review_row_number": int(label.get("review_row_number") or index),
                "lemma": key[0],
                "reading": key[1],
                "decision": str(label.get("decision") or ""),
                "automatic_downshift_allowed": bool(label.get("automatic_downshift_allowed")),
                "anchor_observed": _optional_float(audit_row.get("anchor_observed")),
                "policy_ceiling": _optional_float(audit_row.get("policy_ceiling")),
                "guarded_transparency_score": _optional_float(
                    audit_row.get("guarded_transparency_score")
                ),
                "reading_compositionality": _optional_float(
                    audit_row.get("reading_compositionality")
                ),
                "domain_marked_risk": _optional_float(audit_row.get("domain_marked_risk")),
                "tail": _optional_float(audit_row.get("tail")),
                "written": _optional_float(audit_row.get("written")),
                "min_knownness": _optional_float(audit_row.get("min_knownness")),
                "rationale": str(label.get("rationale") or ""),
            }
        )
    extra_labels = sorted(
        "/".join(key)
        for key in set(labels_by_key)
        - {(str(row.get("lemma") or ""), str(row.get("reading") or "")) for row in audit_rows}
    )
    if missing_labels or extra_labels:
        raise ValueError(
            f"Label/audit mismatch: missing_labels={missing_labels}, extra_labels={extra_labels}"
        )
    return joined


def best_scalar_rule(*, rows: Sequence[Mapping[str, object]], field: str) -> dict[str, object]:
    values = sorted({_optional_float(row.get(field)) for row in rows})
    values = [value for value in values if value is not None]
    candidates = []
    for direction in ("gte", "lte"):
        for threshold in values:
            selected = [
                row
                for row in rows
                if _matches_threshold(
                    value=_optional_float(row.get(field)),
                    threshold=threshold,
                    direction=direction,
                )
            ]
            candidates.append(
                scalar_rule_metrics(
                    rows=rows,
                    selected=selected,
                    field=field,
                    direction=direction,
                    threshold=threshold,
                )
            )
    best = max(
        candidates,
        key=lambda item: (
            float(item.get("f1") or 0.0),
            float(item.get("precision") or 0.0),
            float(item.get("recall") or 0.0),
            -int(item.get("false_positives") or 0),
        ),
    )
    accept_values = [
        _optional_float(row.get(field))
        for row in rows
        if str(row.get("decision") or "") == ACCEPT_DECISION
    ]
    reject_values = [
        _optional_float(row.get(field))
        for row in rows
        if str(row.get("decision") or "") != ACCEPT_DECISION
    ]
    accept_values = [value for value in accept_values if value is not None]
    reject_values = [value for value in reject_values if value is not None]
    perfect = False
    if accept_values and reject_values:
        perfect = max(accept_values) < min(reject_values) or min(accept_values) > max(reject_values)
    return {
        "field": field,
        "perfect_separator": perfect,
        "accept_range": _range_summary(accept_values),
        "non_accept_range": _range_summary(reject_values),
        "best_f1_rule": best,
    }


def source_signal_contrast(
    *,
    rows: Sequence[Mapping[str, object]],
    component_matrix_path: Path,
    limit: int = 20,
) -> list[dict[str, object]]:
    if not component_matrix_path.exists():
        return []
    payload = np.load(component_matrix_path, allow_pickle=False)
    names = [str(value) for value in payload["component_names"]]
    lemmas = [str(value) for value in payload["lemmas"]]
    readings = [str(value) for value in payload["readings"]]
    values = np.asarray(payload["component_values"], dtype=np.float32)
    present = np.asarray(payload["component_present"], dtype=bool)
    index_by_key = {
        (lemma, reading): index
        for index, (lemma, reading) in enumerate(zip(lemmas, readings, strict=False))
    }
    row_indexes = []
    for row in rows:
        key = (str(row.get("lemma") or ""), str(row.get("reading") or ""))
        if key in index_by_key:
            row_indexes.append((row, index_by_key[key]))
    accept = [(row, index) for row, index in row_indexes if _is_accept(row)]
    non_accept = [(row, index) for row, index in row_indexes if not _is_accept(row)]
    blocked = [
        (row, index)
        for row, index in row_indexes
        if str(row.get("decision") or "") == "block_auto_downshift"
    ]
    items = []
    for column, name in enumerate(names):
        accept_values = _nonzero_component_values(
            accept, values=values, present=present, column=column
        )
        non_accept_values = _nonzero_component_values(
            non_accept,
            values=values,
            present=present,
            column=column,
        )
        blocked_values = _nonzero_component_values(
            blocked, values=values, present=present, column=column
        )
        if not accept_values and not non_accept_values:
            continue
        accept_rate = len(accept_values) / len(accept) if accept else 0.0
        non_accept_rate = len(non_accept_values) / len(non_accept) if non_accept else 0.0
        blocked_rate = len(blocked_values) / len(blocked) if blocked else 0.0
        rate_delta = non_accept_rate - accept_rate
        if non_accept_rate < 0.25 or rate_delta < 0.20:
            continue
        items.append(
            {
                "signal": name,
                "accept_present": len(accept_values),
                "non_accept_present": len(non_accept_values),
                "blocked_present": len(blocked_values),
                "accept_rate": _rounded(accept_rate),
                "non_accept_rate": _rounded(non_accept_rate),
                "blocked_rate": _rounded(blocked_rate),
                "rate_delta": _rounded(rate_delta),
                "accept_mean": _rounded(_mean(accept_values)),
                "non_accept_mean": _rounded(_mean(non_accept_values)),
            }
        )
    return sorted(
        items,
        key=lambda item: (
            float(item.get("rate_delta") or 0.0),
            float(item.get("non_accept_rate") or 0.0),
            float(item.get("blocked_rate") or 0.0),
        ),
        reverse=True,
    )[:limit]


def opacity_gate_search_report(
    *,
    rows: Sequence[Mapping[str, object]],
    component_matrix_path: Path,
    max_combo_size: int = 4,
    limit: int = 20,
) -> dict[str, object]:
    feature_rows = rows_with_source_features(
        rows=rows,
        component_matrix_path=component_matrix_path,
        signals=OPACITY_GATE_SIGNALS,
    )
    signals = [
        signal
        for signal in OPACITY_GATE_SIGNALS
        if any(bool(row.get("source_features", {}).get(signal)) for row in feature_rows)
    ]
    candidates = []
    for size in range(1, max_combo_size + 1):
        for combo in combinations(signals, size):
            candidates.append(opacity_gate_metrics(feature_rows, combo))
    candidates.sort(key=gate_sort_key, reverse=True)
    recall_candidates = [item for item in candidates if float(item.get("recall") or 0.0) >= 0.8]
    no_hard_block_candidates = [
        item for item in candidates if int(item.get("hard_blocks_left") or 0) == 0
    ]
    best_precision_gate = candidates[0] if candidates else {}
    best_high_recall_gate = recall_candidates[0] if recall_candidates else {}
    best_no_hard_block_gate = no_hard_block_candidates[0] if no_hard_block_candidates else {}
    return {
        "signals_tested": len(signals),
        "signals": list(signals),
        "max_combo_size": max_combo_size,
        "candidates_tested": len(candidates),
        "best_precision_gate": best_precision_gate,
        "best_high_recall_gate": best_high_recall_gate,
        "best_no_hard_block_gate": best_no_hard_block_gate,
        "top_gates": candidates[:limit],
    }


def rows_with_source_features(
    *,
    rows: Sequence[Mapping[str, object]],
    component_matrix_path: Path,
    signals: Sequence[str],
) -> list[dict[str, object]]:
    if not component_matrix_path.exists():
        return [dict(row) | {"source_features": {}} for row in rows]
    payload = np.load(component_matrix_path, allow_pickle=False)
    names = [str(value) for value in payload["component_names"]]
    name_to_column = {name: index for index, name in enumerate(names)}
    lemmas = [str(value) for value in payload["lemmas"]]
    readings = [str(value) for value in payload["readings"]]
    values = np.asarray(payload["component_values"], dtype=np.float32)
    present = np.asarray(payload["component_present"], dtype=bool)
    index_by_key = {
        (lemma, reading): index
        for index, (lemma, reading) in enumerate(zip(lemmas, readings, strict=False))
    }
    output = []
    for row in rows:
        key = (str(row.get("lemma") or ""), str(row.get("reading") or ""))
        row_index = index_by_key.get(key)
        features = {}
        for signal in signals:
            column = name_to_column.get(signal)
            features[signal] = (
                row_index is not None
                and column is not None
                and bool(present[row_index, column])
                and float(values[row_index, column]) != 0.0
            )
        output.append(dict(row) | {"source_features": features})
    return output


def opacity_gate_metrics(
    rows: Sequence[Mapping[str, object]],
    signals: Sequence[str],
) -> dict[str, object]:
    selected = []
    gated = []
    for row in rows:
        features = _mapping(row.get("source_features"))
        gate = any(bool(features.get(signal)) for signal in signals)
        if gate:
            gated.append(row)
        else:
            selected.append(row)
    selected_ids = {id(row) for row in selected}
    tp = sum(1 for row in selected if _is_accept(row))
    fp = len(selected) - tp
    fn = sum(1 for row in rows if id(row) not in selected_ids and _is_accept(row))
    tn = len(rows) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "signals": list(signals),
        "selected": len(selected),
        "gated": len(gated),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "hard_blocks_left": sum(
            1 for row in selected if str(row.get("decision") or "") == "block_auto_downshift"
        ),
        "hard_blocks_gated": sum(
            1 for row in gated if str(row.get("decision") or "") == "block_auto_downshift"
        ),
        "precision": _rounded(precision),
        "recall": _rounded(recall),
        "f1": _rounded(f1),
        "lost_accepted": [
            entry_label(row) for row in gated if str(row.get("decision") or "") == ACCEPT_DECISION
        ],
        "remaining_non_accepts": [
            entry_label(row)
            for row in selected
            if str(row.get("decision") or "") != ACCEPT_DECISION
        ],
    }


def gate_sort_key(item: Mapping[str, object]) -> tuple[float, float, float, int, int, int]:
    return (
        float(item.get("precision") or 0.0),
        float(item.get("f1") or 0.0),
        float(item.get("recall") or 0.0),
        -int(item.get("hard_blocks_left") or 0),
        -int(item.get("false_negatives") or 0),
        -int(item.get("false_positives") or 0),
    )


def scalar_rule_metrics(
    *,
    rows: Sequence[Mapping[str, object]],
    selected: Sequence[Mapping[str, object]],
    field: str,
    direction: str,
    threshold: float,
) -> dict[str, object]:
    selected_ids = {id(row) for row in selected}
    tp = sum(1 for row in selected if str(row.get("decision") or "") == ACCEPT_DECISION)
    fp = len(selected) - tp
    fn = sum(
        1
        for row in rows
        if id(row) not in selected_ids and str(row.get("decision") or "") == ACCEPT_DECISION
    )
    tn = len(rows) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "field": field,
        "direction": direction,
        "threshold": _rounded(threshold),
        "selected": len(selected),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": _rounded(precision),
        "recall": _rounded(recall),
        "specificity": _rounded(specificity),
        "f1": _rounded(f1),
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _mapping(report.get("summary"))
    lines = [
        "# SRS Learner Difficulty Constituent Transparency Label Eval (en-ja)",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in (
        "reviewed_rows",
        "automatic_downshift_allowed",
        "automatic_downshift_held_or_blocked",
        "current_candidate_strict_precision",
        "current_candidate_hard_false_positive_rate",
        "current_candidate_review_lane_rate",
        "simple_scalar_fields_tested",
        "simple_scalar_perfect_separator_found",
        "opacity_gate_signals_tested",
        "opacity_gate_candidates_tested",
        "best_opacity_gate_precision",
        "best_opacity_gate_recall",
        "best_opacity_gate_f1",
        "best_opacity_gate_selected",
        "best_opacity_gate_false_positives",
        "best_opacity_gate_false_negatives",
        "best_opacity_gate_hard_blocks_left",
    ):
        lines.append(f"| `{key}` | {_escape(summary.get(key))} |")
    lines.extend(
        [
            "",
            "Decision counts:",
            "",
            "| Decision | Rows |",
            "|---|---:|",
        ]
    )
    for decision, count in sorted(_mapping(summary.get("decision_counts")).items()):
        lines.append(f"| `{decision}` | {_escape(count)} |")
    lines.extend(
        [
            "",
            "## Scalar Separability",
            "",
            "| Field | Perfect separator | Accept range | Non-accept range | Best rule | Precision | Recall | F1 | FP | FN |",
            "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for rule in _rows(report.get("scalar_rules")):
        best = _mapping(rule.get("best_f1_rule"))
        best_label = (
            f"{best.get('field')} {best.get('direction')} "
            f"{best.get('threshold')} ({best.get('selected')} selected)"
        )
        lines.append(
            "| "
            f"`{_escape(rule.get('field'))}` | "
            f"{_escape(rule.get('perfect_separator'))} | "
            f"{_escape(_range_label(rule.get('accept_range')))} | "
            f"{_escape(_range_label(rule.get('non_accept_range')))} | "
            f"`{_escape(best_label)}` | "
            f"{_escape(best.get('precision'))} | "
            f"{_escape(best.get('recall'))} | "
            f"{_escape(best.get('f1'))} | "
            f"{_escape(best.get('false_positives'))} | "
            f"{_escape(best.get('false_negatives'))} |"
        )
    contrast = _rows(report.get("source_signal_contrast"))
    if contrast:
        lines.extend(
            [
                "",
                "## Source Signal Contrast",
                "",
                "Signals shown here are more common in held/blocked rows than in accepted rows. They are candidate opacity-lane features, not promotion rules.",
                "",
                "| Signal | Accept present | Non-accept present | Blocked present | Accept rate | Non-accept rate | Delta | Mean accepted | Mean non-accepted |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for item in contrast:
            lines.append(
                "| "
                f"`{_escape(item.get('signal'))}` | "
                f"{_escape(item.get('accept_present'))} | "
                f"{_escape(item.get('non_accept_present'))} | "
                f"{_escape(item.get('blocked_present'))} | "
                f"{_escape(item.get('accept_rate'))} | "
                f"{_escape(item.get('non_accept_rate'))} | "
                f"{_escape(item.get('rate_delta'))} | "
                f"{_escape(item.get('accept_mean'))} | "
                f"{_escape(item.get('non_accept_mean'))} |"
            )
    gate_search = _mapping(report.get("opacity_gate_search"))
    top_gates = _rows(gate_search.get("top_gates"))
    if top_gates:
        lines.extend(
            [
                "",
                "## Opacity Gate Search",
                "",
                "Each gate holds a row out of automatic downshift when any listed source-backed opacity signal is present. This is a reviewed-set diagnostic, not a runtime rule.",
                "",
                "| Rank | Signals | Selected | Precision | Recall | F1 | FP | FN | Hard blocks left | Lost accepted | Remaining non-accepts |",
                "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
            ]
        )
        for rank, item in enumerate(top_gates[:10], start=1):
            signals = ", ".join(f"`{signal}`" for signal in _rows(item.get("signals")))
            lines.append(
                "| "
                f"{rank} | "
                f"{signals} | "
                f"{_escape(item.get('selected'))} | "
                f"{_escape(item.get('precision'))} | "
                f"{_escape(item.get('recall'))} | "
                f"{_escape(item.get('f1'))} | "
                f"{_escape(item.get('false_positives'))} | "
                f"{_escape(item.get('false_negatives'))} | "
                f"{_escape(item.get('hard_blocks_left'))} | "
                f"{_escape(', '.join(str(value) for value in _rows(item.get('lost_accepted'))))} | "
                f"{_escape(', '.join(str(value) for value in _rows(item.get('remaining_non_accepts'))))} |"
            )
    lines.extend(["", "## Interpretation", ""])
    for item in _rows(report.get("interpretation")):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Reviewed Rows",
            "",
            "| # | Entry | Decision | Auto downshift | Anchor | Guarded | Domain risk | Rationale |",
            "|---:|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in _rows(report.get("rows")):
        entry = f"{row.get('lemma')}/{row.get('reading')}"
        lines.append(
            "| "
            f"{_escape(row.get('review_row_number'))} | "
            f"{_escape(entry)} | "
            f"`{_escape(row.get('decision'))}` | "
            f"{_escape(row.get('automatic_downshift_allowed'))} | "
            f"{_escape(row.get('anchor_observed'))} | "
            f"{_escape(row.get('guarded_transparency_score'))} | "
            f"{_escape(row.get('domain_marked_risk'))} | "
            f"{_escape(row.get('rationale'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, dict) else {}


def _rows(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _matches_threshold(
    *,
    value: float | None,
    threshold: float,
    direction: str,
) -> bool:
    if value is None:
        return False
    if direction == "gte":
        return value >= threshold
    return value <= threshold


def _is_accept(row: Mapping[str, object]) -> bool:
    return str(row.get("decision") or "") == ACCEPT_DECISION


def entry_label(row: Mapping[str, object]) -> str:
    return f"{row.get('lemma')}/{row.get('reading')}"


def _nonzero_component_values(
    row_indexes: Sequence[tuple[Mapping[str, object], int]],
    *,
    values: np.ndarray,
    present: np.ndarray,
    column: int,
) -> list[float]:
    output = []
    for _, row_index in row_indexes:
        if bool(present[row_index, column]):
            value = float(values[row_index, column])
            if value != 0.0:
                output.append(value)
    return output


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _range_summary(values: Sequence[float]) -> dict[str, object]:
    if not values:
        return {"min": None, "max": None}
    return {"min": _rounded(min(values)), "max": _rounded(max(values))}


def _range_label(value: object) -> str:
    payload = _mapping(value)
    return f"{payload.get('min')}..{payload.get('max')}"


def _rounded(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _escape(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
