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
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from semantic_example_frame_source_adapter_support import (  # noqa: E402
    active_visible_alias_senses as _active_visible_alias_senses,
    all_family_dataset as _all_family_dataset,
    sense_hint as _base_sense_hint,
    sense_id as _sense_id,
    slug as _slug,
    utc_now as _utc_now,
    write_json as _write_json,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_QUEUE_JSON,
    _load_json,
)
from semantic_reverse_aux_text_pilot_en_es import build_queue_subset_dataset  # noqa: E402
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_wordnet_source_adapter_support import (  # noqa: E402
    WordNetCandidate,
    WordNetIndex,
)


DEFAULT_RUN_ID = "wordnet-example-frames-v10-20260425a"
DEFAULT_INTAKE_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_intake_batch.json"
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_wordnet_example_frame_batch_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_wordnet_example_frame_batch_en_es_latest.md"
DEFAULT_RESIDUAL_CYCLE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_source_admission_cycle_reverse_aux_all_v10_latest.json"
)
SOURCE_TYPE = "external"
SOURCE_ID = "wordnet_example_frames"
SOURCE_FAMILY = "external_sense_graph"
PROMPT_VERSION = "wordnet-example-frames-v1"
DEFAULT_SCOPE = "all_dataset_families"
SUPPORTED_SCOPES = frozenset(
    {"prompt_queue", "all_dataset_families", "residual_semantic_gaps", "family_keys"}
)
DEFAULT_MIN_LINK_SCORE = 0.12
DEFAULT_MAX_ROWS_PER_SENSE = 1
DEFAULT_MAX_RELATED_ROWS_PER_SENSE = 0
DEFAULT_RELATED_HYPONYM_DEPTH = 1
DEFAULT_RELATED_HYPONYM_ROLES = "all"
DEFAULT_EVIDENCE_MODE = "example_preferred"
SUPPORTED_EVIDENCE_MODES = frozenset(
    {"example_preferred", "definition_preferred", "definition_and_example"}
)
SUPPORTED_RELATED_HYPONYM_ROLES = frozenset({"active", "all"})


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build schema-normalized active/shadow example-frame evidence from local "
            "English WordNet JSON. This is a source-coverage adapter, not reviewed or "
            "generated runtime data."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--wordnet-dir", type=Path, default=None)
    parser.add_argument(
        "--scope",
        choices=sorted(SUPPORTED_SCOPES),
        default=DEFAULT_SCOPE,
        help=(
            "`prompt_queue` extracts only queued families; `all_dataset_families` extracts "
            "every v10 family; `residual_semantic_gaps` uses the latest source-cycle "
            "semantic residual keys; `family_keys` uses repeated --family-key values."
        ),
    )
    parser.add_argument("--family-key", action="append", default=[])
    parser.add_argument("--residual-cycle-json", type=Path, default=DEFAULT_RESIDUAL_CYCLE_JSON)
    parser.add_argument("--min-link-score", type=float, default=DEFAULT_MIN_LINK_SCORE)
    parser.add_argument("--max-rows-per-sense", type=int, default=DEFAULT_MAX_ROWS_PER_SENSE)
    parser.add_argument(
        "--include-related-hyponyms",
        action="store_true",
        help=(
            "Also emit direct-hyponym WordNet evidence rows beneath matched direct synsets. "
            "Use with a small --max-related-rows-per-sense cap."
        ),
    )
    parser.add_argument(
        "--max-related-rows-per-sense",
        type=int,
        default=DEFAULT_MAX_RELATED_ROWS_PER_SENSE,
    )
    parser.add_argument(
        "--related-hyponym-depth",
        type=int,
        default=DEFAULT_RELATED_HYPONYM_DEPTH,
        help=(
            "Maximum hyponym graph depth to traverse below a linked direct synset. "
            "Default 1 preserves direct-hyponym-only behavior."
        ),
    )
    parser.add_argument(
        "--related-hyponym-roles",
        choices=sorted(SUPPORTED_RELATED_HYPONYM_ROLES),
        default=DEFAULT_RELATED_HYPONYM_ROLES,
    )
    parser.add_argument(
        "--evidence-mode",
        choices=sorted(SUPPORTED_EVIDENCE_MODES),
        default=DEFAULT_EVIDENCE_MODE,
        help=(
            "`example_preferred` preserves the first example-frame read; "
            "`definition_preferred` prefers WordNet definitions; "
            "`definition_and_example` can emit both, capped by --max-rows-per-sense."
        ),
    )
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--intake-batch-out", type=Path, default=DEFAULT_INTAKE_OUT)
    parser.add_argument("--normalized-batch-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_wordnet_example_frame_bundle(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    wordnet_dir: Path,
    residual_cycle_payload: Mapping[str, object] | None = None,
    data_root: Path | None = None,
    run_id: str = DEFAULT_RUN_ID,
    scope: str = DEFAULT_SCOPE,
    family_keys: Sequence[str] = (),
    min_link_score: float = DEFAULT_MIN_LINK_SCORE,
    max_rows_per_sense: int = DEFAULT_MAX_ROWS_PER_SENSE,
    include_related_hyponyms: bool = False,
    max_related_rows_per_sense: int = DEFAULT_MAX_RELATED_ROWS_PER_SENSE,
    related_hyponym_depth: int = DEFAULT_RELATED_HYPONYM_DEPTH,
    related_hyponym_roles: str = DEFAULT_RELATED_HYPONYM_ROLES,
    evidence_mode: str = DEFAULT_EVIDENCE_MODE,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    source_scope = _normalize_scope(scope)
    wordnet_index = WordNetIndex.load(wordnet_dir)
    missing_resources = []
    if (
        not wordnet_dir.exists()
        or not wordnet_index.entries_by_word
        or not wordnet_index.synsets_by_id
    ):
        missing_resources.append("wordnet_json")
    subset_dataset, family_roles = _build_source_dataset(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        residual_cycle_payload=residual_cycle_payload,
        family_keys=family_keys,
        scope=source_scope,
    )
    intake_batch: dict[str, object] | None = None
    normalized_batch: dict[str, object] | None = None
    family_rows: list[dict[str, object]] = []
    if not missing_resources:
        intake_batch = _build_intake_batch(
            subset_dataset=subset_dataset,
            family_roles=family_roles,
            wordnet_index=wordnet_index,
            run_id=run_id,
            source_scope=source_scope,
            min_link_score=max(0.0, float(min_link_score)),
            max_rows_per_sense=max(1, int(max_rows_per_sense)),
            include_related_hyponyms=bool(include_related_hyponyms),
            max_related_rows_per_sense=max(0, int(max_related_rows_per_sense)),
            related_hyponym_depth=max(1, int(related_hyponym_depth)),
            related_hyponym_roles=_normalize_related_hyponym_roles(related_hyponym_roles),
            evidence_mode=_normalize_evidence_mode(evidence_mode),
            generated_at=generated_at,
        )
        provenance = intake_batch.get("provenance")
        if isinstance(provenance, Mapping):
            family_rows = [
                dict(row) for row in provenance.get("family_rows", ()) if isinstance(row, Mapping)
            ]
        if intake_batch["items"]:
            normalized_batch = normalize_llm_intake_batch(intake_batch)
    report = _build_report(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        family_rows=family_rows,
        normalized_batch=normalized_batch,
        data_root=data_root or PROJECT_ROOT,
        wordnet_dir=wordnet_dir,
        wordnet_index=wordnet_index,
        missing_resources=missing_resources,
        generated_at=generated_at,
        run_id=run_id,
        source_scope=source_scope,
        min_link_score=float(min_link_score),
        evidence_mode=_normalize_evidence_mode(evidence_mode),
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "report": report,
    }


def _build_intake_batch(
    *,
    subset_dataset: Mapping[str, object],
    family_roles: Mapping[str, str],
    wordnet_index: WordNetIndex,
    run_id: str,
    source_scope: str,
    min_link_score: float,
    max_rows_per_sense: int,
    include_related_hyponyms: bool,
    max_related_rows_per_sense: int,
    related_hyponym_depth: int,
    related_hyponym_roles: str,
    evidence_mode: str,
    generated_at: str,
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    for family in subset_dataset.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        role = str(family_roles.get(str(family.get("family_id") or "").strip()) or "target")
        family_items, family_link_rows = _build_family_items(
            family,
            role=role,
            wordnet_index=wordnet_index,
            min_link_score=min_link_score,
            max_rows_per_sense=max_rows_per_sense,
            include_related_hyponyms=include_related_hyponyms,
            max_related_rows_per_sense=max_related_rows_per_sense,
            related_hyponym_depth=related_hyponym_depth,
            related_hyponym_roles=related_hyponym_roles,
            evidence_mode=evidence_mode,
        )
        items.extend(family_items)
        family_rows.append(
            _family_summary_row(
                family,
                role=role,
                items=family_items,
                link_rows=family_link_rows,
            )
        )
    return {
        "schema_version": 1,
        "batch_id": f"en-es:wordnet-example-frames:{run_id}",
        "pair": str(subset_dataset.get("pair") or "").strip() or "en-es",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "roles": ["cue_generation", "discrimination"],
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "unreviewed",
        "model_id": "not_applicable",
        "prompt_version": PROMPT_VERSION,
        "provenance": {
            "dataset_id": str(subset_dataset.get("dataset_id") or "").strip(),
            "source_scope": source_scope,
            "source_note": "local English WordNet definitions/examples linked to dataset senses",
            "min_link_score": min_link_score,
            "evidence_mode": evidence_mode,
            "max_rows_per_sense": max_rows_per_sense,
            "include_related_hyponyms": bool(include_related_hyponyms),
            "max_related_rows_per_sense": max(0, int(max_related_rows_per_sense)),
            "related_hyponym_depth": max(1, int(related_hyponym_depth)),
            "related_hyponym_roles": related_hyponym_roles,
            "family_rows": family_rows,
        },
        "items": items,
    }


def _build_family_items(
    family: Mapping[str, object],
    *,
    role: str,
    wordnet_index: WordNetIndex,
    min_link_score: float,
    max_rows_per_sense: int,
    include_related_hyponyms: bool,
    max_related_rows_per_sense: int,
    related_hyponym_depth: int,
    related_hyponym_roles: str,
    evidence_mode: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    trigger = str(family.get("trigger") or "").strip()
    active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
    items: list[dict[str, object]] = []
    link_rows: list[dict[str, object]] = []
    active_source_senses = [
        ("active", active, {}),
        *(
            (
                f"active-visible-alias-{alias_index}",
                alias_sense,
                {
                    "active_visible_alias_sense_id": _sense_id(alias_sense),
                    "active_visible_alias_target": str(
                        alias_sense.get("target_lemma") or ""
                    ).strip(),
                    "active_visible_alias_pos": str(alias_sense.get("canonical_pos") or "").strip(),
                },
            )
            for alias_index, alias_sense in enumerate(_active_visible_alias_senses(active), start=1)
        ),
    ]
    for source_label, source_sense, extra_metadata in active_source_senses:
        active_candidates = wordnet_index.candidates_for_sense(
            trigger=trigger,
            sense=source_sense,
            min_link_score=min_link_score,
            include_related_hyponyms=include_related_hyponyms,
            max_related_candidates=max_related_rows_per_sense,
            related_hyponym_depth=related_hyponym_depth,
        )
        link_rows.append(_link_row(source_sense, active_candidates, relation_type="anchor_cue"))
        for index, (candidate, evidence_kind, evidence_text) in enumerate(
            _candidate_evidence_rows(
                active_candidates,
                evidence_mode=evidence_mode,
                max_rows_per_sense=max_rows_per_sense,
            ),
            start=1,
        ):
            items.append(
                _item(
                    family=family,
                    role=role,
                    active_sense=active,
                    candidate_sense=active,
                    relation_type="anchor_cue",
                    wordnet_candidate=candidate,
                    evidence_kind=evidence_kind,
                    evidence_text=evidence_text,
                    row_suffix=f"{source_label}-wordnet-{evidence_kind}-{index}",
                    roles=["cue_generation", "discrimination"],
                    example_bucket="active",
                    extra_metadata=extra_metadata,
                )
            )
    for shadow in family.get("shadows", ()):
        if not isinstance(shadow, Mapping):
            continue
        shadow_candidates = wordnet_index.candidates_for_sense(
            trigger=trigger,
            sense=shadow,
            min_link_score=min_link_score,
            include_related_hyponyms=(include_related_hyponyms and related_hyponym_roles == "all"),
            max_related_candidates=max_related_rows_per_sense,
            related_hyponym_depth=related_hyponym_depth,
        )
        link_rows.append(_link_row(shadow, shadow_candidates, relation_type="shadow_candidate"))
        for index, (candidate, evidence_kind, evidence_text) in enumerate(
            _candidate_evidence_rows(
                shadow_candidates,
                evidence_mode=evidence_mode,
                max_rows_per_sense=max_rows_per_sense,
            ),
            start=1,
        ):
            items.append(
                _item(
                    family=family,
                    role=role,
                    active_sense=active,
                    candidate_sense=shadow,
                    relation_type="shadow_candidate",
                    wordnet_candidate=candidate,
                    evidence_kind=evidence_kind,
                    evidence_text=evidence_text,
                    row_suffix=(
                        f"shadow-{_slug(_sense_id(shadow))}-wordnet-{evidence_kind}-{index}"
                    ),
                    roles=["discrimination"],
                    example_bucket="shadow",
                )
            )
    return items, link_rows


def _item(
    *,
    family: Mapping[str, object],
    role: str,
    active_sense: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    relation_type: str,
    wordnet_candidate: WordNetCandidate,
    evidence_kind: str,
    evidence_text: str,
    row_suffix: str,
    roles: Sequence[str],
    example_bucket: str,
    extra_metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    metadata = {
        "family_id": family_id,
        "queue_role": role,
        "active_sense_id": _sense_id(active_sense),
        "candidate_sense_id": _sense_id(candidate_sense),
        "example_bucket": example_bucket,
        "source_view": "wordnet_synset",
        "wordnet_sense_id": wordnet_candidate.sense_id,
        "wordnet_synset_id": wordnet_candidate.synset_id,
        "wordnet_sense_rank": wordnet_candidate.sense_rank,
        "wordnet_link_score": wordnet_candidate.score,
        "wordnet_link_overlap": list(wordnet_candidate.overlap_tokens),
        "wordnet_evidence_kind": evidence_kind,
        "wordnet_source_relation": wordnet_candidate.source_relation,
        "wordnet_relation_path": list(wordnet_candidate.relation_path),
    }
    if extra_metadata:
        metadata.update(dict(extra_metadata))
    return {
        "row_id": f"{_slug(family_id)}:{row_suffix}",
        "relation_type": relation_type,
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active_sense.get("target_lemma") or "").strip(),
        "candidate_target": str(candidate_sense.get("target_lemma") or "").strip(),
        "active_sense_hint": _sense_hint(active_sense, note="fixed_shadow_active"),
        "candidate_sense_hint": _sense_hint(
            candidate_sense,
            note="wordnet_linked_candidate",
            wordnet_candidate=wordnet_candidate,
        ),
        "candidate_pos": str(candidate_sense.get("canonical_pos") or "").strip(),
        "evidence_text": evidence_text,
        "example_count": 1,
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "roles": list(roles),
        "metadata": metadata,
    }


def _sense_hint(
    sense: Mapping[str, object],
    *,
    note: str,
    wordnet_candidate: WordNetCandidate | None = None,
) -> dict[str, object]:
    metadata = None
    if wordnet_candidate is not None:
        metadata = {
            "wordnet_provider": "wordnet_en_json",
            "wordnet_locator_kind": "synset_id",
            "wordnet_sense_id": wordnet_candidate.sense_id,
            "wordnet_synset_id": wordnet_candidate.synset_id,
            "wordnet_sense_rank": wordnet_candidate.sense_rank,
            "wordnet_link_score": wordnet_candidate.score,
            "wordnet_link_overlap": list(wordnet_candidate.overlap_tokens),
            "wordnet_source_relation": wordnet_candidate.source_relation,
            "wordnet_relation_path": list(wordnet_candidate.relation_path),
        }
    return _base_sense_hint(sense, note=note, metadata=metadata)


def _link_row(
    sense: Mapping[str, object],
    candidates: Sequence[WordNetCandidate],
    *,
    relation_type: str,
) -> dict[str, object]:
    best = candidates[0] if candidates else None
    return {
        "sense_id": _sense_id(sense),
        "target_lemma": str(sense.get("target_lemma") or "").strip(),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "relation_type": relation_type,
        "linked": best is not None,
        "best_wordnet_sense_id": best.sense_id if best else "",
        "best_wordnet_synset_id": best.synset_id if best else "",
        "best_wordnet_sense_rank": best.sense_rank if best else 0,
        "best_link_score": best.score if best else 0.0,
        "best_overlap": list(best.overlap_tokens) if best else [],
        "candidate_count": len(candidates),
    }


def _candidate_evidence_rows(
    candidates: Sequence[WordNetCandidate],
    *,
    evidence_mode: str,
    max_rows_per_sense: int,
) -> list[tuple[WordNetCandidate, str, str]]:
    rows: list[tuple[WordNetCandidate, str, str]] = []
    for candidate in candidates:
        for evidence_kind, evidence_text in _candidate_evidence_texts(
            candidate,
            evidence_mode=evidence_mode,
        ):
            if not evidence_text:
                continue
            rows.append((candidate, evidence_kind, evidence_text))
            if len(rows) >= max_rows_per_sense:
                return rows
    return rows


def _candidate_evidence_texts(
    candidate: WordNetCandidate,
    *,
    evidence_mode: str,
) -> list[tuple[str, str]]:
    mode = _normalize_evidence_mode(evidence_mode)
    entry_sentences = [("entry_sentence", text) for text in candidate.entry_sentences]
    examples = [("example", text) for text in candidate.example_texts]
    definitions = [("definition", text) for text in candidate.definition_texts]
    if mode == "definition_preferred":
        values = [*definitions, *entry_sentences, *examples]
    elif mode == "definition_and_example":
        values = [*definitions, *entry_sentences, *examples]
    else:
        values = [*entry_sentences, *examples, *definitions]
    if not values and candidate.members:
        values = [("member_list", " | ".join(candidate.members))]
    deduped: list[tuple[str, str]] = []
    seen = set()
    for kind, text in values:
        clean = str(text or "").strip()
        key = clean.lower()
        if not clean or key in seen:
            continue
        deduped.append((kind, clean))
        seen.add(key)
    return deduped


def _family_summary_row(
    family: Mapping[str, object],
    *,
    role: str,
    items: Sequence[Mapping[str, object]],
    link_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    active_count = sum(1 for item in items if str(item.get("relation_type") or "") == "anchor_cue")
    shadow_count = sum(
        1 for item in items if str(item.get("relation_type") or "") == "shadow_candidate"
    )
    active = family.get("active") if isinstance(family.get("active"), Mapping) else {}
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active.get("target_lemma") or "").strip(),
        "role": role,
        "active_wordnet_count": active_count,
        "shadow_wordnet_count": shadow_count,
        "phrase_control_example_count": 0,
        "row_count": len(items),
        "link_rows": list(link_rows),
    }


def _build_report(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    family_rows: Sequence[Mapping[str, object]],
    normalized_batch: Mapping[str, object] | None,
    data_root: Path,
    wordnet_dir: Path,
    wordnet_index: WordNetIndex,
    missing_resources: Sequence[str],
    generated_at: str,
    run_id: str,
    source_scope: str,
    min_link_score: float,
    evidence_mode: str,
) -> dict[str, object]:
    queue_families = [
        family for family in queue_payload.get("families", ()) if isinstance(family, Mapping)
    ]
    target_rows = [row for row in family_rows if str(row.get("role") or "target") == "target"]
    missing_active = [
        str(row.get("family_id") or "")
        for row in target_rows
        if int(row.get("active_wordnet_count") or 0) <= 0
    ]
    missing_shadow = [
        str(row.get("family_id") or "")
        for row in target_rows
        if int(row.get("shadow_wordnet_count") or 0) <= 0
    ]
    summary = {
        "queue_family_count": len(queue_families),
        "source_family_count": len(family_rows),
        "target_family_count": len(target_rows),
        "row_count": int(normalized_batch.get("row_count") or 0)
        if isinstance(normalized_batch, Mapping)
        else 0,
        "families_with_active_wordnet": sum(
            1 for row in family_rows if int(row.get("active_wordnet_count") or 0) > 0
        ),
        "families_with_shadow_wordnet": sum(
            1 for row in family_rows if int(row.get("shadow_wordnet_count") or 0) > 0
        ),
        "target_families_with_active_wordnet": sum(
            1 for row in target_rows if int(row.get("active_wordnet_count") or 0) > 0
        ),
        "target_families_with_shadow_wordnet": sum(
            1 for row in target_rows if int(row.get("shadow_wordnet_count") or 0) > 0
        ),
        "families_with_phrase_control_examples": 0,
        "missing_active_family_keys": missing_active,
        "missing_shadow_family_keys": missing_shadow,
        "min_link_score": float(min_link_score),
        "evidence_mode": evidence_mode,
    }
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "missing_resources" if missing_resources else "ok",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "run_id": run_id,
        "source_scope": source_scope,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip()
        if isinstance(normalized_batch, Mapping)
        else "",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "resource_status": {
            "data_root": str(data_root),
            "wordnet_dir": str(wordnet_dir),
            "wordnet_dir_exists": wordnet_dir.exists(),
            "wordnet_source_file_count": wordnet_index.source_file_count,
            "wordnet_entry_count": len(wordnet_index.entries_by_word),
            "wordnet_synset_count": len(wordnet_index.synsets_by_id),
            "missing_resources": list(missing_resources),
        },
        "summary": summary,
        "family_rows": list(family_rows),
        "recommendation": _build_recommendation(summary, missing_resources=missing_resources),
    }


def render_wordnet_example_frame_batch_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es WordNet Example-Frame Batch",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Source: `{report.get('source_id', '')}` / `{report.get('source_family', '')}`",
        f"- Scope: `{report.get('source_scope', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Min link score: `{summary.get('min_link_score', 0)}`",
        f"- Evidence mode: `{summary.get('evidence_mode', '')}`",
        "",
        "## Coverage",
        "",
        f"- Queue families: `{summary.get('queue_family_count', 0)}`",
        f"- Source families: `{summary.get('source_family_count', 0)}`",
        f"- Target families: `{summary.get('target_family_count', 0)}`",
        f"- Target families with active WordNet rows: `{summary.get('target_families_with_active_wordnet', 0)}`",
        f"- Target families with shadow WordNet rows: `{summary.get('target_families_with_shadow_wordnet', 0)}`",
        f"- Families with phrase-control examples: `{summary.get('families_with_phrase_control_examples', 0)}`",
        "",
        "| Family | Role | Active | Shadow | Phrase | Rows | Best Links |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        link_summary = _render_link_summary(row.get("link_rows"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('role', '')}`",
                    str(row.get("active_wordnet_count", 0)),
                    str(row.get("shadow_wordnet_count", 0)),
                    str(row.get("phrase_control_example_count", 0)),
                    str(row.get("row_count", 0)),
                    link_summary,
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _build_source_dataset(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    residual_cycle_payload: Mapping[str, object] | None,
    family_keys: Sequence[str],
    scope: str,
) -> tuple[dict[str, object], dict[str, str]]:
    if scope == "prompt_queue":
        return build_queue_subset_dataset(dataset_payload, queue_payload)
    if scope == "all_dataset_families":
        return _all_family_dataset(dataset_payload)
    if scope == "residual_semantic_gaps":
        residual_keys = _residual_semantic_gap_keys(residual_cycle_payload)
        payload, roles = _all_family_dataset(dataset_payload)
        payload["families"] = [
            family
            for family in payload.get("families", ())
            if isinstance(family, Mapping)
            and str(family.get("family_id") or "").strip() in residual_keys
        ]
        roles = {
            str(family.get("family_id") or "").strip(): roles.get(
                str(family.get("family_id") or "").strip(),
                "target",
            )
            for family in payload.get("families", ())
            if isinstance(family, Mapping)
        }
        return payload, roles
    if scope == "family_keys":
        selected_keys = {str(key or "").strip() for key in family_keys if str(key or "").strip()}
        if not selected_keys:
            raise ValueError("family_keys scope requires at least one --family-key value.")
        payload, roles = _all_family_dataset(dataset_payload)
        payload["families"] = [
            family
            for family in payload.get("families", ())
            if isinstance(family, Mapping)
            and str(family.get("family_id") or "").strip() in selected_keys
        ]
        roles = {
            str(family.get("family_id") or "").strip(): roles.get(
                str(family.get("family_id") or "").strip(),
                "target",
            )
            for family in payload.get("families", ())
            if isinstance(family, Mapping)
        }
        return payload, roles
    raise ValueError(f"unsupported source scope: {scope}")


def _residual_semantic_gap_keys(payload: Mapping[str, object] | None) -> set[str]:
    residuals = payload.get("residuals") if isinstance(payload, Mapping) else {}
    if not isinstance(residuals, Mapping):
        return set()
    keys = residuals.get("semantic_gap_family_keys")
    if not isinstance(keys, Sequence) or isinstance(keys, (str, bytes)):
        return set()
    return {str(key or "").strip() for key in keys if str(key or "").strip()}


def _build_recommendation(
    summary: Mapping[str, object],
    *,
    missing_resources: Sequence[str],
) -> str:
    if missing_resources:
        return (
            "Resolve the local English WordNet JSON pack before building WordNet "
            "example-frame evidence."
        )
    return (
        "This adapter is a real local source pass for active/shadow semantic evidence, "
        "but it intentionally does not solve phrase containment. Run the source-admission "
        "cycle before using it as a challenger, and treat missing/low-score links as source "
        "gaps rather than generated coverage."
    )


def _render_link_summary(link_rows: object) -> str:
    if not isinstance(link_rows, Sequence) or isinstance(link_rows, (str, bytes)):
        return "`n/a`"
    parts = []
    for row in link_rows:
        if not isinstance(row, Mapping):
            continue
        target = str(row.get("target_lemma") or "").strip()
        synset = str(row.get("best_wordnet_synset_id") or "").strip()
        score = row.get("best_link_score", 0.0)
        if synset:
            parts.append(f"`{target}:{synset}@{score}`")
        else:
            parts.append(f"`{target}:missing`")
    return "<br>".join(parts) if parts else "`n/a`"


def _normalize_scope(value: str) -> str:
    text = str(value or "").strip() or DEFAULT_SCOPE
    if text not in SUPPORTED_SCOPES:
        raise ValueError(f"unsupported source scope: {text}")
    return text


def _normalize_evidence_mode(value: str) -> str:
    text = str(value or "").strip() or DEFAULT_EVIDENCE_MODE
    if text not in SUPPORTED_EVIDENCE_MODES:
        raise ValueError(f"unsupported WordNet evidence mode: {text}")
    return text


def _normalize_related_hyponym_roles(value: str) -> str:
    text = str(value or "").strip() or DEFAULT_RELATED_HYPONYM_ROLES
    if text not in SUPPORTED_RELATED_HYPONYM_ROLES:
        raise ValueError(f"unsupported WordNet related hyponym roles: {text}")
    return text


def main() -> int:
    args = _parse_args()
    queue_payload = _load_json(args.queue_json)
    dataset_payload = load_sentence_veto_dataset(args.dataset)
    residual_cycle_payload = (
        _load_json(args.residual_cycle_json)
        if args.residual_cycle_json.exists() and args.scope == "residual_semantic_gaps"
        else None
    )
    data_root = Path(args.data_root)
    wordnet_dir = (
        Path(args.wordnet_dir)
        if args.wordnet_dir is not None
        else data_root / "language_packs" / "english-wordnet-2025-json"
    )
    bundle = build_wordnet_example_frame_bundle(
        queue_payload=queue_payload,
        dataset_payload=dataset_payload,
        wordnet_dir=wordnet_dir,
        residual_cycle_payload=residual_cycle_payload,
        data_root=data_root,
        run_id=str(args.run_id or "").strip() or DEFAULT_RUN_ID,
        scope=str(args.scope or "").strip() or DEFAULT_SCOPE,
        family_keys=args.family_key,
        min_link_score=float(args.min_link_score),
        max_rows_per_sense=int(args.max_rows_per_sense),
        include_related_hyponyms=bool(args.include_related_hyponyms),
        max_related_rows_per_sense=int(args.max_related_rows_per_sense),
        related_hyponym_depth=int(args.related_hyponym_depth),
        related_hyponym_roles=str(args.related_hyponym_roles or "").strip()
        or DEFAULT_RELATED_HYPONYM_ROLES,
        evidence_mode=str(args.evidence_mode or "").strip() or DEFAULT_EVIDENCE_MODE,
    )
    if isinstance(bundle.get("intake_batch"), Mapping):
        _write_json(args.intake_batch_out, bundle["intake_batch"])
    if isinstance(bundle.get("normalized_batch"), Mapping):
        _write_json(args.normalized_batch_out, bundle["normalized_batch"])
    _write_json(args.json_out, bundle["report"])
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_wordnet_example_frame_batch_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if isinstance(bundle.get("intake_batch"), Mapping):
        print(f"Wrote intake batch to {args.intake_batch_out}")
    if isinstance(bundle.get("normalized_batch"), Mapping):
        print(f"Wrote normalized batch to {args.normalized_batch_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
