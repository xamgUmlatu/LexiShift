from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_assumption_review_pack_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyAssumptionReviewPackEnEsTests(unittest.TestCase):
    def test_builds_adversarial_pack_with_assumption_families(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            calibration_payload=_calibration_fixture(),
            holdout_payload={"labels": []},
            candidate_id="spalex_blend__lsb_w090_c022__cog_l__no_wf__no_guard",
            target_count=8,
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_assumption_review_pack_ready",
        )
        self.assertFalse(report["production_ranking_changed"])
        self.assertFalse(report["manual_labels_added"])
        self.assertGreaterEqual(report["summary"]["row_count"], 6)
        self.assertEqual(report["summary"]["known_label_count"], 1)

        family_ids = {
            family_id for row in report["review_rows"] for family_id in row["assumption_family_ids"]
        }
        self.assertIn("wordfreq_spalex_disagreement", family_ids)
        self.assertIn("lexcom_rescue", family_ids)
        self.assertIn("cognate_rescue", family_ids)
        self.assertIn("learner_source_rescue", family_ids)

        hospital = next(row for row in report["review_rows"] if row["lemma"] == "hospital")
        self.assertEqual(
            hospital["existing_label"]["expected_learner_difficulty"],
            0.12,
        )
        self.assertIn("candidate", hospital["scores"])
        self.assertTrue(hospital["signals"])

        markdown = render_markdown(report)
        self.assertIn("en-es Learner Difficulty Assumption Review Pack", markdown)
        self.assertIn("Assumption Families", markdown)
        self.assertIn("Family Details", markdown)


def _formula_report_fixture() -> dict[str, object]:
    return {
        "decision": "en_es_formula_probe_ready",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": 8},
        "rows": [
            _row(
                "hospital",
                2,
                "noun",
                "noun",
                0.18,
                learner_gap=0.35,
                cognate=0.55,
                learner_known=1.0,
            ),
            _row(
                "global",
                3,
                "adjective",
                "adjective",
                0.38,
                cognate=0.60,
            ),
            _row(
                "arcaísmo",
                4,
                "noun",
                "noun",
                0.82,
                wordfreq_rescue=0.25,
                wordfreq_tail=0.30,
                marked=0.60,
            ),
            _row(
                "ahorrar",
                5,
                "verb",
                "verb",
                0.34,
                lexcom_known=1.0,
                lexcom_rescue=0.40,
                lexcom_after030=0.25,
            ),
            _row(
                "test",
                6,
                "noun",
                "noun",
                0.42,
                lexcom_known=1.0,
                lexcom_caution=0.20,
            ),
            _row(
                "par",
                7,
                "noun",
                "noun",
                0.19,
                ambiguity=0.70,
                broad_absent=1.0,
            ),
            _row(
                "del",
                8,
                "adposition",
                "other",
                0.05,
                function=1.0,
            ),
            _row(
                "chipirón",
                9,
                "noun",
                "noun",
                0.72,
                domain=0.60,
                diacritic=0.20,
            ),
        ],
    }


def _calibration_fixture() -> dict[str, object]:
    return {
        "labels": [
            {
                "lemma": "hospital",
                "expected_learner_difficulty": 0.12,
                "expected_candidate_state": "normal_vocab",
                "expected_problem_class": "cognate_core",
                "review_treatment": "vocab",
                "review_flags": ["cognate_easy_for_english_speaker"],
            }
        ]
    }


def _row(
    lemma: str,
    rank: int,
    pos: str,
    pos_bucket: str,
    base: float,
    *,
    learner_gap: float = 0.0,
    learner_known: float = 0.0,
    broad_absent: float = 0.0,
    cognate: float = 0.0,
    wordfreq_rescue: float = 0.0,
    wordfreq_tail: float = 0.0,
    lexcom_known: float = 0.0,
    lexcom_rescue: float = 0.0,
    lexcom_after030: float = 0.0,
    lexcom_caution: float = 0.0,
    marked: float = 0.0,
    ambiguity: float = 0.0,
    function: float = 0.0,
    domain: float = 0.0,
    diacritic: float = 0.0,
) -> dict[str, object]:
    components = {
        "spalex_blend": base,
        "zipf_base": base,
        "rank_base": base,
        "learner_core_gap_zipf_confident": learner_gap,
        "learner_core_gap_blend_confident": learner_gap,
        "learner_source_known": learner_known,
        "learner_core_score": 0.15 if learner_known else 0.0,
        "learner_source_count": learner_known,
        "learner_broad_source_absent": broad_absent,
        "unsupported_ease_suspicion": broad_absent,
        "unsupported_ease_content": broad_absent * 0.5,
        "cognate_rescue": cognate,
        "false_friend_caution": 0.0,
        "wordfreq_known": 1.0 if wordfreq_rescue else 0.0,
        "wordfreq_zipf": 4.2 if wordfreq_rescue else 0.0,
        "wordfreq_source_rescue": wordfreq_rescue,
        "wordfreq_tail_rescue": wordfreq_tail,
        "lexcom_known": lexcom_known,
        "lexcom_complexity": 0.20 if lexcom_known else 0.0,
        "lexcom_learner_rescue": lexcom_rescue,
        "lexcom_rescue_after030": lexcom_after030,
        "lexcom_rescue_after040": lexcom_after030,
        "lexcom_learner_caution": lexcom_caution,
        "dict_marked_usage_risk": marked,
        "gated_dict_marked_usage_risk": marked,
        "dict_register_sensitive_score": marked,
        "common_dict_ambiguity": ambiguity,
        "tail_dict_ambiguity": ambiguity,
        "dict_domain_topic_count_score": domain,
        "tail_domain_specificity": domain,
        "regional_colloquial_gate": 0.0,
        "pos_function_risk": function,
        "pos_other_risk": function,
        "char_length_difficulty": 0.30 if len(lemma) >= 8 else 0.0,
        "diacritic_burden_light": diacritic,
        "multiword_risk": 0.0,
        "punctuation_or_digit_risk": 0.0,
    }
    return {
        "lemma": lemma,
        "spalex_rank": float(rank),
        "pos": pos,
        "pos_bucket": pos_bucket,
        "candidate_state": "normal_vocab",
        "translations": [lemma],
        "components": components,
        "dictionary": {
            "entry_count": 1,
            "sense_count": 2,
            "translation_count": 2,
            "marked_terms": ["rare"] if marked else [],
            "region_terms": [],
            "register_terms": ["rare"] if marked else [],
            "domain_terms": ["food"] if domain else [],
            "topics": ["food"] if domain else [],
            "alt_of_count": 0,
            "form_of_count": 0,
        },
        "variant_scores": {
            "spalex_blend_frequency": base,
            "learner_source_zipf_medium": max(0.0, base - learner_gap * 0.2),
            "wordfreq_rescue_probe": max(0.0, base - wordfreq_rescue * 0.2),
            "lexcom_complexity_probe": max(0.0, base - lexcom_rescue * 0.2 + lexcom_caution * 0.2),
            "cognate_rescue_light": max(0.0, base - cognate * 0.1),
            "tail_guard_medium": min(1.0, base + marked * 0.1 + ambiguity * 0.05),
        },
    }


if __name__ == "__main__":
    unittest.main()
