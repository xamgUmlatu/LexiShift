#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_source_packaging"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.rulegen.semantic_routing_runtime_policy import (  # noqa: E402
    SemanticDecisionPolicyConfig,
    evaluate_runtime_semantic_match,
)
from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    RuntimeSimilarityBackend,
    build_runtime_context_views,
    resolve_runtime_evidence_text,
)


DEFAULT_DATASET = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_NORMALIZED_EVIDENCE = (
    EXPERIMENT_ROOT / "en-es-active-only-poc-v5-source-packaging-latest_normalized_evidence.json"
)
DEFAULT_CANDIDATE_INVENTORY_OUT = (
    EXPERIMENT_ROOT / "en-es-active-only-poc-v5-inventory-replay-latest_semantic_inventory.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_inventory_replay_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_inventory_replay_en_es_latest.md"
)
DEFAULT_POLICY = SemanticDecisionPolicyConfig(
    policy_id="active_only_inventory_replay_tfidf_v1",
    pair="en-es",
    scorer_id="tfidf_cosine",
    context_view="masked_sentence",
    evidence_view="all_evidence_text",
    min_active_score=0.05,
    min_margin=0.0,
    phrase_control_mode="off",
    active_rescue_mode="off",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay active-only packaged semantic-veto evidence through an inventory-shaped "
            "runtime evaluator without publishing helper artifacts."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--normalized-evidence", type=Path, default=DEFAULT_NORMALIZED_EVIDENCE)
    parser.add_argument(
        "--candidate-inventory-out", type=Path, default=DEFAULT_CANDIDATE_INVENTORY_OUT
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bundle = build_active_only_inventory_replay_bundle(
        dataset_payload=_load_json(args.dataset),
        normalized_evidence_payload=_load_json(args.normalized_evidence),
        dataset_path=args.dataset,
        normalized_evidence_path=args.normalized_evidence,
    )
    for path, payload in (
        (args.candidate_inventory_out, bundle["candidate_inventory"]),
        (args.json_out, bundle["report"]),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_active_only_inventory_replay_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote candidate inventory to {args.candidate_inventory_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and bundle["report"]["status"] != "ok":
        return 1
    return 0


def build_active_only_inventory_replay_bundle(
    *,
    dataset_payload: Mapping[str, object],
    normalized_evidence_payload: Mapping[str, object],
    dataset_path: Path | None = None,
    normalized_evidence_path: Path | None = None,
    policy: SemanticDecisionPolicyConfig = DEFAULT_POLICY,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    evidence_rows = _mapping_rows(normalized_evidence_payload.get("rows"))
    family_ids = {
        str(_as_mapping(row.get("metadata")).get("family_id") or "").strip()
        for row in evidence_rows
        if str(_as_mapping(row.get("metadata")).get("family_id") or "").strip()
    }
    selected_families = [
        dict(family)
        for family in _mapping_rows(dataset_payload.get("families"))
        if str(family.get("family_id") or "").strip() in family_ids
    ]
    issues: list[str] = []
    if not evidence_rows:
        issues.append("no_packaged_evidence_rows")
    if not selected_families:
        issues.append("no_matching_dataset_families")
    base_inventory = _build_inventory(
        selected_families,
        generated_at=generated_at,
        evidence_rows=(),
    )
    candidate_inventory = _build_inventory(
        selected_families,
        generated_at=generated_at,
        evidence_rows=evidence_rows,
    )
    matches = _build_matches(selected_families)
    base_results = _evaluate_matches(matches=matches, inventory=base_inventory, policy=policy)
    candidate_results = _evaluate_matches(
        matches=matches,
        inventory=candidate_inventory,
        policy=policy,
    )
    base_metrics = _metrics(base_results)
    candidate_metrics = _metrics(candidate_results)
    comparison = _comparison(base_metrics, candidate_metrics)
    applications = _application_rows(
        evidence_rows=evidence_rows, selected_families=selected_families
    )
    unapplied_count = sum(1 for row in applications if row["action"] != "active_evidence_appended")
    if unapplied_count:
        issues.append("some_packaged_rows_not_applied_to_inventory")
    status = "ok" if not issues else "review"
    report = {
        "schema_version": 1,
        "status": status,
        "decision": (
            "inventory_shaped_replay_ready_for_runtime_smoke"
            if status == "ok"
            else "inventory_shaped_replay_needs_review"
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "inputs": {
            "dataset_path": _repo_path(dataset_path),
            "normalized_evidence_path": _repo_path(normalized_evidence_path),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "helper_publication_change": "none",
            "policy_id": policy.policy_id,
            "scorer_id": policy.scorer_id,
            "context_view": policy.context_view,
            "evidence_view": policy.evidence_view,
            "min_active_score": policy.min_active_score,
            "min_margin": policy.min_margin,
            "phrase_control_mode": policy.phrase_control_mode,
            "active_rescue_mode": policy.active_rescue_mode,
        },
        "summary": {
            "family_count": len(selected_families),
            "case_count": len(matches),
            "packaged_row_count": len(evidence_rows),
            "applied_row_count": sum(
                1 for row in applications if row["action"] == "active_evidence_appended"
            ),
            "unapplied_row_count": unapplied_count,
            "base": base_metrics,
            "candidate": candidate_metrics,
            "comparison": comparison,
        },
        "application_rows": applications,
        "changed_cases": _changed_cases(
            base_results=base_results, candidate_results=candidate_results
        ),
        "runtime_boundary": [
            "candidate inventory is an experiment artifact, not a helper-published sidecar",
            "replay uses the no-spend TF-IDF policy that produced the active-only score-contribution result",
            "production helper smoke still needs the actual publication family and configured runtime policy",
        ],
        "issues": issues,
    }
    return {
        "candidate_inventory": candidate_inventory,
        "report": report,
    }


def render_active_only_inventory_replay_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    base = _as_mapping(summary.get("base"))
    candidate = _as_mapping(summary.get("candidate"))
    comparison = _as_mapping(summary.get("comparison"))
    methodology = _as_mapping(report.get("methodology"))
    lines = [
        "# en-es Semantic Veto Active-Only Inventory Replay",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Cases: `{summary.get('case_count', 0)}`",
        f"- Packaged/applied rows: `{summary.get('packaged_row_count', 0)}` / "
        f"`{summary.get('applied_row_count', 0)}`",
        "",
        "## Policy",
        "",
        f"- Policy: `{methodology.get('policy_id', '')}`",
        f"- Scorer/context/evidence: `{methodology.get('scorer_id', '')}` / "
        f"`{methodology.get('context_view', '')}` / `{methodology.get('evidence_view', '')}`",
        f"- Thresholds: min active `{methodology.get('min_active_score', '')}`, "
        f"min margin `{methodology.get('min_margin', '')}`",
        "",
        "## Metrics",
        "",
        "| Mode | Accuracy | Replace recall | Harmful | False abstains | Predicted replaces |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        _metric_row("base", base),
        _metric_row("candidate", candidate),
        "",
        "## Delta",
        "",
        f"- Decision accuracy: `{_fmt_delta(comparison.get('decision_accuracy_delta'))}`",
        f"- Replace recall: `{_fmt_delta(comparison.get('replace_recall_delta'))}`",
        f"- Harmful replacements: `{_fmt_int_delta(comparison.get('harmful_replace_delta'))}`",
        f"- False abstains: `{_fmt_int_delta(comparison.get('false_abstain_delta'))}`",
        "",
        "## Changed Cases",
        "",
        "| Case | Gold | Base | Candidate | Sentence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in _mapping_rows(report.get("changed_cases"))[:30]:
        lines.append(
            f"| `{row.get('case_id', '')}` | `{row.get('gold_decision', '')}` | "
            f"`{row.get('base_decision', '')}` | `{row.get('candidate_decision', '')}` | "
            f"{_markdown_cell(row.get('sentence'))} |"
        )
    lines.extend(["", "## Runtime Boundary", ""])
    lines.extend(f"- `{item}`" for item in report.get("runtime_boundary", ()))
    if report.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- `{item}`" for item in report.get("issues", ()))
    return "\n".join(lines) + "\n"


def _build_inventory(
    families: Sequence[Mapping[str, object]],
    *,
    generated_at: str,
    evidence_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    evidence_by_family = _evidence_by_family(evidence_rows)
    triggers: dict[str, object] = {}
    senses: dict[str, object] = {}
    competition_sets: dict[str, object] = {}
    for family in families:
        family_id = str(family.get("family_id") or "").strip()
        trigger = str(family.get("trigger") or "").strip()
        trigger_id = _trigger_id(family_id)
        triggers[trigger_id] = {
            "trigger_id": trigger_id,
            "source_phrase": trigger,
            "normalized_source_phrase": " ".join(trigger.lower().split()),
            "token_count": max(1, len(trigger.split())),
        }
        active = deepcopy(dict(_as_mapping(family.get("active"))))
        _append_packaged_evidence(active, evidence_by_family.get(family_id, ()))
        if active:
            senses[str(active.get("sense_id") or "")] = active
        shadow_ids: list[str] = []
        for shadow in _mapping_rows(family.get("shadows")):
            shadow_record = deepcopy(dict(shadow))
            shadow_id = str(shadow_record.get("sense_id") or "").strip()
            if shadow_id:
                shadow_ids.append(shadow_id)
                senses[shadow_id] = shadow_record
        competition_set_id = _competition_set_id(family_id)
        competition_sets[competition_set_id] = {
            "competition_set_id": competition_set_id,
            "trigger_id": trigger_id,
            "status": "ready",
            "active_sense_id": str(active.get("sense_id") or ""),
            "shadow_sense_ids": shadow_ids,
            "selection_mode": "offline_inventory_replay",
            "selection_policy_version": "active_only_inventory_replay_v1",
        }
    return {
        "schema_version": 1,
        "pair": "en-es",
        "profile_id": "inventory_replay",
        "generated_at": generated_at,
        "capability": {
            "competition_mode": "offline_inventory_replay",
            "phrase_mode": "not_published",
        },
        "triggers": triggers,
        "senses": senses,
        "competition_sets": competition_sets,
        "phrase_sets": {},
    }


def _append_packaged_evidence(
    active_sense: dict[str, object],
    evidence_rows: Sequence[Mapping[str, object]],
) -> None:
    if not evidence_rows:
        return
    evidence_views = active_sense.setdefault("evidence_views", {})
    if not isinstance(evidence_views, dict):
        return
    existing = str(evidence_views.get("all_evidence_text") or "").strip()
    generated_parts = [
        str(row.get("evidence_text") or "").strip()
        for row in evidence_rows
        if str(row.get("relation_type") or "") == "anchor_cue"
        and str(row.get("evidence_text") or "").strip()
    ]
    if not generated_parts:
        return
    appended = " | ".join(f"generated evidence: {part}" for part in generated_parts)
    evidence_views["all_evidence_text"] = f"{existing} | {appended}" if existing else appended


def _build_matches(families: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for family in families:
        family_id = str(family.get("family_id") or "").strip()
        trigger = str(family.get("trigger") or "").strip()
        active = _as_mapping(family.get("active"))
        for case in _mapping_rows(family.get("cases")):
            matches.append(
                {
                    "match_id": str(case.get("case_id") or ""),
                    "family_id": family_id,
                    "context_text": str(case.get("sentence") or ""),
                    "source_phrase": trigger,
                    "gold_decision": str(case.get("gold_decision") or ""),
                    "gold_winner": str(case.get("gold_winner") or ""),
                    "semantic_admission": {
                        "schema_version": 1,
                        "status": "ready",
                        "trigger_id": _trigger_id(family_id),
                        "sense_id": str(active.get("sense_id") or ""),
                        "competition_set_id": _competition_set_id(family_id),
                    },
                }
            )
    return matches


def _evaluate_matches(
    *,
    matches: Sequence[Mapping[str, object]],
    inventory: Mapping[str, object],
    policy: SemanticDecisionPolicyConfig,
) -> list[dict[str, object]]:
    scorer = RuntimeSimilarityBackend(scorer_id=policy.scorer_id, model_name=policy.model_name)
    scorer.fit(_collect_replay_fit_texts(matches=matches, inventory=inventory, policy=policy))
    senses = _as_mapping(inventory.get("senses"))
    competition_sets = _as_mapping(inventory.get("competition_sets"))
    results: list[dict[str, object]] = []
    for match in matches:
        admission = _as_mapping(match.get("semantic_admission"))
        active_sense = _as_mapping(senses.get(str(admission.get("sense_id") or "")))
        competition_set = _as_mapping(
            competition_sets.get(str(admission.get("competition_set_id") or ""))
        )
        shadow_senses = [
            _as_mapping(senses.get(str(shadow_id or "").strip()))
            for shadow_id in competition_set.get("shadow_sense_ids", ())
            if isinstance(senses.get(str(shadow_id or "").strip()), Mapping)
        ]
        family_pos_tags = tuple(
            {
                str(value or "").strip()
                for value in (
                    active_sense.get("canonical_pos"),
                    *(shadow.get("canonical_pos") for shadow in shadow_senses),
                )
                if str(value or "").strip()
            }
        )
        result = evaluate_runtime_semantic_match(
            match_id=str(match.get("match_id") or ""),
            sentence=str(match.get("context_text") or ""),
            source_phrase=str(match.get("source_phrase") or ""),
            active_sense=active_sense,
            shadow_senses=shadow_senses,
            policy=policy,
            scorer=scorer,
            family_id=str(match.get("family_id") or ""),
            family_pos_tags=family_pos_tags,
        )
        results.append(
            {
                "case_id": str(match.get("match_id") or ""),
                "family_id": str(match.get("family_id") or ""),
                "sentence": str(match.get("context_text") or ""),
                "gold_decision": str(match.get("gold_decision") or ""),
                "gold_winner": str(match.get("gold_winner") or ""),
                "predicted_decision": result.predicted_decision,
                "predicted_winner": result.predicted_winner,
                "predicted_winner_type": result.predicted_winner_type,
                "active_score": result.active_score,
                "top_shadow_score": result.strongest_shadow_score,
                "score_margin": result.margin,
                "reason_codes": list(result.reason_codes),
            }
        )
    return results


def _collect_replay_fit_texts(
    *,
    matches: Sequence[Mapping[str, object]],
    inventory: Mapping[str, object],
    policy: SemanticDecisionPolicyConfig,
) -> list[str]:
    senses = _as_mapping(inventory.get("senses"))
    competition_sets = _as_mapping(inventory.get("competition_sets"))
    texts: list[str] = []
    for match in matches:
        admission = _as_mapping(match.get("semantic_admission"))
        active_sense = _as_mapping(senses.get(str(admission.get("sense_id") or "")))
        if active_sense:
            texts.append(
                resolve_runtime_evidence_text(active_sense, evidence_view=policy.evidence_view)
            )
        competition_set = _as_mapping(
            competition_sets.get(str(admission.get("competition_set_id") or ""))
        )
        for shadow_id in competition_set.get("shadow_sense_ids", ()):
            shadow = _as_mapping(senses.get(str(shadow_id or "").strip()))
            if shadow:
                texts.append(
                    resolve_runtime_evidence_text(shadow, evidence_view=policy.evidence_view)
                )
        context_views = build_runtime_context_views(
            str(match.get("context_text") or ""),
            source_phrase=str(match.get("source_phrase") or ""),
            mask_token=policy.mask_token,
            window_tokens=policy.window_tokens,
        )
        texts.append(str(context_views.get(policy.context_view) or "").strip())
    return [text for text in texts if str(text or "").strip()]


def _metrics(results: Sequence[Mapping[str, object]]) -> dict[str, object]:
    total = len(results)
    gold_replace = sum(1 for row in results if row.get("gold_decision") == "replace")
    correct = sum(1 for row in results if row.get("predicted_decision") == row.get("gold_decision"))
    predicted_replace = sum(1 for row in results if row.get("predicted_decision") == "replace")
    harmful = sum(
        1
        for row in results
        if row.get("predicted_decision") == "replace" and row.get("gold_decision") != "replace"
    )
    false_abstain = sum(
        1
        for row in results
        if row.get("predicted_decision") != "replace" and row.get("gold_decision") == "replace"
    )
    winner_rows = [row for row in results if str(row.get("gold_winner") or "").strip()]
    winner_correct = sum(
        1 for row in winner_rows if row.get("predicted_winner") == row.get("gold_winner")
    )
    return {
        "cases_total": total,
        "decision_accuracy": correct / total if total else 0.0,
        "replace_recall": (gold_replace - false_abstain) / gold_replace if gold_replace else 0.0,
        "harmful_replace_count": harmful,
        "false_abstain_count": false_abstain,
        "predicted_replace_cases": predicted_replace,
        "winner_accuracy": winner_correct / len(winner_rows) if winner_rows else 0.0,
    }


def _comparison(base: Mapping[str, object], candidate: Mapping[str, object]) -> dict[str, object]:
    return {
        "decision_accuracy_delta": round(
            float(candidate.get("decision_accuracy") or 0.0)
            - float(base.get("decision_accuracy") or 0.0),
            6,
        ),
        "replace_recall_delta": round(
            float(candidate.get("replace_recall") or 0.0)
            - float(base.get("replace_recall") or 0.0),
            6,
        ),
        "winner_accuracy_delta": round(
            float(candidate.get("winner_accuracy") or 0.0)
            - float(base.get("winner_accuracy") or 0.0),
            6,
        ),
        "harmful_replace_delta": int(candidate.get("harmful_replace_count") or 0)
        - int(base.get("harmful_replace_count") or 0),
        "false_abstain_delta": int(candidate.get("false_abstain_count") or 0)
        - int(base.get("false_abstain_count") or 0),
        "predicted_replace_delta": int(candidate.get("predicted_replace_cases") or 0)
        - int(base.get("predicted_replace_cases") or 0),
    }


def _changed_cases(
    *,
    base_results: Sequence[Mapping[str, object]],
    candidate_results: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    by_id = {str(row.get("case_id") or ""): row for row in candidate_results}
    changed: list[dict[str, object]] = []
    for base in base_results:
        case_id = str(base.get("case_id") or "")
        candidate = by_id.get(case_id)
        if not candidate:
            continue
        if base.get("predicted_decision") == candidate.get("predicted_decision"):
            continue
        changed.append(
            {
                "case_id": case_id,
                "family_id": str(base.get("family_id") or ""),
                "gold_decision": str(base.get("gold_decision") or ""),
                "base_decision": str(base.get("predicted_decision") or ""),
                "candidate_decision": str(candidate.get("predicted_decision") or ""),
                "sentence": str(base.get("sentence") or ""),
            }
        )
    return changed


def _application_rows(
    *,
    evidence_rows: Sequence[Mapping[str, object]],
    selected_families: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    family_ids = {str(family.get("family_id") or "").strip() for family in selected_families}
    rows: list[dict[str, object]] = []
    for row in evidence_rows:
        family_id = str(_as_mapping(row.get("metadata")).get("family_id") or "").strip()
        rows.append(
            {
                "evidence_id": str(row.get("evidence_id") or ""),
                "family_id": family_id,
                "trigger": str(row.get("trigger") or ""),
                "target": str(row.get("active_target") or ""),
                "action": "active_evidence_appended"
                if family_id in family_ids and row.get("relation_type") == "anchor_cue"
                else "not_applied",
            }
        )
    return rows


def _evidence_by_family(
    evidence_rows: Sequence[Mapping[str, object]],
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in evidence_rows:
        family_id = str(_as_mapping(row.get("metadata")).get("family_id") or "").strip()
        if family_id:
            grouped.setdefault(family_id, []).append(row)
    return grouped


def _trigger_id(family_id: str) -> str:
    return f"{family_id}:trigger"


def _competition_set_id(family_id: str) -> str:
    return f"{family_id}:competition:active-only-replay"


def _metric_row(label: str, metrics: Mapping[str, object]) -> str:
    return (
        f"| `{label}` | {_fmt(metrics.get('decision_accuracy'))} | "
        f"{_fmt(metrics.get('replace_recall'))} | "
        f"{metrics.get('harmful_replace_count', 0)} | "
        f"{metrics.get('false_abstain_count', 0)} | "
        f"{metrics.get('predicted_replace_cases', 0)} |"
    )


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _fmt(value: object) -> str:
    return f"{float(value or 0.0):.4f}"


def _fmt_delta(value: object) -> str:
    return f"{float(value or 0.0):+.4f}"


def _fmt_int_delta(value: object) -> str:
    return f"{int(value or 0):+d}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
