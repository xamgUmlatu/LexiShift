#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _format_percent,
    _load_json,
    _mapping_rows,
    _repo_path,
)


DEFAULT_SRS_ZIPF_BRIDGE_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_ACTIVE_ONLY_PLAN_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_active_only_full_generation_plan_post_tranche_011_en_es_latest.json"
)
DEFAULT_SOURCE_TARGET_REVIEW_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_veto_active_only_generation_source_target_review_en_es.json"
)
DEFAULT_REGISTRY_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_veto_system_registry_en_es.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_denominator_audit_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_denominator_audit_en_es_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Explain the current en-es semantic-veto denominator without running rulegen, "
            "LLM generation, or runtime policy changes."
        )
    )
    parser.add_argument("--srs-zipf-bridge-json", type=Path, default=DEFAULT_SRS_ZIPF_BRIDGE_JSON)
    parser.add_argument("--active-only-plan-json", type=Path, default=DEFAULT_ACTIVE_ONLY_PLAN_JSON)
    parser.add_argument(
        "--source-target-review-json",
        type=Path,
        default=DEFAULT_SOURCE_TARGET_REVIEW_JSON,
    )
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_denominator_audit_report(
        srs_zipf_bridge_payload=_load_json(args.srs_zipf_bridge_json),
        active_only_plan_payload=_load_json(args.active_only_plan_json),
        source_target_review_payload=_load_json(args.source_target_review_json),
        registry_payload=_load_json(args.registry_json),
        srs_zipf_bridge_path=args.srs_zipf_bridge_json,
        active_only_plan_path=args.active_only_plan_json,
        source_target_review_path=args.source_target_review_json,
        registry_path=args.registry_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_denominator_audit_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


def build_denominator_audit_report(
    *,
    srs_zipf_bridge_payload: Mapping[str, object],
    active_only_plan_payload: Mapping[str, object],
    source_target_review_payload: Mapping[str, object] | None = None,
    registry_payload: Mapping[str, object] | None = None,
    srs_zipf_bridge_path: Path | None = None,
    active_only_plan_path: Path | None = None,
    source_target_review_path: Path | None = None,
    registry_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    bridge_summary = _as_mapping(srs_zipf_bridge_payload.get("summary"))
    bridge_inputs = _as_mapping(srs_zipf_bridge_payload.get("inputs"))
    full_srs_inputs = _as_mapping(bridge_inputs.get("full_srs"))
    full_rulegen_inputs = _as_mapping(bridge_inputs.get("full_rulegen"))
    plan_summary = _as_mapping(active_only_plan_payload.get("summary"))
    registry_result = _as_mapping(_as_mapping(registry_payload).get("current_candidate", {})).get(
        "current_result"
    )
    registry_result = _as_mapping(registry_result)

    review_counts = _review_counts(source_target_review_payload)
    exclusion_counts = {
        decision: count
        for decision, count in review_counts.get("decision_counts", {}).items()
        if str(decision).startswith("exclude_")
    }
    approved_review_count = int(review_counts.get("approved_count") or 0)
    excluded_review_count = int(review_counts.get("excluded_count") or 0)
    product_scope_control_families = int(registry_result.get("families") or 0)
    denominator_families = int(plan_summary.get("denominator_family_count") or 0)
    bridge_source_target_pair_count = int(
        bridge_summary.get("full_source_target_pair_count")
        or full_rulegen_inputs.get("source_target_pair_count")
        or 0
    )
    bridge_plan_denominator_delta = bridge_source_target_pair_count - denominator_families
    covered_families = int(plan_summary.get("covered_denominator_family_count") or 0)
    uncovered_families = int(plan_summary.get("uncovered_family_count") or 0)
    accounting_total = (
        product_scope_control_families + approved_review_count + excluded_review_count
    )

    checks = {
        "bridge_and_plan_denominator_match": (
            bridge_source_target_pair_count == denominator_families
        ),
        "covered_plus_uncovered_matches_denominator": (
            covered_families + uncovered_families == denominator_families
        ),
        "current_generation_queue_exhausted": (
            _int_value(plan_summary.get("generation_queue_family_count"), default=-1) == 0
            and _int_value(plan_summary.get("selected_request_count"), default=-1) == 0
        ),
        "uncovered_rows_are_review_exclusions": uncovered_families == excluded_review_count,
        "coverage_plus_review_exclusions_matches_denominator": (
            covered_families + excluded_review_count == denominator_families
        ),
        "product_scope_plus_approved_plus_excluded_matches_denominator": (
            accounting_total == denominator_families if product_scope_control_families else None
        ),
        "no_evidence_outside_denominator": (
            _int_value(plan_summary.get("evidence_outside_denominator_key_count"), default=-1) == 0
        ),
    }
    issues = [name for name, ok in checks.items() if ok is False]

    return {
        "schema_version": 1,
        "pair": str(
            active_only_plan_payload.get("pair") or srs_zipf_bridge_payload.get("pair") or "en-es"
        ),
        "status": "ok" if not issues else "review",
        "decision": "semantic_veto_denominator_audit_current"
        if not issues
        else "semantic_veto_denominator_audit_needs_review",
        "generated_at": generated_at,
        "inputs": {
            "srs_zipf_bridge_json": _repo_path(srs_zipf_bridge_path),
            "active_only_plan_json": _repo_path(active_only_plan_path),
            "source_target_review_json": _repo_path(source_target_review_path),
            "registry_json": _repo_path(registry_path),
            "bridge_decision": str(srs_zipf_bridge_payload.get("decision") or ""),
            "active_only_plan_decision": str(active_only_plan_payload.get("decision") or ""),
            "source_target_review_decision": str(
                _as_mapping(source_target_review_payload).get("decision") or ""
            ),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_generation": "none",
            "denominator_definition": (
                "The semantic-veto source-target denominator is the set of current "
                "rulegen-produced English source / Spanish target replacement families "
                "for the installed en-es SRS target universe."
            ),
            "not_the_denominator": (
                "The 1,984 SRS-admissible Spanish target lemmas are the learner target "
                "universe, not the browser replacement-family denominator."
            ),
            "coverage_definition": (
                "A family is covered when the combined active-only semantic evidence pack "
                "has anchor_cue evidence for the normalized English trigger and Spanish target."
            ),
            "scope_mismatch_definition": (
                "When the SRS Zipf bridge source-target count differs from the active-only "
                "plan denominator, this audit is a current-plan accounting check, not an "
                "expanded-candidate coverage report."
            ),
            "exclusion_definition": (
                "The remaining uncovered families are active-only exclusions from the "
                "source-target review manifest, not pending LLM-generation rows."
            ),
        },
        "source_pipeline": {
            "frequency_db": str(full_srs_inputs.get("frequency_db") or ""),
            "frequency_db_exists": bool(full_srs_inputs.get("frequency_db_exists")),
            "seed_top_n_requested": int(full_srs_inputs.get("top_n") or 0),
            "seed_row_count": int(full_srs_inputs.get("seed_row_count") or 0),
            "unique_srs_target_lemmas": int(full_srs_inputs.get("unique_target_count") or 0),
            "translation_dict_path": str(full_rulegen_inputs.get("translation_dict_path") or ""),
            "translation_dict_exists": bool(full_rulegen_inputs.get("translation_dict_exists")),
            "reverse_translation_dict_path": str(
                full_rulegen_inputs.get("reverse_translation_dict_path") or ""
            ),
            "reverse_translation_dict_exists": bool(
                full_rulegen_inputs.get("reverse_translation_dict_exists")
            ),
            "rulegen_target_count": int(full_rulegen_inputs.get("target_count") or 0),
            "rule_count": int(full_rulegen_inputs.get("rule_count") or 0),
            "source_target_pair_count": int(
                full_rulegen_inputs.get("source_target_pair_count") or 0
            ),
            "rulegen_elapsed_seconds": full_rulegen_inputs.get("elapsed_seconds"),
        },
        "summary": {
            "srs_seed_rows": int(bridge_summary.get("full_srs_admissible_seed_row_count") or 0),
            "srs_unique_target_lemmas": int(
                bridge_summary.get("full_srs_admissible_target_count") or 0
            ),
            "bridge_source_target_pair_count": bridge_source_target_pair_count,
            "semantic_veto_denominator_families": denominator_families,
            "bridge_plan_denominator_delta": bridge_plan_denominator_delta,
            "denominator_scope": (
                "bridge_aligned_current_plan"
                if bridge_plan_denominator_delta == 0
                else "current_active_only_plan_not_expanded_candidate"
            ),
            "semantic_veto_source_triggers": int(
                plan_summary.get("denominator_source_trigger_count") or 0
            ),
            "semantic_veto_targets": int(plan_summary.get("denominator_target_count") or 0),
            "covered_families": covered_families,
            "covered_family_share": plan_summary.get("covered_denominator_family_share"),
            "uncovered_families": uncovered_families,
            "generation_queue_families": int(
                plan_summary.get("generation_queue_family_count") or 0
            ),
            "selected_request_count": int(plan_summary.get("selected_request_count") or 0),
            "product_scope_control_families": product_scope_control_families,
            "source_target_review_decisions": int(review_counts.get("decision_count") or 0),
            "source_target_review_approved": approved_review_count,
            "source_target_review_excluded": excluded_review_count,
            "exclusion_decision_counts": exclusion_counts,
            "accounting_identity": (
                f"{denominator_families} = {product_scope_control_families} pre-full-generation "
                f"covered + {approved_review_count} reviewed/generated + "
                f"{excluded_review_count} excluded"
            ),
        },
        "coverage_by_source_band": _copy_mapping_rows(
            active_only_plan_payload.get("coverage_by_source_band")
        ),
        "coverage_by_target_band": _copy_mapping_rows(
            active_only_plan_payload.get("coverage_by_target_band")
        ),
        "full_source_target_family_zipf_matrix": _copy_mapping_rows(
            srs_zipf_bridge_payload.get("full_source_target_family_zipf_matrix")
        ),
        "excluded_family_breakdown": _excluded_family_breakdown(
            active_only_plan_payload.get("all_uncovered_families")
        ),
        "checks": checks,
        "issues": issues,
        "expansion_levers": [
            {
                "lever": "expand_or_replace_spanish_frequency_pack",
                "effect": "Can increase the SRS target universe beyond the current 1,984 unique target lemmas.",
                "risk": "Only helps semantic veto if rulegen can produce visible source-target rules for the added targets.",
            },
            {
                "lever": "improve_rulegen_dictionary_or_filter_coverage",
                "effect": "Can increase the 570 replacement-family denominator from the existing 1,984 targets.",
                "risk": "Can also add weak or awkward source-target mappings that need review before LLM spend.",
            },
            {
                "lever": "change_source_target_review_policy",
                "effect": "Can admit some of the 115 currently excluded families.",
                "risk": "Would intentionally accept identical/no-visible or weak mappings that were excluded for product reasons.",
            },
            {
                "lever": "generate_shadow_or_phrase_data",
                "effect": "Can improve veto quality for already covered families with harmful-replacement classes.",
                "risk": "Does not expand the denominator by itself.",
            },
        ],
        "cleanup_recommendations": [
            "Keep tranche-011 as the current product checkpoint and tranche-003 as the latest hands-on browser smoke.",
            "Do not run more active-only paid generation while selected_request_count is 0.",
            "Treat the next denominator-expansion task as rulegen/SRS resource work, not LLM prompt work.",
            "Keep the 1,984 learner-target universe and 570 replacement-family universe labeled separately in product docs.",
            "For expanded-candidate coverage, run the active-only full generation planner against the same SRS Zipf bridge artifact.",
        ],
        "limitations": [
            "This audit reads existing no-spend artifacts; it does not rerun full rulegen.",
            "The 570 denominator is current-resource truth, not a claim about all en-es vocabulary.",
            "The 115 exclusions were manually reviewed for active-only generation value, not for every possible future product policy.",
            "Coverage means active-only evidence coverage, not broad semantic-veto accuracy.",
        ],
    }


def render_denominator_audit_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    pipeline = _as_mapping(report.get("source_pipeline"))
    lines = [
        "# en-es Semantic Veto Denominator Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- SRS learner-target universe: `{summary.get('srs_unique_target_lemmas', 0)}` target lemmas from `{summary.get('srs_seed_rows', 0)}` seed rows",
        f"- Candidate bridge source-target families: `{summary.get('bridge_source_target_pair_count', 0)}`",
        f"- Semantic-veto replacement denominator: `{summary.get('semantic_veto_denominator_families', 0)}` source-target families",
        f"- Denominator scope: `{summary.get('denominator_scope', '')}`",
        f"- Covered active-only families: `{summary.get('covered_families', 0)}` ({_format_percent(summary.get('covered_family_share'))})",
        f"- Uncovered active-only families: `{summary.get('uncovered_families', 0)}`",
        f"- Remaining generation queue: `{summary.get('generation_queue_families', 0)}` families / `{summary.get('selected_request_count', 0)}` selected requests",
        "",
        "## What The Denominator Means",
        "",
        str(_as_mapping(report.get("methodology")).get("denominator_definition") or ""),
        "",
        str(_as_mapping(report.get("methodology")).get("not_the_denominator") or ""),
        "",
        f"Current accounting identity: `{_escape_md(str(summary.get('accounting_identity') or ''))}`.",
        "",
        _scope_mismatch_section(report),
        "",
        "## Source Pipeline",
        "",
        "| Step | Current Value |",
        "| --- | --- |",
        f"| Frequency DB | `{_escape_md(str(pipeline.get('frequency_db') or ''))}` |",
        f"| Seed top N requested | `{pipeline.get('seed_top_n_requested', 0)}` |",
        f"| Seed rows | `{pipeline.get('seed_row_count', 0)}` |",
        f"| Unique SRS target lemmas | `{pipeline.get('unique_srs_target_lemmas', 0)}` |",
        f"| Rulegen targets | `{pipeline.get('rulegen_target_count', 0)}` |",
        f"| Rulegen rules | `{pipeline.get('rule_count', 0)}` |",
        f"| Source-target pairs | `{pipeline.get('source_target_pair_count', 0)}` |",
        f"| Translation dictionary | `{_escape_md(str(pipeline.get('translation_dict_path') or ''))}` |",
        f"| Reverse dictionary | `{_escape_md(str(pipeline.get('reverse_translation_dict_path') or ''))}` |",
        "",
        "## Review Outcome",
        "",
        _review_table(summary),
        "",
        "## Coverage By Source Band",
        "",
        _coverage_table(report.get("coverage_by_source_band"), "source_band"),
        "",
        "## Coverage By Target Band",
        "",
        _coverage_table(report.get("coverage_by_target_band"), "target_band"),
        "",
        "## Excluded Family Breakdown",
        "",
        _excluded_table(report.get("excluded_family_breakdown")),
        "",
        "## Expansion Levers",
        "",
        _lever_table(report.get("expansion_levers")),
        "",
        "## Cleanup Recommendations",
        "",
    ]
    lines.extend(f"- {item}" for item in report.get("cleanup_recommendations", ()))
    lines.extend(
        ["", "## Checks", "", _checks_table(report.get("checks")), "", "## Limitations", ""]
    )
    lines.extend(f"- {item}" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _review_counts(payload: Mapping[str, object] | None) -> dict[str, object]:
    rows = _mapping_rows(_as_mapping(payload).get("decisions"))
    decision_counts = Counter(str(row.get("decision") or "") for row in rows)
    approved_count = sum(1 for row in rows if bool(row.get("approved_for_active_only_generation")))
    excluded_count = len(rows) - approved_count
    return {
        "decision_count": len(rows),
        "approved_count": approved_count,
        "excluded_count": excluded_count,
        "decision_counts": dict(sorted(decision_counts.items())),
    }


def _int_value(value: object, *, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _excluded_family_breakdown(value: object) -> list[dict[str, object]]:
    rows = _mapping_rows(value)
    grouped: dict[tuple[str, str, str], list[Mapping[str, object]]] = {}
    for row in rows:
        key = (
            str(row.get("source_target_review_decision") or "unknown"),
            str(row.get("source_zipf_band_en") or "missing"),
            str(row.get("target_zipf_band_es") or "missing"),
        )
        grouped.setdefault(key, []).append(row)
    output = []
    for (decision, source_band, target_band), bucket in sorted(grouped.items()):
        output.append(
            {
                "source_target_review_decision": decision,
                "source_zipf_band_en": source_band,
                "target_zipf_band_es": target_band,
                "family_count": len(bucket),
                "sample_families": [
                    {
                        "source": str(row.get("source") or ""),
                        "target": str(row.get("target") or ""),
                    }
                    for row in bucket[:8]
                ],
            }
        )
    return output


def _copy_mapping_rows(value: object) -> list[dict[str, object]]:
    return [dict(row) for row in _mapping_rows(value)]


def _review_table(summary: Mapping[str, object]) -> str:
    exclusion_counts = _as_mapping(summary.get("exclusion_decision_counts"))
    rows = [
        "| Bucket | Families |",
        "| --- | ---: |",
        f"| Pre-full-generation covered product-scope control | {summary.get('product_scope_control_families', 0)} |",
        f"| Source-target review approved for active-only generation | {summary.get('source_target_review_approved', 0)} |",
        f"| Source-target review excluded | {summary.get('source_target_review_excluded', 0)} |",
    ]
    for decision, count in sorted(exclusion_counts.items()):
        rows.append(f"| `{_escape_md(str(decision))}` | {count} |")
    return "\n".join(rows)


def _scope_mismatch_section(report: Mapping[str, object]) -> str:
    checks = _as_mapping(report.get("checks"))
    if checks.get("bridge_and_plan_denominator_match") is not False:
        return "The SRS Zipf bridge and active-only plan denominator counts match."
    summary = _as_mapping(report.get("summary"))
    bridge_count = summary.get("bridge_source_target_pair_count", 0)
    denominator_count = summary.get("semantic_veto_denominator_families", 0)
    delta = summary.get("bridge_plan_denominator_delta", 0)
    definition = str(_as_mapping(report.get("methodology")).get("scope_mismatch_definition") or "")
    return "\n".join(
        [
            "## Scope Mismatch",
            "",
            definition,
            "",
            (
                f"The bridge input has `{bridge_count}` source-target families, while the "
                f"active-only plan denominator has `{denominator_count}` "
                f"(`delta={delta}`)."
            ),
        ]
    )


def _coverage_table(value: object, band_key: str) -> str:
    rows = _mapping_rows(value)
    lines = [
        "| Band | Families | Covered | Uncovered | Covered Share |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get(band_key) or ''))}`",
                    str(row.get("family_count") or 0),
                    str(row.get("covered_family_count") or 0),
                    str(row.get("uncovered_family_count") or 0),
                    _format_percent(row.get("covered_share")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _excluded_table(value: object) -> str:
    rows = _mapping_rows(value)
    lines = [
        "| Decision | Source Band | Target Band | Families | Samples |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        samples = ", ".join(
            f"`{_escape_md(str(pair.get('source') or ''))}` -> `{_escape_md(str(pair.get('target') or ''))}`"
            for pair in _mapping_rows(row.get("sample_families"))[:4]
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source_target_review_decision') or ''))}`",
                    f"`{_escape_md(str(row.get('source_zipf_band_en') or ''))}`",
                    f"`{_escape_md(str(row.get('target_zipf_band_es') or ''))}`",
                    str(row.get("family_count") or 0),
                    samples,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _lever_table(value: object) -> str:
    rows = _mapping_rows(value)
    lines = [
        "| Lever | Effect | Risk |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('lever') or ''))}`",
                    _escape_md(str(row.get("effect") or "")),
                    _escape_md(str(row.get("risk") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _checks_table(value: object) -> str:
    rows = [
        "| Check | Result |",
        "| --- | --- |",
    ]
    for key, result in sorted(_as_mapping(value).items()):
        rows.append(f"| `{_escape_md(str(key))}` | `{result}` |")
    return "\n".join(rows)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
