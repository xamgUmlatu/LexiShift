from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_rulegen_lp_conformance import validate_rulegen_lp_conformance  # noqa: E402


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class TestCheckRulegenLpConformance(unittest.TestCase):
    def test_validate_rulegen_lp_conformance_passes_for_aligned_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_json(
                root / "docs" / "test_inputs" / "rulegen_lp_profiles" / "en_fr.json",
                {
                    "version": 1,
                    "pair": "en-fr",
                    "languages": {"source": "en", "target": "fr"},
                    "translation_lanes": [],
                    "reverse_lanes": [],
                    "pos_profile": {},
                    "normalization_profile": {},
                    "metadata_family_profile": {},
                    "morphology_profile": {},
                    "mechanism_support": {},
                    "benchmark_profile": {
                        "case_file": "docs/test_inputs/rulegen_benchmark_cases/en_fr.json",
                        "preset_name": "en_fr_canonical_matrix",
                        "wrapper_command": "python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs en-fr",
                        "latest_benchmark_json": "docs/test_outputs/rulegen_benchmark_en_fr_latest.json",
                    },
                },
            )
            _write_json(
                root / "docs" / "test_inputs" / "rulegen_benchmark_cases" / "en_fr.json",
                {"version": 1, "pair": "en-fr", "cases": []},
            )
            _write_json(
                root / "docs" / "test_outputs" / "rulegen_benchmark_en_fr_latest.json",
                {"pairs": {"en-fr": {"best_run": {}}}},
            )
            _write_json(
                root / "docs" / "test_inputs" / "rulegen_benchmark_presets.json",
                {
                    "version": 1,
                    "presets": {
                        "en_fr_canonical_matrix": {
                            "description": "starter",
                            "args": ["--pairs", "en-fr", "--max-configurations", "10"],
                        }
                    },
                },
            )
            pair_module = root / "core" / "lexishift_core" / "rulegen" / "pairs" / "en_fr.py"
            pair_module.parent.mkdir(parents=True, exist_ok=True)
            pair_module.write_text(
                "class EnFrRulegenConfig:\n"
                "    pass\n\n"
                "def generate_en_fr_results():\n"
                "    pass\n\n"
                "def generate_en_fr_rules():\n"
                "    pass\n",
                encoding="utf-8",
            )
            pairs_init = root / "core" / "lexishift_core" / "rulegen" / "pairs" / "__init__.py"
            pairs_init.write_text(
                "from lexishift_core.rulegen.pairs.en_fr import (\n"
                "    EnFrRulegenConfig,\n"
                "    generate_en_fr_results,\n"
                "    generate_en_fr_rules,\n"
                ")\n\n"
                '__all__ = ["EnFrRulegenConfig", "generate_en_fr_results", "generate_en_fr_rules"]\n',
                encoding="utf-8",
            )
            adapters = root / "core" / "lexishift_core" / "rulegen" / "adapters.py"
            adapters.write_text(
                "from lexishift_core.rulegen.pairs.en_fr import EnFrRulegenConfig, generate_en_fr_results\n\n"
                "def _run_en_fr_adapter():\n"
                "    return generate_en_fr_results()\n\n"
                '_RULEGEN_ADAPTERS = {"en_fr": _run_en_fr_adapter}\n',
                encoding="utf-8",
            )
            capabilities = root / "core" / "lexishift_core" / "helper" / "lp_capabilities.py"
            capabilities.parent.mkdir(parents=True, exist_ok=True)
            capabilities.write_text(
                '_PAIR_CAPABILITIES = {"en-fr": PairCapability(pair="en-fr", rulegen_mode="en_fr")}\n',
                encoding="utf-8",
            )

            payload = validate_rulegen_lp_conformance(project_root=root)

            self.assertEqual(payload["checked_profiles"], 1)
            self.assertEqual(payload["issues"], [])

    def test_validate_rulegen_lp_conformance_flags_pair_alignment_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_json(
                root / "docs" / "test_inputs" / "rulegen_lp_profiles" / "en_fr.json",
                {
                    "version": 1,
                    "pair": "en-fr",
                    "languages": {"source": "en", "target": "fr"},
                    "translation_lanes": [],
                    "reverse_lanes": [],
                    "pos_profile": {},
                    "normalization_profile": {},
                    "metadata_family_profile": {},
                    "morphology_profile": {},
                    "mechanism_support": {},
                    "benchmark_profile": {
                        "case_file": "docs/test_inputs/rulegen_benchmark_cases/en_fr.json",
                        "preset_name": "en_fr_canonical_matrix",
                        "wrapper_command": "python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs en-de",
                        "latest_benchmark_json": "docs/test_outputs/rulegen_benchmark_en_fr_latest.json",
                    },
                },
            )
            _write_json(
                root / "docs" / "test_inputs" / "rulegen_benchmark_cases" / "en_fr.json",
                {"version": 1, "pair": "en-fr", "cases": []},
            )
            _write_json(
                root / "docs" / "test_outputs" / "rulegen_benchmark_en_fr_latest.json",
                {"pairs": {"en-de": {}}},
            )
            _write_json(
                root / "docs" / "test_inputs" / "rulegen_benchmark_presets.json",
                {
                    "version": 1,
                    "presets": {
                        "en_fr_canonical_matrix": {
                            "description": "starter",
                            "args": ["--pairs", "en-de", "--max-configurations", "10"],
                        }
                    },
                },
            )
            pair_module = root / "core" / "lexishift_core" / "rulegen" / "pairs" / "en_fr.py"
            pair_module.parent.mkdir(parents=True, exist_ok=True)
            pair_module.write_text(
                "class EnFrRulegenConfig:\n    pass\n\ndef generate_en_fr_rules():\n    pass\n",
                encoding="utf-8",
            )
            pairs_init = root / "core" / "lexishift_core" / "rulegen" / "pairs" / "__init__.py"
            pairs_init.write_text(
                "__all__ = []\n",
                encoding="utf-8",
            )
            adapters = root / "core" / "lexishift_core" / "rulegen" / "adapters.py"
            adapters.write_text(
                "_RULEGEN_ADAPTERS = {}\n",
                encoding="utf-8",
            )
            capabilities = root / "core" / "lexishift_core" / "helper" / "lp_capabilities.py"
            capabilities.parent.mkdir(parents=True, exist_ok=True)
            capabilities.write_text(
                "_PAIR_CAPABILITIES = {}\n",
                encoding="utf-8",
            )

            payload = validate_rulegen_lp_conformance(project_root=root)

            issues = payload["issues"]
            self.assertTrue(any(issue["code"] == "PRESET_PAIR_MISMATCH" for issue in issues))
            self.assertTrue(
                any(issue["code"] == "LATEST_BENCHMARK_PAIR_MISMATCH" for issue in issues)
            )
            self.assertTrue(
                any(issue["code"] == "WRAPPER_COMMAND_PAIR_MISMATCH" for issue in issues)
            )
            self.assertTrue(any(issue["code"] == "PAIR_MODULE_RESULTS_MISSING" for issue in issues))
            self.assertTrue(
                any(issue["code"] == "PAIRS_INIT_CONFIG_EXPORT_MISSING" for issue in issues)
            )
            self.assertTrue(
                any(issue["code"] == "ADAPTERS_REGISTRATION_MISSING" for issue in issues)
            )
            self.assertTrue(
                any(issue["code"] == "PAIR_CAPABILITY_ENTRY_MISSING" for issue in issues)
            )


if __name__ == "__main__":
    unittest.main()
