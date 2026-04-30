#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
DEFAULT_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from semantic_example_frame_source_adapter_support import (  # noqa: E402
    active_visible_alias_senses as _active_visible_alias_senses,
    content_tokens as _content_tokens,
    read_json_object,
    sense_hint as _sense_hint,
    sense_target_tokens as _sense_target_tokens,
    slug as _slug,
    text_list as _text_list,
    utc_now as _utc_now,
    write_json as _write_json,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_wordnet_source_adapter_support import (  # noqa: E402
    WordNetIndex,
    candidate_tokens_for_wordnet_sense,
)


DEFAULT_RUN_ID = "wordnet-alternate-sense-phrase-non-v10-wave6-wiktextract-supported-v1-latest"
DEFAULT_DATASET_JSON = (
    DEFAULT_DRAFT_ROOT / "en_es_source_non_v10_wave6_anypos_wiktextract_supported_v1_dataset.json"
)
DEFAULT_ACTIVE_REFERENCE_BATCH_JSON = EXPERIMENT_ROOT / (
    "en-es-translation-sense-non-v10-wave6-wiktextract-supported-v1-latest"
    "_cycle_sense_admitted_normalized_evidence.json"
)
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / (f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json")
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_wordnet_alternate_sense_phrase_non_v10_wave6_wiktextract_supported_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_wordnet_alternate_sense_phrase_non_v10_wave6_wiktextract_supported_latest.md"
)
SOURCE_TYPE = "external"
SOURCE_ID = "wordnet_alternate_sense_phrase"
SOURCE_FAMILY = "external_sense_graph"
PROMPT_VERSION = "wordnet-alternate-sense-phrase-v1"
DEFAULT_ACTIVE_OVERLAP_SKIP = 0.34
DEFAULT_ACTIVE_REFERENCE_OVERLAP_SKIP = 0.50
DEFAULT_MAX_ROWS_PER_FAMILY = 12
EVIDENCE_META_TOKENS = frozenset(
    {
        "active",
        "adjective",
        "adverb",
        "alternate",
        "example",
        "noun",
        "sense",
        "verb",
        "wordnet",
    }
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build phrase-control semantic-prototype rows from WordNet senses that are "
            "not close token matches for the selected active sense. This creates a "
            "no-spend alternate-sense lane for no-replacement cases."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--wordnet-dir", type=Path, default=None)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument(
        "--active-reference-batch-json",
        type=Path,
        default=DEFAULT_ACTIVE_REFERENCE_BATCH_JSON,
        help=(
            "Optional admitted evidence batch used to reject alternate-sense phrase rows "
            "that are too close to active evidence for the same family."
        ),
    )
    parser.add_argument("--max-rows-per-family", type=int, default=DEFAULT_MAX_ROWS_PER_FAMILY)
    parser.add_argument(
        "--active-overlap-skip",
        type=float,
        default=DEFAULT_ACTIVE_OVERLAP_SKIP,
        help=(
            "Skip a WordNet sense when its content-token overlap with the active sense "
            "is at or above this ratio. This is an active-safety filter, not a tuning claim."
        ),
    )
    parser.add_argument(
        "--active-reference-overlap-skip",
        type=float,
        default=DEFAULT_ACTIVE_REFERENCE_OVERLAP_SKIP,
    )
    parser.add_argument("--normalized-batch-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_wordnet_alternate_sense_phrase_bundle(
    *,
    dataset_payload: Mapping[str, object],
    wordnet_index: WordNetIndex,
    active_reference_batch_payload: Mapping[str, object] | None = None,
    run_id: str = DEFAULT_RUN_ID,
    max_rows_per_family: int = DEFAULT_MAX_ROWS_PER_FAMILY,
    active_overlap_skip: float = DEFAULT_ACTIVE_OVERLAP_SKIP,
    active_reference_overlap_skip: float = DEFAULT_ACTIVE_REFERENCE_OVERLAP_SKIP,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    intake_batch = _build_intake_batch(
        dataset_payload=dataset_payload,
        wordnet_index=wordnet_index,
        active_reference_lookup=_active_reference_lookup(active_reference_batch_payload),
        run_id=run_id,
        max_rows_per_family=max(1, int(max_rows_per_family)),
        active_overlap_skip=max(0.0, float(active_overlap_skip)),
        active_reference_overlap_skip=max(0.0, float(active_reference_overlap_skip)),
        generated_at=generated_at,
    )
    normalized_batch = (
        normalize_llm_intake_batch(intake_batch) if intake_batch.get("items") else None
    )
    family_rows = list(
        intake_batch.get("provenance", {}).get("family_rows", ())
        if isinstance(intake_batch.get("provenance"), Mapping)
        else ()
    )
    report = _build_report(
        dataset_payload=dataset_payload,
        wordnet_index=wordnet_index,
        family_rows=family_rows,
        normalized_batch=normalized_batch,
        run_id=run_id,
        max_rows_per_family=max(1, int(max_rows_per_family)),
        active_overlap_skip=max(0.0, float(active_overlap_skip)),
        active_reference_overlap_skip=max(0.0, float(active_reference_overlap_skip)),
        generated_at=generated_at,
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "report": report,
    }


def render_wordnet_alternate_sense_phrase_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es WordNet Alternate-Sense Phrase Evidence",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Families with rows: `{summary.get('families_with_rows', 0)}` / `{summary.get('family_count', 0)}`",
        f"- Skipped active-like senses: `{summary.get('active_like_skip_count', 0)}`",
        "",
        "## Family Rows",
        "",
        "| Family | Candidates | Rows | Active-like Skips |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('family_id', '')}`",
                    str(row.get("candidate_sense_count", 0)),
                    str(row.get("row_count", 0)),
                    str(row.get("active_like_skip_count", 0)),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _build_intake_batch(
    *,
    dataset_payload: Mapping[str, object],
    wordnet_index: WordNetIndex,
    active_reference_lookup: Mapping[str, Sequence[set[str]]],
    run_id: str,
    max_rows_per_family: int,
    active_overlap_skip: float,
    active_reference_overlap_skip: float,
    generated_at: str,
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_items, candidate_rows = _family_items(
            family,
            wordnet_index=wordnet_index,
            active_reference_lookup=active_reference_lookup,
            max_rows_per_family=max_rows_per_family,
            active_overlap_skip=active_overlap_skip,
            active_reference_overlap_skip=active_reference_overlap_skip,
        )
        items.extend(family_items)
        family_rows.append(_family_summary_row(family, family_items, candidate_rows))
    return {
        "schema_version": 1,
        "batch_id": f"en-es:wordnet-alternate-sense-phrase:{run_id}",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "roles": ["phrase_containment", "discrimination"],
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "unreviewed",
        "model_id": "not_applicable",
        "prompt_version": PROMPT_VERSION,
        "provenance": {
            "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
            "source_note": (
                "WordNet senses for the trigger that are not token-close to the active "
                "sense, emitted as phrase-control semantic prototypes."
            ),
            "wordnet_source_file_count": int(wordnet_index.source_file_count),
            "max_rows_per_family": int(max_rows_per_family),
            "active_overlap_skip": float(active_overlap_skip),
            "active_reference_overlap_skip": float(active_reference_overlap_skip),
            "family_rows": family_rows,
        },
        "items": items,
    }


def _family_items(
    family: Mapping[str, object],
    *,
    wordnet_index: WordNetIndex,
    active_reference_lookup: Mapping[str, Sequence[set[str]]],
    max_rows_per_family: int,
    active_overlap_skip: float,
    active_reference_overlap_skip: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    active = _as_mapping(family.get("active"))
    trigger = str(family.get("trigger") or "").strip()
    active_token_sets = _active_token_sets(family)
    candidates = _wordnet_sense_candidates(
        wordnet_index,
        trigger=trigger,
        active_token_sets=active_token_sets,
        active_reference_token_sets=active_reference_lookup.get(
            str(family.get("family_id") or "").strip(), ()
        ),
        active_overlap_skip=active_overlap_skip,
        active_reference_overlap_skip=active_reference_overlap_skip,
    )
    items: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    for candidate in candidates:
        candidate_rows.append(candidate)
        if candidate.get("active_like_skip"):
            continue
        if len(items) >= max_rows_per_family:
            continue
        evidence_text = _candidate_evidence_text(trigger=trigger, candidate=candidate)
        if not evidence_text:
            continue
        items.append(
            _item(
                family=family,
                active_sense=active,
                candidate=candidate,
                evidence_text=evidence_text,
            )
        )
    return items, candidate_rows


def _wordnet_sense_candidates(
    wordnet_index: WordNetIndex,
    *,
    trigger: str,
    active_token_sets: Sequence[set[str]],
    active_reference_token_sets: Sequence[set[str]],
    active_overlap_skip: float,
    active_reference_overlap_skip: float,
) -> list[dict[str, object]]:
    entry = wordnet_index.entries_by_word.get(str(trigger or "").strip().lower())
    if not isinstance(entry, Mapping):
        return []
    rows: list[dict[str, object]] = []
    for pos_key in sorted(str(key) for key in entry.keys()):
        section = entry.get(pos_key)
        if not isinstance(section, Mapping):
            continue
        senses = section.get("sense")
        if not isinstance(senses, Sequence) or isinstance(senses, (str, bytes)):
            continue
        for sense_rank, raw_sense in enumerate(senses, start=1):
            if not isinstance(raw_sense, Mapping):
                continue
            synset_id = str(raw_sense.get("synset") or "").strip()
            synset = wordnet_index.synsets_by_id.get(synset_id)
            if not isinstance(synset, Mapping):
                continue
            tokens = candidate_tokens_for_wordnet_sense(
                wordnet_sense=raw_sense,
                synset=synset,
                trigger=trigger,
            )
            active_overlap = _max_active_overlap(tokens, active_token_sets)
            active_reference_overlap = _max_active_overlap(tokens, active_reference_token_sets)
            definition_texts = tuple(_text_list(synset.get("definition")))
            example_texts = tuple(_text_list(synset.get("example")))
            rows.append(
                {
                    "wordnet_sense_id": str(raw_sense.get("id") or "").strip(),
                    "wordnet_synset_id": synset_id,
                    "wordnet_pos": pos_key,
                    "wordnet_sense_rank": sense_rank,
                    "definition_texts": definition_texts,
                    "example_texts": example_texts,
                    "members": tuple(_text_list(synset.get("members"))),
                    "candidate_tokens": sorted(tokens),
                    "active_overlap": round(active_overlap, 4),
                    "active_reference_overlap": round(active_reference_overlap, 4),
                    "active_like_skip": active_overlap >= active_overlap_skip
                    or active_reference_overlap >= active_reference_overlap_skip,
                }
            )
    return sorted(rows, key=_candidate_sort_key)


def _item(
    *,
    family: Mapping[str, object],
    active_sense: Mapping[str, object],
    candidate: Mapping[str, object],
    evidence_text: str,
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    synset_id = str(candidate.get("wordnet_synset_id") or "").strip()
    pos = str(candidate.get("wordnet_pos") or "").strip()
    return {
        "row_id": f"{_slug(family_id)}:phrase-control-wordnet-alt-{_slug(synset_id)}",
        "relation_type": "phrase_control_example",
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active_sense.get("target_lemma") or "").strip(),
        "candidate_target": "phrase_control",
        "active_sense_hint": _sense_hint(active_sense, note="phrase_control_anchor"),
        "candidate_sense_hint": {
            "provider": "wordnet_en_json",
            "locator_kind": "synset_id",
            "target_key": synset_id,
            "canonical_pos": pos,
            "note": "wordnet_alternate_sense_phrase_control",
        },
        "candidate_pos": pos,
        "evidence_text": evidence_text,
        "example_count": 1,
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "roles": ["phrase_containment", "discrimination"],
        "metadata": {
            "family_id": family_id,
            "active_sense_id": str(active_sense.get("sense_id") or "").strip(),
            "candidate_sense_id": "phrase_control",
            "example_bucket": "phrase_control",
            "source_view": "wordnet_alternate_sense",
            "wordnet_sense_id": str(candidate.get("wordnet_sense_id") or "").strip(),
            "wordnet_synset_id": synset_id,
            "wordnet_pos": pos,
            "wordnet_sense_rank": int(candidate.get("wordnet_sense_rank") or 0),
            "wordnet_members": list(candidate.get("members") or ()),
            "wordnet_definition_texts": list(candidate.get("definition_texts") or ()),
            "wordnet_example_texts": list(candidate.get("example_texts") or ()),
            "active_overlap": float(candidate.get("active_overlap") or 0.0),
            "active_reference_overlap": float(candidate.get("active_reference_overlap") or 0.0),
        },
    }


def _candidate_evidence_text(*, trigger: str, candidate: Mapping[str, object]) -> str:
    definitions = [str(item).strip() for item in candidate.get("definition_texts", ()) if item]
    examples = [str(item).strip() for item in candidate.get("example_texts", ()) if item]
    parts = []
    if definitions:
        parts.append(definitions[0])
    if examples:
        parts.append(f"example: {examples[0]}")
    if not parts:
        members = [str(item).strip() for item in candidate.get("members", ()) if item]
        parts.extend(members[:3])
    return " ".join(part for part in parts if str(part).strip()).strip()


def _active_token_sets(family: Mapping[str, object]) -> list[set[str]]:
    active = _as_mapping(family.get("active"))
    active_senses = [active, *_active_visible_alias_senses(active)]
    trigger = str(family.get("trigger") or "").strip()
    rows: list[set[str]] = []
    for sense in active_senses:
        tokens = _sense_target_tokens(sense, trigger=trigger)
        metadata = _as_mapping(sense.get("metadata"))
        translation_sense = str(metadata.get("translation_sense_text") or "").strip()
        if translation_sense:
            tokens = tokens | _content_tokens(translation_sense, trigger=trigger)
        if tokens:
            rows.append(tokens)
    return rows


def _active_reference_lookup(
    batch_payload: Mapping[str, object] | None,
) -> dict[str, list[set[str]]]:
    if not isinstance(batch_payload, Mapping):
        return {}
    lookup: dict[str, list[set[str]]] = {}
    for row in batch_payload.get("rows", ()):
        if not isinstance(row, Mapping):
            continue
        if str(row.get("relation_type") or "").strip() != "anchor_cue":
            continue
        metadata = _as_mapping(row.get("metadata"))
        family_id = str(metadata.get("family_id") or "").strip()
        evidence_text = str(row.get("evidence_text") or "").strip()
        if not family_id or not evidence_text:
            continue
        tokens = _semantic_content_tokens(
            evidence_text,
            trigger=str(row.get("trigger") or "").strip(),
        )
        if tokens:
            lookup.setdefault(family_id, []).append(tokens)
    return lookup


def _semantic_content_tokens(text: str, *, trigger: str) -> set[str]:
    return _content_tokens(text, trigger=trigger) - EVIDENCE_META_TOKENS


def _max_active_overlap(tokens: set[str], active_token_sets: Sequence[set[str]]) -> float:
    if not tokens or not active_token_sets:
        return 0.0
    scores = []
    for active_tokens in active_token_sets:
        overlap = len(tokens & active_tokens)
        scores.append(max(overlap / max(len(tokens), 1), overlap / max(len(active_tokens), 1)))
    return max(scores)


def _candidate_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    pos_rank = {"n": 0, "a": 1, "s": 2, "r": 3, "v": 4}
    return (
        bool(row.get("active_like_skip")),
        pos_rank.get(str(row.get("wordnet_pos") or ""), 9),
        int(row.get("wordnet_sense_rank") or 0),
        -int(bool(row.get("example_texts"))),
        str(row.get("wordnet_pos") or ""),
        str(row.get("wordnet_synset_id") or ""),
    )


def _family_summary_row(
    family: Mapping[str, object],
    items: Sequence[Mapping[str, object]],
    candidates: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "candidate_sense_count": len(candidates),
        "active_like_skip_count": sum(1 for row in candidates if row.get("active_like_skip")),
        "row_count": len(items),
        "emitted_synset_ids": [
            str(_as_mapping(row.get("metadata")).get("wordnet_synset_id") or "") for row in items
        ],
    }


def _build_report(
    *,
    dataset_payload: Mapping[str, object],
    wordnet_index: WordNetIndex,
    family_rows: Sequence[Mapping[str, object]],
    normalized_batch: Mapping[str, object] | None,
    run_id: str,
    max_rows_per_family: int,
    active_overlap_skip: float,
    active_reference_overlap_skip: float,
    generated_at: str,
) -> dict[str, object]:
    row_count = (
        int(normalized_batch.get("row_count") or 0) if isinstance(normalized_batch, Mapping) else 0
    )
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok" if row_count else "review",
        "decision": "candidate_batch_ready" if row_count else "no_candidate_rows",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "run_id": run_id,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip()
        if isinstance(normalized_batch, Mapping)
        else "",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "resource_status": {
            "wordnet_source_file_count": int(wordnet_index.source_file_count),
            "wordnet_entry_count": len(wordnet_index.entries_by_word),
            "wordnet_synset_count": len(wordnet_index.synsets_by_id),
        },
        "summary": {
            "family_count": len(family_rows),
            "source_family_count": len(family_rows),
            "target_family_count": len(family_rows),
            "families_with_rows": sum(1 for row in family_rows if int(row.get("row_count") or 0)),
            "candidate_sense_count": sum(
                int(row.get("candidate_sense_count") or 0) for row in family_rows
            ),
            "active_like_skip_count": sum(
                int(row.get("active_like_skip_count") or 0) for row in family_rows
            ),
            "row_count": row_count,
            "max_rows_per_family": int(max_rows_per_family),
            "active_overlap_skip": float(active_overlap_skip),
            "active_reference_overlap_skip": float(active_reference_overlap_skip),
        },
        "family_rows": list(family_rows),
        "limitations": [
            "wordnet_alternate_senses_are_no_winner_prototypes_not_runtime_policy",
            "active_like_filter_is_token_based_and_requires_heldout_validation",
            "phrase_semantic_prototype_guard_must_be_swept_separately_from_scalar_margin",
            "runtime_publishable=false_until_admission_and_heldout_validation",
        ],
    }


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def main() -> int:
    args = _parse_args()
    dataset_payload = load_sentence_veto_dataset(args.dataset)
    data_root = Path(args.data_root)
    wordnet_dir = (
        Path(args.wordnet_dir)
        if args.wordnet_dir is not None
        else data_root / "language_packs" / "english-wordnet-2025-json"
    )
    wordnet_index = WordNetIndex.load(wordnet_dir)
    active_reference_payload = (
        read_json_object(args.active_reference_batch_json)
        if args.active_reference_batch_json.exists()
        else None
    )
    bundle = build_wordnet_alternate_sense_phrase_bundle(
        dataset_payload=dataset_payload,
        wordnet_index=wordnet_index,
        active_reference_batch_payload=active_reference_payload
        if isinstance(active_reference_payload, Mapping)
        else None,
        run_id=str(args.run_id or "").strip() or DEFAULT_RUN_ID,
        max_rows_per_family=int(args.max_rows_per_family),
        active_overlap_skip=float(args.active_overlap_skip),
        active_reference_overlap_skip=float(args.active_reference_overlap_skip),
    )
    if isinstance(bundle.get("normalized_batch"), Mapping):
        _write_json(args.normalized_batch_out, bundle["normalized_batch"])
    _write_json(args.json_out, bundle["report"])
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_wordnet_alternate_sense_phrase_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if isinstance(bundle.get("normalized_batch"), Mapping):
        print(f"Wrote normalized batch to {args.normalized_batch_out}")
    return 0 if bundle["report"]["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
