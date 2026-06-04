#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import nullcontext
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import Callable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
SEMANTIC_CASES_ROOT = TEST_INPUTS_ROOT / "semantic_routing_cases"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_veto_evidence_gap_generation_admission_en_es import (  # noqa: E402
    ACTIVE_SLOT,
)
from semantic_veto_evidence_gap_generation_postprocess_audit import (  # noqa: E402
    POS_ANCHORED_THRESHOLD,
    audit_generated_active_items,
    has_critical_flag,
    scrub_evidence_note,
)
from semantic_veto_evidence_gap_generation_score_contribution_core import (  # noqa: E402
    DEFAULT_CONTEXT_VIEW,
    DEFAULT_EVIDENCE_VIEW,
    DEFAULT_SCORER_ID,
    build_evidence_gap_score_contribution_report,
    _as_mapping,
    _fmt,
    _load_json,
    _mapping_rows,
)
from semantic_veto_product_quality_en_es import _repo_path  # noqa: E402


DEFAULT_DATASET_JSON = SEMANTIC_CASES_ROOT / "en_es_full_family_repaired_full_v1.json"
DEFAULT_ADMISSION_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_admission_active_only_poc_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_postprocess_active_only_poc_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_postprocess_active_only_poc_en_es_latest.md"
)
DEFAULT_AUGMENTED_DIR = (
    TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_evidence_gap_postprocess_datasets"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit admitted semantic-veto LLM evidence and rescore mechanical "
            "postprocess views. This is offline/no-spend and changes no runtime policy."
        )
    )
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--admission-json", type=Path, default=DEFAULT_ADMISSION_JSON)
    parser.add_argument(
        "--augmented-dir",
        type=Path,
        default=None,
        help=(
            "Optional directory for intermediate augmented datasets. "
            "When omitted, a temporary directory is used and only the JSON/Markdown report is kept."
        ),
    )
    parser.add_argument("--scorer-id", default=DEFAULT_SCORER_ID)
    parser.add_argument("--context-view", default=DEFAULT_CONTEXT_VIEW)
    parser.add_argument("--evidence-view", default=DEFAULT_EVIDENCE_VIEW)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    augmented_context = (
        nullcontext(args.augmented_dir)
        if args.augmented_dir is not None
        else _temporary_augmented_dir()
    )
    with augmented_context as augmented_dir:
        report = build_evidence_gap_generation_postprocess_report(
            dataset_payload=_load_json(args.dataset_json),
            admission_payload=_load_json(args.admission_json),
            dataset_path=args.dataset_json,
            admission_path=args.admission_json,
            augmented_dir=Path(augmented_dir),
            scorer_id=args.scorer_id,
            context_view=args.context_view,
            evidence_view=args.evidence_view,
        )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_evidence_gap_generation_postprocess_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def _temporary_augmented_dir():
    return TemporaryDirectory(prefix="semantic-veto-postprocess-")


def build_evidence_gap_generation_postprocess_report(
    *,
    dataset_payload: Mapping[str, object],
    admission_payload: Mapping[str, object],
    dataset_path: Path | None = None,
    admission_path: Path | None = None,
    augmented_dir: Path = DEFAULT_AUGMENTED_DIR,
    scorer_id: str = DEFAULT_SCORER_ID,
    context_view: str = DEFAULT_CONTEXT_VIEW,
    evidence_view: str = DEFAULT_EVIDENCE_VIEW,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    admitted_items = [
        item
        for item in _mapping_rows(admission_payload.get("admitted_items"))
        if str(item.get("slot_type") or "") == ACTIVE_SLOT
    ]
    families = {
        str(family.get("family_id") or ""): family
        for family in _mapping_rows(dataset_payload.get("families"))
        if str(family.get("family_id") or "")
    }
    selected_family_ids = sorted(
        {
            str(item.get("family_id") or "")
            for item in admitted_items
            if str(item.get("family_id") or "")
        }
    )
    issues: list[str] = []
    if not admitted_items:
        issues.append("no_active_admitted_items_to_postprocess")
    if not selected_family_ids:
        issues.append("no_selected_families_for_postprocess")

    item_audits = audit_generated_active_items(admitted_items=admitted_items, families=families)
    views = _build_views(item_audits)
    view_scores = []
    for view in views:
        view_items = _items_for_view(
            admitted_items=admitted_items, item_audits=item_audits, view=view
        )
        score_report = build_evidence_gap_score_contribution_report(
            dataset_payload=dataset_payload,
            admission_payload=_admission_payload_for_view(admission_payload, view_items),
            selected_family_ids=selected_family_ids,
            augmented_dir=augmented_dir / str(view["view_id"]),
            scorer_id=scorer_id,
            context_view=context_view,
            evidence_view=evidence_view,
            include_policy_sweep=False,
            generated_at=generated_at,
        )
        view_scores.append(
            _view_score_row(view=view, view_items=view_items, score_report=score_report)
        )

    return {
        "schema_version": 1,
        "status": "ok" if not issues else "review",
        "decision": (
            "generated_evidence_postprocess_ready_for_interpretation"
            if not issues
            else "generated_evidence_postprocess_inputs_need_repair"
        ),
        "generated_at": generated_at,
        "pair": str(dataset_payload.get("pair") or admission_payload.get("pair") or "en-es"),
        "inputs": {
            "dataset_path": _repo_path(dataset_path),
            "admission_path": _repo_path(admission_path),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "llm_call": "none",
            "raw_llm_output_mutation": "none",
            "scorer_id": scorer_id,
            "context_view": context_view,
            "evidence_view": evidence_view,
            "postprocess_role": "audit_raw_generated_items_then_score_derived_views",
            "current_control_view": "all_sentence_plus_note",
        },
        "summary": _summary(item_audits=item_audits, view_scores=view_scores, issues=issues),
        "item_audits": item_audits,
        "view_scores": view_scores,
        "recommendations": _recommendations(view_scores=view_scores, item_audits=item_audits),
        "limitations": [
            "offline no-spend postprocess over already generated active-only rows",
            "heuristic POS and overlap labels are diagnostic, not gold labels",
            "note-only views are diagnostics and should not be promoted as runtime evidence",
            "same selected-family denominator is held across views for comparability",
            "this does not validate shadow or no-winner generation at scale",
        ],
    }


def render_evidence_gap_generation_postprocess_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Evidence-Gap Generated-Evidence Postprocess",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Active generated items audited: `{summary.get('active_item_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        "",
        "## Audit Counts",
        "",
        "| Count | Value |",
        "| --- | ---: |",
        f"| High eval-overlap items | {summary.get('high_eval_overlap_count', 0)} |",
        f"| Medium eval-overlap items | {summary.get('medium_eval_overlap_count', 0)} |",
        f"| POS-weak items | {summary.get('pos_weak_count', 0)} |",
        f"| Definition-like sentence items | {summary.get('definition_like_count', 0)} |",
        f"| Target lemma in evidence note | {summary.get('target_lemma_in_note_count', 0)} |",
        f"| Items with model POS-frame labels | {summary.get('model_source_pos_frame_count', 0)} |",
        f"| Items with model topic-frame labels | {summary.get('model_topic_frame_count', 0)} |",
        f"| High shadow-confusable items | {summary.get('high_shadow_confusable_count', 0)} |",
        "",
        "## View Bakeoff",
        "",
        "| View | Items | Decision accuracy | Replace recall | Harmful | False abstains | Fixed | Regressed | Notes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in _mapping_rows(report.get("view_scores")):
        metrics = _as_mapping(row.get("generated_active_only"))
        changes = _as_mapping(row.get("case_change_counts"))
        lines.append(
            f"| `{row.get('view_id', '')}` | {row.get('item_count', 0)} | "
            f"{_fmt(metrics.get('decision_accuracy'))} | {_fmt(metrics.get('replace_recall'))} | "
            f"{metrics.get('harmful_replace_count', 0)} | {metrics.get('false_abstain_count', 0)} | "
            f"{changes.get('fixed', 0)} | {changes.get('regressed', 0)} | "
            f"{_escape_md(str(row.get('description') or ''))} |"
        )
    lines.extend(["", "## Regressions By View", ""])
    for row in _mapping_rows(report.get("view_scores")):
        regressions = _mapping_rows(row.get("regressions"))
        if not regressions:
            continue
        lines.append(f"### `{row.get('view_id', '')}`")
        for regression in regressions[:5]:
            lines.append(
                f"- `{regression.get('case_id', '')}`: "
                f"{_escape_md(str(regression.get('sentence') or ''))}"
            )
        lines.append("")
    lines.extend(["## Recommendations", ""])
    lines.extend(f"- {item}" for item in report.get("recommendations", ()))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _build_views(item_audits: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        _view(
            "all_sentence_plus_note",
            "control: current scoring appends generated sentence plus evidence_note",
            "sentence_plus_note",
            lambda _audit: True,
        ),
        _view(
            "sentence_plus_scrubbed_note",
            "mechanically remove target lemmas and meta labels from evidence_note",
            "sentence_plus_scrubbed_note",
            lambda _audit: True,
        ),
        _view(
            "sentence_only_all",
            "use generated browser sentences only, dropping explanatory notes",
            "sentence_only",
            lambda _audit: True,
        ),
        _view(
            "note_only_diagnostic",
            "diagnostic: evidence_note only, to see whether notes are driving lift",
            "note_only",
            lambda _audit: True,
        ),
        _view(
            "no_high_eval_overlap_sentence_plus_note",
            "drop generated rows with high lexical overlap against frozen eval cases",
            "sentence_plus_note",
            lambda audit: str(_as_mapping(audit.get("eval_overlap")).get("risk")) != "high",
        ),
        _view(
            "no_high_eval_overlap_sentence_only",
            "drop high eval-overlap rows and use sentence-only evidence",
            "sentence_only",
            lambda audit: str(_as_mapping(audit.get("eval_overlap")).get("risk")) != "high",
        ),
        _view(
            "pos_anchored_sentence_only",
            "keep rows whose generated source usage mechanically matches expected POS",
            "sentence_only",
            lambda audit: float(audit.get("pos_anchor_strength") or 0.0) >= POS_ANCHORED_THRESHOLD,
        ),
        _view(
            "no_definition_like_sentence_only",
            "drop definition-like generated browser sentences and use sentence-only evidence",
            "sentence_only",
            lambda audit: not bool(audit.get("definition_like_sentence")),
        ),
        _view(
            "conservative_sentence_only",
            "sentence-only rows with no high eval overlap, POS anchor, no definition-like sentence, and no high shadow confusability",
            "sentence_only",
            lambda audit: (
                str(_as_mapping(audit.get("eval_overlap")).get("risk")) != "high"
                and float(audit.get("pos_anchor_strength") or 0.0) >= POS_ANCHORED_THRESHOLD
                and not bool(audit.get("definition_like_sentence"))
                and str(_as_mapping(audit.get("shadow_confusability")).get("risk")) != "high"
                and not has_critical_flag(audit)
            ),
        ),
        _ranked_view(
            "quality_top1_sentence_only",
            "keep one highest-quality sentence-only row per family",
            "sentence_only",
            item_audits,
            top_k=1,
        ),
        _ranked_view(
            "quality_top2_sentence_only",
            "keep up to two highest-quality sentence-only rows per family after audit scoring",
            "sentence_only",
            item_audits,
            top_k=2,
        ),
    ]


def _view(
    view_id: str,
    description: str,
    evidence_variant: str,
    predicate: Callable[[Mapping[str, object]], bool],
) -> dict[str, object]:
    return {
        "view_id": view_id,
        "description": description,
        "evidence_variant": evidence_variant,
        "predicate": predicate,
    }


def _ranked_view(
    view_id: str,
    description: str,
    evidence_variant: str,
    item_audits: Sequence[Mapping[str, object]],
    *,
    top_k: int,
) -> dict[str, object]:
    by_family: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for audit in item_audits:
        by_family[str(audit.get("family_id") or "")].append(audit)
    keep_ids = set()
    for audits in by_family.values():
        ranked = sorted(
            audits,
            key=lambda audit: (
                -float(audit.get("quality_score") or 0.0),
                str(audit.get("item_id") or audit.get("audit_id") or ""),
            ),
        )
        keep_ids.update(str(audit.get("audit_id") or "") for audit in ranked[:top_k])
    return _view(
        view_id,
        description,
        evidence_variant,
        lambda audit: str(audit.get("audit_id") or "") in keep_ids,
    )


def _items_for_view(
    *,
    admitted_items: Sequence[Mapping[str, object]],
    item_audits: Sequence[Mapping[str, object]],
    view: Mapping[str, object],
) -> list[dict[str, object]]:
    items_by_id = {str(item.get("item_id") or ""): item for item in admitted_items}
    predicate = view["predicate"]
    variant = str(view.get("evidence_variant") or "sentence_plus_note")
    view_items = []
    for audit in item_audits:
        if not predicate(audit):
            continue
        item = deepcopy(dict(items_by_id.get(str(audit.get("item_id") or ""), {})))
        if not item:
            continue
        if variant == "sentence_only":
            item["evidence_note"] = ""
        elif variant == "note_only":
            item["sentence"] = ""
        elif variant == "sentence_plus_scrubbed_note":
            item["evidence_note"] = scrub_evidence_note(
                str(item.get("evidence_note") or ""),
                source_phrase=str(item.get("source_phrase") or ""),
                target_lemma=str(item.get("target_lemma") or ""),
            )
        item["postprocess_view_id"] = str(view.get("view_id") or "")
        item["postprocess_audit_id"] = str(audit.get("audit_id") or "")
        return_item = dict(item)
        view_items.append(return_item)
    return view_items


def _admission_payload_for_view(
    admission_payload: Mapping[str, object],
    view_items: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    payload = deepcopy(dict(admission_payload))
    payload["admitted_items"] = [dict(item) for item in view_items]
    summary = dict(_as_mapping(payload.get("summary")))
    summary["admitted_item_count"] = len(view_items)
    payload["summary"] = summary
    return payload


def _view_score_row(
    *,
    view: Mapping[str, object],
    view_items: Sequence[Mapping[str, object]],
    score_report: Mapping[str, object],
) -> dict[str, object]:
    summary = _as_mapping(score_report.get("summary"))
    comparison = _as_mapping(
        _as_mapping(score_report.get("comparisons")).get("generated_active_only")
    )
    case_deltas = _mapping_rows(
        _as_mapping(score_report.get("case_deltas")).get("generated_active_only")
    )
    change_counts = _case_change_counts(case_deltas)
    regressions = [
        _case_digest(row)
        for row in case_deltas
        if row.get("base_predicted_decision") == row.get("gold_decision")
        and row.get("candidate_predicted_decision") != row.get("gold_decision")
    ]
    fixed = [
        _case_digest(row)
        for row in case_deltas
        if row.get("base_predicted_decision") != row.get("gold_decision")
        and row.get("candidate_predicted_decision") == row.get("gold_decision")
    ]
    return {
        "view_id": str(view.get("view_id") or ""),
        "description": str(view.get("description") or ""),
        "evidence_variant": str(view.get("evidence_variant") or ""),
        "item_count": len(view_items),
        "generated_active_only": _as_mapping(summary.get("generated_active_only")),
        "comparison": comparison,
        "case_change_counts": change_counts,
        "regressions": regressions,
        "fixed_cases_sample": fixed[:10],
        "score_status": str(score_report.get("status") or ""),
        "score_issues": _as_mapping(score_report.get("summary")).get("issues", []),
    }


def _summary(
    *,
    item_audits: Sequence[Mapping[str, object]],
    view_scores: Sequence[Mapping[str, object]],
    issues: Sequence[str],
) -> dict[str, object]:
    return {
        "issues": list(issues),
        "active_item_count": len(item_audits),
        "family_count": len({str(audit.get("family_id") or "") for audit in item_audits}),
        "high_eval_overlap_count": sum(
            1
            for audit in item_audits
            if _as_mapping(audit.get("eval_overlap")).get("risk") == "high"
        ),
        "medium_eval_overlap_count": sum(
            1
            for audit in item_audits
            if _as_mapping(audit.get("eval_overlap")).get("risk") == "medium"
        ),
        "pos_weak_count": sum(
            1
            for audit in item_audits
            if float(audit.get("pos_anchor_strength") or 0.0) < POS_ANCHORED_THRESHOLD
        ),
        "definition_like_count": sum(
            1 for audit in item_audits if bool(audit.get("definition_like_sentence"))
        ),
        "target_lemma_in_note_count": sum(
            1 for audit in item_audits if bool(audit.get("target_lemma_in_evidence_note"))
        ),
        "model_source_pos_frame_count": sum(
            1 for audit in item_audits if str(audit.get("model_source_pos_frame") or "")
        ),
        "model_topic_frame_count": sum(
            1 for audit in item_audits if str(audit.get("model_topic_frame") or "")
        ),
        "high_shadow_confusable_count": sum(
            1
            for audit in item_audits
            if _as_mapping(audit.get("shadow_confusability")).get("risk") == "high"
        ),
        "view_count": len(view_scores),
    }


def _recommendations(
    *,
    view_scores: Sequence[Mapping[str, object]],
    item_audits: Sequence[Mapping[str, object]],
) -> list[str]:
    recommendations = []
    by_id = {str(row.get("view_id") or ""): row for row in view_scores}
    control = _as_mapping(by_id.get("all_sentence_plus_note"))
    sentence_only = _as_mapping(by_id.get("sentence_only_all"))
    note_only = _as_mapping(by_id.get("note_only_diagnostic"))
    conservative = _as_mapping(by_id.get("conservative_sentence_only"))
    if note_only:
        note_metrics = _as_mapping(note_only.get("generated_active_only"))
        control_metrics = _as_mapping(control.get("generated_active_only"))
        if float(note_metrics.get("replace_recall") or 0.0) > 0.0:
            recommendations.append(
                "Treat evidence_note text as an active experimental variable; note-only evidence moved decisions, so sentence-only should be the safer promotion candidate."
            )
        if int(note_metrics.get("harmful_replace_count") or 0) > int(
            control_metrics.get("harmful_replace_count") or 0
        ):
            recommendations.append(
                "Do not promote raw evidence_note text without scrubbing; the note-only diagnostic widened harmful replacements."
            )
    if sentence_only:
        sentence_metrics = _as_mapping(sentence_only.get("generated_active_only"))
        control_metrics = _as_mapping(control.get("generated_active_only"))
        if float(sentence_metrics.get("decision_accuracy") or 0.0) >= float(
            control_metrics.get("decision_accuracy") or 0.0
        ):
            recommendations.append(
                "Prefer sentence-only evidence for the next generated batch because it preserves or improves the control without explanatory-note leakage."
            )
        else:
            recommendations.append(
                "Keep sentence-only as the first promotion candidate, but measure the recall tradeoff because it underperforms the current sentence-plus-note control."
            )
    if conservative:
        conservative_metrics = _as_mapping(conservative.get("generated_active_only"))
        if int(conservative_metrics.get("harmful_replace_count") or 0) <= int(
            _as_mapping(control.get("generated_active_only")).get("harmful_replace_count") or 0
        ):
            recommendations.append(
                "Use the conservative sentence-only view as the safety check before any paid scale-up; it removes high-overlap and weak-POS rows while keeping the denominator fixed."
            )
    if any(bool(audit.get("target_lemma_in_evidence_note")) for audit in item_audits):
        recommendations.append(
            "Add an admission or postprocess guard for target lemmas inside evidence_note, even though sentence-level target leakage was already blocked."
        )
    return recommendations


def _case_change_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts = {"fixed": 0, "regressed": 0, "still_correct": 0, "still_wrong": 0}
    for row in rows:
        gold = row.get("gold_decision")
        base = row.get("base_predicted_decision")
        candidate = row.get("candidate_predicted_decision")
        if candidate == gold and base != gold:
            counts["fixed"] += 1
        elif candidate != gold and base == gold:
            counts["regressed"] += 1
        elif candidate == gold:
            counts["still_correct"] += 1
        else:
            counts["still_wrong"] += 1
    return counts


def _case_digest(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "case_id": str(row.get("case_id") or ""),
        "family_id": str(row.get("family_id") or ""),
        "gold_decision": str(row.get("gold_decision") or ""),
        "base_predicted_decision": str(row.get("base_predicted_decision") or ""),
        "candidate_predicted_decision": str(row.get("candidate_predicted_decision") or ""),
        "active_score_delta": row.get("active_score_delta"),
        "sentence": str(row.get("sentence") or ""),
    }


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
