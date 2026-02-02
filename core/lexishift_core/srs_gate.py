from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from lexishift_core.core import VocabRule
from lexishift_core.srs import SrsItem


@dataclass(frozen=True)
class PracticeGate:
    active_items: Sequence[SrsItem]
    include_unpaired_rules: bool = False
    include_all_if_empty: bool = False

    def filter_rules(self, rules: Iterable[VocabRule]) -> list[VocabRule]:
        return select_rules_for_practice(
            rules,
            self.active_items,
            include_unpaired_rules=self.include_unpaired_rules,
            include_all_if_empty=self.include_all_if_empty,
        )


def select_rules_for_practice(
    rules: Iterable[VocabRule],
    active_items: Sequence[SrsItem],
    *,
    include_unpaired_rules: bool = False,
    include_all_if_empty: bool = False,
) -> list[VocabRule]:
    if not active_items:
        return list(rules) if include_all_if_empty else []

    active_map = {(item.language_pair, item.lemma) for item in active_items}
    active_lemmas = {item.lemma for item in active_items}
    result: list[VocabRule] = []
    for rule in rules:
        pair = rule.metadata.language_pair if rule.metadata else None
        if pair is None:
            if include_unpaired_rules and rule.replacement in active_lemmas:
                result.append(rule)
            continue
        if (pair, rule.replacement) in active_map:
            result.append(rule)
    return result
