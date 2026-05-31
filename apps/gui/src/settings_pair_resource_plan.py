from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PairResourceItem:
    kind: str
    pack_id: str
    label: str


@dataclass(frozen=True)
class PairResourcePlan:
    pair: str
    label: str
    resources: tuple[PairResourceItem, ...]


_PAIR_RESOURCE_PLANS: dict[str, PairResourcePlan] = {
    "en-es": PairResourcePlan(
        pair="en-es",
        label="English to Spanish",
        resources=(
            PairResourceItem(
                kind="frequency",
                pack_id="freq-es-cde",
                label="Spanish word frequency data",
            ),
            PairResourceItem(
                kind="language",
                pack_id="freedict-es-en",
                label="Spanish-English dictionary",
            ),
        ),
    ),
}


def normalize_pair_key(pair: str | None) -> str:
    return str(pair or "").strip().lower()


def pair_resource_plan(pair: str | None) -> PairResourcePlan | None:
    return _PAIR_RESOURCE_PLANS.get(normalize_pair_key(pair))


def available_pair_resource_plans() -> tuple[PairResourcePlan, ...]:
    return tuple(_PAIR_RESOURCE_PLANS[pair] for pair in sorted(_PAIR_RESOURCE_PLANS))
