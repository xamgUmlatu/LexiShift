from __future__ import annotations

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
    _format_exact_hit_ambiguity_label,
    _format_kaikki_policy_family_label,
    _load_html_report_renderer,
    _parse_family_set_specs,
    _resolve_pair_resources_for_benchmark,
)


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


if __name__ == "__main__":
    unittest.main()
