#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_EXISTING_INVENTORY_JSONS = (
    DOCS_ROOT / "test_inputs" / "semantic_routing" / "semantic_family_inventory_en_es_v10.json",
    DOCS_ROOT
    / "test_inputs"
    / "semantic_routing"
    / "semantic_source_non_v10_probe_queue_en_es_v1.json",
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_non_v10_inventory_candidates_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_non_v10_inventory_candidates_latest.md"
DEFAULT_LIMIT = 75
DEFAULT_MIN_SCORE = 5.0
SUPPORTED_POS_KEYS = frozenset({"n", "v", "a", "s", "r"})
POS_LABELS = {
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "s": "adjective_satellite",
    "r": "adverb",
}
STOP_HEADWORDS = frozenset(
    {
        "about",
        "after",
        "again",
        "against",
        "also",
        "because",
        "before",
        "being",
        "between",
        "could",
        "every",
        "from",
        "have",
        "into",
        "more",
        "most",
        "other",
        "over",
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a no-spend candidate inventory for the next non-v10 en-es semantic-source "
            "wave from local English WordNet. This ranks ambiguous English headwords; it does "
            "not claim Spanish target/shadow family construction is complete."
        )
    )
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--wordnet-dir", type=Path, default=None)
    parser.add_argument(
        "--existing-inventory-json",
        action="append",
        default=None,
        type=Path,
        help=(
            "Inventory or queue JSON whose triggers should be excluded. Defaults to v10 plus "
            "the current non-v10 source probe queue."
        ),
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_non_v10_inventory_candidate_report(
    *,
    wordnet_index: WordNetIndex,
    existing_trigger_payloads: Sequence[Mapping[str, object]] = (),
    limit: int = DEFAULT_LIMIT,
    min_score: float = DEFAULT_MIN_SCORE,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    existing_triggers = _existing_triggers(existing_trigger_payloads)
    all_candidates = [
        candidate
        for word, entry in wordnet_index.entries_by_word.items()
        if _headword_is_candidate(word)
        if word not in existing_triggers
        for candidate in [_candidate_row_for_entry(word, entry, wordnet_index)]
        if candidate and float(candidate["score"]) >= float(min_score)
    ]
    ranked = sorted(
        all_candidates,
        key=lambda row: (
            float(row["score"]),
            int(row["source_example_count"]),
            int(row["sense_count"]),
            str(row["trigger"]),
        ),
        reverse=True,
    )[: max(0, int(limit))]
    return {
        "schema_version": 1,
        "status": "ok" if ranked else "review",
        "decision": "inventory_candidates_found" if ranked else "inventory_candidates_missing",
        "generated_at": generated_at,
        "pair": "en-es",
        "inventory_id": "semantic_non_v10_inventory_candidates_en_es",
        "source": {
            "source_family": "english_wordnet",
            "source_file_count": int(wordnet_index.source_file_count),
            "existing_trigger_count": len(existing_triggers),
            "min_score": float(min_score),
            "limit": int(limit),
        },
        "summary": {
            "candidate_count": len(ranked),
            "cross_pos_candidate_count": sum(1 for row in ranked if row["cross_pos"]),
            "noun_verb_candidate_count": sum(1 for row in ranked if row["noun_verb"]),
            "same_pos_polysemy_candidate_count": sum(
                1 for row in ranked if row["same_pos_polysemy"]
            ),
            "with_examples_count": sum(1 for row in ranked if int(row["source_example_count"]) > 0),
            "with_definitions_count": sum(
                1 for row in ranked if int(row["source_definition_count"]) > 0
            ),
            "top_score": float(ranked[0]["score"]) if ranked else 0.0,
        },
        "candidates": ranked,
        "limitations": [
            "english_headword_inventory_only_no_spanish_target_family_yet",
            "wordnet_polysemy_is_a_source_availability_prior_not_user_frequency",
            "requires downstream translation_target_shadow_construction_before_admission",
        ],
        "next_steps": [
            "select a bounded wave from the ranked candidates without editing the current seed slice",
            "construct active/shadow Spanish target families for the selected wave",
            "run WordNet definition-preferred source extraction and the source-admission cycle",
            "evaluate new held-out rows and rerun failure-class mining before algorithm changes",
        ],
    }


def render_non_v10_inventory_candidate_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    source = _as_mapping(report.get("source"))
    lines = [
        "# en-es Non-v10 Semantic Inventory Candidates",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate count: `{summary.get('candidate_count', 0)}`",
        f"- Cross-POS candidates: `{summary.get('cross_pos_candidate_count', 0)}`",
        f"- Noun/verb candidates: `{summary.get('noun_verb_candidate_count', 0)}`",
        f"- Same-POS polysemy candidates: `{summary.get('same_pos_polysemy_candidate_count', 0)}`",
        f"- Existing triggers excluded: `{source.get('existing_trigger_count', 0)}`",
        f"- Min score: `{source.get('min_score', 0)}`",
        "",
        "## Top Candidates",
        "",
        _candidate_table(report.get("candidates", ())),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _candidate_row_for_entry(
    word: str, entry: Mapping[str, object], wordnet_index: WordNetIndex
) -> dict[str, object] | None:
    pos_counts: dict[str, int] = {}
    definition_count = 0
    example_count = 0
    member_count = 0
    sample_synsets: list[dict[str, object]] = []
    for pos_key, section in entry.items():
        pos = str(pos_key or "").strip()
        if pos not in SUPPORTED_POS_KEYS or not isinstance(section, Mapping):
            continue
        senses = _as_sequence(section.get("sense"))
        if not senses:
            continue
        sense_count_for_pos = 0
        for sense in senses:
            if not isinstance(sense, Mapping):
                continue
            synset_id = str(sense.get("synset") or "").strip()
            synset = wordnet_index.synsets_by_id.get(synset_id)
            if not isinstance(synset, Mapping):
                continue
            sense_count_for_pos += 1
            definitions = _text_list(synset.get("definition"))
            examples = [*_text_list(synset.get("example")), *_text_list(sense.get("sent"))]
            members = _text_list(synset.get("members"))
            definition_count += len(definitions)
            example_count += len(examples)
            member_count += len(members)
            if len(sample_synsets) < 4:
                sample_synsets.append(
                    {
                        "pos": POS_LABELS.get(pos, pos),
                        "synset_id": synset_id,
                        "definition": definitions[0] if definitions else "",
                        "example": examples[0] if examples else "",
                        "members": members[:5],
                    }
                )
        if sense_count_for_pos:
            pos_counts[pos] = sense_count_for_pos
    if not pos_counts:
        return None
    sense_count = sum(pos_counts.values())
    if sense_count < 2:
        return None
    cross_pos = len(pos_counts) >= 2
    noun_verb = pos_counts.get("n", 0) > 0 and pos_counts.get("v", 0) > 0
    same_pos_polysemy = any(count >= 2 for count in pos_counts.values())
    if not (cross_pos or same_pos_polysemy):
        return None
    score = _candidate_score(
        pos_counts=pos_counts,
        definition_count=definition_count,
        example_count=example_count,
        member_count=member_count,
    )
    return {
        "candidate_id": f"en-es:wordnet-non-v10-candidate:{word}",
        "trigger": word,
        "score": score,
        "archetype": _archetype(pos_counts),
        "complexity_band": _complexity_band(sense_count),
        "cross_pos": cross_pos,
        "noun_verb": noun_verb,
        "same_pos_polysemy": same_pos_polysemy,
        "pos_counts": {
            POS_LABELS.get(pos, pos): count for pos, count in sorted(pos_counts.items())
        },
        "sense_count": sense_count,
        "source_definition_count": definition_count,
        "source_example_count": example_count,
        "source_member_count": member_count,
        "sample_synsets": sample_synsets,
        "recommended_wave_role": _recommended_wave_role(sense_count),
        "recommended_next_action": "construct_translation_family",
    }


def _candidate_score(
    *,
    pos_counts: Mapping[str, int],
    definition_count: int,
    example_count: int,
    member_count: int,
) -> float:
    sense_count = sum(pos_counts.values())
    score = 0.0
    if pos_counts.get("n", 0) > 0 and pos_counts.get("v", 0) > 0:
        score += 7.0
    elif len(pos_counts) >= 2:
        score += 5.0
    if any(count >= 2 for count in pos_counts.values()):
        score += 2.0
    score += min(sense_count, 10) * 0.25
    score += min(example_count, 8) * 0.35
    score += min(definition_count, 8) * 0.15
    score += min(member_count, 12) * 0.05
    score -= max(sense_count - 20, 0) * 0.12
    return round(score, 4)


def _archetype(pos_counts: Mapping[str, int]) -> str:
    if pos_counts.get("n", 0) > 0 and pos_counts.get("v", 0) > 0:
        return "wordnet_noun_verb_cross_pos"
    if len(pos_counts) >= 2:
        return "wordnet_cross_pos"
    if any(count >= 2 for count in pos_counts.values()):
        return "wordnet_same_pos_polysemy"
    return "wordnet_polysemy"


def _complexity_band(sense_count: int) -> str:
    if sense_count <= 8:
        return "tractable"
    if sense_count <= 20:
        return "broad"
    return "high_polysemy_stress"


def _recommended_wave_role(sense_count: int) -> str:
    if sense_count <= 20:
        return "candidate_source_probe"
    return "stress_candidate_holdout"


def _existing_triggers(payloads: Sequence[Mapping[str, object]]) -> set[str]:
    triggers: set[str] = set()
    for payload in payloads:
        for item in _as_sequence(payload.get("families")):
            if not isinstance(item, Mapping):
                continue
            for key in ("trigger", "normalized_trigger"):
                trigger = str(item.get(key) or "").strip().lower()
                if trigger:
                    triggers.add(trigger)
    return triggers


def _headword_is_candidate(word: str) -> bool:
    normalized = str(word or "").strip().lower()
    return (
        len(normalized) >= 3
        and normalized not in STOP_HEADWORDS
        and normalized.isascii()
        and normalized.isalpha()
    )


def _candidate_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No candidates met the configured thresholds."
    lines = [
        "| Rank | Trigger | Score | Band | Archetype | POS counts | Examples | Definitions |",
        "| ---: | --- | ---: | --- | --- | --- | ---: | ---: |",
    ]
    for index, row in enumerate(materialized[:25], start=1):
        pos_counts = ", ".join(
            f"{key}:{value}" for key, value in _as_mapping(row.get("pos_counts")).items()
        )
        lines.append(
            f"| `{index}` | `{row.get('trigger', '')}` | `{row.get('score', 0)}` | "
            f"`{row.get('complexity_band', '')}` | `{row.get('archetype', '')}` | "
            f"`{pos_counts}` | "
            f"`{row.get('source_example_count', 0)}` | "
            f"`{row.get('source_definition_count', 0)}` |"
        )
    return "\n".join(lines)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item or "").strip()]
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    wordnet_dir = args.wordnet_dir or (
        args.data_root / "language_packs" / "english-wordnet-2025-json"
    )
    existing_paths = (
        tuple(args.existing_inventory_json)
        if args.existing_inventory_json is not None
        else DEFAULT_EXISTING_INVENTORY_JSONS
    )
    wordnet_index = WordNetIndex.load(wordnet_dir)
    existing_payloads = [_load_json(path) for path in existing_paths if path.exists()]
    report = build_non_v10_inventory_candidate_report(
        wordnet_index=wordnet_index,
        existing_trigger_payloads=existing_payloads,
        limit=args.limit,
        min_score=args.min_score,
    )
    report["source"] = {
        **_as_mapping(report.get("source")),
        "wordnet_dir": str(wordnet_dir),
        "existing_inventory_jsons": [str(path) for path in existing_paths],
    }
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_non_v10_inventory_candidate_markdown(report), encoding="utf-8"
    )
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
