from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (CORE_ROOT, SCRIPTS_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from pack_lifecycle_source_identity_plan import (  # noqa: E402
    build_source_identity_plan,
    render_source_identity_plan_markdown,
)


class PackLifecycleSourceIdentityPlanTests(unittest.TestCase):
    def test_classifies_safe_labels_policy_and_bundle_cases_without_mutation(self) -> None:
        report = build_source_identity_plan(generated_at="2026-05-15T00:00:00+00:00")
        rows = {str(row["pack_id"]): row for row in report["packs"]}

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["mutation"], "none")
        self.assertEqual(report["runtime_policy_change"], "none")
        self.assertEqual(rows["freedict-en-es"]["classification"], "safe_to_write")
        self.assertEqual(rows["freedict-en-es"]["candidate_field"], "source_version")
        self.assertEqual(rows["freedict-en-es"]["candidate_value"], "freedict-eng-spa-2025.11.23")
        self.assertEqual(rows["freq-es-cde"]["classification"], "label_only")
        self.assertEqual(rows["freq-es-cde"]["candidate_value"], "spanish_lemmas20k")
        self.assertEqual(rows["wiktionary-en-es"]["classification"], "needs_policy")
        self.assertEqual(rows["wiktionary-en-es"]["candidate_field"], "source_dump")
        self.assertEqual(rows["freq-de-default"]["classification"], "source_bundle_needed")
        self.assertGreater(report["summary"]["needs_decision_count"], 0)

    def test_markdown_renders_decision_surface_rows(self) -> None:
        report = build_source_identity_plan(generated_at="2026-05-15T00:00:00+00:00")

        markdown = render_source_identity_plan_markdown(report)

        self.assertIn("# Pack Lifecycle Source Identity Plan", markdown)
        self.assertIn("`safe_to_write`", markdown)
        self.assertIn("`source_bundle_needed`", markdown)
        self.assertIn("freedict-en-es", markdown)
        self.assertIn("does_not_write_source_version_or_source_dump", markdown)
        self.assertIn("does_not_write_undated_kaikki_dump_family_labels", markdown)


if __name__ == "__main__":
    unittest.main()
