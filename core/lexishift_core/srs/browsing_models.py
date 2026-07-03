from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

from lexishift_core.srs.browsing_identity import (
    aggregate_reading_confidence,
    aggregate_target_key,
)
from lexishift_core.srs.browsing_probability import safe_share


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
    min_fractional_browsing_budget: float = 1.0


@dataclass(frozen=True)
class BrowsingSignalAggregate:
    target_lemma: str
    target_key: str = ""
    target_reading: str = ""
    source_hit_count: float = 0.0
    target_hit_count: float = 0.0
    replacement_exposure_count: float = 0.0
    source_mapping_confidence: float = 0.0
    reading_confidence: float = 1.0
    observation_sources: Sequence[str] = field(default_factory=tuple)
    last_seen_at: Optional[str] = None
    decayed_at: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "target_key": aggregate_target_key(self),
            "target_lemma": self.target_lemma,
            "source_hit_count": round(float(self.source_hit_count), 6),
            "target_hit_count": round(float(self.target_hit_count), 6),
            "replacement_exposure_count": round(float(self.replacement_exposure_count), 6),
            "source_mapping_confidence": round(float(self.source_mapping_confidence), 6),
            "reading_confidence": round(aggregate_reading_confidence(self), 6),
        }
        if self.target_reading:
            payload["target_reading"] = self.target_reading
        if self.observation_sources:
            payload["observation_sources"] = list(self.observation_sources)
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
                key: self.items[key].to_dict()
                for key in sorted(self.items)
                if self.items[key].target_lemma
            },
        }


@dataclass(frozen=True)
class BrowsingSignalPacketEntry:
    target_lemma: str
    side: str
    count: float = 1.0
    source_mapping_confidence: float = 1.0
    target_key: str = ""
    target_reading: str = ""
    reading_confidence: float = 1.0
    observation_source: str = ""


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
    target_key: str = ""
    target_reading: str = ""
    readiness_multiplier: float = 1.0
    explicit_preference_fit: float = 0.0
    source_confidence: float = 1.0


@dataclass(frozen=True)
class BrowsingAdmissionSimulationRow:
    lemma: str
    target_key: str
    target_reading: str
    neutral_rank: int
    final_rank: int
    neutral_score: float
    final_score: float
    browsing_signal: float
    browsing_boost: float
    selected: bool
    selected_lane: str = "not_selected"
    neutral_selected: bool = False
    suppressed_reason: Optional[str] = None
    deterministic_selection_probability: float = 0.0
    browsing_lane_probability: float = 0.0
    general_lane_probability: float = 0.0
    approximate_selection_probability: float = 0.0

    def to_dict(self) -> dict[str, object]:
        payload = {
            "lemma": self.lemma,
            "target_key": self.target_key,
            "neutral_rank": self.neutral_rank,
            "final_rank": self.final_rank,
            "neutral_score": round(self.neutral_score, 6),
            "final_score": round(self.final_score, 6),
            "browsing_signal": round(self.browsing_signal, 6),
            "browsing_boost": round(self.browsing_boost, 6),
            "selected": self.selected,
            "selected_lane": self.selected_lane,
            "neutral_selected": self.neutral_selected,
            "deterministic_selection_probability": round(
                self.deterministic_selection_probability,
                6,
            ),
            "browsing_lane_probability": round(self.browsing_lane_probability, 6),
            "general_lane_probability": round(self.general_lane_probability, 6),
            "approximate_selection_probability": round(self.approximate_selection_probability, 6),
        }
        if self.target_reading:
            payload["target_reading"] = self.target_reading
        if self.suppressed_reason:
            payload["suppressed_reason"] = self.suppressed_reason
        return payload


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
    suppressed_count: int
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
            "suppressed_count": self.suppressed_count,
            "browsing_lane_share": safe_share(self.browsing_lane_count, selected_count),
            "browsing_relevant_share": safe_share(
                self.browsing_relevant_selected_count,
                selected_count,
            ),
            "browsing_driven_share": safe_share(self.browsing_driven_count, selected_count),
            "probability_semantics": {
                "deterministic_selection_probability": (
                    "Exact for the current deterministic two-lane simulation."
                ),
                "browsing_lane_probability": (
                    "Approximate inclusion probability if the browsing lane "
                    "uses weighted sampling without replacement."
                ),
                "general_lane_probability": (
                    "Approximate inclusion probability if the general lane "
                    "uses weighted sampling without replacement."
                ),
                "approximate_selection_probability": (
                    "Approximate combined inclusion probability under the "
                    "planned smoother weighted selection model."
                ),
            },
            "rows": [row.to_dict() for row in self.rows],
        }
