from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.engine import list_srs_items  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.persistence.storage import VocabDataset, save_vocab_dataset  # noqa: E402
from lexishift_core.replacement.core import VocabRule  # noqa: E402
from lexishift_core.srs import (  # noqa: E402
    SRS_LIFECYCLE_DISCARDED,
    SrsInventory,
    SrsItem,
    SrsPairInventory,
    SrsStore,
    save_srs_inventory,
    save_srs_store,
)
from lexishift_core.srs.time import format_ts  # noqa: E402


NOW = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)


def _word_package(surface: str, *, pos: str = "noun") -> dict[str, object]:
    return {
        "version": 1,
        "language_tag": "es",
        "surface": surface,
        "reading": surface,
        "script_forms": {"latin": surface},
        "source": {"provider": "freq-es-cde"},
        "pos": pos,
        "pos_canonical": pos,
    }


class TestHelperSrsItems(unittest.TestCase):
    def test_list_srs_items_reports_dashboard_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_srs_store(
                SrsStore(
                    items=(
                        SrsItem(
                            item_id="en-es:perro",
                            lemma="perro",
                            language_pair="en-es",
                            source_type="initial_set",
                            next_due=format_ts(NOW - timedelta(hours=2)),
                            scheduler_state="review",
                            exposures=3,
                            word_package=_word_package("perro"),
                        ),
                        SrsItem(
                            item_id="en-es:gato",
                            lemma="gato",
                            language_pair="en-es",
                            source_type="initial_set",
                            next_due=format_ts(NOW + timedelta(hours=4)),
                            scheduler_state="learning",
                            word_package=_word_package("gato"),
                        ),
                        SrsItem(
                            item_id="en-es:mesa",
                            lemma="mesa",
                            language_pair="en-es",
                            source_type="initial_set",
                            next_due=format_ts(NOW + timedelta(days=4)),
                            word_package=_word_package("mesa"),
                        ),
                        SrsItem(
                            item_id="en-es:planta",
                            lemma="planta",
                            language_pair="en-es",
                            source_type="initial_set",
                            lifecycle_state=SRS_LIFECYCLE_DISCARDED,
                            lifecycle_reason="user_blocked",
                            lifecycle_updated_at=format_ts(NOW),
                            word_package=_word_package("planta"),
                        ),
                        SrsItem(
                            item_id="en-de:hallo",
                            lemma="hallo",
                            language_pair="en-de",
                            source_type="initial_set",
                        ),
                    ),
                    version=2,
                ),
                paths.srs_store_path_for("default"),
            )
            save_srs_inventory(
                SrsInventory(
                    pairs={
                        "en-es": SrsPairInventory(
                            active_item_ids=("en-es:perro", "en-es:gato"),
                        ),
                    }
                ),
                paths.srs_inventory_path_for("default"),
            )
            save_vocab_dataset(
                VocabDataset(
                    rules=(
                        VocabRule(source_phrase="dog", replacement="perro"),
                        VocabRule(source_phrase="hound", replacement="perro"),
                        VocabRule(source_phrase="cat", replacement="gato"),
                        VocabRule(source_phrase="table", replacement="mesa", enabled=False),
                    ),
                ),
                paths.ruleset_path("en-es", profile_id="default"),
            )

            result = list_srs_items(paths, pair="en-es", profile_id="default", now=NOW)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["pair"], "en-es")
            self.assertTrue(result["store_exists"])
            self.assertTrue(result["inventory_exists"])
            self.assertTrue(result["ruleset_exists"])
            self.assertEqual(result["inventory_source"], "inventory")
            self.assertEqual(
                result["rule_summary"],
                {
                    "ruleset_path": str(paths.ruleset_path("en-es", profile_id="default")),
                    "ruleset_exists": True,
                    "rule_count": 4,
                    "enabled_rule_count": 3,
                    "lemmas_with_rules": 3,
                    "load_error": None,
                },
            )
            self.assertEqual(
                result["summary"],
                {
                    "total": 4,
                    "active": 2,
                    "queued": 1,
                    "due_now": 1,
                    "due_soon": 1,
                    "learning": 0,
                    "reviewing": 0,
                    "discarded": 1,
                    "cleared": 0,
                    "removed": 1,
                    "with_word_package": 4,
                    "inventory_active_count": 2,
                },
            )
            by_lemma = {item["lemma"]: item for item in result["items"]}
            self.assertEqual(by_lemma["perro"]["status"], "due_now")
            self.assertEqual(by_lemma["gato"]["status"], "due_soon")
            self.assertEqual(by_lemma["mesa"]["status"], "queued")
            self.assertEqual(by_lemma["planta"]["status"], "discarded")
            self.assertEqual(by_lemma["perro"]["source_label"], "freq-es-cde")
            self.assertEqual(by_lemma["perro"]["pos"], "noun")
            self.assertEqual(by_lemma["perro"]["rule_summary"]["enabled_rule_count"], 2)
            self.assertEqual(by_lemma["perro"]["rule_summary"]["source_phrases"], ["dog", "hound"])
            self.assertEqual(by_lemma["mesa"]["rule_summary"]["enabled_rule_count"], 0)
            self.assertEqual(by_lemma["mesa"]["rule_summary"]["rule_count"], 1)
            self.assertEqual(by_lemma["planta"]["advanced"]["lifecycle_reason"], "user_blocked")

    def test_missing_store_returns_empty_dashboard_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            result = list_srs_items(paths, pair="en-es", profile_id="study profile", now=NOW)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["profile_id"], "study_profile")
            self.assertFalse(result["store_exists"])
            self.assertEqual(result["items"], [])
            self.assertEqual(result["summary"]["total"], 0)
            self.assertEqual(result["inventory_source"], "missing_store")
            self.assertFalse(result["ruleset_exists"])
            self.assertEqual(result["rule_summary"]["rule_count"], 0)


if __name__ == "__main__":
    unittest.main()
