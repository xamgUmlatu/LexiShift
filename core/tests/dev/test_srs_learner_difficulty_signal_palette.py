from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_signal_palette_en_ja import (  # noqa: E402
    DEFAULT_SOURCE_PY,
    build_entries,
    component_names_from_source,
    description_for_signal,
    render_markdown,
    roles_for_signal,
    signal_kind_for_signal,
    source_family_for_signal,
    supporting_signal_entries,
)


class TestSrsLearnerDifficultySignalPalette(unittest.TestCase):
    def test_component_names_are_extracted_from_sweep_source(self) -> None:
        names = component_names_from_source(DEFAULT_SOURCE_PY)

        self.assertIn("frequency", names)
        self.assertIn("jlpt_vocab_difficulty", names)
        self.assertIn("kango_mid_signal", names)
        self.assertIn("named_entity_risk", names)
        self.assertIn("frequency_source_known", names)
        self.assertIn("jmdict_marked_usage_flag", names)
        self.assertIn("jmdict_ambiguity_score", names)
        self.assertIn("kanjidic_nanori_reading_count_score", names)
        self.assertGreaterEqual(len(names), 230)

    def test_entries_have_palette_metadata(self) -> None:
        entries = build_entries(
            ("frequency", "jlpt_vocab_difficulty", "named_entity_risk"),
            component_counts={"frequency": 100, "named_entity_risk": 40},
            coverage_denominator=100,
        )

        for entry in entries:
            self.assertTrue(entry.source_family)
            self.assertTrue(entry.signal_kind)
            self.assertTrue(entry.roles)
            self.assertTrue(entry.description)

        self.assertEqual(entries[0].coverage_rate, 1.0)
        self.assertFalse(entries[1].in_latest_sweep)
        self.assertEqual(entries[2].coverage_rate, 0.4)

    def test_supporting_signals_include_individual_jlpt_level_features(self) -> None:
        names = {entry["name"] for entry in supporting_signal_entries()}

        self.assertIn("jlpt_vocab_levels", names)
        self.assertIn("jlpt_vocab_is_n5", names)
        self.assertIn("jlpt_vocab_is_n4", names)
        self.assertIn("jlpt_vocab_is_n3", names)
        self.assertIn("jlpt_vocab_is_n2", names)
        self.assertIn("jlpt_vocab_is_n1", names)
        self.assertIn("jlpt_vocab_n1_curve_value", names)
        self.assertIn("jlpt_kanji_dampening_strength", names)

    def test_source_family_keeps_kanji_and_name_signals_in_expected_lanes(self) -> None:
        self.assertEqual(source_family_for_signal("max_kanji_burden"), "KANJIDIC2")
        self.assertEqual(source_family_for_signal("jmnedict_name_risk"), "JMnedict names")
        self.assertEqual(
            source_family_for_signal("source_coverage_count"),
            "Cross-source coverage",
        )

    def test_semantic_aliases_are_described_as_aliases_not_raw_risks(self) -> None:
        self.assertEqual(
            signal_kind_for_signal("jmdict_marked_usage_risk"),
            "source_flag_compat",
        )
        self.assertEqual(signal_kind_for_signal("jmdict_marked_usage_flag"), "source_flag")
        self.assertEqual(signal_kind_for_signal("jmdict_ambiguity_score"), "score")
        self.assertEqual(signal_kind_for_signal("frequency_source_known"), "knownness")
        self.assertIn("evidence_quality", roles_for_signal("frequency_source_known"))
        self.assertIn(
            "Compatibility alias",
            description_for_signal("jmdict_marked_usage_risk"),
        )
        self.assertIn("Knownness indicator", description_for_signal("frequency_source_known"))

    def test_render_markdown_includes_signal_rows(self) -> None:
        report = {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "inputs": {
                "source_py": "scripts/testing/example.py",
                "sweep_json": "docs/test_outputs/example.json",
                "coverage_denominator": 100,
                "latest_sweep_generated_at": "2026-01-01T00:00:00Z",
            },
            "summary": {
                "component_count_from_code": 1,
                "component_count_with_latest_coverage": 1,
                "component_count_without_latest_coverage": 0,
                "supporting_signal_count": 1,
                "role_counts": {"presentation_priority": 1},
                "source_family_counts": {"BCCWJ frequency": 1},
            },
            "role_descriptions": {"presentation_priority": "Presentation priority."},
            "source_family_descriptions": {"BCCWJ frequency": "Frequency."},
            "signals": [
                {
                    "name": "frequency",
                    "source_family": "BCCWJ frequency",
                    "signal_kind": "difficulty_proxy",
                    "roles": ["presentation_priority"],
                    "coverage_count": 100,
                    "coverage_rate": 1.0,
                    "description": "Frequency.",
                }
            ],
            "supporting_signals": [
                {
                    "name": "jlpt_vocab_is_n5",
                    "source_family": "JLPT vocabulary",
                    "signal_kind": "derived_binary_gate",
                    "model_surface": "derivable_source_feature",
                    "roles": ["pedagogical_anchor"],
                    "description": "N5 gate.",
                }
            ],
        }

        markdown = render_markdown(report)

        self.assertIn("`frequency`", markdown)
        self.assertIn("`jlpt_vocab_is_n5`", markdown)
        self.assertIn("100 (100.0%)", markdown)


if __name__ == "__main__":
    unittest.main()
