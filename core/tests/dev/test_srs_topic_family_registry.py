from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_family_registry import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsTopicFamilyRegistryTests(unittest.TestCase):
    def test_registry_matrix_taxonomies_and_extension_support_are_aligned(self) -> None:
        report = build_report(generated_at="2026-07-06T00:00:00+00:00")

        self.assertEqual(report["status"], "ok")
        findings = {row["code"]: row for row in report["findings"]}
        self.assertEqual(findings["registry_family_ids_unique"]["level"], "PASS")
        self.assertEqual(findings["registry_family_metadata_valid"]["level"], "PASS")
        self.assertEqual(findings["en-ja_canonical_topic_partition_complete"]["level"], "PASS")
        self.assertEqual(findings["en-es_canonical_topic_partition_complete"]["level"], "PASS")
        self.assertEqual(findings["en-de_canonical_topic_partition_complete"]["level"], "PASS")
        self.assertEqual(findings["en-es_strict_visible_matches_pair_picker"]["level"], "PASS")
        self.assertEqual(
            findings["extension_topic_support_pair_matrix_aligned"]["level"],
            "PASS",
        )
        self.assertEqual(
            findings["options_topic_picker_matches_en_es_strict_picker"]["level"],
            "PASS",
        )
        self.assertEqual(
            findings["en_es_runtime_overlay_matches_supported_runtime_topics"]["level"],
            "PASS",
        )

    def test_pair_support_summary_keeps_picker_hidden_and_planned_states_distinct(self) -> None:
        report = build_report(generated_at="2026-07-06T00:00:00+00:00")
        pair_support = report["pair_support"]
        en_es = pair_support["en-es"]
        en_de = pair_support["en-de"]

        self.assertIn("animals", en_es["picker_supported_topics"])
        self.assertIn("plants_nature", en_es["picker_supported_topics"])
        self.assertIn("travel_places_transport", en_es["picker_supported_topics"])
        self.assertIn("computing_internet", en_es["picker_supported_topics"])
        self.assertIn("science_math", en_es["picker_supported_topics"])
        self.assertIn("anime_manga_pop_culture", en_es["hidden_overlay_topics"])
        self.assertIn("sat_toefl_exam_prep", en_es["not_applicable_topics"])
        self.assertIn("casual_slang_register", en_es["future_register_topics"])

        self.assertIn("games", en_de["picker_supported_topics"])
        self.assertIn("computing_internet", en_de["hidden_overlay_topics"])
        self.assertIn("hobbies_crafts", en_de["hidden_overlay_topics"])
        self.assertIn("plants_nature", en_de["hidden_overlay_topics"])
        self.assertIn("science_math", en_de["hidden_overlay_topics"])
        self.assertIn("shopping_money", en_de["hidden_overlay_topics"])
        self.assertIn("work_office", en_de["hidden_overlay_topics"])
        self.assertNotIn("computing_internet", en_de["picker_supported_topics"])
        self.assertIn("food_cooking", en_de["planned_source_required_topics"])

        markdown = render_markdown(report)
        self.assertIn("| `en-es` | 17 | 1 | 0 | 2 | 1 |", markdown)
        self.assertIn("| `en-de` | 9 | 6 | 3 | 2 | 1 |", markdown)


if __name__ == "__main__":
    unittest.main()
