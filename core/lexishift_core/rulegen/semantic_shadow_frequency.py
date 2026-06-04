from __future__ import annotations

from dataclasses import dataclass
from math import exp, log1p
from typing import Mapping, Optional, Sequence

from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig, SqliteFrequencyStore
from lexishift_core.helper.frequency_packs import resolve_configured_frequency_pack
from lexishift_core.helper.paths import HelperPaths


@dataclass
class ShadowFrequencyLookup:
    pair: str
    pack_id: str
    provider: str
    value_column: str | None
    rank_column: str | None
    max_value: float | None
    max_rank: float | None
    _store: SqliteFrequencyStore

    def close(self) -> None:
        self._store.close()

    def __enter__(self) -> "ShadowFrequencyLookup":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def build_details(self, lemma: str) -> dict[str, object]:
        normalized_lemma = str(lemma or "").strip()
        lowered_lemma = normalized_lemma.lower()
        value = self._lookup_numeric(lowered_lemma, self.value_column)
        rank = self._lookup_numeric(lowered_lemma, self.rank_column)
        value_score = _normalize_frequency_value(value, self.max_value)
        rank_score = _normalize_rank_value(rank, self.max_rank)
        score_candidates = [candidate for candidate in (value_score, rank_score) if candidate > 0.0]
        frequency_score = max(score_candidates) if score_candidates else 0.0
        return {
            "target_frequency_present": value is not None or rank is not None,
            "target_frequency_value": value,
            "target_frequency_rank": rank,
            "target_frequency_score": frequency_score,
            "target_frequency_provider": self.provider,
            "target_frequency_pack_id": self.pack_id,
        }

    def _lookup_numeric(self, lemma: str, column: str | None) -> float | None:
        if not lemma or not column:
            return None
        value = self._store.get_value(lemma, column)
        if value is not None:
            return float(value)
        if lemma != lemma.lower():
            lowered = self._store.get_value(lemma.lower(), column)
            if lowered is not None:
                return float(lowered)
        return None


def open_shadow_frequency_lookup(
    *,
    pair: str,
    helper_paths: HelperPaths,
) -> Optional[ShadowFrequencyLookup]:
    pack_ref, _reason = resolve_configured_frequency_pack(
        pair,
        frequency_packs_dir=helper_paths.frequency_packs_dir,
    )
    if pack_ref is None:
        return None
    store = SqliteFrequencyStore(SqliteFrequencyConfig(path=pack_ref.path))
    value_column = store.resolve_frequency_column()
    rank_column = store.resolve_rank_column()
    max_value = store.max_value(value_column) if value_column else None
    max_rank = store.max_value(rank_column) if rank_column else None
    return ShadowFrequencyLookup(
        pair=pair,
        pack_id=pack_ref.pack_id,
        provider=pack_ref.provider,
        value_column=value_column,
        rank_column=rank_column,
        max_value=max_value,
        max_rank=max_rank,
        _store=store,
    )


def enrich_candidate_frequency_details(
    *,
    candidate: dict[str, object],
    frequency_lookup: ShadowFrequencyLookup | None,
) -> None:
    if frequency_lookup is None:
        return
    target = str(candidate.get("target") or "").strip()
    if not target:
        return
    candidate.update(frequency_lookup.build_details(target))


def select_frequency_representative_targets(
    *,
    shadow_candidates: Sequence[Mapping[str, object]],
    top_k: int,
) -> tuple[str, ...]:
    normalized_top_k = max(0, int(top_k))
    if normalized_top_k <= 0:
        return ()
    best_by_target: dict[str, tuple[float, float, float]] = {}
    for candidate in shadow_candidates:
        target = str(candidate.get("target") or "").strip()
        if not target:
            continue
        score = _safe_float(candidate.get("target_frequency_score"))
        value = _safe_float(candidate.get("target_frequency_value"))
        rank = _safe_float(candidate.get("target_frequency_rank"))
        if score <= 0.0 and value <= 0.0 and rank <= 0.0:
            continue
        current = best_by_target.get(target)
        ranking = (score, value, -rank if rank > 0.0 else 0.0)
        if current is None or ranking > current:
            best_by_target[target] = ranking
    ranked_targets = sorted(
        best_by_target.items(),
        key=lambda item: (
            item[1][0],
            item[1][1],
            item[1][2],
            item[0],
        ),
        reverse=True,
    )
    return tuple(target for target, _ranking in ranked_targets[:normalized_top_k])


def candidate_has_frequency_representative_bonus(
    *,
    candidate: Mapping[str, object],
    representative_targets: Sequence[str],
) -> bool:
    normalized_targets = {
        str(value or "").strip() for value in representative_targets if str(value or "").strip()
    }
    target = str(candidate.get("target") or "").strip()
    return bool(
        target
        and normalized_targets
        and target in normalized_targets
        and _safe_float(candidate.get("target_frequency_score")) > 0.0
    )


def build_frequency_similarity_details(
    *,
    candidate: Mapping[str, object],
    active_candidates: Sequence[Mapping[str, object]],
    tau: float,
) -> dict[str, float | bool | None]:
    candidate_score = _safe_float(candidate.get("target_frequency_score"))
    active_scores = [
        _safe_float(active_candidate.get("target_frequency_score"))
        for active_candidate in active_candidates
        if _safe_float(active_candidate.get("target_frequency_score")) > 0.0
    ]
    active_score = max(active_scores) if active_scores else 0.0
    if candidate_score <= 0.0 or active_score <= 0.0:
        return {
            "frequency_similarity_present": False,
            "active_target_frequency_score": active_score or None,
            "shadow_target_frequency_score": candidate_score or None,
            "frequency_similarity_gap": None,
            "frequency_similarity_score": 0.0,
        }
    normalized_tau = max(float(tau), 1e-6)
    gap = abs(active_score - candidate_score)
    similarity_score = float(exp(-(gap / normalized_tau)))
    return {
        "frequency_similarity_present": True,
        "active_target_frequency_score": active_score,
        "shadow_target_frequency_score": candidate_score,
        "frequency_similarity_gap": gap,
        "frequency_similarity_score": similarity_score,
    }


def _normalize_frequency_value(value: float | None, max_value: float | None) -> float:
    if value is None or max_value is None or value <= 0.0 or max_value <= 0.0:
        return 0.0
    return min(1.0, log1p(float(value)) / log1p(float(max_value)))


def _normalize_rank_value(rank: float | None, max_rank: float | None) -> float:
    if rank is None or max_rank is None or rank <= 0.0 or max_rank <= 0.0:
        return 0.0
    if max_rank <= 1.0:
        return 1.0
    normalized = 1.0 - ((float(rank) - 1.0) / (float(max_rank) - 1.0))
    return max(0.0, min(1.0, normalized))


def _safe_float(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value or "").strip() or "0")
    except (TypeError, ValueError):
        return 0.0
