from __future__ import annotations

from typing import Callable, Mapping, Sequence

import numpy as np

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.semantic_shadow_inventory import build_shadow_candidate_support_details
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss

DEFAULT_EMBEDDING_BRIDGE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_EMBEDDING_BRIDGE_MIN_SIMILARITY = 0.65
DEFAULT_EMBEDDING_BRIDGE_TOP_K = 1


def build_target_embedding_bridge_profiles(
    *,
    benchmark_targets: Sequence[object],
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    target_reverse_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    max_forward_records: int = 8,
    max_reverse_records: int = 8,
) -> dict[str, dict[str, object]]:
    profiles: dict[str, dict[str, object]] = {}
    for benchmark_target in benchmark_targets:
        target = str(getattr(benchmark_target, "target", "") or "").strip()
        if not target:
            continue
        fragments: list[str] = []
        primary_pos = ""
        for record in tuple(forward_records_by_target.get(target, ()))[
            : max(1, int(max_forward_records))
        ]:
            if not primary_pos:
                primary_pos = _build_canonical_pos(record)
            _append_record_fragments(fragments, record)
        for record in tuple(target_reverse_records_by_target.get(target, ()))[
            : max(1, int(max_reverse_records))
        ]:
            if not primary_pos:
                primary_pos = _build_canonical_pos(record)
            _append_record_fragments(fragments, record)
        profiles[target] = {
            "target": target,
            "primary_pos": primary_pos,
            "fragments": tuple(fragments),
            "card_text": " | ".join(fragments),
        }
    return profiles


def build_embedding_bridge_neighbor_index(
    *,
    target_profiles: Mapping[str, Mapping[str, object]],
    model_name: str = DEFAULT_EMBEDDING_BRIDGE_MODEL,
    min_similarity: float = DEFAULT_EMBEDDING_BRIDGE_MIN_SIMILARITY,
    top_k: int = DEFAULT_EMBEDDING_BRIDGE_TOP_K,
) -> dict[str, list[dict[str, object]]]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    return rank_embedding_bridge_neighbors_with_encoder(
        target_profiles=target_profiles,
        encoder=model.encode,
        min_similarity=min_similarity,
        top_k=top_k,
    )


def rank_embedding_bridge_neighbors_with_encoder(
    *,
    target_profiles: Mapping[str, Mapping[str, object]],
    encoder: Callable[..., object],
    min_similarity: float = DEFAULT_EMBEDDING_BRIDGE_MIN_SIMILARITY,
    top_k: int = DEFAULT_EMBEDDING_BRIDGE_TOP_K,
) -> dict[str, list[dict[str, object]]]:
    targets = [
        str(target).strip()
        for target, profile in sorted(target_profiles.items())
        if str(target).strip() and str(profile.get("card_text") or "").strip()
    ]
    if not targets:
        return {}
    texts = [str(target_profiles[target].get("card_text") or "").strip() for target in targets]
    embeddings = _encode_texts(encoder, texts)
    if embeddings.size == 0:
        return {target: [] for target in targets}
    normalized_embeddings = _normalize_rows(embeddings)
    similarity_matrix = normalized_embeddings @ normalized_embeddings.T
    neighbor_index: dict[str, list[dict[str, object]]] = {}
    normalized_top_k = max(1, int(top_k))
    normalized_min_similarity = float(min_similarity)
    for row_index, target in enumerate(targets):
        active_profile = target_profiles[target]
        active_pos = str(active_profile.get("primary_pos") or "").strip().lower()
        ranked_neighbors: list[tuple[float, dict[str, object]]] = []
        for candidate_index, candidate_target in enumerate(targets):
            if candidate_index == row_index:
                continue
            candidate_profile = target_profiles[candidate_target]
            candidate_pos = str(candidate_profile.get("primary_pos") or "").strip().lower()
            if active_pos and candidate_pos and candidate_pos != active_pos:
                continue
            similarity = float(similarity_matrix[row_index, candidate_index])
            if similarity < normalized_min_similarity:
                continue
            ranked_neighbors.append(
                (
                    similarity,
                    {
                        "target": candidate_target,
                        "similarity": similarity,
                        "primary_pos": candidate_pos,
                        "fragments": list(candidate_profile.get("fragments") or ())[:3],
                    },
                )
            )
        ranked_neighbors.sort(key=lambda item: (-item[0], str(item[1].get("target") or "").strip()))
        neighbor_index[target] = [
            payload for _score, payload in ranked_neighbors[:normalized_top_k]
        ]
    return neighbor_index


def augment_inventory_with_embedding_bridge(
    *,
    inventory: Mapping[str, object],
    target_profiles: Mapping[str, Mapping[str, object]],
    neighbor_index: Mapping[str, Sequence[Mapping[str, object]]],
    only_when_no_benchmark_target_shadow: bool = True,
    support_score_min_for_backoff: float | None = None,
) -> dict[str, object]:
    inventory_targets = inventory.get("targets")
    if not isinstance(inventory_targets, Sequence) or isinstance(inventory_targets, (str, bytes)):
        return dict(inventory)
    target_trigger_index = _build_target_trigger_index(inventory_targets)

    updated_targets: list[dict[str, object]] = []
    for target_row in inventory_targets:
        if not isinstance(target_row, Mapping):
            continue
        target = str(target_row.get("target") or "").strip()
        trigger_entries = target_row.get("trigger_entries")
        if not isinstance(trigger_entries, Sequence) or isinstance(trigger_entries, (str, bytes)):
            updated_targets.append(dict(target_row))
            continue
        updated_trigger_entries: list[dict[str, object]] = []
        for trigger_entry in trigger_entries:
            if not isinstance(trigger_entry, Mapping):
                continue
            updated_trigger_entry = dict(trigger_entry)
            active_candidates = [
                dict(candidate)
                for candidate in _as_mapping_sequence(trigger_entry.get("active_candidates"))
            ]
            shadow_candidates = [
                dict(candidate)
                for candidate in _as_mapping_sequence(trigger_entry.get("shadow_candidates"))
            ]
            if not active_candidates:
                updated_trigger_entry["active_candidates"] = active_candidates
                updated_trigger_entry["shadow_candidates"] = shadow_candidates
                updated_trigger_entries.append(updated_trigger_entry)
                continue
            if only_when_no_benchmark_target_shadow and any(
                bool(candidate.get("benchmark_target_present")) for candidate in shadow_candidates
            ):
                updated_trigger_entry["active_candidates"] = active_candidates
                updated_trigger_entry["shadow_candidates"] = shadow_candidates
                updated_trigger_entries.append(updated_trigger_entry)
                continue
            if support_score_min_for_backoff is not None and any(
                float(
                    build_shadow_candidate_support_details(
                        candidate=candidate,
                        active_candidates=active_candidates,
                    ).get("support_score")
                    or 0.0
                )
                >= float(support_score_min_for_backoff)
                for candidate in shadow_candidates
            ):
                updated_trigger_entry["active_candidates"] = active_candidates
                updated_trigger_entry["shadow_candidates"] = shadow_candidates
                updated_trigger_entries.append(updated_trigger_entry)
                continue
            existing_targets = {
                str(candidate.get("target") or "").strip()
                for candidate in shadow_candidates
                if str(candidate.get("target") or "").strip()
            }
            for neighbor in neighbor_index.get(target, ()):
                if not isinstance(neighbor, Mapping):
                    continue
                candidate_target = str(neighbor.get("target") or "").strip()
                if not candidate_target or candidate_target in existing_targets:
                    continue
                normalized_trigger = sanitize_dictionary_gloss(
                    updated_trigger_entry.get("trigger") or ""
                ).lower()
                candidate_profile = target_profiles.get(candidate_target, {})
                reviewed_trigger_support = bool(
                    normalized_trigger
                    and normalized_trigger in target_trigger_index.get(candidate_target, set())
                )
                shadow_candidates.append(
                    {
                        "target": candidate_target,
                        "sense_label": (
                            f"embedding bridge ({float(neighbor.get('similarity') or 0.0):.3f})"
                        ),
                        "canonical_pos": str(neighbor.get("primary_pos") or "").strip().lower(),
                        "provider": "semantic_embedding_bridge",
                        "locator": {
                            "provider": "semantic_embedding_bridge",
                            "locator_kind": "target_profile",
                            "target_key": candidate_target,
                        },
                        "glosses": list(neighbor.get("fragments") or ())[:3],
                        "qualifiers": None,
                        "candidate_sources": ["semantic_embedding_bridge"],
                        "benchmark_target_present": True,
                        "reviewed_trigger_support": reviewed_trigger_support,
                        "embedding_bridge_similarity": float(neighbor.get("similarity") or 0.0),
                        "embedding_bridge_text": str(
                            candidate_profile.get("card_text") or ""
                        ).strip(),
                    }
                )
                existing_targets.add(candidate_target)
            updated_trigger_entry["active_candidates"] = active_candidates
            updated_trigger_entry["shadow_candidates"] = shadow_candidates
            updated_trigger_entries.append(updated_trigger_entry)
        updated_target_row = dict(target_row)
        updated_target_row["trigger_entries"] = updated_trigger_entries
        updated_targets.append(updated_target_row)

    updated_inventory = dict(inventory)
    updated_inventory["targets"] = updated_targets
    return updated_inventory


def _append_record_fragments(fragments: list[str], record: TranslationGlossRecord) -> None:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    _append_fragment(fragments, record.translation)
    raw_glosses = metadata.get("sense_raw_glosses")
    if isinstance(raw_glosses, Sequence) and not isinstance(raw_glosses, (str, bytes)):
        for item in raw_glosses[:3]:
            _append_fragment(fragments, item)
    topics = metadata.get("sense_topics")
    if isinstance(topics, Sequence) and not isinstance(topics, (str, bytes)):
        for item in topics[:2]:
            _append_fragment(fragments, item)


def _append_fragment(fragments: list[str], value: object) -> None:
    normalized = sanitize_dictionary_gloss(value)
    if not normalized or normalized in fragments:
        return
    fragments.append(normalized)


def _build_canonical_pos(record: TranslationGlossRecord) -> str:
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    candidate = str(metadata.get("dictionary_pos_canonical") or "").strip().lower()
    if candidate:
        return candidate
    return str(record.pos_raw or "").strip().lower()


def _encode_texts(encoder: Callable[..., object], texts: Sequence[str]) -> np.ndarray:
    try:
        encoded = encoder(texts, normalize_embeddings=True)
    except TypeError:
        encoded = encoder(texts)
    return np.asarray(encoded, dtype=float)


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError("Expected a 2D embedding matrix.")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


def _as_mapping_sequence(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _build_target_trigger_index(
    inventory_targets: Sequence[object],
) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for target_row in inventory_targets:
        if not isinstance(target_row, Mapping):
            continue
        target = str(target_row.get("target") or "").strip()
        if not target:
            continue
        reviewed_triggers = target_row.get("reviewed_triggers")
        if not isinstance(reviewed_triggers, Sequence) or isinstance(
            reviewed_triggers, (str, bytes)
        ):
            continue
        index[target] = {
            sanitize_dictionary_gloss(trigger).lower()
            for trigger in reviewed_triggers
            if sanitize_dictionary_gloss(trigger)
        }
    return index
