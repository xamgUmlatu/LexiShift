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
    BrowsingSignalContextEvidence,
    BrowsingSignalIngestPolicy,
    BrowsingSignalPacket,
    BrowsingSignalPacketEntry,
    BrowsingSignalStore,
    build_browsing_target_key,
    browsing_evidence_value,
    browsing_signal_value,
    browsing_strength_presets,
    ingest_browsing_signal_packet,
    maintain_browsing_signal_store,
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

    def test_maintenance_uses_fourteen_day_default_half_life_and_prunes(self) -> None:
        policy = BrowsingSignalIngestPolicy(prune_signal_below=0.01)
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "濃い": BrowsingSignalAggregate(
                    target_lemma="濃い",
                    target_hit_count=6.0,
                    context_evidence=(
                        BrowsingSignalContextEvidence(
                            context_key="page-a",
                            target_hit_count=6.0,
                            last_seen_at="2026-05-09T00:00:00Z",
                        ),
                    ),
                    last_seen_at="2026-05-09T00:00:00Z",
                    decayed_at="2026-05-09T00:00:00Z",
                ),
                "薄い": BrowsingSignalAggregate(
                    target_lemma="薄い",
                    target_hit_count=0.01,
                    last_seen_at="2026-05-09T00:00:00Z",
                    decayed_at="2026-05-09T00:00:00Z",
                ),
            },
        )

        maintained = maintain_browsing_signal_store(store, policy=policy, now=NOW)

        self.assertEqual(policy.half_life_days, 14.0)
        self.assertEqual(set(maintained.items), {"濃い"})
        aggregate = maintained.items["濃い"]
        self.assertAlmostEqual(aggregate.target_hit_count, 3.0)
        self.assertAlmostEqual(aggregate.context_evidence[0].target_hit_count, 3.0)
        self.assertEqual(aggregate.decayed_at, "2026-05-23T00:00:00Z")

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
            now=NOW,
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

    def test_browsing_admission_matches_casefolded_latin_target_keys(self) -> None:
        policy = BrowsingSignalIngestPolicy()
        store = BrowsingSignalStore(
            pair="en-de",
            profile_id="default",
            items={
                "küche": BrowsingSignalAggregate(
                    target_lemma="küche",
                    target_key="küche",
                    replacement_exposure_count=10.0,
                    context_evidence=(
                        BrowsingSignalContextEvidence(
                            context_key="ctxh:a",
                            replacement_exposure_count=5.0,
                        ),
                        BrowsingSignalContextEvidence(
                            context_key="ctxh:b",
                            replacement_exposure_count=5.0,
                        ),
                    ),
                    last_seen_at="2026-05-23T00:00:00Z",
                    decayed_at="2026-05-23T00:00:00Z",
                )
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="Haus", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="sein", neutral_score=0.96),
            BrowsingAdmissionCandidate(lemma="sagen", neutral_score=0.90),
            BrowsingAdmissionCandidate(
                lemma="Küche",
                neutral_score=0.64,
                readiness_multiplier=0.92,
                explicit_preference_fit=0.70,
                source_confidence=0.90,
                lexical_commonness=0.35,
                lexical_commonness_known=True,
            ),
        )

        strong = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=3,
            policy=policy,
            now=NOW,
        )[BROWSING_STRENGTH_STRONG].to_dict()
        rows = {row["target_key"]: row for row in strong["rows"]}

        self.assertGreater(rows["Küche"]["browsing_signal"], 0.0)
        self.assertGreater(rows["Küche"]["final_score"], rows["Küche"]["neutral_score"])

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
            now=NOW,
        )
        off = results[BROWSING_STRENGTH_OFF].to_dict()
        strong = results[BROWSING_STRENGTH_STRONG].to_dict()

        self.assertEqual(ingest.store.pair, "en-ja")
        self.assertIn("料理", ingest.store.items)
        self.assertIn("病院", ingest.store.items)
        self.assertEqual(off["selected_lemmas"], off["neutral_selected_lemmas"])
        self.assertGreater(strong["browsing_lane_count"], off["browsing_lane_count"])
        self.assertIn("料理", strong["selected_lemmas"])

    def test_en_ja_source_and_target_signals_coalesce_on_reading_key(self) -> None:
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
                    target_lemma="発酵",
                    target_key="発酵|はっこう",
                    target_reading="はっこう",
                    side=BROWSING_SIGNAL_TARGET,
                    count=2,
                    reading_confidence=1.0,
                    observation_source="target_surface",
                ),
                BrowsingSignalPacketEntry(
                    target_lemma="発酵",
                    target_key="発酵|はっこう",
                    target_reading="はっこう",
                    side=BROWSING_SIGNAL_SOURCE,
                    count=3,
                    source_mapping_confidence=0.5,
                    reading_confidence=1.0,
                    observation_source="source_mapping",
                ),
            ),
        )

        result = ingest_browsing_signal_packet(store, packet, policy=policy, now=NOW)

        self.assertEqual(set(result.store.items), {"発酵|はっこう"})
        aggregate = result.store.items["発酵|はっこう"]
        self.assertEqual(aggregate.target_lemma, "発酵")
        self.assertEqual(aggregate.target_key, "発酵|はっこう")
        self.assertEqual(aggregate.target_reading, "はっこう")
        self.assertEqual(aggregate.target_hit_count, 2.0)
        self.assertEqual(aggregate.source_hit_count, 1.5)
        self.assertEqual(aggregate.reading_confidence, 1.0)
        self.assertEqual(
            set(aggregate.observation_sources),
            {"source_mapping", "target_surface"},
        )

    def test_en_ja_target_key_prevents_wrong_reading_boost(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "辛い|からい": BrowsingSignalAggregate(
                    target_lemma="辛い",
                    target_key="辛い|からい",
                    target_reading="からい",
                    target_hit_count=80.0,
                    reading_confidence=1.0,
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="ある", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="こと", neutral_score=0.96),
            BrowsingAdmissionCandidate(
                lemma="辛い",
                target_key="辛い|つらい",
                target_reading="つらい",
                neutral_score=0.58,
                lexical_commonness=0.30,
                lexical_commonness_known=True,
            ),
        )

        results = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=2,
            now=NOW,
        )
        rows = {
            row["target_key"]: row for row in results[BROWSING_STRENGTH_STRONG].to_dict()["rows"]
        }

        self.assertEqual(rows["辛い|つらい"]["browsing_signal"], 0.0)
        self.assertNotIn("辛い", results[BROWSING_STRENGTH_STRONG].to_dict()["selected_lemmas"])

    def test_en_ja_exact_reading_key_can_boost_matching_candidate(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "辛い|つらい": BrowsingSignalAggregate(
                    target_lemma="辛い",
                    target_key="辛い|つらい",
                    target_reading="つらい",
                    target_hit_count=80.0,
                    reading_confidence=1.0,
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="ある", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="こと", neutral_score=0.96),
            BrowsingAdmissionCandidate(
                lemma="辛い",
                target_key="辛い|つらい",
                target_reading="つらい",
                neutral_score=0.58,
                lexical_commonness=0.30,
                lexical_commonness_known=True,
            ),
        )

        results = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=2,
            now=NOW,
        )
        strong = results[BROWSING_STRENGTH_STRONG].to_dict()
        rows = {row["target_key"]: row for row in strong["rows"]}

        self.assertGreater(rows["辛い|つらい"]["browsing_signal"], 0.0)
        self.assertIn("辛い", strong["selected_lemmas"])

    def test_en_ja_exact_reading_aggregate_wins_over_legacy_bare_key(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "会社": BrowsingSignalAggregate(
                    target_lemma="会社",
                    replacement_exposure_count=80.0,
                    reading_confidence=0.45,
                ),
                "会社|かいしゃ": BrowsingSignalAggregate(
                    target_lemma="会社",
                    target_key="会社|かいしゃ",
                    target_reading="かいしゃ",
                    source_hit_count=3.0,
                    source_mapping_confidence=0.72,
                    reading_confidence=1.0,
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(
                lemma="会社",
                target_key="会社|かいしゃ",
                target_reading="かいしゃ",
                neutral_score=0.80,
            ),
        )

        strong = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=1,
            now=NOW,
        )[BROWSING_STRENGTH_STRONG].to_dict()
        row = strong["rows"][0]

        self.assertEqual(row["target_key"], "会社|かいしゃ")
        self.assertEqual(row["target_reading"], "かいしゃ")
        self.assertEqual(row["browsing_evidence"], 3.0)
        self.assertGreater(row["browsing_signal"], 0.0)

    def test_reading_confidence_dampens_vague_target_surface_observation(self) -> None:
        exact = BrowsingSignalAggregate(
            target_lemma="辛い",
            target_key="辛い|つらい",
            target_reading="つらい",
            target_hit_count=8.0,
            reading_confidence=1.0,
        )
        vague = BrowsingSignalAggregate(
            target_lemma="辛い",
            target_key="辛い|つらい",
            target_reading="つらい",
            target_hit_count=8.0,
            reading_confidence=0.25,
        )

        self.assertEqual(
            build_browsing_target_key(target_lemma="辛い", target_reading="つらい"),
            "辛い|つらい",
        )
        self.assertLess(browsing_signal_value(vague), browsing_signal_value(exact))

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
            now=NOW,
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
            now=NOW,
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
            now=NOW,
        )
        balanced = results[BROWSING_STRENGTH_BALANCED].to_dict()
        rows = {row["lemma"]: row for row in balanced["rows"]}

        self.assertEqual(balanced["browsing_lane_count"], 0)
        self.assertEqual(
            balanced["selected_lemmas"],
            ["casa", "ser", "banco", "perro"],
        )
        self.assertGreater(rows["hipoteca"]["browsing_signal"], 0.0)
        self.assertEqual(rows["hipoteca"]["browsing_count_multiplier"], 0.0)
        self.assertEqual(rows["hipoteca"]["effective_browsing_signal"], 0.0)

    def test_browsing_evidence_count_gate_requires_repeated_hits(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "一回": BrowsingSignalAggregate(target_lemma="一回", target_hit_count=1.0),
                "二回": BrowsingSignalAggregate(target_lemma="二回", target_hit_count=2.0),
                "三回": BrowsingSignalAggregate(target_lemma="三回", target_hit_count=3.0),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="一回", neutral_score=0.80),
            BrowsingAdmissionCandidate(lemma="二回", neutral_score=0.80),
            BrowsingAdmissionCandidate(lemma="三回", neutral_score=0.80),
        )

        strong = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=3,
            now=NOW,
        )[BROWSING_STRENGTH_STRONG].to_dict()
        rows = {row["lemma"]: row for row in strong["rows"]}

        self.assertGreater(rows["一回"]["browsing_signal"], 0.0)
        self.assertEqual(rows["一回"]["browsing_count_multiplier"], 0.0)
        self.assertEqual(rows["一回"]["effective_browsing_signal"], 0.0)
        self.assertEqual(rows["一回"]["browsing_lane_probability"], 0.0)
        self.assertEqual(rows["二回"]["browsing_count_multiplier"], 0.0)
        self.assertEqual(rows["二回"]["effective_browsing_signal"], 0.0)
        self.assertEqual(rows["二回"]["browsing_lane_probability"], 0.0)
        self.assertEqual(rows["三回"]["browsing_count_multiplier"], 1.0)
        self.assertGreater(
            rows["三回"]["effective_browsing_signal"],
            rows["二回"]["effective_browsing_signal"],
        )

    def test_context_evidence_discounts_same_page_repetition(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "同頁": BrowsingSignalAggregate(
                    target_lemma="同頁",
                    target_hit_count=9.0,
                    context_evidence=(
                        BrowsingSignalContextEvidence(
                            context_key="page-a",
                            target_hit_count=9.0,
                        ),
                    ),
                ),
                "三頁": BrowsingSignalAggregate(
                    target_lemma="三頁",
                    target_hit_count=3.0,
                    context_evidence=(
                        BrowsingSignalContextEvidence(
                            context_key="page-a",
                            target_hit_count=1.0,
                        ),
                        BrowsingSignalContextEvidence(
                            context_key="page-b",
                            target_hit_count=1.0,
                        ),
                        BrowsingSignalContextEvidence(
                            context_key="page-c",
                            target_hit_count=1.0,
                        ),
                    ),
                ),
                "二頁": BrowsingSignalAggregate(
                    target_lemma="二頁",
                    target_hit_count=4.0,
                    context_evidence=(
                        BrowsingSignalContextEvidence(
                            context_key="page-a",
                            target_hit_count=2.0,
                        ),
                        BrowsingSignalContextEvidence(
                            context_key="page-b",
                            target_hit_count=2.0,
                        ),
                    ),
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="同頁", neutral_score=0.80),
            BrowsingAdmissionCandidate(lemma="三頁", neutral_score=0.80),
            BrowsingAdmissionCandidate(lemma="二頁", neutral_score=0.80),
        )

        strong = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=3,
            now=NOW,
        )[BROWSING_STRENGTH_STRONG].to_dict()
        rows = {row["lemma"]: row for row in strong["rows"]}

        self.assertEqual(rows["同頁"]["browsing_context_count"], 1)
        self.assertLess(rows["同頁"]["browsing_evidence"], 3.5)
        self.assertEqual(rows["同頁"]["browsing_count_multiplier"], 0.0)
        self.assertEqual(rows["同頁"]["effective_browsing_signal"], 0.0)
        self.assertEqual(rows["三頁"]["browsing_context_count"], 3)
        self.assertEqual(rows["三頁"]["browsing_evidence"], 3.0)
        self.assertEqual(rows["三頁"]["browsing_count_multiplier"], 1.0)
        self.assertEqual(rows["二頁"]["browsing_context_count"], 2)
        self.assertGreater(rows["二頁"]["browsing_evidence"], 3.0)
        self.assertEqual(rows["二頁"]["browsing_count_multiplier"], 1.0)

    def test_ingest_merges_privacy_safe_context_evidence(self) -> None:
        policy = BrowsingSignalIngestPolicy(prune_signal_below=0.0)
        store = BrowsingSignalStore(pair="en-ja", profile_id="default")
        packet = BrowsingSignalPacket(
            pair="en-ja",
            profile_id="default",
            signals=(
                BrowsingSignalPacketEntry(
                    target_lemma="兎",
                    side=BROWSING_SIGNAL_TARGET,
                    count=2,
                    context_key="https://example.invalid/private/path",
                ),
                BrowsingSignalPacketEntry(
                    target_lemma="兎",
                    side=BROWSING_SIGNAL_TARGET,
                    count=1,
                    context_key="page-b",
                ),
            ),
        )

        result = ingest_browsing_signal_packet(store, packet, policy=policy, now=NOW)
        aggregate = result.store.items["兎"]
        serialized = json.dumps(result.store.to_dict(), ensure_ascii=False)

        self.assertEqual(len(aggregate.context_evidence), 2)
        self.assertGreaterEqual(browsing_evidence_value(aggregate, policy=policy), 2.0)
        self.assertNotIn("example.invalid", serialized)
        self.assertIn("ctx:v1:", serialized)

    def test_browsing_lane_uses_admission_suitability_as_quality_gate(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "たいもん": BrowsingSignalAggregate(
                    target_lemma="たいもん",
                    target_hit_count=80.0,
                ),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(lemma="料理", neutral_score=1.00),
            BrowsingAdmissionCandidate(lemma="注文", neutral_score=0.96),
            BrowsingAdmissionCandidate(lemma="玄関", neutral_score=0.90),
            BrowsingAdmissionCandidate(
                lemma="たいもん",
                neutral_score=0.0,
                admission_suitability=0.0,
                lexical_commonness=0.0,
                lexical_commonness_known=False,
            ),
        )

        strong = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=3,
            now=NOW,
        )[BROWSING_STRENGTH_STRONG].to_dict()
        rows = {row["lemma"]: row for row in strong["rows"]}

        self.assertGreater(rows["たいもん"]["browsing_signal"], 0.0)
        self.assertEqual(rows["たいもん"]["browsing_quality_multiplier"], 0.0)
        self.assertEqual(rows["たいもん"]["effective_browsing_signal"], 0.0)
        self.assertEqual(strong["browsing_lane_count"], 0)
        self.assertNotIn("たいもん", strong["selected_lemmas"])

    def test_browsing_specificity_dampens_hypercommon_page_hits(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "ある": BrowsingSignalAggregate(target_lemma="ある", target_hit_count=10.0),
                "料理店": BrowsingSignalAggregate(target_lemma="料理店", target_hit_count=10.0),
                "未知": BrowsingSignalAggregate(target_lemma="未知", target_hit_count=10.0),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(
                lemma="ある",
                neutral_score=0.80,
                lexical_commonness=1.0,
                lexical_commonness_known=True,
            ),
            BrowsingAdmissionCandidate(
                lemma="料理店",
                neutral_score=0.80,
                lexical_commonness=0.10,
                lexical_commonness_known=True,
            ),
            BrowsingAdmissionCandidate(
                lemma="未知",
                neutral_score=0.80,
                lexical_commonness=0.0,
                lexical_commonness_known=False,
            ),
        )

        strong = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=3,
            now=NOW,
        )[BROWSING_STRENGTH_STRONG].to_dict()
        rows = {row["lemma"]: row for row in strong["rows"]}

        self.assertEqual(rows["ある"]["browsing_signal"], rows["料理店"]["browsing_signal"])
        self.assertLess(
            rows["ある"]["effective_browsing_signal"],
            rows["料理店"]["effective_browsing_signal"],
        )
        self.assertLess(
            rows["未知"]["effective_browsing_signal"],
            rows["料理店"]["effective_browsing_signal"],
        )
        self.assertEqual(rows["ある"]["browsing_specificity_multiplier"], 0.65)
        self.assertEqual(rows["未知"]["browsing_specificity_multiplier"], 0.75)

    def test_relative_salience_requires_more_local_evidence_for_common_words(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={
                "ある": BrowsingSignalAggregate(target_lemma="ある", target_hit_count=3.0),
                "料理店": BrowsingSignalAggregate(target_lemma="料理店", target_hit_count=3.0),
            },
        )
        candidates = (
            BrowsingAdmissionCandidate(
                lemma="ある",
                neutral_score=0.80,
                lexical_commonness=1.0,
                lexical_commonness_known=True,
            ),
            BrowsingAdmissionCandidate(
                lemma="料理店",
                neutral_score=0.80,
                lexical_commonness=0.10,
                lexical_commonness_known=True,
            ),
        )

        strong = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=2,
            now=NOW,
        )[BROWSING_STRENGTH_STRONG].to_dict()
        rows = {row["lemma"]: row for row in strong["rows"]}

        self.assertEqual(rows["ある"]["browsing_count_multiplier"], 1.0)
        self.assertEqual(rows["料理店"]["browsing_count_multiplier"], 1.0)
        self.assertLess(
            rows["ある"]["browsing_salience_multiplier"],
            rows["料理店"]["browsing_salience_multiplier"],
        )
        self.assertLess(
            rows["ある"]["effective_browsing_signal"],
            rows["料理店"]["effective_browsing_signal"],
        )

    def test_common_words_regain_salience_with_enough_local_evidence(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            profile_id="default",
            items={"ある": BrowsingSignalAggregate(target_lemma="ある", target_hit_count=25.0)},
        )
        candidates = (
            BrowsingAdmissionCandidate(
                lemma="ある",
                neutral_score=0.80,
                lexical_commonness=1.0,
                lexical_commonness_known=True,
            ),
        )

        strong = simulate_browsing_admission_presets(
            candidates,
            store=store,
            admission_budget=1,
            now=NOW,
        )[BROWSING_STRENGTH_STRONG].to_dict()
        row = strong["rows"][0]

        self.assertEqual(row["browsing_count_multiplier"], 1.0)
        self.assertEqual(row["browsing_salience_multiplier"], 1.0)
        self.assertGreater(row["effective_browsing_signal"], 0.0)

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
            now=NOW,
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
