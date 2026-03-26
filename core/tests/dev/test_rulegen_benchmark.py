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

from rulegen_benchmark import (  # noqa: E402
    SweepConfig,
    SweepRun,
    _build_pair_resources_payload,
    _build_pair_report_payload,
    _build_word_package_snapshot,
    _format_exact_hit_ambiguity_label,
    _format_exact_hit_specificity_label,
    _format_kaikki_policy_family_label,
    _load_frozen_word_package_snapshots,
    _load_html_report_renderer,
    _parse_family_set_specs,
    _resolve_cli_with_preset,
    _resolve_pair_resources_for_benchmark,
)
from rulegen_benchmark_presets import (  # noqa: E402
    format_benchmark_presets_listing,
    load_benchmark_presets,
)
from lexishift_core.rulegen.benchmarking import RulegenBenchmarkSummary  # noqa: E402


class _FakePaths:
    def __init__(self, language_packs_dir: Path) -> None:
        self.language_packs_dir = language_packs_dir
        self.frequency_packs_dir = language_packs_dir


class TestRulegenBenchmark(unittest.TestCase):
    def test_load_html_report_renderer_returns_callable(self) -> None:
        renderer = _load_html_report_renderer()
        self.assertTrue(callable(renderer))

    def test_resolve_pair_resources_includes_reverse_freedict_for_en_es(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            forward = language_packs_dir / "spa-eng.tei"
            reverse = language_packs_dir / "eng-spa.tei"
            forward.write_text("forward", encoding="utf-8")
            reverse.write_text("reverse", encoding="utf-8")

            jmdict_path, freedict_path, reverse_path = _resolve_pair_resources_for_benchmark(
                paths=_FakePaths(language_packs_dir),
                pair="en-es",
                jmdict_override=None,
                freedict_override=forward,
                freedict_reverse_override=None,
            )

            self.assertIsNone(jmdict_path)
            self.assertEqual(freedict_path, forward)
            self.assertEqual(reverse_path, reverse)

    def test_parse_family_set_specs_supports_multiple_sets(self) -> None:
        parsed = _parse_family_set_specs(
            "math_geometry+government_law;none;register_region,hunting_fishing_tools",
            name="kaikki-policy-risk-family-sets",
        )

        self.assertEqual(
            parsed,
            [
                ("math_geometry", "government_law"),
                (),
                ("register_region", "hunting_fishing_tools"),
            ],
        )

    def test_format_kaikki_policy_family_label_uses_short_codes(self) -> None:
        label = _format_kaikki_policy_family_label(
            ("math_geometry", "government_law", "register_region")
        )

        self.assertEqual(label, "mg+gl+rr")

    def test_format_exact_hit_ambiguity_label_uses_threshold_and_penalty(self) -> None:
        config = SweepConfig(
            max_definitions_per_target=3,
            max_rules_per_target=None,
            confidence_threshold=0.0,
            semantic_demotion_scale=1.0,
            include_variants=False,
            pos_scoring_enabled=True,
            pos_exact_match_bonus=1.0,
            pos_compatible_match_bonus=0.5,
            score_weight_dict_priority=0.6,
            score_weight_frequency_weight=0.2,
            score_weight_pos_match=0.1,
            score_weight_variant_penalty=0.1,
            score_weight_phrase_penalty=0.1,
            score_weight_embedding=0.2,
            reverse_check_enabled=True,
            reverse_check_match_bonus=0.2,
            reverse_check_near_bonus=0.1,
            reverse_check_near_rank_max=2,
            reverse_check_far_hit_penalty=0.0,
            reverse_check_miss_penalty=0.2,
            reverse_check_exact_hit_ambiguity_threshold=12,
            reverse_check_exact_hit_ambiguity_penalty=0.4,
            kaikki_policy_live_demotion=False,
            kaikki_policy_risk_families=(),
        )

        self.assertEqual(_format_exact_hit_ambiguity_label(config), "12:0.40")

    def test_format_exact_hit_specificity_label_uses_bonus(self) -> None:
        config = SweepConfig(
            max_definitions_per_target=3,
            max_rules_per_target=None,
            confidence_threshold=0.0,
            semantic_demotion_scale=1.0,
            include_variants=False,
            pos_scoring_enabled=True,
            pos_exact_match_bonus=1.0,
            pos_compatible_match_bonus=0.5,
            score_weight_dict_priority=0.6,
            score_weight_frequency_weight=0.2,
            score_weight_pos_match=0.1,
            score_weight_variant_penalty=0.1,
            score_weight_phrase_penalty=0.1,
            score_weight_embedding=0.2,
            reverse_check_enabled=True,
            reverse_check_match_bonus=0.2,
            reverse_check_near_bonus=0.1,
            reverse_check_near_rank_max=2,
            reverse_check_far_hit_penalty=0.0,
            reverse_check_miss_penalty=0.2,
            reverse_check_exact_hit_ambiguity_threshold=0,
            reverse_check_exact_hit_ambiguity_penalty=0.0,
            kaikki_policy_live_demotion=False,
            kaikki_policy_risk_families=(),
            reverse_check_exact_hit_specificity_bonus=0.15,
        )

        self.assertEqual(_format_exact_hit_specificity_label(config), "0.15")

    def test_build_pair_report_payload_mirrors_pair_resources(self) -> None:
        run = SweepRun(
            pair="en-es",
            run_index=1,
            config=SweepConfig(
                max_definitions_per_target=3,
                max_rules_per_target=None,
                confidence_threshold=0.0,
                semantic_demotion_scale=1.0,
                include_variants=False,
                pos_scoring_enabled=True,
                pos_exact_match_bonus=1.0,
                pos_compatible_match_bonus=0.5,
                score_weight_dict_priority=0.6,
                score_weight_frequency_weight=0.2,
                score_weight_pos_match=0.1,
                score_weight_variant_penalty=0.1,
                score_weight_phrase_penalty=0.1,
                score_weight_embedding=0.2,
                reverse_check_enabled=True,
                reverse_check_match_bonus=0.2,
                reverse_check_near_bonus=0.1,
                reverse_check_near_rank_max=2,
                reverse_check_far_hit_penalty=0.0,
                reverse_check_miss_penalty=0.2,
                reverse_check_exact_hit_ambiguity_threshold=0,
                reverse_check_exact_hit_ambiguity_penalty=0.0,
                kaikki_policy_live_demotion=False,
                kaikki_policy_risk_families=(),
            ),
            summary=RulegenBenchmarkSummary(
                pair="en-es",
                case_count=1,
                top1_correct_count=1,
                top3_contains_expected_count=1,
                forbidden_top1_count=0,
                forbidden_any_count=0,
                avg_rules_per_target=1.0,
                avg_top1_confidence=0.5,
                variant_rule_count=0,
                total_rule_count=1,
                variant_top1_count=0,
                top1_accuracy=1.0,
                top3_recall=1.0,
                forbidden_top1_rate=0.0,
                forbidden_any_rate=0.0,
                variant_rule_rate=0.0,
                variant_top1_rate=0.0,
                objective_score=100.0,
            ),
            case_results=(
                {
                    "case_id": "en-es:test",
                    "pair": "en-es",
                    "target": "casa",
                    "rule_count": 1,
                    "top1_source": "house",
                    "top3_sources": ["house"],
                    "all_sources": ["house"],
                    "top1_confidence": 0.5,
                    "top1_correct": True,
                    "top3_contains_expected": True,
                    "top1_forbidden": False,
                    "forbidden_any_present": False,
                    "variant_rule_count": 0,
                    "top1_is_variant": False,
                    "expected_matches": ["house"],
                    "forbidden_matches": [],
                },
            ),
        )

        payload = _build_pair_report_payload(
            case_count=1,
            runs=[run],
            resources={
                "translation_dict_path": "/tmp/wiktionary-es-en.sqlite",
                "reverse_translation_dict_path": "/tmp/wiktionary-en-es.sqlite",
            },
            word_package_snapshot={"casa": None},
            include_case_results=False,
        )

        self.assertEqual(
            payload["resources"]["translation_dict_path"],
            "/tmp/wiktionary-es-en.sqlite",
        )
        self.assertEqual(
            payload["resources"]["reverse_translation_dict_path"],
            "/tmp/wiktionary-en-es.sqlite",
        )
        self.assertIn("best_run", payload)
        self.assertEqual(payload["run_count"], 1)
        self.assertEqual(payload["word_package_snapshot"]["casa"], None)

    def test_build_pair_resources_payload_includes_sha256_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forward = root / "forward.sqlite"
            reverse = root / "reverse.sqlite"
            forward.write_text("forward", encoding="utf-8")
            reverse.write_text("reverse", encoding="utf-8")

            payload = _build_pair_resources_payload(
                jmdict_path=None,
                translation_dict_path=forward,
                reverse_translation_dict_path=reverse,
            )

            self.assertEqual(payload["translation_dict_path"], str(forward))
            self.assertEqual(payload["reverse_translation_dict_path"], str(reverse))
            checksums = payload["checksums"]
            self.assertTrue(str(checksums["translation_dict_sha256"]).startswith("sha256:"))
            self.assertTrue(str(checksums["reverse_translation_dict_sha256"]).startswith("sha256:"))
            self.assertIsNone(checksums["jmdict_sha256"])

    def test_build_word_package_snapshot_preserves_missing_targets_as_null(self) -> None:
        snapshot = _build_word_package_snapshot(
            targets=["casa", "madre"],
            word_packages_by_target={
                "casa": {
                    "version": 1,
                    "language_tag": "es",
                    "surface": "casa",
                    "reading": "casa",
                    "script_forms": {"default": "casa"},
                    "source": {"provider": "test"},
                }
            },
        )

        self.assertIsInstance(snapshot["casa"], dict)
        self.assertEqual(snapshot["casa"]["surface"], "casa")
        self.assertIsNone(snapshot["madre"])

    def test_load_benchmark_presets_includes_canonical_en_es_matrix(self) -> None:
        presets = load_benchmark_presets(
            REPO_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"
        )

        self.assertIn("en_es_canonical_matrix", presets)
        listing = format_benchmark_presets_listing(presets)
        self.assertIn("en_es_canonical_matrix", listing)

    def test_resolve_cli_with_preset_allows_explicit_cli_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            preset_file = Path(tmp) / "presets.json"
            preset_file.write_text(
                (
                    "{"
                    '"presets":{"tiny":{"description":"tiny preset","args":["--pairs","en-es","--max-configurations","8"]}}'
                    "}"
                ),
                encoding="utf-8",
            )

            args, preset = _resolve_cli_with_preset(
                argv=(
                    "--preset-file",
                    str(preset_file),
                    "--preset",
                    "tiny",
                    "--pairs",
                    "es-en",
                )
            )

            self.assertEqual(args.pairs, "es-en")
            self.assertEqual(args.max_configurations, 8)
            self.assertIsNotNone(preset)
            assert preset is not None
            self.assertEqual(preset.name, "tiny")

    def test_load_frozen_word_package_snapshots_supports_bundle_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload_path = Path(tmp) / "snapshot.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "pairs": {
                            "en-es": {
                                "casa": {
                                    "version": 1,
                                    "language_tag": "es",
                                    "surface": "casa",
                                    "reading": "casa",
                                    "script_forms": {"default": "casa"},
                                    "source": {"provider": "bundle"},
                                },
                                "agua": None,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            snapshots = _load_frozen_word_package_snapshots(payload_path)

            self.assertIn("en-es", snapshots)
            self.assertEqual(snapshots["en-es"]["casa"]["surface"], "casa")
            self.assertIsNone(snapshots["en-es"]["agua"])

    def test_load_frozen_word_package_snapshots_supports_benchmark_report_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload_path = Path(tmp) / "report.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "pairs": {
                            "en-es": {
                                "word_package_snapshot": {
                                    "madre": {
                                        "version": 1,
                                        "language_tag": "es",
                                        "surface": "madre",
                                        "reading": "madre",
                                        "script_forms": {"default": "madre"},
                                        "source": {"provider": "report"},
                                    }
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            snapshots = _load_frozen_word_package_snapshots(payload_path)

            self.assertEqual(snapshots["en-es"]["madre"]["surface"], "madre")


if __name__ == "__main__":
    unittest.main()
