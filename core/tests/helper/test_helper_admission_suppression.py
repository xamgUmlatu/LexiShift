from __future__ import annotations

from datetime import datetime, timezone
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.engine import suppress_srs_admission  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs import (  # noqa: E402
    SRS_LIFECYCLE_DISCARDED,
    SrsInventory,
    SrsItem,
    SrsPairInventory,
    SrsStore,
    load_srs_inventory,
    load_srs_store,
    save_srs_inventory,
    save_srs_store,
)
from lexishift_core.srs.admission_suppression import (  # noqa: E402
    active_suppressed_lemmas,
    load_admission_suppression_store,
)


NOW = datetime(2026, 5, 26, tzinfo=timezone.utc)


class TestHelperAdmissionSuppression(unittest.TestCase):
    def test_user_blocked_persists_without_mutating_srs_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            result = suppress_srs_admission(
                paths,
                pair="en-es",
                profile_id="alpha profile",
                lemma="perro",
                reason="user_blocked",
                note="discard_word",
                now=NOW,
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["profile_id"], "alpha_profile")
            self.assertEqual(result["pair"], "en-es")
            self.assertEqual(result["lemma"], "perro")
            self.assertEqual(result["reason"], "user_blocked")
            self.assertEqual(result["active_reason"], "user_blocked")
            self.assertFalse(result["runtime_srs_mutation"])
            self.assertTrue(result["suppression_store_mutation"])
            self.assertTrue(result["refresh_admission_blocked"])
            self.assertIsNone(result["suppressed_until"])

            store_path = paths.srs_admission_suppression_store_path_for("alpha_profile")
            self.assertTrue(store_path.exists())
            store = load_admission_suppression_store(store_path)
            self.assertEqual(store.profile_id, "alpha_profile")
            self.assertEqual(
                active_suppressed_lemmas(store, pair="en-es", now=NOW), {"perro": "user_blocked"}
            )
            self.assertFalse(paths.srs_store_path_for("alpha_profile").exists())

    def test_user_blocked_marks_existing_srs_item_and_removes_active_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            profile_id = "default"
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-es:perro",
                            lemma="perro",
                            language_pair="en-es",
                            source_type="initial_set",
                        ),
                        SrsItem(
                            item_id="en-es:gato",
                            lemma="gato",
                            language_pair="en-es",
                            source_type="initial_set",
                        ),
                    ),
                    version=2,
                ),
                paths.srs_store_path_for(profile_id),
            )
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-es": SrsPairInventory(
                            active_item_ids=("en-es:perro", "en-es:gato"),
                        ),
                    }
                ),
                paths.srs_inventory_path_for(profile_id),
            )

            result = suppress_srs_admission(
                paths,
                pair="en-es",
                profile_id=profile_id,
                lemma="perro",
                reason="user_blocked",
                now=NOW,
            )

            self.assertTrue(result["runtime_srs_mutation"])
            self.assertTrue(result["srs_store_lifecycle_mutation"])
            self.assertTrue(result["active_item_removed"])
            store = load_srs_store(paths.srs_store_path_for(profile_id))
            perro = next(item for item in store.items if item.lemma == "perro")
            gato = next(item for item in store.items if item.lemma == "gato")
            self.assertEqual(perro.lifecycle_state, SRS_LIFECYCLE_DISCARDED)
            self.assertEqual(perro.lifecycle_reason, "user_blocked")
            self.assertEqual(perro.lifecycle_updated_at, "2026-05-26T00:00:00Z")
            self.assertEqual(gato.lifecycle_state, "active")
            inventory = load_srs_inventory(paths.srs_inventory_path_for(profile_id))
            self.assertEqual(
                tuple(inventory.pairs["en-es"].active_item_ids),
                ("en-es:gato",),
            )

    def test_missing_pair_or_lemma_fails_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            with self.assertRaises(ValueError):
                suppress_srs_admission(paths, pair="", profile_id="default", lemma="perro")
            with self.assertRaises(ValueError):
                suppress_srs_admission(paths, pair="en-es", profile_id="default", lemma="")

            self.assertFalse(paths.srs_admission_suppression_store_path_for("default").exists())
            self.assertFalse(paths.srs_store_path_for("default").exists())


if __name__ == "__main__":
    unittest.main()
