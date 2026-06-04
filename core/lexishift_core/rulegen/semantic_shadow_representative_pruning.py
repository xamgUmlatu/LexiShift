from __future__ import annotations

from typing import Any, Mapping, Sequence, TypeVar


_ScoreT = TypeVar("_ScoreT", bound=tuple[Any, ...])


def apply_representative_pruning(
    ranked_candidates: Sequence[tuple[_ScoreT, dict[str, object]]],
    *,
    mode: str,
    mode_off: str,
    supported_modes: Sequence[str],
    normalize_text,
) -> list[tuple[_ScoreT, dict[str, object]]]:
    normalized_mode = str(mode or "").strip() or str(mode_off or "").strip()
    if normalized_mode == mode_off:
        return list(ranked_candidates)
    if normalized_mode not in supported_modes:
        raise ValueError(
            f"Unsupported representative pruning mode: {normalized_mode!r}; "
            f"expected one of {tuple(supported_modes)!r}"
        )

    cluster_members: dict[tuple[str, str] | tuple[str, str, str], int] = {}
    selected: dict[
        tuple[str, str] | tuple[str, str, str],
        tuple[_ScoreT, dict[str, object]],
    ] = {}
    for score_vector, candidate in ranked_candidates:
        cluster_key = build_representative_cluster_key(candidate, normalize_text=normalize_text)
        cluster_members[cluster_key] = cluster_members.get(cluster_key, 0) + 1
        current = selected.get(cluster_key)
        if current is None or score_vector > current[0]:
            selected[cluster_key] = (score_vector, dict(candidate))

    pruned: list[tuple[_ScoreT, dict[str, object]]] = []
    for cluster_key, (score_vector, candidate) in selected.items():
        candidate["representative_pruning_mode"] = normalized_mode
        candidate["representative_cluster_key"] = list(cluster_key)
        candidate["representative_cluster_size"] = int(cluster_members.get(cluster_key, 1))
        pruned.append((score_vector, candidate))
    return pruned


def build_representative_cluster_key(
    candidate: Mapping[str, object],
    *,
    normalize_text,
) -> tuple[str, str] | tuple[str, str, str]:
    canonical_pos = normalize_text(candidate.get("canonical_pos") or "")
    sense_label = normalize_text(candidate.get("sense_label") or "")
    if sense_label:
        return (canonical_pos, sense_label)
    target = normalize_text(candidate.get("target") or "")
    return ("target_fallback", canonical_pos, target)
