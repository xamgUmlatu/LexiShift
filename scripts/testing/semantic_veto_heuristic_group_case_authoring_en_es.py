#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_PILOT_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_pilot_en_es_latest.json"
DEFAULT_DATASET_OUT = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_heuristic_group_pilot_v1.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_case_authoring_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_case_authoring_en_es_latest.md"
)
DEFAULT_TRIGGER_SPECS_JSON = (
    TEST_INPUTS_ROOT / "semantic_veto_heuristic_group_case_authoring_specs_en_es.json"
)


@dataclass(frozen=True)
class ShadowSpec:
    key: str
    target_lemma: str
    canonical_pos: str
    sense_label: str
    gloss_text: str
    examples: tuple[str, ...]


@dataclass(frozen=True)
class CaseSpec:
    gold_type: str
    sentence: str
    winner: str
    reason: str


@dataclass(frozen=True)
class TriggerSpec:
    trigger: str
    target_lemma: str
    canonical_pos: str
    sense_label: str
    gloss_text: str
    examples: tuple[str, ...]
    human_polysemy_gauge: str
    expected_veto_difficulty: str
    shadow_contract: str
    review_notes: str
    shadows: tuple[ShadowSpec, ...]
    cases: tuple[CaseSpec, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize the frozen en-es heuristic-group manual review packet into a "
            "sentence-veto dataset and an authoring report. This is research data only."
        )
    )
    parser.add_argument("--pilot-json", type=Path, default=DEFAULT_PILOT_JSON)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    pilot = _load_json(args.pilot_json)
    report, dataset = build_heuristic_group_case_authoring_report(
        pilot_payload=pilot,
        pilot_path=args.pilot_json,
        dataset_path=args.dataset_out,
    )
    args.dataset_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.dataset_out.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_case_authoring_markdown(report), encoding="utf-8")
    print(f"Wrote dataset artifact to {args.dataset_out}")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_heuristic_group_case_authoring_report(
    *,
    pilot_payload: Mapping[str, object],
    pilot_path: Path | None = None,
    dataset_path: Path | None = None,
    trigger_specs: Mapping[str, TriggerSpec] | None = None,
    generated_at: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    if generated_at is None:
        generated_at = _utc_now()
    specs = dict(trigger_specs or TRIGGER_SPECS)
    packet_rows = _mapping_rows(pilot_payload.get("manual_review_packet"))
    row_by_trigger = {
        str(row.get("trigger") or "").strip().lower(): dict(row)
        for row in packet_rows
        if str(row.get("trigger") or "").strip()
    }
    missing_specs = sorted(trigger for trigger in row_by_trigger if trigger not in specs)
    unused_specs = sorted(trigger for trigger in specs if trigger not in row_by_trigger)
    authored_rows: list[dict[str, object]] = []
    families: list[dict[str, object]] = []
    case_type_counts: Counter[str] = Counter()
    contract_counts: Counter[str] = Counter()
    group_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for trigger, pilot_row in sorted(row_by_trigger.items(), key=_pilot_row_sort_key):
        spec = specs.get(trigger)
        if spec is None:
            continue
        family, authored_row = _family_from_spec(spec=spec, pilot_row=pilot_row)
        families.append(family)
        authored_rows.append(authored_row)
        contract_counts[spec.shadow_contract] += 1
        for case in family["cases"]:
            gold_type = str(
                _as_mapping(case.get("slice_dimensions")).get("manual_case_type", [""])[0]
            )
            case_type_counts[gold_type] += 1
            group_counts[str(pilot_row.get("group_id") or "")][gold_type] += 1
    dataset = {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "en_es_heuristic_group_pilot_v1",
        "description": (
            "Agent-authored first-pass sentence-veto cases for the frozen en-es "
            "frequency/polysemy heuristic groups. Research-only; not a runtime policy input."
        ),
        "families": families,
    }
    summary = {
        "pilot_manual_review_rows": len(packet_rows),
        "authored_trigger_count": len(authored_rows),
        "dataset_family_count": len(families),
        "dataset_case_count": sum(len(_sequence(family.get("cases"))) for family in families),
        "missing_authoring_specs": missing_specs,
        "unused_authoring_specs": unused_specs,
        "shadow_contract_counts": dict(sorted(contract_counts.items())),
        "case_type_counts": dict(sorted(case_type_counts.items())),
        "group_case_type_counts": {
            group_id: dict(sorted(counts.items()))
            for group_id, counts in sorted(group_counts.items())
        },
        "dataset_fingerprint": _fingerprint_dataset(dataset),
    }
    report = {
        "schema_version": 1,
        "status": "ok" if not missing_specs else "review",
        "decision": (
            "heuristic_group_case_authoring_dataset_ready_for_scoring"
            if not missing_specs
            else "heuristic_group_case_authoring_incomplete"
        ),
        "generated_at": generated_at,
        "pair": "en-es",
        "inputs": {
            "pilot_path": _repo_path(pilot_path),
            "pilot_id": str(pilot_payload.get("pilot_id") or ""),
            "pilot_fingerprint": str(pilot_payload.get("input_fingerprint") or ""),
        },
        "outputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": dataset["dataset_id"],
            "dataset_fingerprint": summary["dataset_fingerprint"],
        },
        "methodology": {
            "primary_selection_remains_pre_outcome": True,
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
            "manual_review_state": "agent_draft_human_review_pending",
            "low_polysemy_control_contract": (
                "When a selected low-polysemy control has no honest alternate sense, "
                "the packet records that and does not fabricate shadow-negative cases."
            ),
        },
        "summary": summary,
        "authored_triggers": authored_rows,
        "limitations": [
            "agent_authored_cases_need_human_review_before_promotion_claims",
            "low_polysemy_controls_are_not_shadow_balanced_when_no_honest_shadow_exists",
            "case_sentences_are_manual_draft_rows_not_representative_browsing_samples",
            "spanish_target_choices_are_plausible_research_targets_not_admitted_source_truth",
        ],
        "next_steps": [
            "Score this dataset with the existing sentence-veto harness as a diagnostic lane.",
            "Compare group-level positive allow and negative abstain rates without mixing sentinel rows into primary-heuristic claims.",
            "Human-review or replace any questionable target/shadow choices before treating the lane as locked evaluation.",
            "Use failures to decide whether frequency/polysemy predicts veto difficulty or whether richer source coverage dominates.",
        ],
    }
    return report, dataset


def render_case_authoring_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Heuristic Group Case Authoring",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Pilot: `{_as_mapping(report.get('inputs')).get('pilot_path', '')}`",
        f"- Dataset: `{_as_mapping(report.get('outputs')).get('dataset_path', '')}`",
        f"- Dataset fingerprint: `{summary.get('dataset_fingerprint', '')}`",
        f"- Authored triggers: `{summary.get('authored_trigger_count', 0)}`",
        f"- Dataset cases: `{summary.get('dataset_case_count', 0)}`",
        "",
        "## Methodology",
        "",
        "This packet materializes the frozen heuristic groups into a sentence-veto "
        "dataset without changing runtime policy. The primary groups still come from "
        "pre-outcome frequency and WordNet polysemy metadata. The measured sentinel "
        "group remains outcome-informed and is only a regression anchor.",
        "",
        "Low-polysemy controls are intentionally not forced to invent shadow senses. "
        "If a trigger is effectively one-sense for this replacement target, the packet "
        "uses active cases plus a mention or phrase no-winner case and records the "
        "shadow contract as `not_applicable`.",
        "",
        "## Summary",
        "",
        _checks_table(summary),
        "",
        "## Group Case Mix",
        "",
        _group_case_mix_table(summary.get("group_case_type_counts")),
        "",
        "## Authored Triggers",
        "",
        _authored_trigger_table(report.get("authored_triggers")),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _family_from_spec(
    *,
    spec: TriggerSpec,
    pilot_row: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    group_id = str(pilot_row.get("group_id") or "")
    selection_mode = "outcome_informed_sentinel" if "sentinel" in group_id else "pre_outcome"
    rank_bin = str(pilot_row.get("source_rank_bin") or "missing")
    polysemy_band = _polysemy_band(int(pilot_row.get("wordnet_sense_count") or 0))
    family_id = f"en-es:heuristic-group:{spec.trigger}:{_slug(spec.target_lemma)}"
    active_id = f"{family_id}:active"
    shadow_ids = {
        shadow.key: f"{family_id}:{_slug(shadow.target_lemma)}:{shadow.key}:shadow"
        for shadow in spec.shadows
    }
    family = {
        "family_id": family_id,
        "trigger": spec.trigger,
        "active": {
            "sense_id": active_id,
            "target_lemma": spec.target_lemma,
            "canonical_pos": spec.canonical_pos,
            "evidence_views": _evidence_views(
                sense_label=spec.sense_label,
                gloss_text=spec.gloss_text,
                examples=spec.examples,
            ),
        },
        "shadows": [
            {
                "sense_id": shadow_ids[shadow.key],
                "target_lemma": shadow.target_lemma,
                "canonical_pos": shadow.canonical_pos,
                "evidence_views": _evidence_views(
                    sense_label=shadow.sense_label,
                    gloss_text=shadow.gloss_text,
                    examples=shadow.examples,
                ),
            }
            for shadow in spec.shadows
        ],
        "cases": [
            _case_payload(
                family_id=family_id,
                trigger=spec.trigger,
                active_id=active_id,
                shadow_ids=shadow_ids,
                group_id=group_id,
                selection_mode=selection_mode,
                rank_bin=rank_bin,
                polysemy_band=polysemy_band,
                shadow_contract=spec.shadow_contract,
                spec_case=case,
                index=index,
            )
            for index, case in enumerate(spec.cases, start=1)
        ],
    }
    authored_row = {
        "trigger": spec.trigger,
        "group_id": group_id,
        "selection_mode": selection_mode,
        "source_rank": pilot_row.get("source_rank"),
        "source_rank_bin": rank_bin,
        "wordnet_sense_count": int(pilot_row.get("wordnet_sense_count") or 0),
        "wordnet_pos_count": int(pilot_row.get("wordnet_pos_count") or 0),
        "polysemy_band": polysemy_band,
        "target_lemma": spec.target_lemma,
        "canonical_pos": spec.canonical_pos,
        "shadow_contract": spec.shadow_contract,
        "shadow_targets": [shadow.target_lemma for shadow in spec.shadows],
        "case_count": len(spec.cases),
        "case_type_counts": dict(Counter(case.gold_type for case in spec.cases)),
        "human_polysemy_gauge": spec.human_polysemy_gauge,
        "expected_veto_difficulty": spec.expected_veto_difficulty,
        "review_notes": spec.review_notes,
    }
    return family, authored_row


def _case_payload(
    *,
    family_id: str,
    trigger: str,
    active_id: str,
    shadow_ids: Mapping[str, str],
    group_id: str,
    selection_mode: str,
    rank_bin: str,
    polysemy_band: str,
    shadow_contract: str,
    spec_case: CaseSpec,
    index: int,
) -> dict[str, object]:
    if spec_case.winner == "active":
        gold_winner = active_id
    elif spec_case.winner == "none":
        gold_winner = "none"
    else:
        gold_winner = shadow_ids[spec_case.winner]
    gold_decision = "replace" if spec_case.winner == "active" else "abstain"
    case_id = f"{family_id}:{index:03d}"
    return {
        "case_id": case_id,
        "sentence": spec_case.sentence,
        "source_phrase": trigger,
        "gold_winner": gold_winner,
        "gold_decision": gold_decision,
        "slice_tags": [
            "heuristic_group_pilot_v1",
            "manual_draft_v1",
            group_id,
            selection_mode,
            f"rank_bin:{rank_bin}",
            f"polysemy:{polysemy_band}",
            spec_case.gold_type,
            f"shadow_contract:{shadow_contract}",
        ],
        "slice_dimensions": {
            "heuristic_group": [group_id],
            "selection_mode": [selection_mode],
            "source_rank_bin": [rank_bin],
            "polysemy_band": [polysemy_band],
            "manual_case_type": [spec_case.gold_type],
            "shadow_contract": [shadow_contract],
            "manual_review_state": ["agent_draft_human_review_pending"],
        },
        "notes": spec_case.reason,
    }


def _evidence_views(
    *,
    sense_label: str,
    gloss_text: str,
    examples: Sequence[str],
) -> dict[str, str]:
    example_text = " | ".join(str(example).strip() for example in examples if str(example).strip())
    all_parts = [sense_label, gloss_text, example_text]
    all_evidence = " | ".join(part for part in all_parts if part)
    return {
        "sense_label": sense_label,
        "gloss_text": gloss_text,
        "sense_gloss_bundle": f"{sense_label} | {gloss_text}",
        "all_evidence_text": all_evidence,
    }


def _checks_table(value: object) -> str:
    rows = _as_mapping(value)
    if not rows:
        return "_No summary rows._"
    lines = ["| Key | Value |", "| --- | --- |"]
    for key, raw_value in rows.items():
        if isinstance(raw_value, (dict, list, tuple)):
            rendered = json.dumps(raw_value, ensure_ascii=False, sort_keys=True)
        else:
            rendered = str(raw_value)
        lines.append(f"| `{_escape_md(str(key))}` | `{_escape_md(rendered)}` |")
    return "\n".join(lines)


def _group_case_mix_table(value: object) -> str:
    rows = _as_mapping(value)
    if not rows:
        return "_No group rows._"
    case_types = sorted(
        {case_type for counts in rows.values() for case_type in _as_mapping(counts)}
    )
    lines = [
        "| Group | " + " | ".join(case_types) + " | Total |",
        "| --- | " + " | ".join("---:" for _ in case_types) + " | ---: |",
    ]
    for group_id, raw_counts in rows.items():
        counts = _as_mapping(raw_counts)
        total = sum(int(counts.get(case_type) or 0) for case_type in case_types)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(group_id))}`",
                    *(str(int(counts.get(case_type) or 0)) for case_type in case_types),
                    str(total),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _authored_trigger_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No authored triggers._"
    lines = [
        "| Trigger | Group | Target | Senses | Contract | Cases | Expected difficulty |",
        "| --- | --- | --- | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('group_id') or ''))}`",
                    f"`{_escape_md(str(row.get('target_lemma') or ''))}`",
                    str(int(row.get("wordnet_sense_count") or 0)),
                    f"`{_escape_md(str(row.get('shadow_contract') or ''))}`",
                    str(int(row.get("case_count") or 0)),
                    _escape_md(str(row.get("expected_veto_difficulty") or "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _mapping_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _sequence(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


def _as_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _pilot_row_sort_key(item: tuple[str, Mapping[str, object]]) -> tuple[object, ...]:
    trigger, row = item
    group_id = str(row.get("group_id") or "")
    return (
        GROUP_ORDER.get(group_id, 99),
        float(row.get("source_rank") or 999999.0),
        trigger,
    )


def _polysemy_band(sense_count: int) -> str:
    if sense_count >= 10:
        return "high_10_plus"
    if sense_count >= 4:
        return "medium_4_to_9"
    return "low_1_to_3"


def _fingerprint_dataset(dataset: Mapping[str, object]) -> str:
    payload = json.dumps(dataset, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _slug(value: str) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _escape_md(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _shadow_from_payload(payload: Mapping[str, object]) -> ShadowSpec:
    return ShadowSpec(
        key=str(payload.get("key") or ""),
        target_lemma=str(payload.get("target_lemma") or ""),
        canonical_pos=str(payload.get("canonical_pos") or ""),
        sense_label=str(payload.get("sense_label") or ""),
        gloss_text=str(payload.get("gloss_text") or ""),
        examples=tuple(str(item) for item in _sequence(payload.get("examples"))),
    )


def _case_from_payload(payload: Mapping[str, object]) -> CaseSpec:
    return CaseSpec(
        gold_type=str(payload.get("gold_type") or ""),
        sentence=str(payload.get("sentence") or ""),
        winner=str(payload.get("winner") or ""),
        reason=str(payload.get("reason") or ""),
    )


def _trigger_spec_from_payload(payload: Mapping[str, object]) -> TriggerSpec:
    return TriggerSpec(
        trigger=str(payload.get("trigger") or ""),
        target_lemma=str(payload.get("target_lemma") or ""),
        canonical_pos=str(payload.get("canonical_pos") or ""),
        sense_label=str(payload.get("sense_label") or ""),
        gloss_text=str(payload.get("gloss_text") or ""),
        examples=tuple(str(item) for item in _sequence(payload.get("examples"))),
        human_polysemy_gauge=str(payload.get("human_polysemy_gauge") or ""),
        expected_veto_difficulty=str(payload.get("expected_veto_difficulty") or ""),
        shadow_contract=str(payload.get("shadow_contract") or ""),
        review_notes=str(payload.get("review_notes") or ""),
        shadows=tuple(
            _shadow_from_payload(_as_mapping(item)) for item in _sequence(payload.get("shadows"))
        ),
        cases=tuple(
            _case_from_payload(_as_mapping(item)) for item in _sequence(payload.get("cases"))
        ),
    )


def _load_trigger_specs(path: Path = DEFAULT_TRIGGER_SPECS_JSON) -> dict[str, TriggerSpec]:
    payload = _load_json(path)
    specs_payload = _as_mapping(payload.get("trigger_specs"))
    return {
        str(trigger): _trigger_spec_from_payload(_as_mapping(spec_payload))
        for trigger, spec_payload in specs_payload.items()
    }


def _load_group_order(path: Path = DEFAULT_TRIGGER_SPECS_JSON) -> dict[str, int]:
    payload = _load_json(path)
    order_payload = _as_mapping(payload.get("group_order"))
    return {str(key): int(value) for key, value in order_payload.items()}


GROUP_ORDER = _load_group_order()
TRIGGER_SPECS = _load_trigger_specs()
