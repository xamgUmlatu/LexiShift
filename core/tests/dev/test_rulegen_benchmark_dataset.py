from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_benchmark_dataset import (  # noqa: E402
    load_benchmark_dataset,
    materialize_benchmark_dataset,
)


class TestRulegenBenchmarkDataset(unittest.TestCase):
    def test_load_benchmark_dataset_directory_merges_lp_files_and_infers_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_dir = root / "rulegen_benchmark_cases"
            dataset_dir.mkdir()
            (dataset_dir / "en_de.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pair": "en-de",
                        "cases": [
                            {
                                "case_id": "en-de:Haus",
                                "target": "Haus",
                                "expected_any": ["house"],
                                "expected_top1_any": ["house"],
                                "forbidden_top1": [],
                                "forbidden_any": [],
                                "tier": "smoke",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (dataset_dir / "en_es.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pair": "en-es",
                        "cases": [
                            {
                                "case_id": "en-es:casa",
                                "target": "casa",
                                "expected_any": ["house"],
                                "expected_top1_any": ["house"],
                                "forbidden_top1": [],
                                "forbidden_any": [],
                                "tier": "smoke",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload, cases_by_pair = load_benchmark_dataset(
                dataset_dir,
                pair_filter={"en-de"},
            )

            self.assertEqual(payload["source_layout"], "directory")
            self.assertEqual(payload["pairs"], ["en-de", "en-es"])
            raw_cases = payload["cases"]
            self.assertIsInstance(raw_cases, list)
            first_case = raw_cases[0]
            self.assertIsInstance(first_case, dict)
            self.assertEqual(first_case["pair"], "en-de")
            self.assertEqual(sorted(cases_by_pair.keys()), ["en-de"])
            self.assertEqual(cases_by_pair["en-de"][0].pair, "en-de")
            self.assertEqual(cases_by_pair["en-de"][0].target, "Haus")

    def test_materialize_benchmark_dataset_filters_selected_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_dir = root / "rulegen_benchmark_cases"
            dataset_dir.mkdir()
            (dataset_dir / "en_de.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pair": "en-de",
                        "cases": [
                            {
                                "case_id": "en-de:Haus",
                                "target": "Haus",
                                "expected_any": ["house"],
                                "expected_top1_any": ["house"],
                                "forbidden_top1": [],
                                "forbidden_any": [],
                                "tier": "smoke",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (dataset_dir / "en_es.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pair": "en-es",
                        "cases": [
                            {
                                "case_id": "en-es:casa",
                                "target": "casa",
                                "expected_any": ["house"],
                                "expected_top1_any": ["house"],
                                "forbidden_top1": [],
                                "forbidden_any": [],
                                "tier": "smoke",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            materialized = materialize_benchmark_dataset(
                source_path=dataset_dir,
                output_path=root / "merged.json",
                pair_filter={"en-de"},
            )

            payload = json.loads(materialized.read_text(encoding="utf-8"))
            self.assertEqual(payload["pairs"], ["en-de"])
            raw_cases = payload["cases"]
            self.assertEqual(len(raw_cases), 1)
            self.assertEqual(raw_cases[0]["pair"], "en-de")


if __name__ == "__main__":
    unittest.main()
