from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_benchmark_presets import load_benchmark_presets  # noqa: E402


class TestRulegenBenchmarkPresetRegistry(unittest.TestCase):
    def test_en_ja_canonical_matrix_is_registered(self) -> None:
        presets = load_benchmark_presets(
            REPO_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"
        )

        self.assertIn("en_ja_canonical_matrix", presets)
        preset = presets["en_ja_canonical_matrix"]
        self.assertIn("--pairs", preset.args)
        self.assertIn("en-ja", preset.args)
        self.assertIn("--dataset", preset.args)
        self.assertIn("docs/test_inputs/rulegen_benchmark_cases/en_ja.json", preset.args)
        self.assertIn("--max-definitions-values", preset.args)
        self.assertIn("1,2,3", preset.args)
        self.assertIn("--max-rules-values", preset.args)
        self.assertIn("1,none", preset.args)
        self.assertIn("--reverse-check-enabled-values", preset.args)
        self.assertIn("--kaikki-policy-live-demotion-values", preset.args)
        self.assertIn("--kaikki-policy-risk-family-demotion-sets", preset.args)
        self.assertIn("false", preset.args)
        self.assertIn("none", preset.args)

    def test_en_es_canonical_matrix_uses_pair_local_dataset(self) -> None:
        presets = load_benchmark_presets(
            REPO_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"
        )

        self.assertIn("en_es_canonical_matrix", presets)
        preset = presets["en_es_canonical_matrix"]
        self.assertIn("--dataset", preset.args)
        self.assertIn("docs/test_inputs/rulegen_benchmark_cases/en_es.json", preset.args)


if __name__ == "__main__":
    unittest.main()
