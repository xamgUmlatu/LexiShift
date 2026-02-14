from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class SrsPairPolicy:
    pair: str
    bootstrap_top_n_default: int = 800
    refresh_top_n_default: int = 2000
    feedback_window_size_default: int = 100
    initial_active_count_default: int = 40
    max_new_items_per_day_default: Optional[int] = None
    notes: Sequence[str] = ()


_DEFAULT_POLICY = SrsPairPolicy(pair="*")

_PAIR_POLICIES: dict[str, SrsPairPolicy] = {
    "en-ja": SrsPairPolicy(
        pair="en-ja",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
    "en-de": SrsPairPolicy(
        pair="en-de",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
    "de-en": SrsPairPolicy(
        pair="de-en",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
    "en-es": SrsPairPolicy(
        pair="en-es",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
    "es-en": SrsPairPolicy(
        pair="es-en",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
    "es-es": SrsPairPolicy(
        pair="es-es",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
    "en-en": SrsPairPolicy(
        pair="en-en",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
    "ja-ja": SrsPairPolicy(
        pair="ja-ja",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
    "de-de": SrsPairPolicy(
        pair="de-de",
        bootstrap_top_n_default=800,
        refresh_top_n_default=2000,
        feedback_window_size_default=100,
        initial_active_count_default=40,
    ),
}


def resolve_srs_pair_policy(pair: str) -> SrsPairPolicy:
    normalized = str(pair or "").strip().lower()
    if not normalized:
        return _DEFAULT_POLICY
    return _PAIR_POLICIES.get(normalized, SrsPairPolicy(pair=normalized))


def pair_policy_to_dict(policy: SrsPairPolicy) -> dict[str, object]:
    return {
        "pair": policy.pair,
        "bootstrap_top_n_default": int(policy.bootstrap_top_n_default),
        "refresh_top_n_default": int(policy.refresh_top_n_default),
        "feedback_window_size_default": int(policy.feedback_window_size_default),
        "initial_active_count_default": int(policy.initial_active_count_default),
        "max_new_items_per_day_default": policy.max_new_items_per_day_default,
        "notes": list(policy.notes),
    }
