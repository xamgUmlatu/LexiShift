from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.time import format_ts, now_utc, parse_ts

BROWSING_SIGNAL_SOURCE = "source"
BROWSING_SIGNAL_TARGET = "target"
BROWSING_SIGNAL_REPLACEMENT_EXPOSURE = "replacement_exposure"
BROWSING_SIGNAL_SIDES = frozenset(
    {
        BROWSING_SIGNAL_SOURCE,
        BROWSING_SIGNAL_TARGET,
        BROWSING_SIGNAL_REPLACEMENT_EXPOSURE,
    }
)

BROWSING_STRENGTH_OFF = "off"
BROWSING_STRENGTH_BALANCED = "balanced"
BROWSING_STRENGTH_STRONG = "strong"


@dataclass(frozen=True)
class BrowsingSignalIngestPolicy:
    version: str = "browsing_signal_aggregate_v1"
    max_signals_per_packet: int = 200
    max_count_per_signal: float = 5.0
    max_items_per_store: int = 5000
    prune_signal_below: float = 0.01
    half_life_days: float = 30.0
    browsing_signal_cap: float = 16.0
    replacement_exposure_weight: float = 0.35


@dataclass(frozen=True)
class BrowsingAdmissionStrength:
    name: str
    browsing_alpha: float
    max_browsing_boost: float
    browsing_budget_share: float
    volume_tau: float = 2.0
    min_browsing_signal: float = 0.05
    preference_alignment_weight: float = 0.25


@dataclass(frozen=True)
class BrowsingSignalAggregate:
    target_lemma: str
    source_hit_count: float = 0.0
    target_hit_count: float = 0.0
    replacement_exposure_count: float = 0.0
    source_mapping_confidence: float = 0.0
    last_seen_at: Optional[str] = None
    decayed_at: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "target_lemma": self.target_lemma,
            "source_hit_count": round(float(self.source_hit_count), 6),
            "target_hit_count": round(float(self.target_hit_count), 6),
            "replacement_exposure_count": round(float(self.replacement_exposure_count), 6),
            "source_mapping_confidence": round(float(self.source_mapping_confidence), 6),
        }
        if self.last_seen_at:
            payload["last_seen_at"] = self.last_seen_at
        if self.decayed_at:
            payload["decayed_at"] = self.decayed_at
        return payload


@dataclass(frozen=True)
class BrowsingSignalStore:
    pair: str
    profile_id: str = "default"
    items: Mapping[str, BrowsingSignalAggregate] = field(default_factory=dict)
    version: int = 1
    updated_at: Optional[str] = None
    policy_version: str = "browsing_signal_aggregate_v1"

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "pair": self.pair,
            "profile_id": self.profile_id,
            "updated_at": self.updated_at,
            "policy_version": self.policy_version,
            "items": {
                lemma: self.items[lemma].to_dict()
                for lemma in sorted(self.items)
                if self.items[lemma].target_lemma
            },
        }


@dataclass(frozen=True)
class BrowsingSignalPacketEntry:
    target_lemma: str
    side: str
    count: float = 1.0
    source_mapping_confidence: float = 1.0


@dataclass(frozen=True)
class BrowsingSignalPacket:
    pair: str
    profile_id: str = "default"
    signals: Sequence[BrowsingSignalPacketEntry] = field(default_factory=tuple)
    captured_at: Optional[str] = None


@dataclass(frozen=True)
class BrowsingSignalIngestResult:
    store: BrowsingSignalStore
    input_signal_count: int
    accepted_signal_count: int
    dropped_signal_count: int
    capped_signal_count: int
    pruned_item_count: int
    retained_item_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "input_signal_count": self.input_signal_count,
            "accepted_signal_count": self.accepted_signal_count,
            "dropped_signal_count": self.dropped_signal_count,
            "capped_signal_count": self.capped_signal_count,
            "pruned_item_count": self.pruned_item_count,
            "retained_item_count": self.retained_item_count,
        }


@dataclass(frozen=True)
class BrowsingAdmissionCandidate:
    lemma: str
    neutral_score: float
    readiness_multiplier: float = 1.0
    explicit_preference_fit: float = 0.0
    source_confidence: float = 1.0


@dataclass(frozen=True)
class BrowsingAdmissionSimulationRow:
    lemma: str
    neutral_rank: int
    final_rank: int
    neutral_score: float
    final_score: float
    browsing_signal: float
    browsing_boost: float
    selected: bool
    selected_lane: str = "not_selected"
    neutral_selected: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "lemma": self.lemma,
            "neutral_rank": self.neutral_rank,
            "final_rank": self.final_rank,
            "neutral_score": round(self.neutral_score, 6),
            "final_score": round(self.final_score, 6),
            "browsing_signal": round(self.browsing_signal, 6),
            "browsing_boost": round(self.browsing_boost, 6),
            "selected": self.selected,
            "selected_lane": self.selected_lane,
            "neutral_selected": self.neutral_selected,
        }


@dataclass(frozen=True)
class BrowsingAdmissionSimulationResult:
    strength: str
    admission_budget: int
    browsing_budget: int
    general_budget: int
    signal_volume: float
    volume_factor: float
    selected_lemmas: Sequence[str]
    neutral_selected_lemmas: Sequence[str]
    browsing_lane_count: int
    browsing_relevant_selected_count: int
    browsing_driven_count: int
    rows: Sequence[BrowsingAdmissionSimulationRow]

    def to_dict(self) -> dict[str, object]:
        selected_count = len(self.selected_lemmas)
        return {
            "strength": self.strength,
            "admission_budget": self.admission_budget,
            "browsing_budget": self.browsing_budget,
            "general_budget": self.general_budget,
            "signal_volume": round(self.signal_volume, 6),
            "volume_factor": round(self.volume_factor, 6),
            "selected_lemmas": list(self.selected_lemmas),
            "neutral_selected_lemmas": list(self.neutral_selected_lemmas),
            "browsing_lane_count": self.browsing_lane_count,
            "browsing_relevant_selected_count": self.browsing_relevant_selected_count,
            "browsing_driven_count": self.browsing_driven_count,
            "browsing_lane_share": _safe_share(self.browsing_lane_count, selected_count),
            "browsing_relevant_share": _safe_share(
                self.browsing_relevant_selected_count,
                selected_count,
            ),
            "browsing_driven_share": _safe_share(self.browsing_driven_count, selected_count),
            "rows": [row.to_dict() for row in self.rows],
        }


def browsing_strength_presets() -> dict[str, BrowsingAdmissionStrength]:
    return {
        BROWSING_STRENGTH_OFF: BrowsingAdmissionStrength(
            name=BROWSING_STRENGTH_OFF,
            browsing_alpha=0.0,
            max_browsing_boost=1.0,
            browsing_budget_share=0.0,
        ),
        BROWSING_STRENGTH_BALANCED: BrowsingAdmissionStrength(
            name=BROWSING_STRENGTH_BALANCED,
            browsing_alpha=0.22,
            max_browsing_boost=1.35,
            browsing_budget_share=0.30,
        ),
        BROWSING_STRENGTH_STRONG: BrowsingAdmissionStrength(
            name=BROWSING_STRENGTH_STRONG,
            browsing_alpha=0.45,
            max_browsing_boost=1.65,
            browsing_budget_share=0.55,
        ),
    }


def browsing_signal_store_from_dict(data: Mapping[str, object]) -> BrowsingSignalStore:
    raw_items = data.get("items")
    items: dict[str, BrowsingSignalAggregate] = {}
    if isinstance(raw_items, Mapping):
        for key, value in raw_items.items():
            if not isinstance(value, Mapping):
                continue
            aggregate = browsing_signal_aggregate_from_dict(value, fallback_lemma=str(key))
            if aggregate.target_lemma:
                items[aggregate.target_lemma] = aggregate
    return BrowsingSignalStore(
        pair=str(data.get("pair", "") or ""),
        profile_id=str(data.get("profile_id", "") or "default"),
        items=items,
        version=max(1, int(_safe_float(data.get("version")) or 1)),
        updated_at=_optional_str(data.get("updated_at")),
        policy_version=str(data.get("policy_version", "") or "browsing_signal_aggregate_v1"),
    )


def browsing_signal_aggregate_from_dict(
    data: Mapping[str, object],
    *,
    fallback_lemma: str = "",
) -> BrowsingSignalAggregate:
    return BrowsingSignalAggregate(
        target_lemma=str(data.get("target_lemma", "") or fallback_lemma).strip(),
        source_hit_count=max(0.0, _safe_float(data.get("source_hit_count")) or 0.0),
        target_hit_count=max(0.0, _safe_float(data.get("target_hit_count")) or 0.0),
        replacement_exposure_count=max(
            0.0,
            _safe_float(data.get("replacement_exposure_count")) or 0.0,
        ),
        source_mapping_confidence=_clamp01(data.get("source_mapping_confidence")),
        last_seen_at=_optional_str(data.get("last_seen_at")),
        decayed_at=_optional_str(data.get("decayed_at")),
    )


def load_browsing_signal_store(path: Path) -> BrowsingSignalStore:
    if not path.exists():
        return BrowsingSignalStore(pair="")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return BrowsingSignalStore(pair="")
    if not isinstance(payload, Mapping):
        return BrowsingSignalStore(pair="")
    return browsing_signal_store_from_dict(payload)


def save_browsing_signal_store(store: BrowsingSignalStore, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(store.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def ingest_browsing_signal_packet(
    store: BrowsingSignalStore,
    packet: BrowsingSignalPacket,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
    now: Optional[datetime] = None,
) -> BrowsingSignalIngestResult:
    policy = policy or BrowsingSignalIngestPolicy()
    now = now or now_utc()
    now_text = format_ts(now)
    pair = str(packet.pair or store.pair or "").strip()
    profile_id = str(packet.profile_id or store.profile_id or "default").strip() or "default"
    decayed_items = {
        lemma: _decay_aggregate(item, policy=policy, now=now) for lemma, item in store.items.items()
    }

    capped_signal_count = 0
    accepted_signal_count = 0
    packet_signals = tuple(packet.signals or ())
    accepted_packet_signals = packet_signals[: max(0, int(policy.max_signals_per_packet))]
    dropped_signal_count = max(0, len(packet_signals) - len(accepted_packet_signals))

    for signal in accepted_packet_signals:
        lemma = str(signal.target_lemma or "").strip()
        side = _normalize_signal_side(signal.side)
        if not lemma or not side:
            dropped_signal_count += 1
            continue
        raw_count = max(0.0, _safe_float(signal.count) or 0.0)
        if raw_count <= 0.0:
            dropped_signal_count += 1
            continue
        capped_count = min(raw_count, max(0.0, float(policy.max_count_per_signal)))
        if capped_count < raw_count:
            capped_signal_count += 1
        current = decayed_items.get(lemma) or BrowsingSignalAggregate(target_lemma=lemma)
        source_count = current.source_hit_count
        target_count = current.target_hit_count
        replacement_count = current.replacement_exposure_count
        mapping_confidence = current.source_mapping_confidence
        if side == BROWSING_SIGNAL_SOURCE:
            confidence = _clamp01(signal.source_mapping_confidence)
            source_count += capped_count * confidence
            mapping_confidence = max(mapping_confidence, confidence)
        elif side == BROWSING_SIGNAL_TARGET:
            target_count += capped_count
        elif side == BROWSING_SIGNAL_REPLACEMENT_EXPOSURE:
            replacement_count += capped_count
        decayed_items[lemma] = BrowsingSignalAggregate(
            target_lemma=lemma,
            source_hit_count=source_count,
            target_hit_count=target_count,
            replacement_exposure_count=replacement_count,
            source_mapping_confidence=mapping_confidence,
            last_seen_at=now_text,
            decayed_at=now_text,
        )
        accepted_signal_count += 1

    retained = _prune_aggregates(decayed_items, policy=policy)
    pruned_item_count = max(0, len(decayed_items) - len(retained))
    updated_store = BrowsingSignalStore(
        pair=pair,
        profile_id=profile_id,
        items=retained,
        version=store.version,
        updated_at=now_text,
        policy_version=policy.version,
    )
    return BrowsingSignalIngestResult(
        store=updated_store,
        input_signal_count=len(packet_signals),
        accepted_signal_count=accepted_signal_count,
        dropped_signal_count=dropped_signal_count,
        capped_signal_count=capped_signal_count,
        pruned_item_count=pruned_item_count,
        retained_item_count=len(retained),
    )


def browsing_raw_value(
    aggregate: BrowsingSignalAggregate | None,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> float:
    policy = policy or BrowsingSignalIngestPolicy()
    if aggregate is None:
        return 0.0
    return (
        max(0.0, aggregate.source_hit_count)
        + max(0.0, aggregate.target_hit_count)
        + max(0.0, aggregate.replacement_exposure_count)
        * max(0.0, policy.replacement_exposure_weight)
    )


def browsing_signal_value(
    aggregate: BrowsingSignalAggregate | None,
    *,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> float:
    policy = policy or BrowsingSignalIngestPolicy()
    raw = browsing_raw_value(aggregate, policy=policy)
    if raw <= 0.0:
        return 0.0
    return _clamp01(math.log1p(raw) / math.log1p(max(0.01, policy.browsing_signal_cap)))


def browsing_boost_value(
    signal_value: float,
    *,
    candidate: Optional[BrowsingAdmissionCandidate] = None,
    strength: Optional[BrowsingAdmissionStrength] = None,
) -> float:
    strength = strength or browsing_strength_presets()[BROWSING_STRENGTH_BALANCED]
    fit = 1.0
    if candidate is not None:
        fit = (
            _clamp01(candidate.readiness_multiplier)
            * _clamp01(candidate.source_confidence)
            * (
                1.0
                + max(0.0, strength.preference_alignment_weight)
                * _clamp01(candidate.explicit_preference_fit)
            )
        )
    return 1.0 + min(
        max(0.0, strength.max_browsing_boost - 1.0),
        max(0.0, strength.browsing_alpha) * _clamp01(signal_value) * fit,
    )


def simulate_browsing_admission(
    candidates: Sequence[BrowsingAdmissionCandidate],
    *,
    store: BrowsingSignalStore,
    admission_budget: int,
    strength: BrowsingAdmissionStrength,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> BrowsingAdmissionSimulationResult:
    policy = policy or BrowsingSignalIngestPolicy()
    budget = max(0, int(admission_budget))
    neutral_ranked = sorted(
        candidates,
        key=lambda item: (-float(item.neutral_score), item.lemma),
    )
    neutral_rank_by_lemma = {
        candidate.lemma: index + 1 for index, candidate in enumerate(neutral_ranked)
    }
    neutral_selected_lemmas = tuple(candidate.lemma for candidate in neutral_ranked[:budget])
    neutral_selected = set(neutral_selected_lemmas)

    scored_rows: list[dict[str, object]] = []
    for candidate in neutral_ranked:
        aggregate = store.items.get(candidate.lemma)
        signal = browsing_signal_value(aggregate, policy=policy)
        boost = browsing_boost_value(signal, candidate=candidate, strength=strength)
        scored_rows.append(
            {
                "candidate": candidate,
                "lemma": candidate.lemma,
                "neutral_rank": neutral_rank_by_lemma[candidate.lemma],
                "neutral_score": float(candidate.neutral_score),
                "browsing_signal": signal,
                "browsing_boost": boost,
                "final_score": float(candidate.neutral_score) * boost,
            }
        )

    signal_volume = sum(float(row["browsing_signal"]) for row in scored_rows)
    volume_factor = 0.0
    if signal_volume > 0.0 and strength.volume_tau > 0.0:
        volume_factor = 1.0 - math.exp(-signal_volume / strength.volume_tau)
    browsing_budget = int(
        math.floor(budget * _clamp01(strength.browsing_budget_share) * _clamp01(volume_factor))
    )
    browsing_pool = [
        row
        for row in scored_rows
        if float(row["browsing_signal"]) >= max(0.0, strength.min_browsing_signal)
    ]
    browsing_budget = min(browsing_budget, budget, len(browsing_pool))
    selected_browsing = sorted(
        browsing_pool,
        key=lambda row: (
            -float(row["final_score"]),
            int(row["neutral_rank"]),
            str(row["lemma"]),
        ),
    )[:browsing_budget]
    selected_lemmas = {str(row["lemma"]) for row in selected_browsing}
    general_budget = max(0, budget - len(selected_browsing))
    selected_general = [
        row
        for row in sorted(
            scored_rows,
            key=lambda item: (
                -float(item["neutral_score"]),
                int(item["neutral_rank"]),
                str(item["lemma"]),
            ),
        )
        if str(row["lemma"]) not in selected_lemmas
    ][:general_budget]
    selected_lemmas.update(str(row["lemma"]) for row in selected_general)
    lane_by_lemma = {str(row["lemma"]): "browsing" for row in selected_browsing}
    lane_by_lemma.update({str(row["lemma"]): "general" for row in selected_general})

    final_ranked = sorted(
        scored_rows,
        key=lambda row: (
            -float(row["final_score"]),
            int(row["neutral_rank"]),
            str(row["lemma"]),
        ),
    )
    final_rank_by_lemma = {str(row["lemma"]): index + 1 for index, row in enumerate(final_ranked)}
    rows = [
        BrowsingAdmissionSimulationRow(
            lemma=str(row["lemma"]),
            neutral_rank=int(row["neutral_rank"]),
            final_rank=final_rank_by_lemma[str(row["lemma"])],
            neutral_score=float(row["neutral_score"]),
            final_score=float(row["final_score"]),
            browsing_signal=float(row["browsing_signal"]),
            browsing_boost=float(row["browsing_boost"]),
            selected=str(row["lemma"]) in selected_lemmas,
            selected_lane=lane_by_lemma.get(str(row["lemma"]), "not_selected"),
            neutral_selected=str(row["lemma"]) in neutral_selected,
        )
        for row in final_ranked
    ]
    selected_order = tuple(
        str(row["lemma"]) for row in list(selected_browsing) + list(selected_general)
    )
    browsing_relevant_selected_count = sum(
        1
        for row in rows
        if row.selected and row.browsing_signal >= max(0.0, strength.min_browsing_signal)
    )
    browsing_driven_count = sum(1 for row in rows if row.selected and not row.neutral_selected)
    return BrowsingAdmissionSimulationResult(
        strength=strength.name,
        admission_budget=budget,
        browsing_budget=browsing_budget,
        general_budget=general_budget,
        signal_volume=signal_volume,
        volume_factor=volume_factor,
        selected_lemmas=selected_order,
        neutral_selected_lemmas=neutral_selected_lemmas,
        browsing_lane_count=len(selected_browsing),
        browsing_relevant_selected_count=browsing_relevant_selected_count,
        browsing_driven_count=browsing_driven_count,
        rows=tuple(rows),
    )


def simulate_browsing_admission_presets(
    candidates: Sequence[BrowsingAdmissionCandidate],
    *,
    store: BrowsingSignalStore,
    admission_budget: int,
    policy: Optional[BrowsingSignalIngestPolicy] = None,
) -> dict[str, BrowsingAdmissionSimulationResult]:
    return {
        name: simulate_browsing_admission(
            candidates,
            store=store,
            admission_budget=admission_budget,
            strength=strength,
            policy=policy,
        )
        for name, strength in browsing_strength_presets().items()
    }


def _decay_aggregate(
    aggregate: BrowsingSignalAggregate,
    *,
    policy: BrowsingSignalIngestPolicy,
    now: datetime,
) -> BrowsingSignalAggregate:
    anchor = parse_ts(aggregate.decayed_at) or parse_ts(aggregate.last_seen_at)
    if anchor is None:
        return aggregate
    elapsed_seconds = max(0.0, (now - anchor).total_seconds())
    elapsed_days = elapsed_seconds / 86400.0
    half_life_days = max(0.01, float(policy.half_life_days))
    multiplier = 0.5 ** (elapsed_days / half_life_days)
    return BrowsingSignalAggregate(
        target_lemma=aggregate.target_lemma,
        source_hit_count=max(0.0, aggregate.source_hit_count) * multiplier,
        target_hit_count=max(0.0, aggregate.target_hit_count) * multiplier,
        replacement_exposure_count=max(0.0, aggregate.replacement_exposure_count) * multiplier,
        source_mapping_confidence=aggregate.source_mapping_confidence,
        last_seen_at=aggregate.last_seen_at,
        decayed_at=format_ts(now),
    )


def _prune_aggregates(
    items: Mapping[str, BrowsingSignalAggregate],
    *,
    policy: BrowsingSignalIngestPolicy,
) -> dict[str, BrowsingSignalAggregate]:
    threshold = max(0.0, float(policy.prune_signal_below))
    candidates = [
        item
        for item in items.values()
        if item.target_lemma and browsing_signal_value(item, policy=policy) >= threshold
    ]
    candidates.sort(
        key=lambda item: (
            -browsing_raw_value(item, policy=policy),
            str(item.last_seen_at or ""),
            item.target_lemma,
        )
    )
    retained = candidates[: max(0, int(policy.max_items_per_store))]
    return {
        item.target_lemma: item for item in sorted(retained, key=lambda item: item.target_lemma)
    }


def _normalize_signal_side(value: object) -> str:
    side = str(value or "").strip().lower()
    return side if side in BROWSING_SIGNAL_SIDES else ""


def _optional_str(value: object) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _safe_float(value: object) -> Optional[float]:
    try:
        if value is None:
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def _clamp01(value: object) -> float:
    parsed = _safe_float(value)
    if parsed is None:
        return 0.0
    return max(0.0, min(1.0, parsed))


def _safe_share(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total, 6)
