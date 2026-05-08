#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_support import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    build_sentence_veto_report,
)


TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
SEMANTIC_CASES_ROOT = TEST_INPUTS_ROOT / "semantic_routing_cases"
DEFAULT_BASE_DATASET = SEMANTIC_CASES_ROOT / "en_es_sentence_veto_v10.json"
DEFAULT_REPRESENTATIVE_FRAME = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_representative_frame_en_es_latest.json"
)
DEFAULT_SOURCE_CONFIG_REPORT = TEST_OUTPUTS_ROOT / "semantic_routing_sentence_veto_latest.json"
DEFAULT_DATASET_OUT = SEMANTIC_CASES_ROOT / "en_es_sampling_stage1_representative_v1.json"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_representative_scoring_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_representative_scoring_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build and score the filled Stage 1 representative semantic-veto frame "
            "as a sentence-veto dataset. This changes no runtime policy."
        )
    )
    parser.add_argument("--base-dataset", type=Path, default=DEFAULT_BASE_DATASET)
    parser.add_argument("--representative-frame", type=Path, default=DEFAULT_REPRESENTATIVE_FRAME)
    parser.add_argument("--source-config-report", type=Path, default=DEFAULT_SOURCE_CONFIG_REPORT)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    base_dataset = _load_json(args.base_dataset)
    representative_frame = _load_json(args.representative_frame)
    source_config_report = _load_json(args.source_config_report)
    dataset, dataset_summary = build_stage1_representative_sentence_veto_dataset(
        base_dataset=base_dataset,
        representative_frame=representative_frame,
        base_dataset_path=args.base_dataset,
        representative_frame_path=args.representative_frame,
        dataset_out_path=args.dataset_out,
    )
    args.dataset_out.parent.mkdir(parents=True, exist_ok=True)
    args.dataset_out.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = build_stage1_representative_scoring_report(
        dataset_summary=dataset_summary,
        dataset_path=args.dataset_out,
        source_config_report=source_config_report,
        source_config_report_path=args.source_config_report,
        generated_at=_utc_now(),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_stage1_representative_scoring_markdown(report), encoding="utf-8"
    )
    print(f"Wrote representative dataset artifact to {args.dataset_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_stage1_representative_sentence_veto_dataset(
    *,
    base_dataset: Mapping[str, object],
    representative_frame: Mapping[str, object],
    base_dataset_path: Path | None = None,
    representative_frame_path: Path | None = None,
    dataset_out_path: Path | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    if generated_at is None:
        generated_at = _utc_now()
    base_families = {
        str(family.get("family_id") or "").strip(): family
        for family in _mapping_rows(base_dataset.get("families"))
        if str(family.get("family_id") or "").strip()
    }
    base_cases: dict[str, Mapping[str, object]] = {}
    for family in base_families.values():
        for case in _mapping_rows(family.get("cases")):
            case_id = str(case.get("case_id") or "").strip()
            if case_id:
                base_cases[case_id] = case

    issues: list[str] = []
    grouped_cases: dict[str, list[dict[str, object]]] = defaultdict(list)
    for frame_row in _mapping_rows(representative_frame.get("rows")):
        if not bool(frame_row.get("selected_for_locked_eval")):
            continue
        family_id = str(frame_row.get("family_id") or "").strip()
        if family_id not in base_families:
            issues.append(f"missing_base_family:{family_id}")
            continue
        case = _case_from_frame_row(frame_row=frame_row, base_cases=base_cases)
        if not case.get("gold_winner"):
            issues.append(f"missing_gold_winner:{case.get('case_id', '')}")
            continue
        grouped_cases[family_id].append(case)

    families = []
    for family_id in sorted(grouped_cases):
        base_family = base_families[family_id]
        family_payload = {
            "family_id": family_id,
            "trigger": str(base_family.get("trigger") or "").strip(),
            "active": dict(_as_mapping(base_family.get("active"))),
            "shadows": [dict(row) for row in _mapping_rows(base_family.get("shadows"))],
            "cases": sorted(
                grouped_cases[family_id], key=lambda row: str(row.get("case_id") or "")
            ),
        }
        families.append(family_payload)

    selected_rows = [
        row
        for row in _mapping_rows(representative_frame.get("rows"))
        if bool(row.get("selected_for_locked_eval"))
    ]
    context_source_counts = Counter(str(row.get("context_source") or "") for row in selected_rows)
    review_state_counts = Counter(
        str(row.get("review_state") or "reviewed_or_existing_source") for row in selected_rows
    )
    gold_decision_counts = Counter(str(row.get("gold_decision") or "") for row in selected_rows)
    gold_winner_type_counts = Counter(
        str(row.get("gold_winner_type") or "") for row in selected_rows
    )
    dataset = {
        "schema_version": 1,
        "pair": str(base_dataset.get("pair") or representative_frame.get("pair") or "en-es"),
        "dataset_id": "en_es_sampling_stage1_representative_v1",
        "description": (
            "Stage 1 representative semantic-veto frame materialized as a "
            "sentence-veto dataset for current-policy scoring. Uses existing "
            "v10 family evidence and the frozen 120-row representative frame."
        ),
        "source_frame_id": str(representative_frame.get("frame_id") or ""),
        "generated_at": generated_at,
        "methodology": {
            "runtime_policy_change": "none",
            "threshold_or_scorer_change": "none",
            "family_evidence_source": _repo_path(base_dataset_path),
            "representative_frame_source": _repo_path(representative_frame_path),
            "selection_used_scoring_fields": False,
            "gap_rows_are_agent_draft_human_review_pending": True,
        },
        "families": families,
    }
    summary = {
        "status": "review" if issues else "ok",
        "issues": sorted(set(issues)),
        "dataset_path": _repo_path(dataset_out_path),
        "base_dataset_path": _repo_path(base_dataset_path),
        "representative_frame_path": _repo_path(representative_frame_path),
        "source_frame_id": str(representative_frame.get("frame_id") or ""),
        "source_frame_fingerprint": str(
            _as_mapping(representative_frame.get("summary")).get("frame_fingerprint") or ""
        ),
        "case_count": sum(len(_mapping_rows(family.get("cases"))) for family in families),
        "family_count": len(families),
        "context_source_counts": dict(sorted(context_source_counts.items())),
        "review_state_counts": dict(sorted(review_state_counts.items())),
        "gold_decision_counts": dict(sorted(gold_decision_counts.items())),
        "gold_winner_type_counts": dict(sorted(gold_winner_type_counts.items())),
    }
    return dataset, summary


def build_stage1_representative_scoring_report(
    *,
    dataset_summary: Mapping[str, object],
    dataset_path: Path,
    source_config_report: Mapping[str, object],
    source_config_report_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    issues = list(_sequence(dataset_summary.get("issues")))
    if issues:
        return {
            "schema_version": 1,
            "status": "review",
            "decision": "stage1_representative_dataset_incomplete",
            "generated_at": generated_at,
            "pair": "en-es",
            "dataset_build_summary": dict(dataset_summary),
            "summary": {"issues": issues},
            "row_results": [],
            "next_steps": [
                "Repair dataset materialization issues before scoring the Stage 1 representative frame."
            ],
        }
    config = _as_mapping(source_config_report.get("config"))
    sentence_report = build_sentence_veto_report(
        dataset_path=dataset_path,
        scorer_id=str(config.get("scorer_id") or "tfidf_cosine"),
        model_name=str(config.get("model_name") or "").strip() or None,
        context_view=str(config.get("context_view") or "masked_sentence"),
        evidence_view=str(config.get("evidence_view") or "all_evidence_text"),
        min_active_score=float(config.get("min_active_score") or 0.05),
        min_margin=float(config.get("min_margin") or 0.0),
        phrase_control_mode=str(config.get("phrase_control_mode") or "noun_family_frame_guard"),
        phrase_guard_pos_scope=str(config.get("phrase_guard_pos_scope") or "family_all"),
        active_rescue_mode=str(
            config.get("active_rescue_mode") or "sense_label_near_tie_active_rescue"
        ),
        window_tokens=int(config.get("window_tokens") or 4),
        mask_token=str(config.get("mask_token") or "").strip() or DEFAULT_SENTENCE_VETO_MASK_TOKEN,
    )
    metadata_by_case = _case_metadata_by_id(dataset_path)
    annotated_rows = [
        _annotate_row_result(row, metadata_by_case=metadata_by_case)
        for row in _mapping_rows(sentence_report.get("row_results"))
    ]
    summary = dict(_as_mapping(sentence_report.get("summary")))
    summary.update(
        {
            "issues": [],
            "dataset_case_count": int(dataset_summary.get("case_count") or 0),
            "dataset_family_count": int(dataset_summary.get("family_count") or 0),
            "context_source_counts": dict(
                _as_mapping(dataset_summary.get("context_source_counts"))
            ),
            "review_state_counts": dict(_as_mapping(dataset_summary.get("review_state_counts"))),
        }
    )
    report = {
        **sentence_report,
        "status": "ok",
        "decision": "stage1_representative_current_policy_scored",
        "generated_at": generated_at,
        "dataset_build_summary": dict(dataset_summary),
        "source_config_report_path": _repo_path(source_config_report_path),
        "summary": summary,
        "row_results": annotated_rows,
        "sample_harmful_replace_rows": [
            _annotate_row_result(row, metadata_by_case=metadata_by_case)
            for row in _mapping_rows(sentence_report.get("sample_harmful_replace_rows"))
        ],
        "sample_false_abstain_rows": [
            _annotate_row_result(row, metadata_by_case=metadata_by_case)
            for row in _mapping_rows(sentence_report.get("sample_false_abstain_rows"))
        ],
        "next_steps": [
            "Use this filled-frame score as the representative-proxy lane in product-quality reporting.",
            "Human-review the 25 corpus-like gap rows before using the result for promotion claims.",
            "Prefer observed runtime/browser contexts for the next representative refresh.",
        ],
        "limitations": [
            "stage1_frame_is_representative_proxy_not_final_browsing_distribution",
            "gap_rows_are_agent_draft_human_review_pending",
            "runtime_policy_change_none",
        ],
    }
    return report


def render_stage1_representative_scoring_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    dataset_summary = _as_mapping(report.get("dataset_build_summary"))
    lines = [
        "# en-es Semantic Veto Stage 1 Representative Scoring",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_path', dataset_summary.get('dataset_path', ''))}`",
        f"- Source config: `{report.get('source_config_report_path', '')}`",
        "",
        "## Dataset Build",
        "",
        _dataset_summary_table(dataset_summary),
        "",
        "## Current-Policy Score",
        "",
        _score_summary_table(summary),
        "",
        "## Context Sources",
        "",
        _counter_table(summary.get("context_source_counts")),
        "",
        "## Review States",
        "",
        _counter_table(summary.get("review_state_counts")),
        "",
        "## Gold Winner Types",
        "",
        _gold_winner_type_table(report.get("gold_winner_type_breakdown")),
        "",
        "## Failure Samples",
        "",
        _failure_table(
            report.get("sample_false_abstain_rows"), report.get("sample_harmful_replace_rows")
        ),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _case_from_frame_row(
    *,
    frame_row: Mapping[str, object],
    base_cases: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    source_case_id = str(frame_row.get("source_case_id") or "").strip()
    base_case = _as_mapping(base_cases.get(source_case_id))
    case_id = source_case_id
    if not case_id:
        case_id = str(frame_row.get("row_id") or frame_row.get("frame_row_id") or "").strip()
    gold_winner = str(frame_row.get("gold_winner") or base_case.get("gold_winner") or "").strip()
    slice_tags = _string_list(base_case.get("slice_tags"))
    for tag in _string_list(frame_row.get("slice_tags")):
        if tag not in slice_tags:
            slice_tags.append(tag)
    slice_dimensions = _normalize_slice_dimensions(base_case.get("slice_dimensions"))
    _append_dimension(slice_dimensions, "winner_type", str(frame_row.get("gold_winner_type") or ""))
    _append_dimension(slice_dimensions, "family", str(frame_row.get("trigger") or ""))
    _append_dimension(
        slice_dimensions, "context_source", str(frame_row.get("context_source") or "")
    )
    _append_dimension(slice_dimensions, "source_id", str(frame_row.get("source_id") or ""))
    _append_dimension(slice_dimensions, "frame_row_id", str(frame_row.get("frame_row_id") or ""))
    if bool(frame_row.get("selected_for_locked_eval")):
        _append_dimension(slice_dimensions, "selected_for_locked_eval", "true")
    review_state = str(frame_row.get("review_state") or "").strip()
    if review_state:
        _append_dimension(slice_dimensions, "review_state", review_state)
    case = {
        "case_id": case_id,
        "sentence": str(frame_row.get("sentence") or base_case.get("sentence") or "").strip(),
        "source_phrase": str(
            frame_row.get("trigger") or base_case.get("source_phrase") or ""
        ).strip(),
        "gold_winner": gold_winner,
        "gold_decision": str(
            frame_row.get("gold_decision") or base_case.get("gold_decision") or ""
        ).strip(),
        "slice_tags": slice_tags,
        "slice_dimensions": slice_dimensions,
        "notes": _notes(frame_row=frame_row, base_case=base_case),
    }
    return case


def _annotate_row_result(
    row: Mapping[str, object],
    *,
    metadata_by_case: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    payload = dict(row)
    metadata = _as_mapping(metadata_by_case.get(str(row.get("case_id") or "")))
    for key in (
        "context_source",
        "review_state",
        "source_id",
        "source_frame_id",
        "frame_row_id",
        "selected_for_locked_eval",
    ):
        if key in metadata:
            payload[key] = metadata[key]
    return payload


def _case_metadata_by_id(dataset_path: Path) -> dict[str, dict[str, object]]:
    payload = _load_json(dataset_path)
    metadata_by_case: dict[str, dict[str, object]] = {}
    source_frame_id = str(payload.get("source_frame_id") or "")
    for family in _mapping_rows(payload.get("families")):
        for case in _mapping_rows(family.get("cases")):
            dims = _normalize_slice_dimensions(case.get("slice_dimensions"))
            case_id = str(case.get("case_id") or "").strip()
            if not case_id:
                continue
            metadata_by_case[case_id] = {
                "context_source": _first(dims.get("context_source")),
                "review_state": _first(dims.get("review_state")),
                "source_id": _first(dims.get("source_id")),
                "source_frame_id": source_frame_id,
                "frame_row_id": _first(dims.get("frame_row_id")),
                "selected_for_locked_eval": _first(dims.get("selected_for_locked_eval")) == "true",
            }
    return metadata_by_case


def _notes(*, frame_row: Mapping[str, object], base_case: Mapping[str, object]) -> str:
    values = []
    existing = str(base_case.get("notes") or "").strip()
    if existing:
        values.append(existing)
    frame_row_id = str(frame_row.get("frame_row_id") or "").strip()
    if frame_row_id:
        values.append(f"stage1_frame_row={frame_row_id}")
    context_source = str(frame_row.get("context_source") or "").strip()
    if context_source:
        values.append(f"context_source={context_source}")
    return "; ".join(values)


def _dataset_summary_table(summary: Mapping[str, object]) -> str:
    rows = [
        ("dataset path", summary.get("dataset_path")),
        ("base dataset", summary.get("base_dataset_path")),
        ("representative frame", summary.get("representative_frame_path")),
        ("source frame fingerprint", summary.get("source_frame_fingerprint")),
        ("families", summary.get("family_count")),
        ("cases", summary.get("case_count")),
        ("issues", ", ".join(str(value) for value in _sequence(summary.get("issues"))) or "none"),
    ]
    return _kv_table(rows)


def _score_summary_table(summary: Mapping[str, object]) -> str:
    rows = [
        ("cases", summary.get("cases_total")),
        ("gold replace", summary.get("gold_replace_cases")),
        ("gold abstain", summary.get("gold_abstain_cases")),
        ("predicted replace", summary.get("predicted_replace_cases")),
        ("harmful replacements", summary.get("harmful_replace_count")),
        ("false abstains", summary.get("false_abstain_count")),
        ("decision accuracy", _format_percent(summary.get("decision_accuracy"))),
        ("replace recall", _format_percent(summary.get("replace_recall"))),
        ("harmful replace rate", _format_percent(summary.get("harmful_replace_rate"))),
        ("false abstain rate", _format_percent(summary.get("false_abstain_rate"))),
    ]
    return _kv_table(rows)


def _kv_table(rows: Sequence[tuple[str, object]]) -> str:
    lines = ["| Metric | Value |", "| --- | ---: |"]
    for label, value in rows:
        lines.append(f"| {_escape_md(str(label))} | `{_escape_md(str(value))}` |")
    return "\n".join(lines)


def _counter_table(value: object) -> str:
    mapping = _as_mapping(value)
    if not mapping:
        return "_None._"
    lines = ["| Key | Count |", "| --- | ---: |"]
    for key, count in sorted(mapping.items()):
        lines.append(f"| `{_escape_md(str(key))}` | `{int(count or 0)}` |")
    return "\n".join(lines)


def _gold_winner_type_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_None._"
    lines = [
        "| Type | Cases | Replace Recall | Harmful Replace Rate | False Abstain Rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        summary = _as_mapping(row.get("summary"))
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape_md(str(row.get('gold_winner_type') or ''))}`",
                    f"`{int(summary.get('cases_total') or 0)}`",
                    f"`{_format_percent(summary.get('replace_recall'))}`",
                    f"`{_format_percent(summary.get('harmful_replace_rate'))}`",
                    f"`{_format_percent(summary.get('false_abstain_rate'))}`",
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _failure_table(false_abstains: object, harmful_replacements: object) -> str:
    rows = list(_mapping_rows(false_abstains)) + list(_mapping_rows(harmful_replacements))
    if not rows:
        return "_No sampled failures._"
    lines = [
        "| Case | Trigger | Gold | Predicted | Context Source | Sentence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:20]:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{_escape_md(str(row.get('case_id') or ''))}`",
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_decision') or ''))}`",
                    f"`{_escape_md(str(row.get('predicted_decision') or ''))}`",
                    f"`{_escape_md(str(row.get('context_source') or ''))}`",
                    _escape_md(str(row.get("sentence") or "")),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _append_dimension(dimensions: dict[str, list[str]], key: str, value: str) -> None:
    normalized = str(value or "").strip()
    if not normalized:
        return
    values = dimensions.setdefault(key, [])
    if normalized not in values:
        values.append(normalized)


def _normalize_slice_dimensions(value: object) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): _string_list(raw_values) for key, raw_values in value.items()}


def _string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value if str(item).strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def _first(value: object) -> str:
    values = _string_list(value)
    return values[0] if values else ""


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _format_percent(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
