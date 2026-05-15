from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from project_structure_inventory import (  # noqa: E402
    build_project_structure_inventory,
    render_project_structure_markdown,
)


class ProjectStructureInventoryTests(unittest.TestCase):
    def test_inventory_enumerates_paths_and_ignores_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_project_structure_inventory(root)

        paths = {row["path"] for row in report["paths"]}
        self.assertIn("scripts/dev/current_tool.py", paths)
        self.assertIn("docs/test_outputs/example_latest.json", paths)
        self.assertNotIn(".git/ignored.txt", paths)
        self.assertNotIn("node_modules/ignored.txt", paths)

        summary = report["summary"]
        self.assertGreater(summary["path_count"], 0)
        self.assertGreater(summary["file_count"], 0)
        self.assertGreater(summary["candidate_path_count"], 0)

    def test_inventory_classifies_families_and_candidate_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_project_structure_inventory(root)

        families = {row["family"]: row for row in report["family_counts"]}
        self.assertIn("scripts_dev", families)
        self.assertIn("scripts_testing", families)
        self.assertIn("docs_test_outputs", families)
        self.assertIn("docs_archive", families)

        candidate_counts = {row["flag"]: row["path_count"] for row in report["candidate_counts"]}
        self.assertGreaterEqual(candidate_counts["generated_latest_alias"], 1)
        self.assertGreaterEqual(candidate_counts["archive_tree"], 1)
        self.assertGreaterEqual(candidate_counts["legacy_or_temporary_name"], 1)

    def test_duplicate_groups_and_script_reference_candidates_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_project_structure_inventory(root)

        duplicate_names = {row["name"] for row in report["duplicate_filename_groups"]}
        self.assertIn("duplicate.md", duplicate_names)

        script_rows = {row["path"]: row for row in report["script_reference_rows"]}
        self.assertFalse(script_rows["scripts/dev/current_tool.py"]["unreferenced_candidate"])
        self.assertTrue(script_rows["scripts/testing/orphan_probe.py"]["unreferenced_candidate"])

        candidate_paths = {row["path"]: row for row in report["candidate_rows"]}
        self.assertIn("scripts/testing/orphan_probe.py", candidate_paths)
        self.assertIn(
            "unreferenced_script_candidate",
            candidate_paths["scripts/testing/orphan_probe.py"]["flags"],
        )

    def test_markdown_renderer_includes_candidate_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_tree(root)

            report = build_project_structure_inventory(root)
            markdown = render_project_structure_markdown(report)

        self.assertIn("# Project Structure Inventory", markdown)
        self.assertIn("## Candidate Signal Counts", markdown)
        self.assertIn("scripts/testing/orphan_probe.py", markdown)


def _write_fixture_tree(root: Path) -> None:
    files = {
        "scripts/package.json": json.dumps(
            {
                "scripts": {
                    "inventory:current": "node dev/run_python.js dev/current_tool.py",
                }
            }
        ),
        "scripts/dev/current_tool.py": "print('current')\n",
        "scripts/testing/orphan_probe.py": "print('orphan')\n",
        "docs/README.md": textwrap.dedent(
            """
            # Docs

            Current path: `scripts/dev/current_tool.py`.
            """
        ).strip()
        + "\n",
        "docs/a/duplicate.md": "one\n",
        "docs/b/duplicate.md": "two\n",
        "docs/archive/old_packet.md": "old\n",
        "docs/test_outputs/example_latest.json": "{}\n",
        "core/lexishift_core/runtime.py": "VALUE = 1\n",
        "core/tests/test_runtime.py": "def test_runtime(): pass\n",
        ".git/ignored.txt": "ignored\n",
        "node_modules/ignored.txt": "ignored\n",
    }
    for relative_path, content in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
