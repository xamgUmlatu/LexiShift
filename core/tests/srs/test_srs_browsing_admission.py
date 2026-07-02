from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BROWSING_SIGNAL_SOURCE,
    BROWSING_SIGNAL_TARGET,
    BROWSING_STRENGTH_BALANCED,
    BROWSING_STRENGTH_OFF,
    BROWSING_STRENGTH_STRONG,
    BrowsingAdmissionCandidate,
    BrowsingSignalAggregate,
    BrowsingSignalIngestPolicy,
    BrowsingSignalPacket,
    BrowsingSignalPacketEntry,
    BrowsingSignalStore,
    browsing_signal_value,
    browsing_strength_presets,
    ingest_browsing_signal_packet,
    simulate_browsing_admission_presets,
)
from lexishift_core.srs.admission_suppression import (  # noqa: E402
    SUPPRESSION_REASON_DISCARDED,
    SUPPRESSION_REASON_SUSPENDED,
    SUPPRESSION_REASON_USER_BLOCKED,
    SrsAdmissionSuppressionPolicy,
    SrsAdmissionSuppressionStore,
    active_suppressed_lemmas,
    create_admission_suppression,
    prune_expired_suppression_entries,
    upsert_admission_suppression,
)


NOW = datetime(2026, 5, 23, tzinfo=timezone.utc)


class TestSrsBrowsingAdmission(unittest.TestCase):
    def test_ingest_caps_packet_and_count_without_private_payload_fields(self) -> None:
        policy = BrowsingSignalIngestPolicy(
            max_signals_per_packet=2,
            max_count_per_signal=3.0,
            max_items_per_store=10,
            prune_signal_below=0.0,
        )
        store = BrowsingSignalStore(pair="en-es", profile_id="default")
        packet = BrowsingSignalPacket(
            pair="en-es",
            profile_id="default",
            signals=(
                BrowsingSignalPacketEntry(
                    target_lemma="hipoteca",
                    side=BROWSING_SIGNAL_SOURCE,
                    count=10,
                    source_mapping_confidence=0.5,
                ),
                BrowsingSignalPacketEntry(
                    target_lemma="salud",
                    side=BROWSING_SIGNAL_TARGET,
                    count=2,
                ),
                BrowsingSignalPacketEntry(
                    target_lemma="descartado",
                    side=BROWSING_SIGNAL_TARGET,
                    count=1,
                ),
            ),
        )

        result = ingest_browsing_signal_packet(store, packet, policy=policy, now=NOW)

        self.assertEqual(result.input_signal_count, 3)
        self.assertEqual(result.accepted_signal_count, 2)
        self.assertEqual(result.dropped_signal_count, 1)
        self.assertEqual(result.capped_signal_count, 1)
        self.assertAlmostEqual(result.store.items["hipoteca"].source_hit_count, 1.5)
        self.assertEqual(result.store.items["salud"].target_hit_count, 2.0)
        serialized = json.dumps(result.store.to_dict())
        self.assertNotIn("raw_text", serialized)
        self.assertNotIn("url", serialized)

    def test_ingest_decays_prunes_and_bounds_store_size(self) -> None:
        policy = BrowsingSignalIngestPolicy(
            max_signals_per_packet=10,
            max_count_per_signal=5.0,
            max_items_per_store=2,
            prune_signal_below=0.02,
            half_life_days=1.0,
        )
        store = BrowsingSignalStore(
            pair="en-es",
            profile_id="default",
            items={
                "arcaico": BrowsingSignalAggregate(
                    target_lemma="arcaico",
                    source_hit_count=0.20,
                    last_seen_at="2026-01-01T00:00:00Z",
                    decayed_at="2026-01-01T00:00:00Z",
                )
            },
        )
        packet = BrowsingSignalPacket(
            pair="en-es",
            profile_id="default",
            signals=(
                BrowsingSignalPacketEntry(
                    target_lemma="hipoteca",
                    side=BROWSING_SIGNAL_TARGET,
                    count=5,
                ),
                BrowsingSignalPacketEntry(
                    target_lemma="salud",
                    side=BROWSING_SIGNAL_TARGET,
                    count=4,
                ),
                BrowsingSignalPacketEntry(
                    target_lemma="viaje",
                    side=BROWSING_SIGNAL_TARGET,
                    count=3,
                ),
            ),
        )

        result = ingest_browsing_signal_packet(store, packet, policy=policy, now=NOW)

        self.assertEqual(result.retained_item_count, 2)
        self.assertGreaterEqual(result.pruned_item_count, 2)
        self.assertEqual(set(result.store.items), {"hipoteca", "salud"})
        self.assertNotIn("arcaico", result.store.items)

    def test_strength_presets_increase_browsing_lane_without_mutating_store(self) -> None:
        policy = BrowsingSignalIngestPolicy()
        store = BrowsingSignalStore(
            pair="en-es",
            profile_id="default",
            items={
                "hipoteca": BrowsingSignalAggregate(
                    target_lemma="hipoteca",
                    source_hit_count=5.0,
                    source_mapping_confidence=0.9,
                    last_seen_at="2026-05-23T00:00:00Z",
                    decayed_at="2026-05-23T00:00:00Z",
                ),
                "préstamo": BrowsingSignalAggregate(
                    target_lemma="préstamo",
                    source_hit_count=4.0,
                    source_mapping_confidence=0.8,
                    last_seen_at="2026-05-23T00:00:00Z",
                    decayed_at="2026-05-23T00:00:00Z",
                ),
                "salud": BrowsingSignalAggregate(
                    target_lemma="salud",
                    target_hit_count=4.0,
                    last_seen_at="2026-05-23T00:00:00Z",
                    decayed_at="2026-05-23T00:00:00Z",
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="casa", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="ser", neutral_score=0.96),
            BrowsingAdmissionCandidate(lemma="banco", neutral_score=0.90),
            BrowsingAdmissionCandidate(lemma="perro", neutral_score=0.84),
            BrowsingAdmissionCandidate(lemma="gato", neutral_score=0.82),
            BrowsingAdmissionCandidate(lemma="comida", neutral_score=0.80),
            BrowsingAdmissionCandidate(
                lemma="hipoteca",
                neutral_score=0.64,
                readiness_multiplier=0.92,
                explicit_preference_fit=0.65,
                source_confidence=0.90,
            ),
            BrowsingAdmissionCandidate(
                lemma="préstamo",
                neutral_score=0.62,
                readiness_multiplier=0.88,
                explicit_preference_fit=0.60,
                source_confidence=0.85,
            ),
            BrowsingAdmissionCandidate(
                lemma="salud",
                neutral_score=0.60,
                readiness_multiplier=0.86,
                explicit_preference_fit=0.55,
                source_confidence=0.90,
            ),
        )

        before = store.to_dict()
        results = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=6,
            policy=policy,
        )

        off = results[BROWSING_STRENGTH_OFF].to_dict()
        balanced = results[BROWSING_STRENGTH_BALANCED].to_dict()
        strong = results[BROWSING_STRENGTH_STRONG].to_dict()

        self.assertEqual(
            off["selected_lemmas"],
            ["casa", "ser", "banco", "perro", "gato", "comida"],
        )
        self.assertEqual(off["browsing_lane_count"], 0)
        self.assertGreaterEqual(
            balanced["browsing_lane_count"],
            off["browsing_lane_count"],
        )
        self.assertGreaterEqual(
            strong["browsing_lane_count"],
            balanced["browsing_lane_count"],
        )
        self.assertGreater(strong["browsing_lane_count"], 0)
        self.assertEqual(store.to_dict(), before)

    def test_unicode_en_ja_lemmas_ingest_and_simulate_without_pair_assumptions(self) -> None:
        policy = BrowsingSignalIngestPolicy(
            max_signals_per_packet=4,
            max_count_per_signal=5.0,
            max_items_per_store=10,
            prune_signal_below=0.0,
        )
        store = BrowsingSignalStore(pair="en-ja", profile_id="default")
        packet = BrowsingSignalPacket(
            pair="en-ja",
            profile_id="default",
            signals=(
                BrowsingSignalPacketEntry(
                    target_lemma="料理",
                    side=BROWSING_SIGNAL_SOURCE,
                    count=8,
                    source_mapping_confidence=0.75,
                ),
                BrowsingSignalPacketEntry(
                    target_lemma="病院",
                    side=BROWSING_SIGNAL_TARGET,
                    count=4,
                ),
            ),
        )

        ingest = ingest_browsing_signal_packet(store, packet, policy=policy, now=NOW)
        candidates = (
            BrowsingAdmissionCandidate(lemma="する", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="いる", neutral_score=0.96),
            BrowsingAdmissionCandidate(
                lemma="料理",
                neutral_score=0.62,
                readiness_multiplier=0.90,
                explicit_preference_fit=0.60,
                source_confidence=0.90,
            ),
            BrowsingAdmissionCandidate(
                lemma="病院",
                neutral_score=0.58,
                readiness_multiplier=0.85,
                explicit_preference_fit=0.40,
                source_confidence=0.95,
            ),
        )

        results = simulate_browsing_admission_presets(
            candidates,
            store=ingest.store,
            admission_budget=3,
            policy=policy,
        )
        off = results[BROWSING_STRENGTH_OFF].to_dict()
        strong = results[BROWSING_STRENGTH_STRONG].to_dict()

        self.assertEqual(ingest.store.pair, "en-ja")
        self.assertIn("料理", ingest.store.items)
        self.assertIn("病院", ingest.store.items)
        self.assertEqual(off["selected_lemmas"], off["neutral_selected_lemmas"])
        self.assertGreater(strong["browsing_lane_count"], off["browsing_lane_count"])
        self.assertIn("料理", strong["selected_lemmas"])

    def test_probability_preview_reports_weighted_and_deterministic_shapes(self) -> None:
        policy = BrowsingSignalIngestPolicy()
        store = BrowsingSignalStore(
            pair="en-es",
            profile_id="default",
            items={
                "hipoteca": BrowsingSignalAggregate(
                    target_lemma="hipoteca",
                    source_hit_count=5.0,
                    source_mapping_confidence=0.9,
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="casa", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="ser", neutral_score=0.96),
            BrowsingAdmissionCandidate(
                lemma="hipoteca",
                neutral_score=0.64,
                readiness_multiplier=0.92,
                explicit_preference_fit=0.65,
                source_confidence=0.90,
            ),
        )

        results = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=10,
            policy=policy,
        )
        strong_rows = {
            row["lemma"]: row for row in results[BROWSING_STRENGTH_STRONG].to_dict()["rows"]
        }

        self.assertGreater(strong_rows["hipoteca"]["approximate_selection_probability"], 0.0)
        self.assertGreater(strong_rows["hipoteca"]["browsing_lane_probability"], 0.0)
        self.assertIn(
            strong_rows["hipoteca"]["deterministic_selection_probability"],
            (0.0, 1.0),
        )

    def test_balanced_realizes_one_slot_for_small_budget_with_clear_signal(self) -> None:
        store = BrowsingSignalStore(
            pair="en-es",
            profile_id="default",
            items={
                "hipoteca": BrowsingSignalAggregate(
                    target_lemma="hipoteca",
                    target_hit_count=80.0,
                ),
                "préstamo": BrowsingSignalAggregate(
                    target_lemma="préstamo",
                    target_hit_count=30.0,
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="casa", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="ser", neutral_score=0.96),
            BrowsingAdmissionCandidate(lemma="banco", neutral_score=0.92),
            BrowsingAdmissionCandidate(lemma="perro", neutral_score=0.88),
            BrowsingAdmissionCandidate(
                lemma="hipoteca",
                neutral_score=0.58,
                readiness_multiplier=0.95,
                source_confidence=0.95,
            ),
            BrowsingAdmissionCandidate(
                lemma="préstamo",
                neutral_score=0.54,
                readiness_multiplier=0.95,
                source_confidence=0.95,
            ),
        )

        results = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=4,
        )
        off = results[BROWSING_STRENGTH_OFF].to_dict()
        balanced = results[BROWSING_STRENGTH_BALANCED].to_dict()

        self.assertEqual(off["browsing_lane_count"], 0)
        self.assertEqual(balanced["browsing_lane_count"], 1)
        self.assertEqual(balanced["browsing_driven_count"], 1)
        self.assertIn("hipoteca", balanced["selected_lemmas"])
        self.assertNotIn("perro", balanced["selected_lemmas"])

    def test_balanced_does_not_realize_slot_for_tiny_signal(self) -> None:
        store = BrowsingSignalStore(
            pair="en-es",
            profile_id="default",
            items={
                "hipoteca": BrowsingSignalAggregate(
                    target_lemma="hipoteca",
                    target_hit_count=1.0,
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="casa", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="ser", neutral_score=0.96),
            BrowsingAdmissionCandidate(lemma="banco", neutral_score=0.92),
            BrowsingAdmissionCandidate(lemma="perro", neutral_score=0.88),
            BrowsingAdmissionCandidate(lemma="hipoteca", neutral_score=0.58),
        )

        results = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=4,
        )
        balanced = results[BROWSING_STRENGTH_BALANCED].to_dict()

        self.assertEqual(balanced["browsing_lane_count"], 0)
        self.assertEqual(
            balanced["selected_lemmas"],
            ["casa", "ser", "banco", "perro"],
        )

    def test_suppressed_lemma_has_zero_admission_probability(self) -> None:
        store = BrowsingSignalStore(
            pair="en-es",
            profile_id="default",
            items={
                "viaje": BrowsingSignalAggregate(target_lemma="viaje", target_hit_count=10.0),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="casa", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="viaje", neutral_score=0.99),
        )

        results = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=1,
            suppressed_lemmas={"viaje": SUPPRESSION_REASON_SUSPENDED},
        )
        rows = {row["lemma"]: row for row in results[BROWSING_STRENGTH_STRONG].to_dict()["rows"]}

        self.assertEqual(rows["viaje"]["suppressed_reason"], SUPPRESSION_REASON_SUSPENDED)
        self.assertFalse(rows["viaje"]["selected"])
        self.assertEqual(rows["viaje"]["deterministic_selection_probability"], 0.0)
        self.assertEqual(rows["viaje"]["approximate_selection_probability"], 0.0)

    def test_admission_suppression_cooldown_store(self) -> None:
        policy = SrsAdmissionSuppressionPolicy(
            discarded_cooldown_days=10,
            suspended_cooldown_days=20,
        )
        store = SrsAdmissionSuppressionStore(profile_id="default")
        discarded = create_admission_suppression(
            pair="en-es",
            lemma="gato",
            reason=SUPPRESSION_REASON_DISCARDED,
            policy=policy,
            now=NOW,
        )
        blocked = create_admission_suppression(
            pair="en-es",
            lemma="perro",
            reason=SUPPRESSION_REASON_USER_BLOCKED,
            policy=policy,
            now=NOW,
        )
        store = upsert_admission_suppression(store, discarded, now=NOW)
        store = upsert_admission_suppression(store, blocked, now=NOW)

        active = active_suppressed_lemmas(store, pair="en-es", now=NOW)
        self.assertEqual(active["gato"], SUPPRESSION_REASON_DISCARDED)
        self.assertEqual(active["perro"], SUPPRESSION_REASON_USER_BLOCKED)

        future = datetime(2026, 6, 15, tzinfo=timezone.utc)
        pruned = prune_expired_suppression_entries(store, now=future)
        active_future = active_suppressed_lemmas(pruned, pair="en-es", now=future)
        self.assertNotIn("gato", active_future)
        self.assertEqual(active_future["perro"], SUPPRESSION_REASON_USER_BLOCKED)

    def test_browsing_signal_is_saturating(self) -> None:
        policy = BrowsingSignalIngestPolicy(browsing_signal_cap=4.0)
        weak = BrowsingSignalAggregate(target_lemma="x", target_hit_count=1.0)
        strong = BrowsingSignalAggregate(target_lemma="x", target_hit_count=100.0)

        self.assertGreater(browsing_signal_value(strong, policy=policy), 0.0)
        self.assertLessEqual(browsing_signal_value(strong, policy=policy), 1.0)
        self.assertLess(
            browsing_signal_value(weak, policy=policy),
            browsing_signal_value(strong, policy=policy),
        )

    def test_strength_presets_keep_expected_order(self) -> None:
        presets = browsing_strength_presets()

        self.assertLess(
            presets[BROWSING_STRENGTH_OFF].browsing_budget_share,
            presets[BROWSING_STRENGTH_BALANCED].browsing_budget_share,
        )
        self.assertLess(
            presets[BROWSING_STRENGTH_BALANCED].browsing_budget_share,
            presets[BROWSING_STRENGTH_STRONG].browsing_budget_share,
        )


if __name__ == "__main__":
    unittest.main()
