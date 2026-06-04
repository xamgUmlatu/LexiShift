from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(SCRIPTS_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_srs_case_mix_prior_en_es import (  # noqa: E402
    build_srs_case_mix_prior_report,
    render_srs_case_mix_prior_markdown,
)


class SemanticVetoSrsCaseMixPriorTests(unittest.TestCase):
    def test_estimates_case_mix_priors_and_reweights_band_success(self) -> None:
        report = build_srs_case_mix_prior_report(
            srs_bridge_payload=_srs_bridge(),
            score_surface_payload=_score_surface(),
            wordnet_index=_wordnet_index(),
            generated_at="2026-05-08T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "srs_case_mix_prior_established")
        self.assertEqual(report["summary"]["source_target_pair_count"], 3)
        self.assertTrue(report["e2e_checks"]["case_type_priors_sum_to_one"])
        self.assertTrue(report["e2e_checks"]["weighted_success_rows_available"])

        base = report["summary"]["base_scenario"]
        self.assertTrue(base["band_prior_rows"])
        for row in base["band_prior_rows"]:
            total = row["p_positive_active"] + row["p_shadow_negative"] + row["p_phrase_no_winner"]
            self.assertAlmostEqual(total, 1.0, places=3)

        markdown = render_srs_case_mix_prior_markdown(report)
        self.assertIn("SRS Case-Mix Prior", markdown)
        self.assertIn("Base Weighted Success", markdown)


def _srs_bridge() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "srs_zipf_bridge_established",
        "full_source_target_pairs": [
            {
                "source": "change",
                "target": "cambio",
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "source_zipf_frequency_en": 5.2,
                "target_zipf_band_es": "zipf_4_to_5_common",
                "target_zipf_frequency_es": 4.5,
            },
            {
                "source": "change",
                "target": "monedas",
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "source_zipf_frequency_en": 5.2,
                "target_zipf_band_es": "zipf_3_to_4_mid",
                "target_zipf_frequency_es": 3.4,
            },
            {
                "source": "bouillon",
                "target": "caldo",
                "source_zipf_band_en": "zipf_below_3_rare",
                "source_zipf_frequency_en": 2.5,
                "target_zipf_band_es": "zipf_3_to_4_mid",
                "target_zipf_frequency_es": 3.5,
            },
        ],
    }


def _score_surface() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "full_family_score_surface_established",
        "breakdowns": {
            "scorer_x_source_band_x_case_type": [
                _rate_row(
                    "sentence_transformer_cosine",
                    "zipf_5_plus_very_common",
                    "positive_active",
                    "positive_allow_rate",
                    0.9,
                ),
                _rate_row(
                    "sentence_transformer_cosine",
                    "zipf_5_plus_very_common",
                    "shadow_negative",
                    "shadow_negative_abstain_rate",
                    0.8,
                ),
                _rate_row(
                    "sentence_transformer_cosine",
                    "zipf_5_plus_very_common",
                    "phrase_no_winner",
                    "phrase_no_winner_abstain_rate",
                    0.2,
                ),
                _rate_row(
                    "sentence_transformer_cosine",
                    "zipf_below_3_rare",
                    "positive_active",
                    "positive_allow_rate",
                    0.7,
                ),
                _rate_row(
                    "sentence_transformer_cosine",
                    "zipf_below_3_rare",
                    "shadow_negative",
                    "shadow_negative_abstain_rate",
                    1.0,
                ),
                _rate_row(
                    "sentence_transformer_cosine",
                    "zipf_below_3_rare",
                    "phrase_no_winner",
                    "phrase_no_winner_abstain_rate",
                    0.5,
                ),
            ]
        },
    }


def _rate_row(
    scorer: str,
    band: str,
    case_type: str,
    rate_key: str,
    rate: float,
) -> dict[str, object]:
    return {
        "scorer_id": scorer,
        "source_zipf_band_en": band,
        "manual_case_type": case_type,
        rate_key: rate,
    }


def _wordnet_index() -> object:
    return type(
        "WordNetFixture",
        (),
        {
            "source_file_count": 1,
            "entries_by_word": {
                "change": {
                    "n": {"sense": [{"synset": "change-n-1"}, {"synset": "change-n-2"}]},
                    "v": {"sense": [{"synset": "change-v-1"}]},
                },
                "bouillon": {"n": {"sense": [{"synset": "bouillon-n-1"}]}},
            },
        },
    )()


if __name__ == "__main__":
    unittest.main()
