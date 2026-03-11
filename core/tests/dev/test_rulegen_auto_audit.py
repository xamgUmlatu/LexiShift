from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_auto_audit import (  # noqa: E402
    BENCHMARKABLE_PAIRS,
    _build_artifact_paths,
    _infer_pairs,
    _parse_pairs,
)


class TestRulegenAutoAudit(unittest.TestCase):
    def test_parse_pairs_normalizes_and_deduplicates(self) -> None:
        self.assertEqual(_parse_pairs("en-es, en-ja,EN-ES"), ["en-es", "en-ja"])

    def test_infer_pairs_from_pair_specific_path(self) -> None:
        pairs = _infer_pairs(["core/lexishift_core/rulegen/pairs/en_es.py"])
        self.assertEqual(pairs, ["en-es"])

    def test_infer_pairs_from_generic_quality_path_expands_all_pairs(self) -> None:
        pairs = _infer_pairs(["core/lexishift_core/rulegen/ranking.py"])
        self.assertEqual(pairs, list(BENCHMARKABLE_PAIRS))

    def test_infer_pairs_ignores_meta_only_paths(self) -> None:
        pairs = _infer_pairs(
            [
                "docs/developer/feature_state_matrix.md",
                "scripts/testing/rulegen_auto_audit.py",
                "scripts/testing/rulegen_pair_audit_cycle.py",
            ]
        )
        self.assertEqual(pairs, [])

    def test_build_artifact_paths_uses_dated_and_latest_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _build_artifact_paths(
                output_dir=Path(tmp),
                pair_suffix="en_es",
                date_stamp="2026-03-11",
            )
            self.assertEqual(
                paths["benchmark_json_dated"].name,
                "rulegen_benchmark_en_es_2026-03-11.json",
            )
            self.assertEqual(
                paths["quality_gate_json_latest"].name,
                "rulegen_quality_gate_en_es_latest.json",
            )
            self.assertEqual(
                paths["manifest_json_dated"].name,
                "rulegen_auto_audit_en_es_2026-03-11.json",
            )


if __name__ == "__main__":
    unittest.main()
