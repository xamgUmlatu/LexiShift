from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_quality_gate_validators import validate_dataset_contract  # noqa: E402


class TestRulegenQualityGateValidators(unittest.TestCase):
    def test_dataset_contract_scopes_minima_to_benchmarked_pairs(self) -> None:
        findings: list[object] = []
        validate_dataset_contract(
            dataset_payload={
                "cases": [
                    {
                        "case_id": "en-ja:本",
                        "pair": "en-ja",
                        "target": "本",
                        "tier": "hard",
                        "expected_any": ["book"],
                        "expected_top1_any": ["book"],
                        "forbidden_top1": [],
                        "forbidden_any": [],
                    },
                    {
                        "case_id": "en-ja:犬",
                        "pair": "en-ja",
                        "target": "犬",
                        "tier": "smoke",
                        "expected_any": ["dog"],
                        "expected_top1_any": ["dog"],
                        "forbidden_top1": [],
                        "forbidden_any": [],
                    },
                ]
            },
            policy_payload={
                "dataset_contract": {
                    "required_case_fields": [
                        "case_id",
                        "pair",
                        "target",
                        "expected_any",
                        "expected_top1_any",
                        "forbidden_top1",
                        "forbidden_any",
                        "tier",
                    ],
                    "allowed_tiers": ["smoke", "hard"],
                    "min_cases_per_pair": {"en-es": 2, "en-ja": 2},
                    "min_hard_cases_per_pair": {"en-es": 1, "en-ja": 1},
                }
            },
            findings=findings,  # type: ignore[arg-type]
            benchmark_pairs={"en-ja"},
        )

        finding_map = {finding.code: finding for finding in findings}  # type: ignore[attr-defined]
        self.assertEqual(finding_map["DATASET_MIN_CASES"].level, "PASS")
        self.assertEqual(finding_map["DATASET_MIN_HARD_CASES"].level, "PASS")

    def test_dataset_contract_fails_when_benchmarked_pair_is_below_minimum(self) -> None:
        findings: list[object] = []
        validate_dataset_contract(
            dataset_payload={
                "cases": [
                    {
                        "case_id": "en-ja:本",
                        "pair": "en-ja",
                        "target": "本",
                        "tier": "smoke",
                        "expected_any": ["book"],
                        "expected_top1_any": ["book"],
                        "forbidden_top1": [],
                        "forbidden_any": [],
                    }
                ]
            },
            policy_payload={
                "dataset_contract": {
                    "required_case_fields": [
                        "case_id",
                        "pair",
                        "target",
                        "expected_any",
                        "expected_top1_any",
                        "forbidden_top1",
                        "forbidden_any",
                        "tier",
                    ],
                    "allowed_tiers": ["smoke", "hard"],
                    "min_cases_per_pair": {"en-ja": 2},
                    "min_hard_cases_per_pair": {"en-ja": 1},
                }
            },
            findings=findings,  # type: ignore[arg-type]
            benchmark_pairs={"en-ja"},
        )

        finding_map = {finding.code: finding for finding in findings}  # type: ignore[attr-defined]
        self.assertEqual(finding_map["DATASET_MIN_CASES"].level, "FAIL")
        self.assertEqual(finding_map["DATASET_MIN_HARD_CASES"].level, "FAIL")


if __name__ == "__main__":
    unittest.main()
