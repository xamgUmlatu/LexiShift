from __future__ import annotations

import os
import sys
import unittest
from types import SimpleNamespace

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import SrsInventory, SrsItem, SrsPairInventory, SrsStore  # noqa: E402
from lexishift_core.srs.rebalance import (  # noqa: E402
    PROTECTION_RULE_HISTORY_COUNT,
    build_rebalance_plan,
    classify_rebalance_protection,
)


class TestSrsRebalance(unittest.TestCase):
    def test_classify_rebalance_protection_uses_explicit_rules(self) -> None:
        item = SrsItem(
            item_id="en-ja:alpha",
            lemma="alpha",
            language_pair="en-ja",
            source_type="initial_set",
            history=(
                {"ts": "2026-04-01T00:00:00Z", "rating": "good"},  # type: ignore[list-item]
                {"ts": "2026-04-02T00:00:00Z", "rating": "good"},  # type: ignore[list-item]
                {"ts": "2026-04-03T00:00:00Z", "rating": "good"},  # type: ignore[list-item]
                {"ts": "2026-04-04T00:00:00Z", "rating": "good"},  # type: ignore[list-item]
            ),
        )

        is_protected, rule = classify_rebalance_protection(item)

        self.assertTrue(is_protected)
        self.assertEqual(rule, PROTECTION_RULE_HISTORY_COUNT)

    def test_build_rebalance_plan_keeps_protected_and_prefers_retained_before_new(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                    history=(
                        SimpleNamespace(ts="2026-04-01T00:00:00Z", rating="good"),
                        SimpleNamespace(ts="2026-04-02T00:00:00Z", rating="good"),
                        SimpleNamespace(ts="2026-04-03T00:00:00Z", rating="good"),
                        SimpleNamespace(ts="2026-04-04T00:00:00Z", rating="good"),
                    ),
                ),
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="initial_set",
                    confidence=0.55,
                ),
                SrsItem(
                    item_id="en-ja:gamma",
                    lemma="gamma",
                    language_pair="en-ja",
                    source_type="initial_set",
                    confidence=0.52,
                ),
                SrsItem(
                    item_id="en-ja:delta",
                    lemma="delta",
                    language_pair="en-ja",
                    source_type="frequency_list",
                    confidence=0.5,
                ),
            ),
            version=1,
        )
        inventory = SrsInventory(
            pairs={
                "en-ja": SrsPairInventory(
                    active_item_ids=("en-ja:alpha", "en-ja:beta", "en-ja:gamma")
                )
            }
        )
        candidates = [
            SimpleNamespace(
                lemma="beta",
                language_pair="en-ja",
                pos_bucket="noun",
                base_weight=0.55,
                admission_weight=0.55,
                metadata={},
            ),
            SimpleNamespace(
                lemma="gamma",
                language_pair="en-ja",
                pos_bucket="noun",
                base_weight=0.52,
                admission_weight=0.52,
                metadata={},
            ),
            SimpleNamespace(
                lemma="delta",
                language_pair="en-ja",
                pos_bucket="noun",
                base_weight=0.5,
                admission_weight=0.5,
                metadata={"topics": ["animals"]},
            ),
            SimpleNamespace(
                lemma="epsilon",
                language_pair="en-ja",
                pos_bucket="noun",
                base_weight=0.49,
                admission_weight=0.49,
                metadata={"topics": ["animals"]},
            ),
        ]

        plan = build_rebalance_plan(
            store=store,
            pair="en-ja",
            inventory=inventory,
            candidates=candidates,
            profile_context={"interests": ["animals"]},
            target_active_count=10,
        )

        self.assertEqual(plan.target_active_count, 3)
        self.assertEqual([entry.lemma for entry in plan.protected_items], ["alpha"])
        self.assertEqual([entry.lemma for entry in plan.proposed_parks], ["beta", "gamma"])
        self.assertEqual([entry.lemma for entry in plan.proposed_activations], ["delta", "epsilon"])
        self.assertEqual(
            plan.proposed_active_item_ids,
            ("en-ja:alpha", "en-ja:delta", "en-ja:epsilon"),
        )


if __name__ == "__main__":
    unittest.main()
