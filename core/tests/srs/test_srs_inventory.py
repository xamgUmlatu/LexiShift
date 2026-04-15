from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.srs import (  # noqa: E402
    SrsInventory,
    SrsItem,
    SrsPairInventory,
    SrsStore,
    load_srs_inventory,
    merge_active_item_ids,
    remove_pair_inventory,
    resolve_active_item_ids,
    save_srs_inventory,
    set_active_item_ids,
)


class TestSrsInventory(unittest.TestCase):
    def test_inventory_roundtrip_and_pair_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "srs_inventory.json"
            inventory = SrsInventory(
                pairs={
                    "en-ja": SrsPairInventory(
                        active_item_ids=("en-ja:alpha", "en-ja:beta"),
                        last_initialized_at="2026-04-12T00:00:00Z",
                    ),
                }
            )

            save_srs_inventory(inventory, path)
            loaded = load_srs_inventory(path)
            self.assertEqual(
                tuple(loaded.pairs["en-ja"].active_item_ids),
                ("en-ja:alpha", "en-ja:beta"),
            )
            self.assertEqual(
                loaded.pairs["en-ja"].last_initialized_at,
                "2026-04-12T00:00:00Z",
            )

            updated = set_active_item_ids(
                loaded,
                pair="en-ja",
                active_item_ids=("en-ja:beta", "en-ja:gamma"),
                last_refreshed_at="2026-04-12T12:00:00Z",
            )
            self.assertEqual(
                tuple(updated.pairs["en-ja"].active_item_ids),
                ("en-ja:beta", "en-ja:gamma"),
            )
            self.assertEqual(
                updated.pairs["en-ja"].last_refreshed_at,
                "2026-04-12T12:00:00Z",
            )

            removed = remove_pair_inventory(updated, "en-ja")
            self.assertNotIn("en-ja", dict(removed.pairs))

    def test_resolve_active_item_ids_uses_inventory_when_present(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
                SrsItem(
                    item_id="en-en:other",
                    lemma="other",
                    language_pair="en-en",
                    source_type="initial_set",
                ),
            ),
            version=1,
        )
        inventory = SrsInventory(
            pairs={
                "en-ja": SrsPairInventory(
                    active_item_ids=("en-ja:beta", "en-ja:missing", "en-ja:beta")
                ),
            }
        )

        active_item_ids, source = resolve_active_item_ids(
            store=store,
            pair="en-ja",
            inventory=inventory,
        )

        self.assertEqual(active_item_ids, ("en-ja:beta",))
        self.assertEqual(source, "inventory")

    def test_resolve_active_item_ids_falls_back_to_store(self) -> None:
        store = SrsStore(
            items=(
                SrsItem(
                    item_id="en-ja:alpha",
                    lemma="alpha",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
                SrsItem(
                    item_id="en-ja:beta",
                    lemma="beta",
                    language_pair="en-ja",
                    source_type="initial_set",
                ),
            ),
            version=1,
        )

        active_item_ids, source = resolve_active_item_ids(
            store=store,
            pair="en-ja",
            inventory=None,
        )

        self.assertEqual(active_item_ids, ("en-ja:alpha", "en-ja:beta"))
        self.assertEqual(source, "store_fallback")

    def test_merge_active_item_ids_preserves_order_and_deduplicates(self) -> None:
        merged = merge_active_item_ids(
            ("en-ja:alpha", "en-ja:beta"),
            ("en-ja:beta", "en-ja:gamma", ""),
        )
        self.assertEqual(merged, ("en-ja:alpha", "en-ja:beta", "en-ja:gamma"))
