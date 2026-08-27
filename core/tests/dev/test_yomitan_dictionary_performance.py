from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[3]
PERFORMANCE_SCRIPT = REPO_ROOT / "scripts" / "testing" / "yomitan_dictionary_performance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "yomitan_dictionary_performance_test", PERFORMANCE_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {PERFORMANCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestYomitanDictionaryPerformance(unittest.TestCase):
    def test_generated_fixture_exercises_multiple_banks(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "fixture.zip"

            targets = module.write_synthetic_yomitan_archive(
                archive_path,
                bank_count=3,
                terms_per_bank=4,
            )

            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(
                    sorted(archive.namelist()),
                    [
                        "index.json",
                        "term_bank_1.json",
                        "term_bank_2.json",
                        "term_bank_3.json",
                    ],
                )
            self.assertEqual(len(targets), 3)

    def test_small_report_separates_correctness_and_timings(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = module.build_report(
                work_dir=root / "work",
                archive_path=root / "fixture.zip",
                bank_count=2,
                terms_per_bank=5,
                lookup_repetitions=6,
            )

            self.assertEqual(report["fixture"]["term_count"], 10)
            self.assertTrue(all(report["correctness"].values()))
            self.assertEqual(report["timings_ms"]["lookup"]["repetitions"], 6)
            self.assertGreaterEqual(report["timings_ms"]["initial_import"], 0)
            self.assertIn("Third-party data: no", module.render_markdown(report))

    def test_performance_budgets_are_optional_and_independent(self) -> None:
        module = _load_module()
        report = {
            "timings_ms": {
                "initial_import": 20.0,
                "repeat_import": 3.0,
                "lookup": {"p95": 2.0},
                "cancel_after_first_bank": 8.0,
            }
        }
        no_budgets = argparse.Namespace(
            max_import_ms=None,
            max_repeat_import_ms=None,
            max_lookup_p95_ms=None,
            max_cancel_ms=None,
        )
        strict_import = argparse.Namespace(
            max_import_ms=10.0,
            max_repeat_import_ms=None,
            max_lookup_p95_ms=None,
            max_cancel_ms=None,
        )

        self.assertEqual(module.performance_failures(report, no_budgets), [])
        self.assertEqual(
            module.performance_failures(report, strict_import),
            ["initial_import 20.000 ms exceeded 10.000 ms"],
        )

    def test_cli_writes_both_reports_for_small_fixture(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_out = root / "report.json"
            markdown_out = root / "report.md"

            exit_code = module.main(
                [
                    "--banks",
                    "2",
                    "--terms-per-bank",
                    "4",
                    "--lookup-repetitions",
                    "3",
                    "--json-out",
                    str(json_out),
                    "--markdown-out",
                    str(markdown_out),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(all(json.loads(json_out.read_text())["correctness"].values()))
            self.assertIn("## Timings", markdown_out.read_text())


if __name__ == "__main__":
    unittest.main()
