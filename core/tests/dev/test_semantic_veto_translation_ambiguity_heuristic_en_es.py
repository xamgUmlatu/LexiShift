from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_translation_ambiguity_heuristic_en_es import (  # noqa: E402
    build_translation_ambiguity_heuristic_report,
    render_translation_ambiguity_heuristic_markdown,
)


class SemanticVetoTranslationAmbiguityHeuristicTests(unittest.TestCase):
    def test_builds_inventory_available_heuristic_bakeoff(self) -> None:
        report = build_translation_ambiguity_heuristic_report(
            dataset_payload=_dataset(),
            score_surface_payload=_score_surface(),
            srs_bridge_payload=_srs_bridge(),
            wordnet_index=_wordnet_index(),
            generated_at="2026-05-08T00:00:00Z",
            top_k=2,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "translation_ambiguity_heuristic_bakeoff_established",
        )
        self.assertTrue(
            report["e2e_checks"]["formula_features_do_not_use_gold_or_prediction_labels"]
        )
        self.assertTrue(report["e2e_checks"]["internal_split_has_discovery_and_locked_proxy"])
        self.assertGreater(report["summary"]["sweep_formula_count"], 0)
        self.assertTrue(report["summary"]["best_by_scope"])

        observations = report["observations"]
        rich = next(row for row in observations if row["trigger"] == "bank")
        plain = next(row for row in observations if row["trigger"] == "quartz")
        self.assertGreater(
            rich["features"]["translation_fanout_risk"],
            plain["features"]["translation_fanout_risk"],
        )

        markdown = render_translation_ambiguity_heuristic_markdown(report)
        self.assertIn("Translation-Ambiguity Heuristic Bakeoff", markdown)
        self.assertIn("Signal Read", markdown)


def _dataset() -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "test",
        "manual_review_state": "approved_by_user",
        "families": [
            _family("en-es:test:f0:t", "bank", "banco", "zipf_5_plus_very_common"),
            _family("en-es:test:f2:t", "quartz", "cuarzo", "zipf_below_3_rare"),
        ],
    }


def _family(family_id: str, trigger: str, target: str, source_band: str) -> dict[str, object]:
    return {
        "family_id": family_id,
        "trigger": trigger,
        "active": {
            "target_lemma": target,
            "evidence_views": {
                "all_evidence_text": f"{trigger} -> {target} | active evidence",
            },
        },
        "shadows": [
            {
                "target_lemma": f"{target}_shadow",
                "evidence_views": {
                    "all_evidence_text": f"{trigger} -> other | shadow evidence",
                },
            }
        ],
        "cases": [
            {
                "case_id": f"{family_id}:001",
                "slice_dimensions": {
                    "source_zipf_band_en": [source_band],
                    "target_zipf_band_es": ["zipf_3_to_4_mid"],
                    "polysemy_band": ["medium_4_to_9"],
                    "pos_shape": ["same_pos_polysemy"],
                },
            }
        ],
    }


def _score_surface() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "full_family_score_surface_established",
        "row_results": [
            _score_row("tfidf_cosine", "en-es:test:f0:t", "bank", "harmful_replace"),
            _score_row("tfidf_cosine", "en-es:test:f2:t", "quartz", "correct"),
            _score_row("sentence_transformer_cosine", "en-es:test:f0:t", "bank", "harmful_replace"),
            _score_row("sentence_transformer_cosine", "en-es:test:f2:t", "quartz", "correct"),
        ],
    }


def _score_row(scorer: str, family_id: str, trigger: str, error_type: str) -> dict[str, object]:
    return {
        "scorer_id": scorer,
        "family_id": family_id,
        "trigger": trigger,
        "gold_decision": "abstain" if error_type == "harmful_replace" else "replace",
        "error_type": error_type,
    }


def _srs_bridge() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "srs_zipf_bridge_established",
        "full_source_target_pairs": [
            {
                "source": "bank",
                "target": "banco",
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "source_zipf_frequency_en": 5.2,
                "target_zipf_band_es": "zipf_4_to_5_common",
                "target_zipf_frequency_es": 4.4,
            },
            {
                "source": "bank",
                "target": "orilla",
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "source_zipf_frequency_en": 5.2,
                "target_zipf_band_es": "zipf_3_to_4_mid",
                "target_zipf_frequency_es": 3.4,
            },
            {
                "source": "quartz",
                "target": "cuarzo",
                "source_zipf_band_en": "zipf_below_3_rare",
                "source_zipf_frequency_en": 2.5,
                "target_zipf_band_es": "zipf_3_to_4_mid",
                "target_zipf_frequency_es": 3.6,
            },
        ],
    }


def _wordnet_index() -> object:
    return type(
        "WordNetFixture",
        (),
        {
            "source_file_count": 1,
            "entries_by_word": {
                "bank": {
                    "n": {
                        "sense": [
                            {"synset": "bank-n-1"},
                            {"synset": "bank-n-2"},
                            {"synset": "bank-n-3"},
                        ]
                    },
                    "v": {"sense": [{"synset": "bank-v-1"}]},
                },
                "quartz": {"n": {"sense": [{"synset": "quartz-n-1"}]}},
            },
        },
    )()


if __name__ == "__main__":
    unittest.main()
