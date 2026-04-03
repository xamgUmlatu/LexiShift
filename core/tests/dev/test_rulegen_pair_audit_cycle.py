from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_pair_audit_cycle import _build_cycle_commands  # noqa: E402


class TestRulegenPairAuditCycle(unittest.TestCase):
    def test_build_cycle_commands_uses_compute_then_render_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benchmark_json = root / "benchmark.json"
            benchmark_md = root / "benchmark.md"
            benchmark_html = root / "benchmark.html"
            gate_json = root / "gate.json"
            triage_json = root / "triage.json"
            triage_md = root / "triage.md"
            policy_json = root / "policy.json"
            baseline_json = root / "baseline.json"
            pos_probe_json = root / "pos_probe.json"
            pos_inventory_json = root / "pos_inventory.json"

            benchmark_cmd, render_cmd, gate_cmd, triage_cmd = _build_cycle_commands(
                pairs=["en-es", "en-ja"],
                benchmark_preset=None,
                quality_gate_pair_scope=None,
                max_definitions_values="3",
                max_rules_values="none,1",
                confidence_threshold_values="0.0,0.05",
                semantic_demotion_scale_values="1.0",
                include_variants_values="false",
                pos_scoring_values="true,false",
                score_weight_pos_values="0.0,0.1",
                reverse_enabled_values="false,true",
                reverse_match_bonus_values="0.2",
                reverse_near_bonus_values="0.1",
                reverse_near_rank_max_values="2",
                reverse_far_hit_penalty_values="0.0",
                reverse_miss_penalty_values="0.2",
                top_runs=20,
                max_configurations=100,
                benchmark_json=benchmark_json,
                benchmark_markdown=benchmark_md,
                benchmark_html=benchmark_html,
                quality_gate_json=gate_json,
                triage_json=triage_json,
                triage_markdown=triage_md,
                policy_json=policy_json,
                baseline_json=baseline_json,
                pos_probe_json=pos_probe_json,
                pos_inventory_json=pos_inventory_json,
            )

        self.assertIn("--compute-only", benchmark_cmd)
        self.assertIn("--render-from-json", render_cmd)
        self.assertEqual(
            render_cmd[render_cmd.index("--render-from-json") + 1],
            str(benchmark_json),
        )
        self.assertEqual(
            gate_cmd[gate_cmd.index("--benchmark-json") + 1],
            str(benchmark_json),
        )
        self.assertEqual(
            triage_cmd[triage_cmd.index("--benchmark-json") + 1],
            str(benchmark_json),
        )

    def test_build_cycle_commands_preserves_report_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benchmark_cmd, render_cmd, _, triage_cmd = _build_cycle_commands(
                pairs=["en-es"],
                benchmark_preset=None,
                quality_gate_pair_scope=None,
                max_definitions_values="3",
                max_rules_values="none",
                confidence_threshold_values="0.0",
                semantic_demotion_scale_values="1.0",
                include_variants_values="false",
                pos_scoring_values="true",
                score_weight_pos_values="0.1",
                reverse_enabled_values="true",
                reverse_match_bonus_values="0.2",
                reverse_near_bonus_values="0.1",
                reverse_near_rank_max_values="2",
                reverse_far_hit_penalty_values="0.0",
                reverse_miss_penalty_values="0.2",
                top_runs=5,
                max_configurations=8,
                benchmark_json=root / "bench.json",
                benchmark_markdown=root / "bench.md",
                benchmark_html=root / "bench.html",
                quality_gate_json=root / "gate.json",
                triage_json=root / "triage.json",
                triage_markdown=root / "triage.md",
                policy_json=root / "policy.json",
                baseline_json=root / "baseline.json",
                pos_probe_json=root / "probe.json",
                pos_inventory_json=root / "inventory.json",
            )

        self.assertEqual(
            benchmark_cmd[benchmark_cmd.index("--json-output") + 1],
            str(root / "bench.json"),
        )
        self.assertEqual(
            render_cmd[render_cmd.index("--markdown-output") + 1],
            str(root / "bench.md"),
        )
        self.assertEqual(
            render_cmd[render_cmd.index("--html-output") + 1],
            str(root / "bench.html"),
        )
        self.assertEqual(
            triage_cmd[triage_cmd.index("--markdown-out") + 1],
            str(root / "triage.md"),
        )

    def test_build_cycle_commands_allows_scoped_quality_gate_and_benchmark_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benchmark_cmd, _render_cmd, gate_cmd, _triage_cmd = _build_cycle_commands(
                pairs=["en-de"],
                benchmark_preset="en_de_canonical_matrix",
                quality_gate_pair_scope="en-de",
                max_definitions_values="3",
                max_rules_values="none",
                confidence_threshold_values="0.0",
                semantic_demotion_scale_values="1.0",
                include_variants_values="false",
                pos_scoring_values="true",
                score_weight_pos_values="0.0",
                reverse_enabled_values="false",
                reverse_match_bonus_values="0.2",
                reverse_near_bonus_values="0.1",
                reverse_near_rank_max_values="2",
                reverse_far_hit_penalty_values="0.0",
                reverse_miss_penalty_values="0.2",
                top_runs=5,
                max_configurations=8,
                benchmark_json=root / "bench.json",
                benchmark_markdown=root / "bench.md",
                benchmark_html=root / "bench.html",
                quality_gate_json=root / "gate.json",
                triage_json=root / "triage.json",
                triage_markdown=root / "triage.md",
                policy_json=root / "policy.json",
                baseline_json=root / "baseline.json",
                pos_probe_json=root / "probe.json",
                pos_inventory_json=root / "inventory.json",
            )

        self.assertIn("--preset", benchmark_cmd)
        self.assertEqual(
            benchmark_cmd[benchmark_cmd.index("--preset") + 1],
            "en_de_canonical_matrix",
        )
        self.assertIn("--pair-scope", gate_cmd)
        self.assertEqual(
            gate_cmd[gate_cmd.index("--pair-scope") + 1],
            "en-de",
        )


if __name__ == "__main__":
    unittest.main()
