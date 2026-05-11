#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Callable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_source_packaging"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402


DEFAULT_RUN_ID = "active-only-poc-v5-source-packaging-latest"
DEFAULT_VIEW_ID = "no_high_eval_overlap_sentence_only"
DEFAULT_ADMISSION = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_admission_active_only_poc_en_es_latest.json"
)
DEFAULT_GENERATION_RUN = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_run_active_only_poc_en_es_latest.json"
)
DEFAULT_POSTPROCESS = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_postprocess_active_only_poc_en_es_latest.json"
)
DEFAULT_INTAKE_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_intake_batch.json"
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_source_packaging_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_source_packaging_en_es_latest.md"
)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Package the active-only en-es semantic-veto PoC generated rows as canonical "
            "semantic evidence without publishing them to runtime artifacts."
        )
    )
    parser.add_argument("--admission", type=Path, default=DEFAULT_ADMISSION)
    parser.add_argument("--generation-run", type=Path, default=DEFAULT_GENERATION_RUN)
    parser.add_argument("--postprocess", type=Path, default=DEFAULT_POSTPROCESS)
    parser.add_argument("--view-id", default=DEFAULT_VIEW_ID)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--intake-out", type=Path, default=DEFAULT_INTAKE_OUT)
    parser.add_argument("--normalized-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bundle = build_active_only_source_packaging_bundle(
        admission_payload=_load_json(args.admission),
        generation_run_payload=_load_json(args.generation_run),
        postprocess_payload=_load_json(args.postprocess),
        admission_path=args.admission,
        generation_run_path=args.generation_run,
        postprocess_path=args.postprocess,
        view_id=args.view_id,
        run_id=args.run_id,
    )
    for path, payload in (
        (args.intake_out, bundle["intake_batch"]),
        (args.normalized_out, bundle["normalized_batch"]),
        (args.json_out, bundle["report"]),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_active_only_source_packaging_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote intake batch to {args.intake_out}")
    print(f"Wrote normalized evidence to {args.normalized_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and bundle["report"]["status"] != "ok":
        return 1
    return 0


def build_active_only_source_packaging_bundle(
    *,
    admission_payload: Mapping[str, object],
    generation_run_payload: Mapping[str, object],
    postprocess_payload: Mapping[str, object],
    admission_path: Path | None = None,
    generation_run_path: Path | None = None,
    postprocess_path: Path | None = None,
    view_id: str = DEFAULT_VIEW_ID,
    run_id: str = DEFAULT_RUN_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    selected_items, excluded_items, issues = _select_candidate_items(
        admission_payload=admission_payload,
        postprocess_payload=postprocess_payload,
        view_id=view_id,
    )
    intake_batch = _build_intake_batch(
        selected_items=selected_items,
        excluded_items=excluded_items,
        admission_payload=admission_payload,
        generation_run_payload=generation_run_payload,
        postprocess_payload=postprocess_payload,
        view_id=view_id,
        run_id=run_id,
        generated_at=generated_at,
    )
    normalized_batch = normalize_llm_intake_batch(intake_batch) if selected_items else None
    report = _build_report(
        selected_items=selected_items,
        excluded_items=excluded_items,
        issues=issues,
        intake_batch=intake_batch,
        normalized_batch=normalized_batch,
        admission_payload=admission_payload,
        generation_run_payload=generation_run_payload,
        postprocess_payload=postprocess_payload,
        admission_path=admission_path,
        generation_run_path=generation_run_path,
        postprocess_path=postprocess_path,
        view_id=view_id,
        generated_at=generated_at,
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch or {},
        "report": report,
    }


def render_active_only_source_packaging_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    provenance = _as_mapping(report.get("provenance_summary"))
    lines = [
        "# en-es Semantic Veto Active-Only Source Packaging",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- View: `{report.get('view_id', '')}`",
        f"- Intake batch: `{report.get('batch_id', '')}`",
        f"- Normalization: `{report.get('normalization_version', '')}`",
        "",
        "## Summary",
        "",
        f"- Admitted input items: `{summary.get('admitted_input_item_count', 0)}`",
        f"- Packaged evidence rows: `{summary.get('packaged_row_count', 0)}`",
        f"- Excluded rows: `{summary.get('excluded_row_count', 0)}`",
        f"- Family count: `{summary.get('family_count', 0)}`",
        f"- Runtime publishable rows: `{summary.get('runtime_publishable_row_count', 0)}`",
        f"- Relation types: `{summary.get('relation_type_counts', {})}`",
        f"- Exclusion reasons: `{summary.get('exclusion_reason_counts', {})}`",
        "",
        "## Provenance",
        "",
        f"- Prompt: `{provenance.get('prompt_id', '')}`",
        f"- Model: `{provenance.get('model_id', '')}`",
        f"- Input/output tokens: `{provenance.get('input_tokens', 0)}` / "
        f"`{provenance.get('output_tokens', 0)}`",
        f"- Source packaging mutates raw LLM output: `{provenance.get('raw_output_mutation', '')}`",
        "",
        "## Family Rows",
        "",
        "| Family | Packaged | Excluded | Targets |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in _mapping_rows(report.get("family_rows")):
        lines.append(
            f"| `{row.get('family_id', '')}` | {row.get('packaged_row_count', 0)} | "
            f"{row.get('excluded_row_count', 0)} | `{', '.join(row.get('targets', []))}` |"
        )
    lines.extend(["", "## Runtime Boundary", ""])
    lines.extend(f"- `{item}`" for item in report.get("runtime_boundary", ()))
    if report.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- `{item}`" for item in report.get("issues", ()))
    return "\n".join(lines) + "\n"


def _select_candidate_items(
    *,
    admission_payload: Mapping[str, object],
    postprocess_payload: Mapping[str, object],
    view_id: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    admitted_items = [
        dict(item)
        for item in _mapping_rows(admission_payload.get("admitted_items"))
        if str(item.get("slot_type") or "") == "active_evidence_expansion"
    ]
    audits_by_item_id = {
        str(audit.get("item_id") or ""): audit
        for audit in _mapping_rows(postprocess_payload.get("item_audits"))
    }
    predicate = _view_predicate(view_id)
    evidence_variant = _view_evidence_variant(view_id)
    selected: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    issues: list[str] = []
    if not admitted_items:
        issues.append("no_active_admitted_items")
    for item in admitted_items:
        item_id = str(item.get("item_id") or "")
        audit = _as_mapping(audits_by_item_id.get(item_id))
        if not audit:
            excluded.append(_excluded_item(item, reason="missing_postprocess_audit"))
            continue
        if not predicate(audit):
            excluded.append(
                _excluded_item(item, audit=audit, reason=_exclusion_reason(view_id, audit))
            )
            continue
        packaged = dict(item)
        packaged["postprocess_view_id"] = view_id
        packaged["postprocess_audit_id"] = str(audit.get("audit_id") or "")
        packaged["packaged_evidence_text"] = _evidence_text_for_variant(
            item=packaged,
            evidence_variant=evidence_variant,
        )
        packaged["packaging_audit"] = _audit_digest(audit)
        selected.append(packaged)
    if not selected:
        issues.append("no_items_selected_for_packaging")
    return selected, excluded, issues


def _build_intake_batch(
    *,
    selected_items: Sequence[Mapping[str, object]],
    excluded_items: Sequence[Mapping[str, object]],
    admission_payload: Mapping[str, object],
    generation_run_payload: Mapping[str, object],
    postprocess_payload: Mapping[str, object],
    view_id: str,
    run_id: str,
    generated_at: str,
) -> dict[str, object]:
    generation_summary = _as_mapping(generation_run_payload.get("summary"))
    batch_id = f"en-es:semantic-veto:{run_id}"
    return {
        "schema_version": 1,
        "batch_id": batch_id,
        "pair": "en-es",
        "source_type": "llm",
        "source_id": run_id,
        "source_family": "silver_llm_generation",
        "roles": ["cue_generation"],
        "generated_at": str(generation_run_payload.get("generated_at") or generated_at),
        "ingested_at": generated_at,
        "review_state": "unreviewed",
        "model_id": str(generation_run_payload.get("selected_model_id") or "unknown"),
        "prompt_version": str(
            generation_run_payload.get("prompt_id") or "semantic_veto_evidence_gap_generation_v5"
        ),
        "temperature": _optional_float(generation_run_payload.get("selected_temperature")),
        "cost_metadata": {
            "input_tokens": int(generation_summary.get("input_tokens") or 0),
            "output_tokens": int(generation_summary.get("output_tokens") or 0),
            "reasoning_tokens": int(generation_summary.get("reasoning_tokens") or 0),
        },
        "provenance": {
            "source_packaging_run_id": run_id,
            "postprocess_view_id": view_id,
            "admission_generated_at": str(admission_payload.get("generated_at") or ""),
            "postprocess_generated_at": str(postprocess_payload.get("generated_at") or ""),
            "raw_output_mutation": "none",
            "evidence_variant": _view_evidence_variant(view_id),
            "admitted_input_item_count": int(
                _as_mapping(admission_payload.get("summary")).get("admitted_item_count") or 0
            ),
            "selected_item_count": len(selected_items),
            "excluded_item_count": len(excluded_items),
        },
        "items": [
            _intake_item(item, index=index, run_id=run_id)
            for index, item in enumerate(selected_items, 1)
        ],
    }


def _intake_item(item: Mapping[str, object], *, index: int, run_id: str) -> dict[str, object]:
    source_phrase = str(item.get("source_phrase") or "").strip()
    target = str(item.get("active_target_lemma") or item.get("target_lemma") or "").strip()
    audit = _as_mapping(item.get("packaging_audit"))
    expected_pos = str(audit.get("expected_pos") or "").strip().lower()
    row_prefix = _slug(run_id) or "active-only-source"
    row: dict[str, object] = {
        "row_id": f"{row_prefix}-source-row-{index:03d}-{_slug(source_phrase)}-{_slug(target)}",
        "relation_type": "anchor_cue",
        "trigger": source_phrase,
        "active_target": target,
        "candidate_target": target,
        "evidence_text": str(item.get("packaged_evidence_text") or "").strip(),
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "prompt_slot": str(item.get("slot_type") or "active_evidence_expansion"),
        "input_ref": str(item.get("request_id") or ""),
        "raw_response_ref": str(item.get("item_id") or ""),
        "metadata": {
            "family_id": str(item.get("family_id") or ""),
            "item_id": str(item.get("item_id") or ""),
            "request_id": str(item.get("request_id") or ""),
            "slot_id": str(item.get("slot_id") or ""),
            "pilot_arm": str(item.get("pilot_arm") or ""),
            "global_need_rank": item.get("global_need_rank"),
            "arm_rank": item.get("arm_rank"),
            "predicted_need": item.get("predicted_need"),
            "source_sentence": str(item.get("sentence") or ""),
            "evidence_note": str(item.get("evidence_note") or ""),
            "postprocess_view_id": str(item.get("postprocess_view_id") or ""),
            "postprocess_audit_id": str(item.get("postprocess_audit_id") or ""),
            "packaging_audit": dict(audit),
        },
    }
    if expected_pos:
        row["candidate_pos"] = expected_pos
    sense_hint = {
        "target_key": target,
        "sense_label": f"{source_phrase} -> {target}",
        "note": "active-only generated anchor cue",
    }
    if expected_pos:
        sense_hint["canonical_pos"] = expected_pos
    row["active_sense_hint"] = dict(sense_hint)
    row["candidate_sense_hint"] = dict(sense_hint)
    return row


def _build_report(
    *,
    selected_items: Sequence[Mapping[str, object]],
    excluded_items: Sequence[Mapping[str, object]],
    issues: Sequence[str],
    intake_batch: Mapping[str, object],
    normalized_batch: Mapping[str, object] | None,
    admission_payload: Mapping[str, object],
    generation_run_payload: Mapping[str, object],
    postprocess_payload: Mapping[str, object],
    admission_path: Path | None,
    generation_run_path: Path | None,
    postprocess_path: Path | None,
    view_id: str,
    generated_at: str,
) -> dict[str, object]:
    rows = _mapping_rows((normalized_batch or {}).get("rows"))
    runtime_publishable_count = sum(1 for row in rows if bool(row.get("runtime_publishable")))
    generation_summary = _as_mapping(generation_run_payload.get("summary"))
    family_rows = _family_rows(selected_items=selected_items, excluded_items=excluded_items)
    report_issues = list(issues)
    if runtime_publishable_count:
        report_issues.append("normalized_rows_marked_runtime_publishable")
    status = "ok" if not report_issues else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "active_only_source_packaging_ready_for_inventory_compile"
            if status == "ok"
            else "active_only_source_packaging_needs_review"
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "view_id": view_id,
        "batch_id": str(intake_batch.get("batch_id") or ""),
        "normalization_version": str((normalized_batch or {}).get("normalization_version") or ""),
        "inputs": {
            "admission_path": _repo_path(admission_path),
            "generation_run_path": _repo_path(generation_run_path),
            "postprocess_path": _repo_path(postprocess_path),
        },
        "summary": {
            "admitted_input_item_count": int(
                _as_mapping(admission_payload.get("summary")).get("admitted_item_count") or 0
            ),
            "packaged_row_count": len(rows),
            "excluded_row_count": len(excluded_items),
            "family_count": len(family_rows),
            "runtime_publishable_row_count": runtime_publishable_count,
            "relation_type_counts": _count_by(rows, "relation_type"),
            "review_state_counts": _count_by(rows, "review_state"),
            "promotion_state_counts": _count_by(rows, "promotion_state"),
            "exclusion_reason_counts": _count_by(excluded_items, "exclusion_reason"),
        },
        "provenance_summary": {
            "prompt_id": str(generation_run_payload.get("prompt_id") or ""),
            "model_id": str(generation_run_payload.get("selected_model_id") or ""),
            "temperature": generation_run_payload.get("selected_temperature"),
            "input_tokens": int(generation_summary.get("input_tokens") or 0),
            "output_tokens": int(generation_summary.get("output_tokens") or 0),
            "raw_output_mutation": "none",
            "postprocess_status": str(postprocess_payload.get("status") or ""),
        },
        "family_rows": family_rows,
        "excluded_items": list(excluded_items),
        "runtime_boundary": [
            "normalized rows remain runtime_publishable=false",
            "this output is canonical source evidence, not a semantic inventory sidecar",
            "the next step is an inventory compiler that appends packaged anchor cues to ready active-sense evidence_views",
            "runtime policy and thresholds remain unchanged",
        ],
        "issues": report_issues,
    }


def _family_rows(
    *,
    selected_items: Sequence[Mapping[str, object]],
    excluded_items: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    by_family: dict[str, dict[str, object]] = {}
    for item in selected_items:
        family_id = str(item.get("family_id") or "").strip()
        row = by_family.setdefault(
            family_id,
            {
                "family_id": family_id,
                "packaged_row_count": 0,
                "excluded_row_count": 0,
                "targets": [],
            },
        )
        row["packaged_row_count"] = int(row["packaged_row_count"]) + 1
        target = str(item.get("target_lemma") or item.get("active_target_lemma") or "").strip()
        if target and target not in row["targets"]:
            row["targets"].append(target)
    for item in excluded_items:
        family_id = str(item.get("family_id") or "").strip()
        row = by_family.setdefault(
            family_id,
            {
                "family_id": family_id,
                "packaged_row_count": 0,
                "excluded_row_count": 0,
                "targets": [],
            },
        )
        row["excluded_row_count"] = int(row["excluded_row_count"]) + 1
        target = str(item.get("target_lemma") or item.get("active_target_lemma") or "").strip()
        if target and target not in row["targets"]:
            row["targets"].append(target)
    return sorted(by_family.values(), key=lambda row: str(row.get("family_id") or ""))


def _view_predicate(view_id: str) -> Callable[[Mapping[str, object]], bool]:
    normalized = str(view_id or "").strip()
    if normalized == "no_high_eval_overlap_sentence_only":
        return lambda audit: str(_as_mapping(audit.get("eval_overlap")).get("risk") or "") != "high"
    if normalized == "sentence_only_all":
        return lambda _audit: True
    raise ValueError(f"Unsupported active-only packaging view: {normalized!r}")


def _view_evidence_variant(view_id: str) -> str:
    if str(view_id or "").strip() in {
        "no_high_eval_overlap_sentence_only",
        "sentence_only_all",
    }:
        return "sentence_only"
    raise ValueError(f"Unsupported active-only packaging view: {view_id!r}")


def _evidence_text_for_variant(*, item: Mapping[str, object], evidence_variant: str) -> str:
    if evidence_variant == "sentence_only":
        return str(item.get("sentence") or "").strip()
    return " ".join(
        part
        for part in (
            str(item.get("sentence") or "").strip(),
            str(item.get("evidence_note") or "").strip(),
        )
        if part
    )


def _exclusion_reason(view_id: str, audit: Mapping[str, object]) -> str:
    if str(view_id or "").strip() == "no_high_eval_overlap_sentence_only":
        risk = str(_as_mapping(audit.get("eval_overlap")).get("risk") or "").strip()
        if risk == "high":
            return "high_eval_overlap"
    return "view_filter"


def _excluded_item(
    item: Mapping[str, object],
    *,
    reason: str,
    audit: Mapping[str, object] | None = None,
) -> dict[str, object]:
    audit = audit or {}
    return {
        "item_id": str(item.get("item_id") or ""),
        "family_id": str(item.get("family_id") or ""),
        "source_phrase": str(item.get("source_phrase") or ""),
        "target_lemma": str(item.get("target_lemma") or item.get("active_target_lemma") or ""),
        "exclusion_reason": reason,
        "postprocess_audit_id": str(audit.get("audit_id") or ""),
    }


def _audit_digest(audit: Mapping[str, object]) -> dict[str, object]:
    eval_overlap = _as_mapping(audit.get("eval_overlap"))
    shadow_confusability = _as_mapping(audit.get("shadow_confusability"))
    return {
        "audit_id": str(audit.get("audit_id") or ""),
        "flags": [str(flag) for flag in audit.get("flags", ()) if str(flag).strip()]
        if isinstance(audit.get("flags"), Sequence)
        and not isinstance(audit.get("flags"), (str, bytes))
        else [],
        "eval_overlap_risk": str(eval_overlap.get("risk") or ""),
        "eval_overlap_case_id": str(eval_overlap.get("case_id") or ""),
        "definition_like_sentence": bool(audit.get("definition_like_sentence")),
        "expected_pos": str(audit.get("expected_pos") or ""),
        "observed_source_syntax": str(audit.get("observed_source_syntax") or ""),
        "quality_score": audit.get("quality_score"),
        "shadow_confusability_risk": str(shadow_confusability.get("risk") or ""),
        "target_lemma_in_evidence_note": bool(audit.get("target_lemma_in_evidence_note")),
    }


def _count_by(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "").strip() or "missing"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _slug(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return _SLUG_RE.sub("-", normalized).strip("-") or "item"


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
