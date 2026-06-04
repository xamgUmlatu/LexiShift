#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_MANIFEST = TEST_INPUTS_ROOT / "semantic_veto_representative_gap_source_manifest_en_es.json"
DEFAULT_STAGE1_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_materialization_en_es_latest.json"
)
DEFAULT_REPRESENTATIVE_FRAME = (
    TEST_OUTPUTS_ROOT / "semantic_veto_sampling_stage1_representative_frame_en_es_latest.json"
)
DEFAULT_LLM_SCORING = TEST_OUTPUTS_ROOT / "semantic_veto_llm_pilot_scoring_en_es_latest.json"
DEFAULT_PRODUCT_QUALITY = TEST_OUTPUTS_ROOT / "semantic_veto_product_quality_en_es_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_representative_gap_plan_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_representative_gap_plan_en_es_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create an explicit collection plan for the semantic-veto representative "
            "row shortfall without contaminating the representative lane with targeted "
            "or generated discovery rows."
        )
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--stage1-report", type=Path, default=DEFAULT_STAGE1_REPORT)
    parser.add_argument("--representative-frame", type=Path, default=DEFAULT_REPRESENTATIVE_FRAME)
    parser.add_argument("--llm-scoring-json", type=Path, default=DEFAULT_LLM_SCORING)
    parser.add_argument("--product-quality-json", type=Path, default=DEFAULT_PRODUCT_QUALITY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_representative_gap_plan_report(
        manifest=_load_json(args.manifest),
        stage1_report=_load_json(args.stage1_report),
        representative_frame=_load_json(args.representative_frame),
        llm_scoring=_load_optional_json(args.llm_scoring_json),
        product_quality=_load_optional_json(args.product_quality_json),
        manifest_path=args.manifest,
        stage1_report_path=args.stage1_report,
        representative_frame_path=args.representative_frame,
        llm_scoring_path=args.llm_scoring_json,
        product_quality_path=args.product_quality_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_representative_gap_plan_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_representative_gap_plan_report(
    *,
    manifest: Mapping[str, object],
    stage1_report: Mapping[str, object],
    representative_frame: Mapping[str, object],
    llm_scoring: Mapping[str, object] | None = None,
    product_quality: Mapping[str, object] | None = None,
    manifest_path: Path | None = None,
    stage1_report_path: Path | None = None,
    representative_frame_path: Path | None = None,
    llm_scoring_path: Path | None = None,
    product_quality_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    llm_scoring = llm_scoring or {}
    product_quality = product_quality or {}
    stage_summary = _as_mapping(stage1_report.get("summary"))
    frame_summary = _as_mapping(representative_frame.get("summary"))
    target_rows = _int_value(
        stage_summary.get("target_locked_eval_rows"),
        fallback=_int_value(frame_summary.get("target_locked_eval_rows")),
    )
    available_rows = _int_value(
        stage_summary.get("available_representative_rows"),
        fallback=_int_value(frame_summary.get("available_representative_rows")),
    )
    selected_rows = _int_value(
        stage_summary.get("selected_locked_eval_rows"),
        fallback=_int_value(frame_summary.get("selected_locked_eval_rows")),
    )
    shortfall = max(0, target_rows - selected_rows)
    source_lanes = _mapping_rows(manifest.get("source_lanes"))
    issues = _issues(
        manifest=manifest,
        source_lanes=source_lanes,
        target_rows=target_rows,
        available_rows=available_rows,
        selected_rows=selected_rows,
        shortfall=shortfall,
    )
    collection_slots = _collection_slots(
        source_lanes=source_lanes,
        shortfall=shortfall,
        random_seed=str(manifest.get("random_seed") or ""),
    )
    llm_case_rows = _mapping_rows(llm_scoring.get("case_results"))
    product_rows = _mapping_rows(product_quality.get("case_traces"))
    proxy_backstop_rows = _llm_locked_proxy_rows(llm_case_rows)
    summary = {
        "target_locked_eval_rows": target_rows,
        "available_representative_rows": available_rows,
        "selected_locked_eval_rows": selected_rows,
        "remaining_representative_rows_needed": shortfall,
        "open_primary_collection_slots": len(collection_slots),
        "primary_slot_source_counts": dict(
            sorted(
                Counter(
                    str(row.get("preferred_source_id") or "") for row in collection_slots
                ).items()
            )
        ),
        "llm_locked_proxy_rows_available": len(proxy_backstop_rows),
        "llm_discovery_rows_seen": sum(
            1 for row in llm_case_rows if str(row.get("split") or "") == "discovery"
        ),
        "product_quality_lane_type_counts": dict(
            sorted(Counter(str(row.get("lane_type") or "") for row in product_rows).items())
        ),
        "issues": issues,
    }
    return {
        "schema_version": 1,
        "status": "review" if issues else "ok",
        "decision": (
            "representative_gap_plan_incomplete"
            if issues
            else (
                "representative_gap_closed"
                if shortfall == 0
                else "representative_gap_collection_plan_ready"
            )
        ),
        "generated_at": generated_at,
        "pair": str(manifest.get("pair") or stage1_report.get("pair") or "en-es"),
        "inputs": {
            "manifest_path": _repo_path(manifest_path),
            "stage1_report_path": _repo_path(stage1_report_path),
            "representative_frame_path": _repo_path(representative_frame_path),
            "llm_scoring_path": _repo_path(llm_scoring_path),
            "product_quality_path": _repo_path(product_quality_path),
            "stage1_decision": str(stage1_report.get("decision") or ""),
            "representative_frame_id": str(representative_frame.get("frame_id") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "threshold_or_scorer_change": "none",
            "source_evidence_promotion": "none",
            "random_seed": str(manifest.get("random_seed") or ""),
            "primary_rule": (
                "Only rows sampled from normal observed or corpus-like app candidate "
                "contexts before scoring can fill the primary representative shortfall."
            ),
            "proxy_rule": (
                "Generated or targeted rows may be used as temporary proxy/backstop "
                "diagnostics, but they do not count toward the primary representative "
                "product-quality target."
            ),
            "global_rules": [str(item) for item in _sequence(manifest.get("global_rules"))],
        },
        "summary": summary,
        "source_lane_audit": _source_lane_audit(
            source_lanes=source_lanes,
            llm_case_rows=llm_case_rows,
            product_rows=product_rows,
            stage_summary=stage_summary,
            shortfall=shortfall,
        ),
        "collection_slots": collection_slots,
        "proxy_backstop_rows": proxy_backstop_rows[: min(25, len(proxy_backstop_rows))],
        "next_steps": _next_steps(shortfall=shortfall),
    }


def render_representative_gap_plan_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Representative Gap Plan",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Remaining representative rows needed: `{summary.get('remaining_representative_rows_needed', 0)}`",
        f"- Open primary collection slots: `{summary.get('open_primary_collection_slots', 0)}`",
        f"- LLM locked proxy rows available: `{summary.get('llm_locked_proxy_rows_available', 0)}`",
        "",
        "## Source Audit",
        "",
        _source_lane_table(report.get("source_lane_audit")),
        "",
        "## Open Slots",
        "",
        _slot_table(report.get("collection_slots")),
        "",
        "## Proxy Backstop",
        "",
        _proxy_table(report.get("proxy_backstop_rows")),
        "",
        "## Methodology",
        "",
    ]
    methodology = _as_mapping(report.get("methodology"))
    lines.append(f"- Primary rule: {methodology.get('primary_rule', '')}")
    lines.append(f"- Proxy rule: {methodology.get('proxy_rule', '')}")
    lines.append(f"- Random seed: `{methodology.get('random_seed', '')}`")
    for item in _sequence(methodology.get("global_rules")):
        lines.append(f"- {item}")
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _issues(
    *,
    manifest: Mapping[str, object],
    source_lanes: Sequence[Mapping[str, object]],
    target_rows: int,
    available_rows: int,
    selected_rows: int,
    shortfall: int,
) -> list[str]:
    issues = []
    if not str(manifest.get("random_seed") or ""):
        issues.append("manifest_missing_random_seed")
    if not source_lanes:
        issues.append("manifest_missing_source_lanes")
    if target_rows <= 0:
        issues.append("missing_representative_target_rows")
    if selected_rows > available_rows:
        issues.append("selected_rows_exceed_available_rows")
    if shortfall < 0:
        issues.append("negative_shortfall")
    if shortfall and not any(
        str(row.get("eligibility") or "").startswith("primary")
        or "primary_" in str(row.get("source_class") or "")
        for row in source_lanes
    ):
        issues.append("no_primary_source_lane_for_shortfall")
    return issues


def _collection_slots(
    *,
    source_lanes: Sequence[Mapping[str, object]],
    shortfall: int,
    random_seed: str,
) -> list[dict[str, object]]:
    if shortfall <= 0:
        return []
    primary_lanes = [
        row
        for row in source_lanes
        if str(row.get("eligibility") or "").startswith("primary")
        or "primary_" in str(row.get("source_class") or "")
    ]
    quota_by_source = _primary_quota_by_source(primary_lanes=primary_lanes, shortfall=shortfall)
    slots: list[dict[str, object]] = []
    slot_index = 0
    for source in primary_lanes:
        source_id = str(source.get("source_id") or "")
        for _ in range(quota_by_source.get(source_id, 0)):
            slot_index += 1
            slot_key = _stable_hash(f"{random_seed}|representative_gap|{slot_index}|{source_id}")
            slots.append(
                {
                    "slot_id": f"en-es:representative-gap:primary:{slot_index:03d}",
                    "stable_random_key": slot_key,
                    "status": "open",
                    "target_lane_id": "representative_random_product_lane",
                    "split": "locked_eval",
                    "preferred_source_id": source_id,
                    "preferred_source_class": str(source.get("source_class") or ""),
                    "context_source_required": True,
                    "counts_toward_primary_representative_target": True,
                    "eligibility_gates": [
                        "sample_trigger_target_context_before_scoring",
                        "dedupe_trigger_target_normalized_sentence",
                        "exclude_targeted_p0_and_stress_rows",
                        "label_after_sampling",
                        "record_context_source_and_sampling_key",
                    ],
                }
            )
    slots.sort(key=lambda row: str(row.get("stable_random_key") or ""))
    for rank, row in enumerate(slots, start=1):
        row["selection_rank"] = rank
    return slots


def _primary_quota_by_source(
    *,
    primary_lanes: Sequence[Mapping[str, object]],
    shortfall: int,
) -> dict[str, int]:
    if not primary_lanes or shortfall <= 0:
        return {}
    quotas: dict[str, int] = {}
    remaining = shortfall
    for source in primary_lanes:
        source_id = str(source.get("source_id") or "")
        quota = max(0, min(remaining, _int_value(source.get("slot_quota"))))
        quotas[source_id] = quota
        remaining -= quota
    if remaining > 0:
        last_source_id = str(primary_lanes[-1].get("source_id") or "")
        quotas[last_source_id] = quotas.get(last_source_id, 0) + remaining
    return quotas


def _source_lane_audit(
    *,
    source_lanes: Sequence[Mapping[str, object]],
    llm_case_rows: Sequence[Mapping[str, object]],
    product_rows: Sequence[Mapping[str, object]],
    stage_summary: Mapping[str, object],
    shortfall: int,
) -> list[dict[str, object]]:
    llm_split_counts = Counter(str(row.get("split") or "") for row in llm_case_rows)
    product_lane_counts = Counter(str(row.get("lane_type") or "") for row in product_rows)
    audit = [
        {
            "source_id": "current_stage1_representative_frame",
            "source_class": "current_primary_proxy_frame",
            "available_rows": _int_value(stage_summary.get("available_representative_rows")),
            "primary_gap_eligible": False,
            "reason": (
                "Representative target is currently filled in Stage 1."
                if shortfall == 0
                else "Already materialized; cannot fill its own remaining shortfall."
            ),
        },
        {
            "source_id": "existing_product_quality_stress_rows",
            "source_class": "stress",
            "available_rows": product_lane_counts.get("stress", 0),
            "primary_gap_eligible": False,
            "reason": "Stress rows are known hard cases and would bias representative estimates.",
        },
        {
            "source_id": "existing_llm_pilot_locked_eval_rows",
            "source_class": "generated_proxy",
            "available_rows": llm_split_counts.get("locked_eval", 0),
            "primary_gap_eligible": False,
            "reason": "Generated pilot rows can be proxy diagnostics, not primary browsing evidence.",
        },
        {
            "source_id": "existing_llm_pilot_discovery_rows",
            "source_class": "generated_discovery",
            "available_rows": llm_split_counts.get("discovery", 0),
            "primary_gap_eligible": False,
            "reason": "Discovery rows are not locked representative rows.",
        },
    ]
    for source in source_lanes:
        audit.append(
            {
                "source_id": str(source.get("source_id") or ""),
                "source_class": str(source.get("source_class") or ""),
                "planned_slot_quota": _int_value(source.get("slot_quota")),
                "primary_gap_eligible": str(source.get("eligibility") or "").startswith("primary")
                or "primary_" in str(source.get("source_class") or ""),
                "eligibility": str(source.get("eligibility") or ""),
                "reason": str(source.get("collection_contract") or ""),
            }
        )
    return audit


def _next_steps(*, shortfall: int) -> list[str]:
    if shortfall == 0:
        return [
            "Human-review the 25 corpus-like representative gap rows before using them for promotion claims.",
            "Keep the filled 120-row representative scoring and product-quality reports current after any row review or source refresh.",
            "Prefer observed semantic-admit contexts for the next representative refresh when browser/helper logs are available.",
            "Keep LLM pilot locked rows as proxy diagnostics only; do not count them as observed representative browsing rows.",
        ]
    return [
        f"Collect or export the {shortfall} open primary slots in parallel with P0 LLM discovery work.",
        "Prefer observed semantic-admit contexts; use corpus-like candidate contexts only with proxy labeling.",
        "Keep LLM pilot locked rows as a temporary diagnostic backstop only; do not count them as representative browsing rows.",
        "Rerun Stage 1 materialization after primary rows are added and require the shortfall to reach zero before representative product claims.",
    ]


def _llm_locked_proxy_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    output = []
    for row in rows:
        if str(row.get("split") or "") != "locked_eval":
            continue
        output.append(
            {
                "row_id": str(row.get("case_id") or ""),
                "trigger": str(row.get("trigger") or ""),
                "gold_type": str(row.get("gold_type") or ""),
                "gold_decision": str(row.get("gold_decision") or ""),
                "sentence": str(row.get("sentence") or ""),
                "context_source": "llm_pilot_locked_eval_proxy",
                "counts_toward_primary_representative_target": False,
            }
        )
    output.sort(key=lambda row: (str(row.get("trigger") or ""), str(row.get("row_id") or "")))
    return output


def _source_lane_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No source lanes._"
    lines = [
        "| Source | Class | Rows/Quota | Primary Eligible | Reason |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        count = row.get("available_rows", row.get("planned_slot_quota", ""))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('source_id') or ''))}`",
                    f"`{_escape_md(str(row.get('source_class') or ''))}`",
                    f"`{count}`",
                    f"`{bool(row.get('primary_gap_eligible'))}`",
                    _escape_md(str(row.get("reason") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _slot_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No open slots._"
    lines = [
        "| Rank | Slot | Preferred Source | Status |",
        "| ---: | --- | --- | --- |",
    ]
    for row in rows[:25]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("selection_rank") or ""),
                    f"`{_escape_md(str(row.get('slot_id') or ''))}`",
                    f"`{_escape_md(str(row.get('preferred_source_id') or ''))}`",
                    f"`{_escape_md(str(row.get('status') or ''))}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _proxy_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No proxy rows available._"
    lines = [
        "| Row | Trigger | Gold Type | Counts Primary? | Sentence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows[:12]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('row_id') or ''))}`",
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('gold_type') or ''))}`",
                    f"`{bool(row.get('counts_toward_primary_representative_target'))}`",
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict[str, object]:
    candidate = Path(path)
    if not candidate.exists():
        return {}
    return _load_json(candidate)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    return [row for row in _sequence(value) if isinstance(row, Mapping)]


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _int_value(value: object, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
