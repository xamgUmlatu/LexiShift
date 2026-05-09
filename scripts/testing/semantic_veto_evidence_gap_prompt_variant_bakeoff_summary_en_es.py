#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"

VARIANTS = (
    "v5_refresh_control",
    "v6_pos_only",
    "v6_diversity_only",
    "v6_pos_diversity",
)
PRIMARY_VIEW_ID = "no_high_eval_overlap_sentence_only"
COMPARISON_VIEW_IDS = (
    "all_sentence_plus_note",
    "sentence_only_all",
    PRIMARY_VIEW_ID,
    "conservative_sentence_only",
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_prompt_variant_bakeoff_summary_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_prompt_variant_bakeoff_summary_en_es_latest.md"
)
DEFAULT_INPUT_RATE_PER_1M = 0.75
DEFAULT_OUTPUT_RATE_PER_1M = 4.50


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize the en-es semantic-veto active-only prompt-variant bakeoff "
            "from generation, admission, and postprocess artifacts."
        )
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--input-rate-per-1m", type=float, default=DEFAULT_INPUT_RATE_PER_1M)
    parser.add_argument("--output-rate-per-1m", type=float, default=DEFAULT_OUTPUT_RATE_PER_1M)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_prompt_variant_bakeoff_summary_report(
        input_rate_per_1m=args.input_rate_per_1m,
        output_rate_per_1m=args.output_rate_per_1m,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_prompt_variant_bakeoff_summary_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_prompt_variant_bakeoff_summary_report(
    *,
    generation_payloads: Mapping[str, Mapping[str, object]] | None = None,
    admission_payloads: Mapping[str, Mapping[str, object]] | None = None,
    postprocess_payloads: Mapping[str, Mapping[str, object]] | None = None,
    input_rate_per_1m: float = DEFAULT_INPUT_RATE_PER_1M,
    output_rate_per_1m: float = DEFAULT_OUTPUT_RATE_PER_1M,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    generation_payloads = generation_payloads or {
        variant_id: _load_json(_generation_path(variant_id)) for variant_id in VARIANTS
    }
    admission_payloads = admission_payloads or {
        variant_id: _load_json(_admission_path(variant_id)) for variant_id in VARIANTS
    }
    postprocess_payloads = postprocess_payloads or {
        variant_id: _load_json(_postprocess_path(variant_id)) for variant_id in VARIANTS
    }

    rows = [
        _variant_row(
            variant_id=variant_id,
            generation_payload=_as_mapping(generation_payloads.get(variant_id)),
            admission_payload=_as_mapping(admission_payloads.get(variant_id)),
            postprocess_payload=_as_mapping(postprocess_payloads.get(variant_id)),
            input_rate_per_1m=input_rate_per_1m,
            output_rate_per_1m=output_rate_per_1m,
        )
        for variant_id in VARIANTS
    ]
    issues = _issues(rows)
    has_error = any(str(issue.get("severity") or "") == "error" for issue in issues)
    best = _best_primary_candidate(rows)
    return {
        "schema_version": 1,
        "status": "ok" if not has_error else "review",
        "decision": (
            "prompt_variant_bakeoff_ready_for_interpretation"
            if not has_error
            else "prompt_variant_bakeoff_has_review_items"
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "primary_view_id": PRIMARY_VIEW_ID,
        "methodology": {
            "runtime_policy_change": "none",
            "threshold_tuning": "none",
            "raw_llm_output_mutation": "none",
            "same_family_denominator": "all variants use the frozen 24 active-only PoC request packet",
            "primary_comparison_view": PRIMARY_VIEW_ID,
            "cost_rate_source": "rates passed to the live run and this summary",
        },
        "summary": {
            "variant_count": len(rows),
            "issue_count": len(issues),
            "issues": issues,
            "total_estimated_cost_usd": sum(float(row["estimated_cost_usd"]) for row in rows),
            "best_primary_variant_id": best.get("variant_id", ""),
        },
        "variants": rows,
        "best_primary_candidate": best,
        "interpretation": _interpretation(best, rows),
        "limitations": [
            "active-only prompt bakeoff over 24 selected en-es families",
            "postprocess labels are mechanical diagnostics, not human semantic review",
            "this does not test shadow or no-winner generation quality",
            "one variant can have fewer admitted rows if admission rejected raw model output",
            "prompt variants should not change runtime policy without a later locked evaluation pass",
        ],
    }


def render_prompt_variant_bakeoff_summary_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Prompt Variant Bakeoff Summary",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Primary view: `{report.get('primary_view_id', '')}`",
        f"- Best primary variant: `{summary.get('best_primary_variant_id', '')}`",
        f"- Total estimated API cost: `${float(summary.get('total_estimated_cost_usd') or 0.0):.4f}`",
        "",
        "## Primary Results",
        "",
        "| Variant | Generation | Admission | Items | Rejected | Cost | Accuracy | Recall | Harmful | False abstains | Fixed | Regressed |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in _mapping_rows(report.get("variants")):
        primary = _as_mapping(row.get("primary_view"))
        metrics = _as_mapping(primary.get("generated_active_only"))
        changes = _as_mapping(primary.get("case_change_counts"))
        lines.append(
            f"| `{row.get('variant_id', '')}` | `{row.get('generation_status', '')}` | "
            f"`{row.get('admission_status', '')}` | {row.get('admitted_item_count', 0)} | "
            f"{row.get('rejected_item_count', 0)} | "
            f"${float(row.get('estimated_cost_usd') or 0.0):.4f} | "
            f"{_fmt(metrics.get('decision_accuracy'))} | {_fmt(metrics.get('replace_recall'))} | "
            f"{metrics.get('harmful_replace_count', 0)} | "
            f"{metrics.get('false_abstain_count', 0)} | "
            f"{changes.get('fixed', 0)} | {changes.get('regressed', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Mechanical Audit Counts",
            "",
            "| Variant | High eval overlap | POS weak | Definition-like | Target lemma in note | Model POS labels | Model topic labels |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("variants")):
        audit = _as_mapping(row.get("postprocess_audit_summary"))
        lines.append(
            f"| `{row.get('variant_id', '')}` | "
            f"{audit.get('high_eval_overlap_count', 0)} | "
            f"{audit.get('pos_weak_count', 0)} | "
            f"{audit.get('definition_like_count', 0)} | "
            f"{audit.get('target_lemma_in_note_count', 0)} | "
            f"{audit.get('model_source_pos_frame_count', 0)} | "
            f"{audit.get('model_topic_frame_count', 0)} |"
        )
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in report.get("interpretation", ()))
    lines.extend(["", "## Methodology", ""])
    for key, value in _as_mapping(report.get("methodology")).items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _variant_row(
    *,
    variant_id: str,
    generation_payload: Mapping[str, object],
    admission_payload: Mapping[str, object],
    postprocess_payload: Mapping[str, object],
    input_rate_per_1m: float,
    output_rate_per_1m: float,
) -> dict[str, object]:
    generation_summary = _as_mapping(generation_payload.get("summary"))
    admission_summary = _as_mapping(admission_payload.get("summary"))
    postprocess_summary = _as_mapping(postprocess_payload.get("summary"))
    view_scores = _mapping_rows(postprocess_payload.get("view_scores"))
    primary_view = _view_by_id(view_scores, PRIMARY_VIEW_ID)
    input_tokens = int(generation_summary.get("input_tokens") or 0)
    output_tokens = int(generation_summary.get("output_tokens") or 0)
    return {
        "variant_id": variant_id,
        "prompt_id": str(generation_payload.get("prompt_id") or ""),
        "generation_status": str(generation_payload.get("status") or ""),
        "admission_status": str(admission_payload.get("status") or ""),
        "postprocess_status": str(postprocess_payload.get("status") or ""),
        "selected_request_count": int(generation_summary.get("selected_request_count") or 0),
        "accepted_response_count": int(generation_summary.get("accepted_response_count") or 0),
        "accepted_generated_item_count": int(
            generation_summary.get("accepted_generated_item_count") or 0
        ),
        "admitted_item_count": int(admission_summary.get("admitted_item_count") or 0),
        "rejected_item_count": int(admission_summary.get("rejected_item_count") or 0),
        "coverage_shortfall_count": int(admission_summary.get("coverage_shortfall_count") or 0),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": _estimated_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_rate_per_1m=input_rate_per_1m,
            output_rate_per_1m=output_rate_per_1m,
        ),
        "postprocess_audit_summary": {
            "active_item_count": int(postprocess_summary.get("active_item_count") or 0),
            "family_count": int(postprocess_summary.get("family_count") or 0),
            "high_eval_overlap_count": int(postprocess_summary.get("high_eval_overlap_count") or 0),
            "medium_eval_overlap_count": int(
                postprocess_summary.get("medium_eval_overlap_count") or 0
            ),
            "pos_weak_count": int(postprocess_summary.get("pos_weak_count") or 0),
            "definition_like_count": int(postprocess_summary.get("definition_like_count") or 0),
            "target_lemma_in_note_count": int(
                postprocess_summary.get("target_lemma_in_note_count") or 0
            ),
            "model_source_pos_frame_count": int(
                postprocess_summary.get("model_source_pos_frame_count") or 0
            ),
            "model_topic_frame_count": int(postprocess_summary.get("model_topic_frame_count") or 0),
            "high_shadow_confusable_count": int(
                postprocess_summary.get("high_shadow_confusable_count") or 0
            ),
        },
        "primary_view": primary_view,
        "comparison_views": [
            view for view in view_scores if str(view.get("view_id") or "") in COMPARISON_VIEW_IDS
        ],
        "artifact_paths": {
            "generation_json": _repo_path(_generation_path(variant_id)),
            "admission_json": _repo_path(_admission_path(variant_id)),
            "postprocess_json": _repo_path(_postprocess_path(variant_id)),
        },
    }


def _issues(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for row in rows:
        variant_id = str(row.get("variant_id") or "")
        if str(row.get("generation_status") or "") != "ok":
            issues.append(
                {
                    "severity": "error",
                    "variant_id": variant_id,
                    "message": "generation status is not ok",
                }
            )
        if str(row.get("postprocess_status") or "") != "ok":
            issues.append(
                {
                    "severity": "error",
                    "variant_id": variant_id,
                    "message": "postprocess status is not ok",
                }
            )
        if int(row.get("rejected_item_count") or 0) > 0:
            issues.append(
                {
                    "severity": "warn",
                    "variant_id": variant_id,
                    "message": "admission rejected generated items",
                    "rejected_item_count": int(row.get("rejected_item_count") or 0),
                }
            )
    return issues


def _best_primary_candidate(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    sortable = []
    for row in rows:
        primary = _as_mapping(row.get("primary_view"))
        metrics = _as_mapping(primary.get("generated_active_only"))
        changes = _as_mapping(primary.get("case_change_counts"))
        sortable.append(
            (
                int(metrics.get("harmful_replace_count") or 0),
                int(row.get("rejected_item_count") or 0),
                -float(metrics.get("decision_accuracy") or 0.0),
                int(metrics.get("false_abstain_count") or 0),
                -int(changes.get("fixed") or 0),
                str(row.get("variant_id") or ""),
                row,
            )
        )
    if not sortable:
        return {}
    return dict(sorted(sortable)[0][-1])


def _interpretation(
    best: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
) -> list[str]:
    if not best:
        return ["No primary candidate could be selected from the available artifacts."]
    best_id = str(best.get("variant_id") or "")
    lines = [
        f"`{best_id}` is the best primary-view candidate under the current ordering: avoid harmful replacements first, then avoid admission rejects, then maximize decision accuracy.",
    ]
    if best_id == "v5_refresh_control":
        lines.append(
            "The new v6 prompt constraints did not beat the simpler v5 control on downstream veto decisions in this run."
        )
    pos_row = _row_by_variant(rows, "v6_pos_only")
    if pos_row:
        pos_audit = _as_mapping(pos_row.get("postprocess_audit_summary"))
        lines.append(
            "`v6_pos_only` successfully produced model POS/topic labels and reduced POS-weak rows, but that mechanical improvement did not translate into the best veto score."
        )
        lines.append(f"`v6_pos_only` POS-weak rows: {pos_audit.get('pos_weak_count', 0)}.")
    combined = _row_by_variant(rows, "v6_pos_diversity")
    if combined and int(combined.get("rejected_item_count") or 0):
        lines.append(
            "`v6_pos_diversity` had one admission rejection because a generated sentence used an inflected form instead of the exact replacement trigger."
        )
    return lines


def _row_by_variant(
    rows: Sequence[Mapping[str, object]], variant_id: str
) -> Mapping[str, object] | None:
    return next((row for row in rows if str(row.get("variant_id") or "") == variant_id), None)


def _view_by_id(view_scores: Sequence[Mapping[str, object]], view_id: str) -> Mapping[str, object]:
    return next(
        (view for view in view_scores if str(view.get("view_id") or "") == view_id),
        {},
    )


def _estimated_cost(
    *,
    input_tokens: int,
    output_tokens: int,
    input_rate_per_1m: float,
    output_rate_per_1m: float,
) -> float:
    return (input_tokens / 1_000_000.0) * input_rate_per_1m + (
        output_tokens / 1_000_000.0
    ) * output_rate_per_1m


def _generation_path(variant_id: str) -> Path:
    return (
        TEST_OUTPUTS_ROOT
        / f"semantic_veto_evidence_gap_generation_run_prompt_bakeoff_{variant_id}_en_es_latest.json"
    )


def _admission_path(variant_id: str) -> Path:
    return (
        TEST_OUTPUTS_ROOT
        / f"semantic_veto_evidence_gap_generation_admission_prompt_bakeoff_{variant_id}_en_es_latest.json"
    )


def _postprocess_path(variant_id: str) -> Path:
    return (
        TEST_OUTPUTS_ROOT
        / f"semantic_veto_evidence_gap_generation_postprocess_prompt_bakeoff_{variant_id}_en_es_latest.json"
    )


def _load_json(path: Path) -> Mapping[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _fmt(value: object) -> str:
    if isinstance(value, int | float):
        return f"{float(value):.4f}"
    return ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
