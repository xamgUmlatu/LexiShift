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

from rulegen_benchmark_case_sync import (  # noqa: E402
    merge_pair_files_to_aggregate,
    split_aggregate_to_pair_files,
)


class TestRulegenBenchmarkCaseSync(unittest.TestCase):
    def test_split_writes_pair_local_files_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aggregate_path = root / "rulegen_benchmark_cases.json"
            aggregate_path.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "name": "Benchmark Cases",
                        "description": "aggregate",
                        "breadth": "v2",
                        "cases": [
                            {
                                "case_id": "en-es:casa",
                                "pair": "en-es",
                                "target": "casa",
                                "tier": "smoke",
                                "expected_any": ["house"],
                                "expected_top1_any": ["house"],
                                "forbidden_top1": [],
                                "forbidden_any": [],
                            },
                            {
                                "case_id": "en-ja:本",
                                "pair": "en-ja",
                                "target": "本",
                                "tier": "hard",
                                "expected_any": ["book"],
                                "expected_top1_any": ["book"],
                                "forbidden_top1": [],
                                "forbidden_any": ["jeans"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            manifest_path = split_aggregate_to_pair_files(
                aggregate_path=aggregate_path,
                split_dir=root / "split",
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["pair_order"], ["en-es", "en-ja"])
            self.assertTrue((root / "split" / "en_es.json").exists())
            self.assertTrue((root / "split" / "en_ja.json").exists())

            en_ja_payload = json.loads((root / "split" / "en_ja.json").read_text(encoding="utf-8"))
            self.assertEqual(en_ja_payload["pair"], "en-ja")
            self.assertEqual(en_ja_payload["case_count"], 1)
            self.assertEqual(en_ja_payload["cases"][0]["case_id"], "en-ja:本")

    def test_merge_rebuilds_aggregate_from_pair_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            split_dir = root / "split"
            split_dir.mkdir(parents=True, exist_ok=True)
            (split_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "aggregate_path": "docs/test_inputs/rulegen_benchmark_cases.json",
                        "aggregate_metadata": {
                            "version": 2,
                            "name": "Benchmark Cases",
                            "description": "aggregate",
                            "breadth": "v2",
                        },
                        "pair_order": ["en-es", "en-ja"],
                        "pairs": {
                            "en-es": {"file": "en_es.json", "case_count": 1},
                            "en-ja": {"file": "en_ja.json", "case_count": 1},
                        },
                    }
                ),
                encoding="utf-8",
            )
            (split_dir / "en_es.json").write_text(
                json.dumps(
                    {
                        "pair": "en-es",
                        "cases": [
                            {
                                "case_id": "en-es:casa",
                                "pair": "en-es",
                                "target": "casa",
                                "tier": "smoke",
                                "expected_any": ["house"],
                                "expected_top1_any": ["house"],
                                "forbidden_top1": [],
                                "forbidden_any": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (split_dir / "en_ja.json").write_text(
                json.dumps(
                    {
                        "pair": "en-ja",
                        "cases": [
                            {
                                "case_id": "en-ja:本",
                                "pair": "en-ja",
                                "target": "本",
                                "tier": "hard",
                                "expected_any": ["book"],
                                "expected_top1_any": ["book"],
                                "forbidden_top1": [],
                                "forbidden_any": ["jeans"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            aggregate_path = merge_pair_files_to_aggregate(
                split_dir=split_dir,
                aggregate_path=root / "rulegen_benchmark_cases.json",
            )

            aggregate_payload = json.loads(aggregate_path.read_text(encoding="utf-8"))
            self.assertEqual(aggregate_payload["version"], 2)
            self.assertEqual(len(aggregate_payload["cases"]), 2)
            self.assertEqual(aggregate_payload["cases"][0]["case_id"], "en-es:casa")
            self.assertEqual(aggregate_payload["cases"][1]["case_id"], "en-ja:本")


if __name__ == "__main__":
    unittest.main()
