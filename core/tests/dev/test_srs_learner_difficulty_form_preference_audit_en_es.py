from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_form_preference_audit_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyFormPreferenceAuditEnEsTests(unittest.TestCase):
    def test_flags_only_material_singular_plural_surface_gaps(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            wordfreq_zipf_by_term={
                "gafa": 2.54,
                "gafas": 4.03,
                "tortita": 2.44,
                "tortitas": 2.85,
                "flan": 3.19,
                "flanes": 2.17,
                "tostada": 3.29,
                "tostadas": 3.38,
                "datos": 4.10,
                "dato": 3.55,
            },
            min_gap=0.35,
            strong_gap=0.75,
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(report["decision"], "en_es_form_preference_audit_ready")
        self.assertFalse(report["production_ranking_changed"])
        rows = {row["lemma"]: row for row in report["audit_rows"]}

        self.assertIn("gafa", rows)
        self.assertEqual(rows["gafa"]["preferred_mate"], "gafas")
        self.assertFalse(rows["gafa"]["preferred_mate_in_candidate_rows"])
        self.assertEqual(rows["gafa"]["severity"], "strong")
        self.assertTrue(rows["gafa"]["suspicious_support"])

        self.assertIn("tortita", rows)
        self.assertEqual(rows["tortita"]["preferred_mate"], "tortitas")
        self.assertEqual(rows["tortita"]["severity"], "moderate")

        self.assertNotIn("flan", rows)
        self.assertNotIn("tostada", rows)
        self.assertNotIn("datos", rows)
        self.assertEqual(report["summary"]["preferred_mate_missing_count"], 2)

        markdown = render_markdown(report)
        self.assertIn("en-es Form Preference Audit", markdown)
        self.assertIn("gafa", markdown)
        self.assertIn("gafas", markdown)


def _formula_report_fixture() -> dict[str, object]:
    return {
        "decision": "fixture_formula_probe",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": 5},
        "rows": [
            _row("gafa", "other", "other", 0.74, dict_entries=0),
            _row("tortita", "other", "other", 0.74, dict_entries=0),
            _row("flan", "noun", "noun", 0.46, dict_entries=1),
            _row("tostada", "other", "other", 0.38, dict_entries=1),
            _row("datos", "noun", "noun", 0.30, dict_entries=1),
        ],
    }


def _row(
    lemma: str,
    pos: str,
    pos_bucket: str,
    score: float,
    *,
    dict_entries: int,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "spalex_rank": 1000.0,
        "pos": pos,
        "pos_bucket": pos_bucket,
        "candidate_state": "normal_vocab",
        "translations": [lemma],
        "components": {
            "pos_other_risk": 1.0 if pos_bucket == "other" else 0.0,
            "dict_marked_usage_risk": 0.0,
            "learner_source_known": 0.0,
            "learner_source_count": 0.0,
        },
        "dictionary": {
            "entry_count": dict_entries,
            "sense_count": dict_entries,
        },
        "variant_scores": {
            "spalex_blend_frequency": score,
        },
    }


if __name__ == "__main__":
    unittest.main()
