from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_browsing_admission_research_support import (  # noqa: E402
    BrowsingAdmissionPolicy,
    BrowsingSignal,
    TextDocument,
    browsing_boost_value,
    browsing_signal_value,
    build_bridge_indexes,
    compute_browsing_signals,
    extract_document_signals,
    source_variants,
    target_variants,
)
from srs_browsing_admission_research_en_es import (  # noqa: E402
    build_canonical_helper_probe,
    canonical_signal_payloads,
)


class TestSrsBrowsingAdmissionResearchEnEs(unittest.TestCase):
    def test_source_inflection_maps_to_target_candidate(self) -> None:
        policy = BrowsingAdmissionPolicy()
        source_index, target_index, summary = build_bridge_indexes(
            {
                "full_source_target_pairs": [
                    {
                        "source": "mortgage",
                        "target": "hipoteca",
                        "target_zipf_frequency_es": 4.1,
                    }
                ]
            },
            policy=policy,
        )

        extraction = extract_document_signals(
            [TextDocument(document_id="unit", text="Mortgages and mortgaged homes.")],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )
        signals = compute_browsing_signals(
            extraction["source_token_counts"],
            extraction["target_token_counts"],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )

        self.assertEqual(summary["raw_pair_count"], 1)
        self.assertIn("mortgage", source_variants("mortgages"))
        self.assertIn("hipoteca", signals)
        self.assertGreater(signals["hipoteca"].source_weighted_count, 0.0)
        self.assertEqual(signals["hipoteca"].source_terms, ("mortgage",))

    def test_ambiguous_source_mapping_is_dampened(self) -> None:
        policy = BrowsingAdmissionPolicy()
        source_index, target_index, _summary = build_bridge_indexes(
            {
                "full_source_target_pairs": [
                    {"source": "charge", "target": "cargo"},
                    {"source": "charge", "target": "cobrar"},
                    {"source": "charge", "target": "cargar"},
                    {"source": "charge", "target": "acusación"},
                ]
            },
            policy=policy,
        )

        extraction = extract_document_signals(
            [TextDocument(document_id="unit", text="charge charge charge charge")],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )
        signals = compute_browsing_signals(
            extraction["source_token_counts"],
            extraction["target_token_counts"],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )

        self.assertEqual(len(signals), 4)
        for signal in signals.values():
            self.assertAlmostEqual(signal.mapping_confidence_max, 0.5)
            self.assertEqual(signal.ambiguous_source_terms, ("charge",))
            self.assertLess(signal.source_weighted_count, 3.0)

    def test_target_plural_and_accent_fold_direct_hits(self) -> None:
        policy = BrowsingAdmissionPolicy()
        source_index, target_index, _summary = build_bridge_indexes(
            {
                "full_source_target_pairs": [
                    {"source": "mortgage", "target": "hipoteca"},
                    {"source": "loan", "target": "préstamo"},
                ]
            },
            policy=policy,
        )

        extraction = extract_document_signals(
            [TextDocument(document_id="unit", text="hipotecas prestamos", side="target")],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )
        signals = compute_browsing_signals(
            extraction["source_token_counts"],
            extraction["target_token_counts"],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )

        self.assertIn("hipoteca", target_variants("hipotecas"))
        self.assertEqual(signals["hipoteca"].target_hit_count, 1)
        self.assertEqual(signals["préstamo"].target_hit_count, 1)

    def test_source_side_does_not_count_target_direct_hits(self) -> None:
        policy = BrowsingAdmissionPolicy()
        source_index, target_index, _summary = build_bridge_indexes(
            {"full_source_target_pairs": [{"source": "physician", "target": "doctor"}]},
            policy=policy,
        )

        source_extraction = extract_document_signals(
            [TextDocument(document_id="unit", text="doctor", side="source")],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )
        target_extraction = extract_document_signals(
            [TextDocument(document_id="unit", text="doctor", side="target")],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )

        self.assertEqual(source_extraction["target_token_counts"], {})
        self.assertEqual(source_extraction["summary"]["unmapped_token_count"], 1)
        self.assertEqual(target_extraction["target_token_counts"]["doctor"], 1)

    def test_browsing_signal_saturates_and_boost_is_capped(self) -> None:
        policy = BrowsingAdmissionPolicy(
            browsing_signal_cap=4.0,
            browsing_alpha=1.0,
            max_browsing_boost=1.25,
        )
        source_index, target_index, _summary = build_bridge_indexes(
            {"full_source_target_pairs": [{"source": "loan", "target": "préstamo"}]},
            policy=policy,
        )
        extraction = extract_document_signals(
            [TextDocument(document_id="unit", text=" ".join(["loan"] * 100))],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )
        signals = compute_browsing_signals(
            extraction["source_token_counts"],
            extraction["target_token_counts"],
            source_index=source_index,
            target_index=target_index,
            policy=policy,
        )

        signal_value = browsing_signal_value(signals["préstamo"], policy=policy)
        boost = browsing_boost_value(signal_value, policy=policy)

        self.assertLessEqual(signal_value, 1.0)
        self.assertLessEqual(boost, 1.25)
        self.assertEqual(extraction["source_token_counts"]["loan"], 3)

    def test_research_signals_convert_to_canonical_helper_payloads(self) -> None:
        payloads = canonical_signal_payloads(
            {
                "hipoteca": BrowsingSignal(
                    lemma="hipoteca",
                    source_weighted_count=2.0,
                    target_hit_count=1.0,
                    mapping_confidence_max=0.5,
                )
            }
        )

        self.assertEqual(len(payloads), 2)
        source_payload = next(payload for payload in payloads if payload["side"] == "source")
        target_payload = next(payload for payload in payloads if payload["side"] == "target")
        self.assertEqual(source_payload["target_lemma"], "hipoteca")
        self.assertEqual(source_payload["source_mapping_confidence"], 0.5)
        self.assertEqual(source_payload["count"], 4.0)
        self.assertEqual(target_payload["count"], 1.0)

    def test_canonical_helper_probe_is_privacy_safe_and_monotonic(self) -> None:
        probe = build_canonical_helper_probe(
            pair="en-es",
            browsing_by_lemma={
                "hipoteca": BrowsingSignal(
                    lemma="hipoteca",
                    source_weighted_count=3.0,
                    mapping_confidence_max=0.75,
                )
            },
            neutral_rows=[
                {
                    "lemma": "casa",
                    "neutral_score": 1.0,
                    "readiness_multiplier": 1.0,
                    "topic_affinity": 0.0,
                },
                {
                    "lemma": "hipoteca",
                    "neutral_score": 0.8,
                    "readiness_multiplier": 1.0,
                    "topic_affinity": 0.6,
                },
                {
                    "lemma": "préstamo",
                    "neutral_score": 0.7,
                    "readiness_multiplier": 1.0,
                    "topic_affinity": 0.0,
                },
            ],
            preview_count=2,
            generated_at="2026-05-23T00:00:00Z",
        )

        self.assertEqual(probe["status"], "ok")
        self.assertFalse(probe["privacy"]["raw_text_stored"])
        self.assertFalse(probe["privacy"]["url_stored"])
        self.assertFalse(probe["privacy"]["runtime_srs_mutation"])
        helper_ingest = probe["helper_ingest"]
        self.assertEqual(helper_ingest["status"], "ok")
        self.assertEqual(helper_ingest["ingest_result"]["accepted_signal_count"], 1)
        simulations = probe["simulations"]
        self.assertLessEqual(
            simulations["off"]["browsing_lane_share"],
            simulations["balanced"]["browsing_lane_share"],
        )
        self.assertLessEqual(
            simulations["balanced"]["browsing_lane_share"],
            simulations["strong"]["browsing_lane_share"],
        )
        self.assertIn("rows", simulations["balanced"])
        self.assertLessEqual(
            len(simulations["balanced"]["rows"]),
            simulations["balanced"]["row_count"],
        )


if __name__ == "__main__":
    unittest.main()
