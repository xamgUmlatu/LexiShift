from __future__ import annotations

from dataclasses import dataclass

from i18n import t


@dataclass(frozen=True)
class PairResourceItem:
    kind: str
    pack_id: str
    label_key: str

    @property
    def label(self) -> str:
        return t(self.label_key)


@dataclass(frozen=True)
class PairResourcePlan:
    pair: str
    label_key: str
    resources: tuple[PairResourceItem, ...]

    @property
    def label(self) -> str:
        return t(self.label_key)


_PAIR_RESOURCE_PLANS: dict[str, PairResourcePlan] = {
    "en-es": PairResourcePlan(
        pair="en-es",
        label_key="language_packs.learning_pairs.pairs.en_es",
        resources=(
            PairResourceItem(
                kind="frequency",
                pack_id="freq-es-cde",
                label_key="language_packs.learning_pairs.resources.freq_es_cde",
            ),
            PairResourceItem(
                kind="language",
                pack_id="wiktionary-es-en",
                label_key="language_packs.learning_pairs.resources.wiktionary_es_en",
            ),
            PairResourceItem(
                kind="language",
                pack_id="freedict-es-en",
                label_key="language_packs.learning_pairs.resources.freedict_es_en",
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
