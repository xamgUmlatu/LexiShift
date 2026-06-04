from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import textwrap
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from experiment_payload_retention_audit import (  # noqa: E402
    build_experiment_payload_retention_audit,
    render_experiment_payload_retention_markdown,
)


class ExperimentPayloadRetentionAuditTests(unittest.TestCase):
    def test_classifies_family_reference_postures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_experiment_payload_retention_audit(root)

        families = _families_by_name(report)
        self.assertEqual(families["family_routed"]["retention_posture"], "routed")
        self.assertEqual(
            families["family_generated"]["retention_posture"],
            "generated_linked",
        )
        self.assertEqual(
            families["family_experiment_target"]["retention_posture"],
            "experiment_linked",
        )
        self.assertEqual(
            families["family_self"]["retention_posture"],
            "self_linked_review",
        )
        self.assertEqual(
            families["family_unrouted"]["retention_posture"],
            "unrouted_review",
        )
        self.assertEqual(families["_root_files"]["retention_posture"], "unrouted_review")

    def test_summarizes_counts_and_review_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_experiment_payload_retention_audit(root)

        summary = report["summary"]
        self.assertEqual(summary["family_count"], 7)
        self.assertEqual(summary["routed_family_count"], 1)
        self.assertEqual(summary["generated_linked_family_count"], 1)
        self.assertEqual(summary["experiment_linked_family_count"], 1)
        self.assertEqual(summary["self_linked_review_family_count"], 1)
        self.assertEqual(summary["unrouted_review_family_count"], 3)
        routed = _families_by_name(report)["family_routed"]
        self.assertIn("raw_response_bundle", routed["review_flags"])
        generated = _families_by_name(report)["family_generated"]
        self.assertIn("generated_only_route", generated["review_flags"])

    def test_markdown_renderer_includes_posture_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_experiment_payload_retention_audit(root)
            markdown = render_experiment_payload_retention_markdown(report)

        self.assertIn("# Experiment Payload Retention Audit", markdown)
        self.assertIn("## Family Retention Posture", markdown)
        self.assertIn("family_unrouted", markdown)
        self.assertIn("unrouted_review", markdown)


def _families_by_name(report: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(family["family"]): family for family in report["families"] if isinstance(family, dict)
    }


def _write_fixture_tree(root: Path) -> None:
    files = {
        "docs/current.md": textwrap.dedent(
            """
            # Current

            This doc references
            `docs/test_outputs/experiments/family_routed/batch_raw_responses.json`.
            """
        ).strip()
        + "\n",
        "docs/test_outputs/root_latest.json": (
            '{"path": "docs/test_outputs/experiments/family_generated/payload.json"}\n'
        ),
        "docs/test_outputs/experiments/family_routed/batch_raw_responses.json": "{}\n",
        "docs/test_outputs/experiments/family_generated/payload.json": "{}\n",
        "docs/test_outputs/experiments/family_experiment_source/source.json": (
            '{"path": "docs/test_outputs/experiments/family_experiment_target/payload.json"}\n'
        ),
        "docs/test_outputs/experiments/family_experiment_target/payload.json": "{}\n",
        "docs/test_outputs/experiments/family_self/a.json": (
            '{"path": "docs/test_outputs/experiments/family_self/b.json"}\n'
        ),
        "docs/test_outputs/experiments/family_self/b.json": "{}\n",
        "docs/test_outputs/experiments/family_unrouted/payload.json": "{}\n",
        "docs/test_outputs/experiments/rulegen_root_level_stage_20260101.json": "{}\n",
    }
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
