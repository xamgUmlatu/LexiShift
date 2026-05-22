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
    TextDocument,
    browsing_boost_value,
    browsing_signal_value,
    build_bridge_indexes,
    compute_browsing_signals,
    extract_document_signals,
    source_variants,
    target_variants,
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


if __name__ == "__main__":
    unittest.main()
