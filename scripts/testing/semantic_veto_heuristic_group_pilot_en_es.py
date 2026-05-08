#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_difficulty_stratification_en_es import (
    DEFAULT_SOURCE_FREQUENCY_DB,
    FrequencyLookup,
    _escape_md,
    _load_json,
    _optional_float,
    _rank_bin,
    _repo_path,
    _resolve_repo_path,
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows
from semantic_wordnet_source_adapter_support import WordNetIndex


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DIFFICULTY_REPORT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_difficulty_stratification_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_pilot_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_heuristic_group_pilot_en_es_latest.md"
DEFAULT_WORDNET_DIR = (
    Path.home()
    / "Library"
    / "Application Support"
    / "LexiShift"
    / "LexiShift"
    / "language_packs"
    / "english-wordnet-2025-json"
)
DEFAULT_GROUP_SIZE = 4
DEFAULT_SENTINEL_SIZE = 5
WORDNET_POS_LABELS = {
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "s": "adjective_satellite",
    "r": "adverb",
}
SUPPORTED_POS_KEYS = frozenset(WORDNET_POS_LABELS)
STOP_HEADWORDS = frozenset(
    {
        "about",
        "again",
        "against",
        "also",
        "because",
        "before",
        "being",
        "could",
        "every",
        "have",
        "into",
        "more",
        "most",
        "other",
        "should",
        "some",
        "than",
        "that",
        "their",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "under",
        "very",
        "were",
        "when",
        "where",
        "which",
        "while",
        "with",
        "would",
    }
)


@dataclass(frozen=True)
class GroupSpec:
    group_id: str
    label: str
    heuristic_family: str
    selection_mode: str
    rank_min: float
    rank_max: float
    sense_min: int
    sense_max: int | None
    pos_count_min: int
    pos_count_max: int | None
    description: str


GROUP_SPECS = (
    GroupSpec(
        group_id="core_high_polysemy",
        label="Core high-polysemy",
        heuristic_family="frequency_x_wordnet_polysemy",
        selection_mode="pre_outcome",
        rank_min=1,
        rank_max=1000,
        sense_min=8,
        sense_max=None,
        pos_count_min=2,
        pos_count_max=None,
        description="Top-1000 English triggers with many WordNet senses across POS.",
    ),
    GroupSpec(
        group_id="core_low_polysemy_control",
        label="Core low-polysemy control",
        heuristic_family="frequency_x_wordnet_polysemy",
        selection_mode="pre_outcome",
        rank_min=1,
        rank_max=1000,
        sense_min=1,
        sense_max=3,
        pos_count_min=1,
        pos_count_max=1,
        description="Top-1000 English triggers with few WordNet senses in one POS.",
    ),
    GroupSpec(
        group_id="mid_high_polysemy",
        label="Mid-rank high-polysemy",
        heuristic_family="frequency_x_wordnet_polysemy",
        selection_mode="pre_outcome",
        rank_min=1001,
        rank_max=5000,
        sense_min=8,
        sense_max=None,
        pos_count_min=2,
        pos_count_max=None,
        description="Rank 1001-5000 English triggers with many senses across POS.",
    ),
    GroupSpec(
        group_id="mid_low_polysemy_control",
        label="Mid-rank low-polysemy control",
        heuristic_family="frequency_x_wordnet_polysemy",
        selection_mode="pre_outcome",
        rank_min=1001,
        rank_max=5000,
        sense_min=1,
        sense_max=3,
        pos_count_min=1,
        pos_count_max=1,
        description="Rank 1001-5000 English triggers with few senses in one POS.",
    ),
    GroupSpec(
        group_id="tail_high_polysemy",
        label="Tail high-polysemy",
        heuristic_family="frequency_x_wordnet_polysemy",
        selection_mode="pre_outcome",
        rank_min=5001,
        rank_max=999999,
        sense_min=8,
        sense_max=None,
        pos_count_min=2,
        pos_count_max=None,
        description="Rank >5000 English triggers with many senses across POS.",
    ),
    GroupSpec(
        group_id="tail_low_polysemy_control",
        label="Tail low-polysemy control",
        heuristic_family="frequency_x_wordnet_polysemy",
        selection_mode="pre_outcome",
        rank_min=5001,
        rank_max=999999,
        sense_min=1,
        sense_max=3,
        pos_count_min=1,
        pos_count_max=1,
        description="Rank >5000 English triggers with few senses in one POS.",
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze small en-es semantic-veto heuristic word groups before manual test "
            "authoring. Primary groups use only cheap pre-outcome frequency and WordNet "
            "metadata; measured-failure sentinels are labeled separately."
        )
    )
    parser.add_argument("--source-frequency-db", type=Path, default=DEFAULT_SOURCE_FREQUENCY_DB)
    parser.add_argument("--wordnet-dir", type=Path, default=DEFAULT_WORDNET_DIR)
    parser.add_argument("--difficulty-json", type=Path, default=DEFAULT_DIFFICULTY_REPORT)
    parser.add_argument("--group-size", type=int, default=DEFAULT_GROUP_SIZE)
    parser.add_argument("--sentinel-size", type=int, default=DEFAULT_SENTINEL_SIZE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_heuristic_group_pilot_report(
        source_frequency=FrequencyLookup.from_sqlite(
            path=args.source_frequency_db,
            language="en",
        ),
        wordnet_index=WordNetIndex.load(args.wordnet_dir),
        difficulty_payload=_load_optional_json(args.difficulty_json),
        source_frequency_path=args.source_frequency_db,
        wordnet_dir=args.wordnet_dir,
        difficulty_path=args.difficulty_json,
        group_size=max(1, int(args.group_size)),
        sentinel_size=max(1, int(args.sentinel_size)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_heuristic_group_pilot_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_heuristic_group_pilot_report(
    *,
    source_frequency: FrequencyLookup,
    wordnet_index: WordNetIndex,
    difficulty_payload: Mapping[str, object] | None = None,
    source_frequency_path: Path | None = None,
    wordnet_dir: Path | None = None,
    difficulty_path: Path | None = None,
    group_size: int = DEFAULT_GROUP_SIZE,
    sentinel_size: int = DEFAULT_SENTINEL_SIZE,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    difficulty_payload = difficulty_payload or {}
    measured_triggers = _measured_triggers(difficulty_payload)
    candidate_pool = _candidate_pool(
        source_frequency=source_frequency,
        wordnet_index=wordnet_index,
        measured_triggers=measured_triggers,
    )
    primary_groups = [
        _group_from_spec(spec=spec, candidate_pool=candidate_pool, group_size=group_size)
        for spec in GROUP_SPECS
    ]
    sentinel_group = _outcome_informed_sentinel_group(
        difficulty_payload=difficulty_payload,
        wordnet_index=wordnet_index,
        sentinel_size=sentinel_size,
    )
    groups = [*primary_groups, sentinel_group]
    manual_packet = [
        _manual_review_row(row=row, group_id=str(group["group_id"]))
        for group in groups
        for row in _mapping_rows(group.get("triggers"))
    ]
    selected_rows = [row for group in groups for row in _mapping_rows(group.get("triggers"))]
    decision = (
        "heuristic_group_pilot_ready_for_manual_tests" if manual_packet else "no_groups_selected"
    )
    return {
        "schema_version": 1,
        "status": "ok" if manual_packet else "review",
        "decision": decision,
        "generated_at": generated_at,
        "pair": "en-es",
        "pilot_id": "semantic_veto_heuristic_group_pilot_en_es_v1",
        "input_fingerprint": _fingerprint(selected_rows),
        "inputs": {
            "source_frequency_path": _repo_path(source_frequency_path),
            "source_frequency_status": source_frequency.status,
            "source_frequency_record_count": len(source_frequency.records_by_key),
            "wordnet_dir": _repo_path(wordnet_dir),
            "wordnet_source_file_count": int(wordnet_index.source_file_count),
            "difficulty_report_path": _repo_path(difficulty_path),
            "difficulty_report_status": str(difficulty_payload.get("status") or ""),
        },
        "methodology": {
            "goal": (
                "Freeze small word groups selected by cheap heuristics before manual "
                "case authoring, then compare whether those heuristics predict veto difficulty."
            ),
            "primary_selection_inputs": [
                "English source frequency rank",
                "WordNet sense count",
                "WordNet POS count",
            ],
            "primary_group_selection": "pre_outcome_only_excludes_current_measured_triggers",
            "sentinel_group_selection": "outcome_informed_not_used_to_validate_heuristic",
            "manual_case_target_per_trigger": {
                "positive_active": 2,
                "shadow_negative": 2,
                "phrase_no_winner": 1,
            },
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
        },
        "summary": {
            "group_count": len(groups),
            "primary_group_count": len(primary_groups),
            "candidate_pool_count": len(candidate_pool),
            "measured_trigger_exclusion_count": len(measured_triggers),
            "selected_trigger_count": len(selected_rows),
            "manual_review_row_count": len(manual_packet),
            "empty_primary_groups": [
                group["group_id"]
                for group in primary_groups
                if not _mapping_rows(group.get("triggers"))
            ],
        },
        "group_specs": [_public_group_spec(spec) for spec in GROUP_SPECS],
        "groups": groups,
        "manual_review_packet": manual_packet,
        "limitations": [
            "primary_groups_do_not_have_manual_cases_yet",
            "outcome_informed_sentinel_group_must_not_validate_frequency_polysemy_heuristic",
            "wordnet_polysemy_is_a_proxy_and_can_miss_browser_phrase_difficulty",
            "source_frequency_pack_is_local_and_sparser_than_a_full_corpus_rank_list",
            "spanish_target_selection_still_requires_manual_or_translation_family_review",
        ],
        "next_steps": [
            "Freeze this group manifest before writing manual cases.",
            "For each trigger, choose one plausible Spanish replacement target and at least one shadow sense.",
            "Write two positive, two shadow-negative, and one phrase/no-winner sentence per trigger where possible.",
            "Score the filled manual packet with the frozen veto candidate and compare group-level positive allow plus negative abstain rates.",
            "Use only the pre-outcome groups to judge whether frequency and polysemy predict difficulty; use the sentinel group as a regression anchor.",
        ],
    }


def render_heuristic_group_pilot_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    methodology = _as_mapping(report.get("methodology"))
    lines = [
        "# en-es Semantic Veto Heuristic Group Pilot",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Input fingerprint: `{report.get('input_fingerprint', '')}`",
        f"- Candidate pool: `{summary.get('candidate_pool_count', 0)}`",
        f"- Selected triggers: `{summary.get('selected_trigger_count', 0)}`",
        f"- Manual review rows: `{summary.get('manual_review_row_count', 0)}`",
        f"- Primary group selection: `{methodology.get('primary_group_selection', '')}`",
        f"- Sentinel group selection: `{methodology.get('sentinel_group_selection', '')}`",
        "",
        "## Methodology",
        "",
        "Primary groups are selected before outcome review from cheap metadata only: "
        "English frequency rank, WordNet sense count, and WordNet POS count. Current "
        "measured triggers are excluded from those primary groups. The sentinel group "
        "is deliberately outcome-informed and must be used only as a regression anchor.",
        "",
        "After this manifest is frozen, the manual step is to choose a Spanish target "
        "and write balanced test sentences for each trigger. The later scoring pass "
        "will compare group-level positive allow and negative abstain rates.",
        "",
        "## Groups",
        "",
    ]
    for group in _mapping_rows(report.get("groups")):
        lines.extend(
            [
                f"### {group.get('label', group.get('group_id', ''))}",
                "",
                f"- Group id: `{group.get('group_id', '')}`",
                f"- Selection mode: `{group.get('selection_mode', '')}`",
                f"- Heuristic: `{group.get('heuristic_family', '')}`",
                f"- Description: {group.get('description', '')}",
                "",
                _trigger_table(group.get("triggers")),
                "",
            ]
        )
    lines.extend(
        [
            "## Manual Review Packet",
            "",
            _manual_packet_table(report.get("manual_review_packet")),
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in _sequence(report.get("limitations")))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _sequence(report.get("next_steps")))
    return "\n".join(lines) + "\n"


def _candidate_pool(
    *,
    source_frequency: FrequencyLookup,
    wordnet_index: WordNetIndex,
    measured_triggers: set[str],
) -> list[dict[str, object]]:
    candidates = []
    for key, frequency in source_frequency.records_by_key.items():
        trigger = str(frequency.lemma or key).strip().lower()
        if not _headword_is_candidate(trigger):
            continue
        if trigger in measured_triggers:
            continue
        profile = _wordnet_profile(trigger=trigger, wordnet_index=wordnet_index)
        if not profile:
            continue
        rank = _optional_float(frequency.rank)
        if rank is None or rank <= 0:
            continue
        candidates.append(
            {
                "trigger": trigger,
                "source_rank": rank,
                "source_rank_bin": _rank_bin(rank),
                "source_frequency": frequency.frequency,
                **profile,
            }
        )
    return candidates


def _group_from_spec(
    *,
    spec: GroupSpec,
    candidate_pool: Sequence[Mapping[str, object]],
    group_size: int,
) -> dict[str, object]:
    matching = [row for row in candidate_pool if _row_matches_spec(row=row, spec=spec)]
    sorted_rows = sorted(matching, key=_candidate_sort_key)[: max(1, int(group_size))]
    return {
        "group_id": spec.group_id,
        "label": spec.label,
        "heuristic_family": spec.heuristic_family,
        "selection_mode": spec.selection_mode,
        "description": spec.description,
        "eligible_count": len(matching),
        "trigger_count": len(sorted_rows),
        "triggers": [
            _public_trigger_row(row, selection_reason=spec.group_id) for row in sorted_rows
        ],
    }


def _outcome_informed_sentinel_group(
    *,
    difficulty_payload: Mapping[str, object],
    wordnet_index: WordNetIndex,
    sentinel_size: int,
) -> dict[str, object]:
    risk_rows = _mapping_rows(difficulty_payload.get("trigger_risk_summary"))
    filtered = [
        row
        for row in risk_rows
        if str(row.get("source_trigger_rank_bin_en") or "") == "missing"
        and int(row.get("failure_count") or 0) > 0
    ]
    selected = sorted(
        filtered,
        key=lambda row: (
            -int(row.get("negative_allow_count") or 0),
            -int(row.get("failure_count") or 0),
            str(row.get("trigger") or ""),
        ),
    )[: max(1, int(sentinel_size))]
    triggers = []
    for row in selected:
        trigger = str(row.get("trigger") or "").strip().lower()
        profile = _wordnet_profile(trigger=trigger, wordnet_index=wordnet_index) or {}
        triggers.append(
            _public_trigger_row(
                {
                    "trigger": trigger,
                    "source_rank": None,
                    "source_rank_bin": "missing",
                    "source_frequency": None,
                    "observed_failure_count": int(row.get("failure_count") or 0),
                    "observed_negative_allow_count": int(row.get("negative_allow_count") or 0),
                    "observed_positive_abstain_count": int(row.get("positive_abstain_count") or 0),
                    **profile,
                },
                selection_reason="measured_missing_rank_high_failure_sentinel",
            )
        )
    return {
        "group_id": "measured_missing_rank_high_failure_sentinel",
        "label": "Measured missing-rank high-failure sentinel",
        "heuristic_family": "outcome_informed_metadata_gap",
        "selection_mode": "outcome_informed_sentinel",
        "description": (
            "Currently measured high-failure triggers missing local source rank. This is "
            "not used to validate the frequency/polysemy heuristic."
        ),
        "eligible_count": len(filtered),
        "trigger_count": len(triggers),
        "triggers": triggers,
    }


def _wordnet_profile(
    *,
    trigger: str,
    wordnet_index: WordNetIndex,
) -> dict[str, object]:
    entry = wordnet_index.entries_by_word.get(str(trigger or "").strip().lower())
    if not isinstance(entry, Mapping):
        return {}
    pos_counts: dict[str, int] = {}
    definition_count = 0
    example_count = 0
    member_count = 0
    sample_synsets = []
    for pos_key, section in entry.items():
        pos = str(pos_key or "").strip()
        if pos not in SUPPORTED_POS_KEYS or not isinstance(section, Mapping):
            continue
        sense_count_for_pos = 0
        for sense in _sequence(section.get("sense")):
            if not isinstance(sense, Mapping):
                continue
            synset_id = str(sense.get("synset") or "").strip()
            synset = wordnet_index.synsets_by_id.get(synset_id)
            if not isinstance(synset, Mapping):
                continue
            definitions = _text_list(synset.get("definition"))
            examples = [*_text_list(synset.get("example")), *_text_list(sense.get("sent"))]
            members = _text_list(synset.get("members"))
            sense_count_for_pos += 1
            definition_count += len(definitions)
            example_count += len(examples)
            member_count += len(members)
            if len(sample_synsets) < 3:
                sample_synsets.append(
                    {
                        "pos": WORDNET_POS_LABELS.get(pos, pos),
                        "synset_id": synset_id,
                        "definition": definitions[0] if definitions else "",
                        "example": examples[0] if examples else "",
                        "members": members[:5],
                    }
                )
        if sense_count_for_pos:
            pos_counts[pos] = sense_count_for_pos
    sense_count = sum(pos_counts.values())
    if sense_count <= 0:
        return {}
    pos_count = len(pos_counts)
    return {
        "wordnet_sense_count": sense_count,
        "wordnet_pos_count": pos_count,
        "wordnet_pos_counts": {
            WORDNET_POS_LABELS.get(pos, pos): count for pos, count in sorted(pos_counts.items())
        },
        "wordnet_definition_count": definition_count,
        "wordnet_example_count": example_count,
        "wordnet_member_count": member_count,
        "wordnet_sample_synsets": sample_synsets,
    }


def _row_matches_spec(*, row: Mapping[str, object], spec: GroupSpec) -> bool:
    rank = _optional_float(row.get("source_rank"))
    senses = int(row.get("wordnet_sense_count") or 0)
    pos_count = int(row.get("wordnet_pos_count") or 0)
    if rank is None or rank < spec.rank_min or rank > spec.rank_max:
        return False
    if senses < spec.sense_min:
        return False
    if spec.sense_max is not None and senses > spec.sense_max:
        return False
    if pos_count < spec.pos_count_min:
        return False
    if spec.pos_count_max is not None and pos_count > spec.pos_count_max:
        return False
    return True


def _candidate_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _optional_float(row.get("source_rank")) or 999999.0,
        -int(row.get("wordnet_sense_count") or 0),
        -int(row.get("wordnet_pos_count") or 0),
        str(row.get("trigger") or ""),
    )


def _public_trigger_row(
    row: Mapping[str, object],
    *,
    selection_reason: str,
) -> dict[str, object]:
    return {
        "trigger": str(row.get("trigger") or ""),
        "selection_reason": selection_reason,
        "source_rank": row.get("source_rank"),
        "source_rank_bin": str(row.get("source_rank_bin") or "missing"),
        "source_frequency": row.get("source_frequency"),
        "wordnet_sense_count": int(row.get("wordnet_sense_count") or 0),
        "wordnet_pos_count": int(row.get("wordnet_pos_count") or 0),
        "wordnet_pos_counts": dict(_as_mapping(row.get("wordnet_pos_counts"))),
        "wordnet_definition_count": int(row.get("wordnet_definition_count") or 0),
        "wordnet_example_count": int(row.get("wordnet_example_count") or 0),
        "observed_failure_count": row.get("observed_failure_count"),
        "observed_negative_allow_count": row.get("observed_negative_allow_count"),
        "observed_positive_abstain_count": row.get("observed_positive_abstain_count"),
        "sample_synsets": list(_sequence(row.get("wordnet_sample_synsets"))),
    }


def _manual_review_row(
    *,
    row: Mapping[str, object],
    group_id: str,
) -> dict[str, object]:
    trigger = str(row.get("trigger") or "")
    return {
        "group_id": group_id,
        "trigger": trigger,
        "selection_reason": str(row.get("selection_reason") or ""),
        "source_rank": row.get("source_rank"),
        "source_rank_bin": str(row.get("source_rank_bin") or "missing"),
        "wordnet_sense_count": int(row.get("wordnet_sense_count") or 0),
        "wordnet_pos_count": int(row.get("wordnet_pos_count") or 0),
        "sample_synsets": list(_sequence(row.get("sample_synsets"))),
        "manual_review_fields": {
            "candidate_replacement_es": "",
            "active_sense_en": "",
            "shadow_senses_en": [],
            "phrase_or_no_winner_patterns_en": [],
            "human_polysemy_gauge": "",
            "expected_veto_difficulty": "",
            "review_notes": "",
        },
        "case_slots": [
            _case_slot(trigger=trigger, gold_type="positive_active", index=1),
            _case_slot(trigger=trigger, gold_type="positive_active", index=2),
            _case_slot(trigger=trigger, gold_type="shadow_negative", index=1),
            _case_slot(trigger=trigger, gold_type="shadow_negative", index=2),
            _case_slot(trigger=trigger, gold_type="phrase_no_winner", index=1),
        ],
    }


def _case_slot(*, trigger: str, gold_type: str, index: int) -> dict[str, object]:
    return {
        "slot_id": f"{trigger}:{gold_type}:{index:02d}",
        "gold_type": gold_type,
        "sentence": "",
        "gold_decision": "replace" if gold_type == "positive_active" else "abstain",
        "label_reason": "",
    }


def _measured_triggers(difficulty_payload: Mapping[str, object]) -> set[str]:
    triggers = {
        str(row.get("trigger") or "").strip().lower()
        for row in _mapping_rows(difficulty_payload.get("case_traces"))
        if str(row.get("trigger") or "").strip()
    }
    return triggers


def _public_group_spec(spec: GroupSpec) -> dict[str, object]:
    return {
        "group_id": spec.group_id,
        "label": spec.label,
        "heuristic_family": spec.heuristic_family,
        "selection_mode": spec.selection_mode,
        "rank_min": spec.rank_min,
        "rank_max": spec.rank_max,
        "sense_min": spec.sense_min,
        "sense_max": spec.sense_max,
        "pos_count_min": spec.pos_count_min,
        "pos_count_max": spec.pos_count_max,
        "description": spec.description,
    }


def _headword_is_candidate(word: str) -> bool:
    normalized = str(word or "").strip().lower()
    return (
        len(normalized) >= 3
        and normalized not in STOP_HEADWORDS
        and normalized.isascii()
        and normalized.isalpha()
    )


def _trigger_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No triggers selected for this group._"
    lines = [
        "| Trigger | Rank | Rank bin | Senses | POS | POS counts | Observed failures |",
        "| --- | ---: | --- | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        pos_counts = ", ".join(
            f"{key}:{value}" for key, value in _as_mapping(row.get("wordnet_pos_counts")).items()
        )
        observed = row.get("observed_failure_count")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    str(row.get("source_rank") or ""),
                    f"`{_escape_md(str(row.get('source_rank_bin') or ''))}`",
                    str(row.get("wordnet_sense_count") or ""),
                    str(row.get("wordnet_pos_count") or ""),
                    f"`{_escape_md(pos_counts)}`",
                    str(observed if observed is not None else ""),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _manual_packet_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No manual review rows._"
    lines = [
        "| Group | Trigger | Rank bin | Senses | POS | Case slots |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('group_id') or ''))}`",
                    f"`{_escape_md(str(row.get('trigger') or ''))}`",
                    f"`{_escape_md(str(row.get('source_rank_bin') or ''))}`",
                    str(row.get("wordnet_sense_count") or ""),
                    str(row.get("wordnet_pos_count") or ""),
                    str(len(_sequence(row.get("case_slots")))),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _fingerprint(rows: Sequence[Mapping[str, object]]) -> str:
    payload = [
        {
            "trigger": str(row.get("trigger") or ""),
            "selection_reason": str(row.get("selection_reason") or ""),
            "source_rank": row.get("source_rank"),
            "wordnet_sense_count": row.get("wordnet_sense_count"),
            "wordnet_pos_count": row.get("wordnet_pos_count"),
        }
        for row in rows
    ]
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_optional_json(path: Path) -> dict[str, object]:
    resolved = _resolve_repo_path(str(path)) if not Path(path).is_absolute() else Path(path)
    if not resolved.exists():
        return {}
    return _load_json(resolved)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item or "").strip()]
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
