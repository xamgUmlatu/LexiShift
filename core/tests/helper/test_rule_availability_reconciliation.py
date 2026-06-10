from __future__ import annotations

from datetime import datetime, timezone
import sys
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.use_cases.rule_availability import (  # noqa: E402
    NO_ENABLED_RULES_LIFECYCLE_REASON,
    reconcile_active_items_without_enabled_rules,
)
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.srs import (  # noqa: E402
    SRS_LIFECYCLE_ACTIVE,
    SRS_LIFECYCLE_DISCARDED,
    SrsInventory,
    SrsItem,
    SrsPairInventory,
    SrsStore,
)


NOW = datetime(2026, 6, 6, tzinfo=timezone.utc)


class TestRuleAvailabilityReconciliation(unittest.TestCase):
    def test_discards_active_items_without_enabled_rules(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-es:autor",
                    lemma="autor",
                    language_pair="en-es",
                    source_type="initial_set",
                ),
                SrsItem(
                    item_id="en-es:ii",
                    lemma="ii",
                    language_pair="en-es",
                    source_type="initial_set",
                ),
            )
        )
        inventory = SrsInventory(
            pairs={
                "en-es": SrsPairInventory(
                    active_item_ids=("en-es:autor", "en-es:ii"),
                    last_initialized_at="2026-06-05T21:00:14Z",
                )
            }
        )

        updated_store, updated_inventory, report = reconcile_active_items_without_enabled_rules(
            store=store,
            inventory=inventory,
            pair="en-es",
            active_item_ids=("en-es:autor", "en-es:ii"),
            rules=(VocabRule(source_phrase="author", replacement="autor"),),
            now=NOW,
            last_refreshed_at="2026-06-06T00:00:00Z",
        )

        by_lemma = {item.lemma: item for item in updated_store.items}
        self.assertEqual(by_lemma["autor"].lifecycle_state, SRS_LIFECYCLE_ACTIVE)
        self.assertEqual(by_lemma["ii"].lifecycle_state, SRS_LIFECYCLE_DISCARDED)
        self.assertEqual(by_lemma["ii"].lifecycle_reason, NO_ENABLED_RULES_LIFECYCLE_REASON)
        self.assertEqual(by_lemma["ii"].lifecycle_updated_at, "2026-06-06T00:00:00Z")
        pair_inventory = updated_inventory.pairs["en-es"]
        self.assertEqual(tuple(pair_inventory.active_item_ids), ("en-es:autor",))
        self.assertEqual(pair_inventory.last_initialized_at, "2026-06-05T21:00:14Z")
        self.assertEqual(pair_inventory.last_refreshed_at, "2026-06-06T00:00:00Z")
        self.assertTrue(report.changed)
        self.assertEqual(report.discarded_lemmas, ("ii",))
        self.assertEqual(report.active_item_ids_after, ("en-es:autor",))

    def test_disabled_rules_do_not_satisfy_active_item_availability(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-es:cuestión",
                    lemma="cuestión",
                    language_pair="en-es",
                    source_type="initial_set",
                ),
            )
        )
        inventory = SrsInventory(
            pairs={"en-es": SrsPairInventory(active_item_ids=("en-es:cuestión",))}
        )

        updated_store, updated_inventory, report = reconcile_active_items_without_enabled_rules(
            store=store,
            inventory=inventory,
            pair="en-es",
            active_item_ids=("en-es:cuestión",),
            rules=(
                VocabRule(
                    source_phrase="question",
                    replacement="cuestión",
                    enabled=False,
                ),
            ),
            now=NOW,
        )

        item = updated_store.items[0]
        self.assertEqual(item.lifecycle_state, SRS_LIFECYCLE_DISCARDED)
        self.assertEqual(item.lifecycle_reason, NO_ENABLED_RULES_LIFECYCLE_REASON)
        self.assertEqual(tuple(updated_inventory.pairs["en-es"].active_item_ids), ())
        self.assertEqual(report.discarded_lemmas, ("cuestión",))

    def test_keeps_inventory_when_all_active_items_have_enabled_rules(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-es:autor",
                    lemma="autor",
                    language_pair="en-es",
                    source_type="initial_set",
                ),
            )
        )
        inventory = SrsInventory(
            pairs={"en-es": SrsPairInventory(active_item_ids=("en-es:autor",))}
        )

        updated_store, updated_inventory, report = reconcile_active_items_without_enabled_rules(
            store=store,
            inventory=inventory,
            pair="en-es",
            active_item_ids=("en-es:autor",),
            rules=(VocabRule(source_phrase="author", replacement="autor"),),
            now=NOW,
        )

        self.assertIs(updated_store, store)
        self.assertIs(updated_inventory, inventory)
        self.assertFalse(report.changed)
        self.assertEqual(report.active_item_ids_after, ("en-es:autor",))


if __name__ == "__main__":
    unittest.main()
