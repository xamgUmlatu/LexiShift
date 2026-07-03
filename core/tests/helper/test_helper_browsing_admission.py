from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.engine import ingest_browsing_admission_signals  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BrowsingSignalAggregate,
    BrowsingSignalIngestPolicy,
    BrowsingSignalStore,
    load_browsing_signal_store,
    save_browsing_signal_store,
)


NOW = datetime(2026, 5, 23, tzinfo=timezone.utc)


class TestHelperBrowsingAdmissionIngest(unittest.TestCase):
    def test_opt_in_ingest_persists_only_bounded_aggregate_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            policy = BrowsingSignalIngestPolicy(
                max_signals_per_packet=3,
                max_count_per_signal=3.0,
                max_items_per_store=10,
            )

            result = ingest_browsing_admission_signals(
                paths,
                pair="en-es",
                profile_id="alpha profile",
                captured_at="2026-05-23T00:00:00Z",
                opt_in=True,
                signals=[
                    {
                        "target_key": "hipoteca",
                        "target_lemma": "hipoteca",
                        "side": "source",
                        "count": 10,
                        "source_mapping_confidence": 0.5,
                        "url": "https://example.invalid/private",
                        "raw_text": "raw page text should never be stored",
                    },
                    {
                        "target_key": "salud",
                        "target_lemma": "salud",
                        "side": "target",
                        "count": 2,
                    },
                    "invalid-signal",
                ],
                policy=policy,
                now=NOW,
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["profile_id"], "alpha_profile")
            self.assertFalse(result["runtime_srs_mutation"])
            self.assertEqual(result["privacy"]["private_payload_fields_ignored"], 2)
            self.assertEqual(result["ingest_result"]["input_signal_count"], 3)
            self.assertEqual(result["ingest_result"]["accepted_signal_count"], 2)
            self.assertEqual(result["ingest_result"]["dropped_signal_count"], 1)
            self.assertEqual(result["ingest_result"]["capped_signal_count"], 1)

            store_path = paths.srs_browsing_signal_store_path_for("alpha_profile", "en-es")
            self.assertTrue(store_path.exists())
            store = load_browsing_signal_store(store_path)
            self.assertAlmostEqual(store.items["hipoteca"].source_hit_count, 1.5)
            self.assertEqual(store.items["salud"].target_hit_count, 2.0)
            self.assertEqual(store.items["hipoteca"].target_key, "hipoteca")
            self.assertEqual(result["aggregate_store"]["top_items"][0]["target_key"], "salud")
            self.assertFalse(paths.srs_store_path_for("alpha_profile").exists())
            serialized = json.dumps(store.to_dict(), ensure_ascii=False)
            self.assertNotIn("raw page text", serialized)
            self.assertNotIn("example.invalid", serialized)

    def test_missing_opt_in_skips_without_writing_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            result = ingest_browsing_admission_signals(
                paths,
                pair="en-es",
                profile_id="default",
                opt_in=False,
                signals=[{"target_lemma": "viaje", "side": "target", "count": 3}],
            )

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "browsing_admission_not_opted_in")
            self.assertFalse(paths.srs_browsing_signal_store_path_for("default", "en-es").exists())
            self.assertFalse(paths.srs_store_path_for("default").exists())

    def test_missing_opt_in_maintains_existing_store_without_srs_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            store_path = paths.srs_browsing_signal_store_path_for("default", "en-es")
            save_browsing_signal_store(
                BrowsingSignalStore(
                    pair="en-es",
                    profile_id="default",
                    items={
                        "hipoteca": BrowsingSignalAggregate(
                            target_lemma="hipoteca",
                            target_hit_count=6.0,
                            last_seen_at="2026-05-09T00:00:00Z",
                            decayed_at="2026-05-09T00:00:00Z",
                        )
                    },
                    updated_at="2026-05-09T00:00:00Z",
                ),
                store_path,
            )

            result = ingest_browsing_admission_signals(
                paths,
                pair="en-es",
                profile_id="default",
                captured_at="2026-05-23T00:00:00Z",
                opt_in=False,
                signals=[{"target_lemma": "viaje", "side": "target", "count": 3}],
            )

            self.assertEqual(result["status"], "skipped")
            self.assertFalse(result["runtime_srs_mutation"])
            self.assertFalse(paths.srs_store_path_for("default").exists())
            maintained = load_browsing_signal_store(store_path)
            self.assertAlmostEqual(maintained.items["hipoteca"].target_hit_count, 3.0)
            self.assertEqual(maintained.items["hipoteca"].decayed_at, "2026-05-23T00:00:00Z")

    def test_en_ja_ingest_preserves_target_key_reading_and_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))

            result = ingest_browsing_admission_signals(
                paths,
                pair="en-ja",
                profile_id="default",
                captured_at="2026-05-23T00:00:00Z",
                opt_in=True,
                signals=[
                    {
                        "target_lemma": "辛い",
                        "target_reading": "つらい",
                        "side": "target",
                        "count": 4,
                        "reading_confidence": 0.6,
                        "observation_source": "target_surface",
                    }
                ],
                now=NOW,
            )

            self.assertEqual(result["status"], "ok")
            store = load_browsing_signal_store(
                paths.srs_browsing_signal_store_path_for("default", "en-ja")
            )
            aggregate = store.items["辛い|つらい"]
            self.assertEqual(aggregate.target_lemma, "辛い")
            self.assertEqual(aggregate.target_reading, "つらい")
            self.assertAlmostEqual(aggregate.reading_confidence, 0.6)
            self.assertEqual(aggregate.observation_sources, ("target_surface",))


if __name__ == "__main__":
    unittest.main()
