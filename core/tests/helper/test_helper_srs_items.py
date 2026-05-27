from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.engine import (  # noqa: E402
    SetInitializationJobConfig,
    get_srs_item_rule_details,
    initialize_srs_set,
    list_srs_items,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.persistence.storage import VocabDataset, save_vocab_dataset  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
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


def _create_profile_frequency_db(path: Path) -> Path:
    rows = (
        ("money", 1.0, 90.0, "noun", "finance"),
        ("home", 2.0, 84.0, "noun", "daily_life"),
        ("food", 3.0, 78.0, "noun", "food_cooking"),
        ("travel", 4.0, 66.0, "noun", "travel"),
        ("music", 5.0, 62.0, "noun", "music_entertainment"),
        ("dog", 6.0, 60.0, "noun", "animals,pets"),
        ("elephant", 7.0, 52.0, "noun", "animals"),
        ("falcon", 8.0, 40.0, "noun", "animals"),
        ("reptile", 9.0, 36.0, "noun", "animals"),
        ("thesis", 10.0, 38.0, "noun", "academic"),
    )
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                core_rank REAL,
                pmw REAL,
                pos TEXT,
                sense_topics TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO frequency (lemma, core_rank, pmw, pos, sense_topics)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _stub_rulegen_for_pair(*, store, pair: str, active_item_ids=None, **_kwargs):
    active_ids = {str(item_id).strip() for item_id in (active_item_ids or ())}
    lemmas = [
        item.lemma
        for item in store.items
        if item.language_pair == pair and (not active_ids or item.item_id in active_ids)
    ]
    rules = tuple(VocabRule(source_phrase=f"source_{lemma}", replacement=lemma) for lemma in lemmas)
    snapshot = {
        "version": 1,
        "pair": pair,
        "targets": [{"lemma": lemma} for lemma in lemmas],
        "stats": {
            "target_count": len(lemmas),
            "rule_count": len(rules),
            "source_count": len(rules),
        },
    }
    return store, SimpleNamespace(
        rules=rules,
        snapshot=snapshot,
        target_count=len(lemmas),
        semantic_inventory=None,
    )


class TestHelperSrsItems(unittest.TestCase):
    def test_profile_bootstrap_initialize_publishes_dashboard_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            frequency_db = _create_profile_frequency_db(Path(tmp) / "profile_freq.sqlite")

            with patch(
                "lexishift_core.helper.engine.run_rulegen_for_pair",
                side_effect=_stub_rulegen_for_pair,
            ):
                init_payload = initialize_srs_set(
                    paths,
                    config=SetInitializationJobConfig(
                        pair="en-en",
                        set_source_db=frequency_db,
                        set_top_n=10,
                        initial_active_count=3,
                        replace_pair=True,
                        strategy="profile_bootstrap",
                        profile_context={
                            "topic_weights": {"animals": 1.0},
                            "proficiency": {"estimated_value": 0.45},
                        },
                    ),
                )

            self.assertTrue(init_payload["applied"])
            self.assertEqual(init_payload["plan"]["strategy_effective"], "profile_bootstrap")
            self.assertEqual(init_payload["plan"]["execution_mode"], "profile_bootstrap")
            self.assertEqual(
                init_payload["bootstrap_diagnostics"]["selection_strategy"],
                "profile_bootstrap",
            )
            self.assertEqual(
                init_payload["bootstrap_diagnostics"]["initial_active_preview"],
                ["falcon", "reptile", "thesis"],
            )

            dashboard = list_srs_items(paths, pair="en-en", profile_id="default", now=NOW)

            self.assertEqual(dashboard["status"], "ok")
            self.assertTrue(dashboard["store_exists"])
            self.assertTrue(dashboard["inventory_exists"])
            self.assertTrue(dashboard["ruleset_exists"])
            self.assertEqual(dashboard["inventory_source"], "inventory")
            self.assertEqual(
                dashboard["summary"],
                {
                    "total": 3,
                    "active": 3,
                    "queued": 0,
                    "due_now": 0,
                    "due_soon": 0,
                    "learning": 3,
                    "reviewing": 0,
                    "discarded": 0,
                    "cleared": 0,
                    "removed": 0,
                    "with_word_package": 3,
                    "inventory_active_count": 3,
                    "serving_now": 3,
                    "serving_not_due": 0,
                    "serving_without_enabled_rules": 0,
                    "active_zero_exposure": 3,
                    "active_zero_feedback": 3,
                    "active_zero_exposure_zero_feedback": 3,
                    "active_zero_exposure_zero_feedback_age_unknown": 0,
                    "active_stale_zero_exposure_zero_feedback": 0,
                    "active_without_enabled_rules": 0,
                    "encounter_watch": 3,
                    "encounter_stale_age_days": 7,
                },
            )
            self.assertEqual(dashboard["rule_summary"]["lemmas_with_rules"], 3)
            by_lemma = {item["lemma"]: item for item in dashboard["items"]}
            self.assertEqual(set(by_lemma), {"falcon", "reptile", "thesis"})
            self.assertEqual(by_lemma["falcon"]["status"], "learning")
            self.assertEqual(
                by_lemma["falcon"]["rule_summary"],
                {
                    "rule_count": 1,
                    "enabled_rule_count": 1,
                    "source_phrases": ["source_falcon"],
                    "source_phrase_count": 1,
                    "source_preview_truncated": False,
                },
            )

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
                            admitted_at=format_ts(NOW - timedelta(days=10)),
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
                            admitted_at=format_ts(NOW - timedelta(days=8)),
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
                    "serving_now": 1,
                    "serving_not_due": 1,
                    "serving_without_enabled_rules": 0,
                    "active_zero_exposure": 1,
                    "active_zero_feedback": 2,
                    "active_zero_exposure_zero_feedback": 1,
                    "active_zero_exposure_zero_feedback_age_unknown": 0,
                    "active_stale_zero_exposure_zero_feedback": 1,
                    "active_without_enabled_rules": 0,
                    "encounter_watch": 1,
                    "encounter_stale_age_days": 7,
                },
            )
            by_lemma = {item["lemma"]: item for item in result["items"]}
            self.assertEqual(by_lemma["perro"]["status"], "due_now")
            self.assertEqual(by_lemma["gato"]["status"], "due_soon")
            self.assertEqual(by_lemma["mesa"]["status"], "queued")
            self.assertEqual(by_lemma["planta"]["status"], "discarded")
            self.assertTrue(by_lemma["perro"]["serving"])
            self.assertEqual(by_lemma["perro"]["serving_state"], "replacing_now")
            self.assertEqual(by_lemma["perro"]["serving_label"], "Now")
            self.assertFalse(by_lemma["gato"]["serving"])
            self.assertEqual(by_lemma["gato"]["serving_state"], "not_due")
            self.assertEqual(by_lemma["mesa"]["serving_state"], "queued")
            self.assertEqual(by_lemma["planta"]["serving_state"], "removed")
            self.assertEqual(by_lemma["perro"]["source_label"], "freq-es-cde")
            self.assertEqual(by_lemma["perro"]["pos"], "noun")
            self.assertEqual(by_lemma["perro"]["rule_summary"]["enabled_rule_count"], 2)
            self.assertEqual(by_lemma["perro"]["rule_summary"]["source_phrases"], ["dog", "hound"])
            self.assertFalse(by_lemma["perro"]["encounter_state"]["zero_exposure"])
            self.assertTrue(by_lemma["perro"]["encounter_state"]["zero_feedback"])
            self.assertTrue(by_lemma["gato"]["encounter_state"]["zero_exposure_zero_feedback"])
            self.assertTrue(
                by_lemma["gato"]["encounter_state"]["stale_zero_exposure_zero_feedback"]
            )
            self.assertEqual(by_lemma["gato"]["admitted_age_days"], 8)
            self.assertTrue(by_lemma["gato"]["encounter_state"]["needs_attention"])
            self.assertEqual(by_lemma["mesa"]["rule_summary"]["enabled_rule_count"], 0)
            self.assertEqual(by_lemma["mesa"]["rule_summary"]["rule_count"], 1)
            self.assertFalse(by_lemma["mesa"]["encounter_state"]["without_enabled_rules"])
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
            self.assertEqual(result["summary"]["encounter_watch"], 0)
            self.assertEqual(result["inventory_source"], "missing_store")
            self.assertFalse(result["ruleset_exists"])
            self.assertEqual(result["rule_summary"]["rule_count"], 0)

    def test_rule_details_are_capped_and_include_compact_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            save_vocab_dataset(
                VocabDataset(
                    rules=(
                        VocabRule(
                            source_phrase="dog",
                            replacement="perro",
                            metadata=RuleMetadata(
                                confidence=0.91,
                                source_type="rulegen",
                                language_pair="en-es",
                                word_package={
                                    "version": 1,
                                    "language_tag": "es",
                                    "surface": "perro",
                                    "reading": "perro",
                                    "script_forms": {"latin": "perro"},
                                    "source": {"provider": "freq-es-cde"},
                                    "pos_canonical": "noun",
                                },
                            ),
                        ),
                        VocabRule(
                            source_phrase="hound",
                            replacement="perro",
                            priority=5,
                            tags=("animal",),
                        ),
                        VocabRule(
                            source_phrase="cur",
                            replacement="perro",
                            enabled=False,
                        ),
                        VocabRule(source_phrase="cat", replacement="gato"),
                    ),
                ),
                paths.ruleset_path("en-es", profile_id="study profile"),
            )

            result = get_srs_item_rule_details(
                paths,
                pair="en-es",
                profile_id="study profile",
                lemma="perro",
                limit=2,
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["profile_id"], "study_profile")
            self.assertEqual(result["lemma"], "perro")
            self.assertTrue(result["ruleset_exists"])
            self.assertEqual(result["rule_count"], 3)
            self.assertEqual(result["enabled_rule_count"], 2)
            self.assertEqual(result["returned_rule_count"], 2)
            self.assertTrue(result["truncated"])
            self.assertEqual(result["rules"][0]["source_phrase"], "hound")
            self.assertEqual(result["rules"][0]["tags"], ["animal"])
            self.assertEqual(result["rules"][1]["source_phrase"], "dog")
            self.assertEqual(result["rules"][1]["metadata"]["confidence"], 0.91)
            self.assertEqual(
                result["rules"][1]["metadata"]["word_package"]["source_provider"],
                "freq-es-cde",
            )

    def test_missing_ruleset_returns_empty_rule_details_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            result = get_srs_item_rule_details(
                paths,
                pair="en-es",
                profile_id="study profile",
                lemma="perro",
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["profile_id"], "study_profile")
            self.assertFalse(result["ruleset_exists"])
            self.assertEqual(result["rules"], [])
            self.assertEqual(result["rule_count"], 0)


if __name__ == "__main__":
    unittest.main()
