from __future__ import annotations

from pathlib import Path
import sys
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_support import (  # noqa: E402
    build_sentence_veto_ladder_report,
)


class SemanticRoutingSentenceVetoLadderTests(unittest.TestCase):
    def test_best_zero_noise_soft_ladder_on_current_dataset(self) -> None:
        report = build_sentence_veto_ladder_report(
            dataset_path=REPO_ROOT
            / "docs"
            / "test_inputs"
            / "semantic_routing_cases"
            / "en_es_sentence_veto_v10.json",
        )
        self.assertEqual(int(report["base_summary"]["harmful_replace_count"]), 1)
        self.assertEqual(int(report["base_summary"]["false_abstain_count"]), 9)
        best_budget_rows = {
            int(entry.get("soft_false_positive_budget") or 0): entry.get("row")
            for entry in report.get("best_rows_by_soft_false_positive_budget", [])
            if isinstance(entry, dict)
        }
        zero_noise_row = best_budget_rows[0]
        self.assertIsInstance(zero_noise_row, dict)
        self.assertEqual(str(zero_noise_row["config_id"]), "soft:a=0.60:m=0.00")
        self.assertEqual(int(zero_noise_row["soft_false_positive_count"]), 0)
        self.assertEqual(int(zero_noise_row["soft_true_positive_count"]), 0)
        self.assertEqual(int(zero_noise_row["remaining_missed_replace_count"]), 9)
        self.assertAlmostEqual(float(zero_noise_row["replace_or_soft_recall"]), 29 / 38)
        self.assertAlmostEqual(float(zero_noise_row["replace_or_soft_recall_lift"]), 0.0)
        soft_samples = zero_noise_row.get("sample_soft_true_positive_rows")
        self.assertEqual(list(soft_samples), [])


if __name__ == "__main__":
    unittest.main()
