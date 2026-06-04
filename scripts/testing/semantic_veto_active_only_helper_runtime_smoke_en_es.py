#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_source_packaging"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.rulegen_outputs import build_snapshot, write_rulegen_outputs  # noqa: E402
from lexishift_core.helper.use_cases.semantic_pack_install import (  # noqa: E402
    build_rules_from_semantic_inventory,
    normalize_semantic_inventory_for_helper,
)
from lexishift_core.helper.use_cases.semantic_admission import semantic_admit_batch  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402


DEFAULT_DATASET = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_CANDIDATE_INVENTORY = (
    EXPERIMENT_ROOT / "en-es-active-only-poc-v5-inventory-replay-latest_semantic_inventory.json"
)
DEFAULT_FIXTURE_ROOT = EXPERIMENT_ROOT / "en-es-active-only-poc-v5-helper-runtime-smoke-data-root"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_helper_runtime_smoke_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_active_only_helper_runtime_smoke_en_es_latest.md"
)
DEFAULT_PROFILE_ID = "default"
DEFAULT_DECISION_POLICY_ID = ""
ACTIVE_ONLY_COMPETITION_MODE = "active_only_anchor_cue"
ACTIVE_ONLY_SELECTION_POLICY = "active_only_anchor_cue_v1"
MIXED_SELECTION_POLICY = "active_only_anchor_cue_with_repaired_shadows_v1"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Publish the active-only en-es semantic-veto PoC into an isolated helper data root "
            "and call the real helper semantic_admit_batch path."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--candidate-inventory", type=Path, default=DEFAULT_CANDIDATE_INVENTORY)
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURE_ROOT)
    parser.add_argument("--profile-id", default=DEFAULT_PROFILE_ID)
    parser.add_argument(
        "--decision-policy-id",
        default=DEFAULT_DECISION_POLICY_ID,
        help=(
            "Optional helper decision policy override. Omit to exercise the browser-style "
            "auto-selected policy for the active-only fixture."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--keep-existing-fixture", action="store_true")
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_helper_runtime_smoke_report(
        dataset_payload=_load_json(args.dataset),
        candidate_inventory_payload=_load_json(args.candidate_inventory),
        dataset_path=args.dataset,
        candidate_inventory_path=args.candidate_inventory,
        fixture_root=args.fixture_root,
        profile_id=args.profile_id,
        decision_policy_id=args.decision_policy_id,
        reset_fixture=not args.keep_existing_fixture,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_helper_runtime_smoke_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_helper_runtime_smoke_report(
    *,
    dataset_payload: Mapping[str, object],
    candidate_inventory_payload: Mapping[str, object],
    dataset_path: Path | None = None,
    candidate_inventory_path: Path | None = None,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    profile_id: str = DEFAULT_PROFILE_ID,
    decision_policy_id: str = DEFAULT_DECISION_POLICY_ID,
    reset_fixture: bool = True,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    normalized_profile = str(profile_id or "").strip() or DEFAULT_PROFILE_ID
    if reset_fixture:
        _reset_fixture_root(fixture_root)
    paths = build_helper_paths(fixture_root)
    inventory = normalize_semantic_inventory_for_helper(
        candidate_inventory_payload,
        pair="en-es",
        profile_id=normalized_profile,
        generated_at=generated_at,
    )
    rules = build_rules_from_semantic_inventory(
        inventory,
        pair="en-es",
        rule_source="semantic_veto_active_only_helper_runtime_smoke",
        rule_source_type="semantic_veto_candidate",
    )
    snapshot = build_snapshot(
        rules=rules,
        pair="en-es",
        max_targets=len(rules) or 1,
        max_sources=10,
        generated_at=generated_at,
    )
    write_rulegen_outputs(
        paths=paths,
        pair="en-es",
        profile_id=normalized_profile,
        rules=rules,
        snapshot=snapshot,
        semantic_inventory=inventory,
    )
    matches = _build_matches_from_dataset(dataset_payload, inventory=inventory)
    response = semantic_admit_batch(
        paths,
        payload={
            "schema_version": 1,
            "pair": "en-es",
            "profile_id": normalized_profile,
            "decision_policy_id": str(decision_policy_id or "").strip(),
            "fallback_policy": "abstain_on_unavailable",
            "surface_kind": "helper_runtime_smoke",
            "matches": matches,
        },
    )
    metrics = _metrics(matches=matches, response=response, inventory=inventory)
    generated_paths = {
        "fixture_data_root": str(fixture_root.resolve()),
        "ruleset_path": str(paths.ruleset_path("en-es", profile_id=normalized_profile).resolve()),
        "snapshot_path": str(paths.snapshot_path("en-es", profile_id=normalized_profile).resolve()),
        "semantic_inventory_path": str(
            paths.semantic_inventory_path("en-es", profile_id=normalized_profile).resolve()
        ),
        "publication_manifest_path": str(
            paths.publication_manifest_path("en-es", profile_id=normalized_profile).resolve()
        ),
    }
    issues = _issues(metrics=metrics, generated_paths=generated_paths)
    status = "ok" if not issues else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "manual_testing_ready" if status == "ok" else "runtime_smoke_needs_review",
        "generated_at": generated_at,
        "pair": "en-es",
        "profile_id": normalized_profile,
        "inputs": {
            "dataset_path": _repo_path(dataset_path),
            "candidate_inventory_path": _repo_path(candidate_inventory_path),
        },
        "fixture": generated_paths,
        "methodology": {
            "scope": "isolated_helper_publication_and_semantic_admit_batch_smoke",
            "runtime_policy_change": "active_only_competition_sets_can_score_without_shadows",
            "decision_policy_id": response.get("decision_policy_id"),
            "fallback_policy": response.get("fallback_policy"),
            "data_root_isolation": "fixture root under docs/test_outputs; default user profile data is not mutated",
            "publication_family": [
                "ruleset",
                "snapshot",
                "semantic_inventory",
                "publication_manifest",
            ],
        },
        "summary": metrics,
        "sample_decisions": _sample_decisions(matches=matches, response=response, limit=16),
        "manual_test_notes": [
            "The fixture data root is isolated; point LEXISHIFT_DATA_DIR at it for manual helper/app tests.",
            "With no explicit override, active-only fixture inventories auto-select en_es_sentence_veto_v2.",
            "The production default en_es_sentence_veto_v3 still requires sentence_transformers/model availability.",
            "Expected user-facing outcome remains binary: replace or abstain.",
        ],
        "issues": issues,
    }


def render_helper_runtime_smoke_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    fixture = _as_mapping(report.get("fixture"))
    methodology = _as_mapping(report.get("methodology"))
    lines = [
        "# en-es Semantic Veto Active-Only Helper Runtime Smoke",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Fixture data root: `{fixture.get('fixture_data_root', '')}`",
        f"- Profile: `{report.get('profile_id', '')}`",
        f"- Decision policy: `{methodology.get('decision_policy_id', '')}`",
        f"- Fallback policy: `{methodology.get('fallback_policy', '')}`",
        "",
        "## Publication Family",
        "",
        f"- Ruleset: `{fixture.get('ruleset_path', '')}`",
        f"- Snapshot: `{fixture.get('snapshot_path', '')}`",
        f"- Semantic inventory: `{fixture.get('semantic_inventory_path', '')}`",
        f"- Manifest: `{fixture.get('publication_manifest_path', '')}`",
        "",
        "## Runtime Smoke Metrics",
        "",
        f"- Rules: `{summary.get('rule_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Cases: `{summary.get('case_count', 0)}`",
        f"- Active-only competition sets: `{summary.get('active_only_competition_set_count', 0)}`",
        f"- Shadowed competition sets: `{summary.get('shadowed_competition_set_count', 0)}`",
        f"- Policy decisions: `{summary.get('policy_decision_count', 0)}`",
        f"- Fallback decisions: `{summary.get('fallback_decision_count', 0)}`",
        f"- Decision accuracy on repaired-full smoke denominator: "
        f"`{_fmt(summary.get('decision_accuracy'))}`",
        f"- Replace recall: `{_fmt(summary.get('replace_recall'))}`",
        f"- Harmful replaces: `{summary.get('harmful_replace_count', 0)}`",
        f"- False abstains: `{summary.get('false_abstain_count', 0)}`",
        "",
        "## Manual Test Notes",
        "",
    ]
    lines.extend(f"- {item}" for item in report.get("manual_test_notes", ()))
    lines.extend(
        [
            "",
            "Use this environment override for manual helper/app smoke tests:",
            "",
            "```bash",
            f"export LEXISHIFT_DATA_DIR='{fixture.get('fixture_data_root', '')}'",
            "```",
            "",
            "## Sample Decisions",
            "",
            "| Case | Gold | Decision | Source | Active | Shadow | Margin | Sentence |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in _mapping_rows(report.get("sample_decisions")):
        lines.append(
            f"| `{row.get('case_id', '')}` | `{row.get('gold_decision', '')}` | "
            f"`{row.get('decision', '')}` | `{row.get('decision_source', '')}` | "
            f"{_fmt(row.get('active_score'))} | {_fmt(row.get('top_shadow_score'))} | "
            f"{_fmt(row.get('score_margin'))} | {_markdown_cell(row.get('sentence'))} |"
        )
    if report.get("issues"):
        lines.extend(["", "## Issues", ""])
        lines.extend(f"- `{item}`" for item in report.get("issues", ()))
    return "\n".join(lines) + "\n"


def _normalize_candidate_inventory_for_helper(
    payload: Mapping[str, object],
    *,
    profile_id: str,
    generated_at: str,
) -> dict[str, object]:
    inventory = deepcopy(dict(payload))
    triggers = _mapping_copy(inventory.get("triggers"))
    competition_sets = _mapping_copy(inventory.get("competition_sets"))
    sense_trigger_ids = _sense_trigger_ids(competition_sets)
    senses: dict[str, object] = {}
    for sense_id, raw_sense in _mapping_copy(inventory.get("senses")).items():
        sense = dict(raw_sense)
        sense["sense_id"] = str(sense.get("sense_id") or sense_id)
        sense["trigger_id"] = str(sense.get("trigger_id") or sense_trigger_ids.get(sense_id) or "")
        sense["status"] = str(sense.get("status") or "ready")
        sense["provider"] = str(sense.get("provider") or "semantic_veto_repaired_full_dataset")
        sense["locator"] = _as_mapping(sense.get("locator")) or {
            "provider": sense["provider"],
            "locator_kind": "opaque",
            "opaque_id": sense_id,
        }
        evidence_views = _as_mapping(sense.get("evidence_views"))
        if "sense_label" not in sense and evidence_views.get("sense_label"):
            sense["sense_label"] = str(evidence_views.get("sense_label") or "")
        if "sense_label" not in sense:
            sense["sense_label"] = str(sense.get("target_lemma") or sense_id)
        senses[sense_id] = sense
    normalized_competition_sets: dict[str, object] = {}
    for competition_set_id, raw_set in competition_sets.items():
        competition_set = dict(raw_set)
        shadow_sense_ids = [
            str(item or "").strip()
            for item in competition_set.get("shadow_sense_ids", ())
            if str(item or "").strip()
        ]
        competition_set["competition_set_id"] = str(
            competition_set.get("competition_set_id") or competition_set_id
        )
        competition_set["status"] = "ready"
        competition_set["shadow_sense_ids"] = shadow_sense_ids
        if shadow_sense_ids:
            competition_set["selection_mode"] = "mixed"
            competition_set["selection_policy_version"] = MIXED_SELECTION_POLICY
        else:
            competition_set["selection_mode"] = "active_only"
            competition_set["selection_policy_version"] = ACTIVE_ONLY_SELECTION_POLICY
        normalized_competition_sets[competition_set_id] = competition_set
    return {
        "schema_version": 1,
        "pair": "en-es",
        "profile_id": profile_id,
        "generated_at": generated_at,
        "capability": {
            "pointer_modes": ["trigger_only"],
            "default_unavailable_reason_code": "missing_source_sense_locator",
            "competition_mode": ACTIVE_ONLY_COMPETITION_MODE,
            "competition_reason_code": "missing_shadow_selection",
            "phrase_mode": "not_published",
            "phrase_reason_code": "missing_phrase_inventory",
        },
        "triggers": triggers,
        "senses": senses,
        "competition_sets": normalized_competition_sets,
        "phrase_sets": _mapping_copy(inventory.get("phrase_sets")),
    }


def _build_rules_from_inventory(inventory: Mapping[str, object]) -> tuple[VocabRule, ...]:
    triggers = _as_mapping(inventory.get("triggers"))
    senses = _as_mapping(inventory.get("senses"))
    rules: list[VocabRule] = []
    for competition_set_id, competition_set in sorted(
        _as_mapping(inventory.get("competition_sets")).items()
    ):
        if not isinstance(competition_set, Mapping):
            continue
        active_sense_id = str(competition_set.get("active_sense_id") or "").strip()
        active_sense = _as_mapping(senses.get(active_sense_id))
        trigger_id = str(competition_set.get("trigger_id") or "").strip()
        trigger = _as_mapping(triggers.get(trigger_id))
        source_phrase = str(trigger.get("source_phrase") or "").strip()
        replacement = str(active_sense.get("target_lemma") or "").strip()
        if not source_phrase or not replacement:
            continue
        rules.append(
            VocabRule(
                source_phrase=source_phrase,
                replacement=replacement,
                metadata=RuleMetadata(
                    language_pair="en-es",
                    source="semantic_veto_active_only_helper_runtime_smoke",
                    source_type="semantic_veto_candidate",
                    semantic_admission={
                        "schema_version": 1,
                        "status": "ready",
                        "trigger_id": trigger_id,
                        "sense_id": active_sense_id,
                        "competition_set_id": str(competition_set_id),
                    },
                ),
            )
        )
    return tuple(rules)


def _build_matches_from_dataset(
    dataset_payload: Mapping[str, object],
    *,
    inventory: Mapping[str, object],
) -> list[dict[str, object]]:
    active_by_family = {
        _family_id_from_trigger_id(str(competition_set.get("trigger_id") or "")): competition_set
        for competition_set in _mapping_rows(
            _as_mapping(inventory.get("competition_sets")).values()
        )
    }
    matches: list[dict[str, object]] = []
    for family in _mapping_rows(dataset_payload.get("families")):
        family_id = str(family.get("family_id") or "").strip()
        competition_set = _as_mapping(active_by_family.get(family_id))
        if not competition_set:
            continue
        active_sense_id = str(competition_set.get("active_sense_id") or "").strip()
        trigger_id = str(competition_set.get("trigger_id") or "").strip()
        trigger = str(family.get("trigger") or "").strip()
        for case in _mapping_rows(family.get("cases")):
            matches.append(
                {
                    "match_id": str(case.get("case_id") or ""),
                    "source_phrase": trigger,
                    "context_text": str(case.get("sentence") or ""),
                    "gold_decision": str(case.get("gold_decision") or ""),
                    "gold_winner": str(case.get("gold_winner") or ""),
                    "semantic_admission": {
                        "schema_version": 1,
                        "status": "ready",
                        "trigger_id": trigger_id,
                        "sense_id": active_sense_id,
                        "competition_set_id": str(competition_set.get("competition_set_id") or ""),
                    },
                }
            )
    return matches


def _metrics(
    *,
    matches: Sequence[Mapping[str, object]],
    response: Mapping[str, object],
    inventory: Mapping[str, object],
) -> dict[str, object]:
    decisions = _mapping_rows(response.get("decisions"))
    decision_by_id = {str(row.get("match_id") or ""): row for row in decisions}
    total = len(matches)
    correct = 0
    gold_replace = 0
    false_abstain = 0
    harmful = 0
    predicted_replace = 0
    fallback_reasons: Counter[str] = Counter()
    for match in matches:
        gold = str(match.get("gold_decision") or "")
        decision = _as_mapping(decision_by_id.get(str(match.get("match_id") or "")))
        predicted = str(decision.get("decision") or "")
        if gold == "replace":
            gold_replace += 1
            if predicted != "replace":
                false_abstain += 1
        if predicted == "replace":
            predicted_replace += 1
            if gold != "replace":
                harmful += 1
        if predicted == gold:
            correct += 1
        if str(decision.get("decision_source") or "") == "fallback_policy":
            fallback_reasons.update(str(code) for code in decision.get("reason_codes", ()))
    competition_sets = _mapping_rows(_as_mapping(inventory.get("competition_sets")).values())
    source_counts = Counter(str(row.get("decision_source") or "") for row in decisions)
    return {
        "rule_count": len(_as_mapping(inventory.get("competition_sets"))),
        "family_count": len(competition_sets),
        "case_count": total,
        "decision_count": len(decisions),
        "active_only_competition_set_count": sum(
            1 for row in competition_sets if str(row.get("selection_mode") or "") == "active_only"
        ),
        "shadowed_competition_set_count": sum(
            1 for row in competition_sets if row.get("shadow_sense_ids")
        ),
        "policy_decision_count": int(source_counts.get("policy", 0)),
        "fallback_decision_count": int(source_counts.get("fallback_policy", 0)),
        "fallback_reason_counts": dict(sorted(fallback_reasons.items())),
        "decision_accuracy": correct / total if total else 0.0,
        "replace_recall": (gold_replace - false_abstain) / gold_replace if gold_replace else 0.0,
        "harmful_replace_count": harmful,
        "false_abstain_count": false_abstain,
        "predicted_replace_cases": predicted_replace,
    }


def _sample_decisions(
    *,
    matches: Sequence[Mapping[str, object]],
    response: Mapping[str, object],
    limit: int,
) -> list[dict[str, object]]:
    decisions = {
        str(row.get("match_id") or ""): row for row in _mapping_rows(response.get("decisions"))
    }
    rows: list[dict[str, object]] = []
    for match in matches:
        decision = _as_mapping(decisions.get(str(match.get("match_id") or "")))
        if not decision:
            continue
        rows.append(
            {
                "case_id": str(match.get("match_id") or ""),
                "gold_decision": str(match.get("gold_decision") or ""),
                "decision": str(decision.get("decision") or ""),
                "decision_source": str(decision.get("decision_source") or ""),
                "active_score": float(decision.get("active_score") or 0.0),
                "top_shadow_score": float(decision.get("top_shadow_score") or 0.0),
                "score_margin": float(decision.get("score_margin") or 0.0),
                "sentence": str(match.get("context_text") or ""),
            }
        )
    return rows[:limit]


def _issues(*, metrics: Mapping[str, object], generated_paths: Mapping[str, str]) -> list[str]:
    issues: list[str] = []
    if int(metrics.get("rule_count") or 0) == 0:
        issues.append("no_rules_published")
    if int(metrics.get("case_count") or 0) == 0:
        issues.append("no_runtime_smoke_cases")
    if int(metrics.get("decision_count") or 0) != int(metrics.get("case_count") or 0):
        issues.append("helper_decision_count_mismatch")
    if int(metrics.get("fallback_decision_count") or 0) > 0:
        issues.append("helper_runtime_fallback_decisions_present")
    for key, raw_path in generated_paths.items():
        if key == "fixture_data_root":
            continue
        if not Path(raw_path).exists():
            issues.append(f"missing_{key}")
    return issues


def _sense_trigger_ids(competition_sets: Mapping[str, object]) -> dict[str, str]:
    trigger_ids: dict[str, str] = {}
    for competition_set in _mapping_rows(competition_sets.values()):
        trigger_id = str(competition_set.get("trigger_id") or "").strip()
        active_sense_id = str(competition_set.get("active_sense_id") or "").strip()
        if active_sense_id and trigger_id:
            trigger_ids[active_sense_id] = trigger_id
        for shadow_sense_id in competition_set.get("shadow_sense_ids", ()):
            normalized = str(shadow_sense_id or "").strip()
            if normalized and trigger_id:
                trigger_ids[normalized] = trigger_id
    return trigger_ids


def _family_id_from_trigger_id(trigger_id: str) -> str:
    suffix = ":trigger"
    return trigger_id[: -len(suffix)] if trigger_id.endswith(suffix) else trigger_id


def _reset_fixture_root(path: Path) -> None:
    if not path.exists():
        return
    resolved = path.resolve()
    experiment_root = EXPERIMENT_ROOT.resolve()
    if resolved == experiment_root or experiment_root not in resolved.parents:
        raise ValueError(f"Refusing to remove non-experiment fixture root: {resolved}")
    shutil.rmtree(resolved)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_copy(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): dict(entry) if isinstance(entry, Mapping) else entry
        for key, entry in value.items()
        if str(key).strip()
    }


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Mapping):
        iterable = value.values()
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        iterable = value
    elif not isinstance(value, (str, bytes)):
        try:
            iterable = iter(value)  # type: ignore[arg-type]
        except TypeError:
            return []
    else:
        return []
    return [item for item in iterable if isinstance(item, Mapping)]


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _fmt(value: object) -> str:
    return f"{float(value or 0.0):.4f}"


def _markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
