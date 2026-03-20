from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_doc_references import (  # noqa: E402
    _metadata_issues,
    _resolve_candidate,
    _should_audit_code_span,
)


class TestCheckDocReferences(unittest.TestCase):
    def test_same_directory_markdown_code_span_is_audited_and_resolved(self) -> None:
        doc_path = REPO_ROOT / "docs" / "developer" / "documentation_grooming_workstream.md"
        candidate = "documentation_governance_typo.md"

        self.assertTrue(_should_audit_code_span(candidate))

        resolved = _resolve_candidate(doc_path, candidate)
        self.assertIsNotNone(resolved)
        self.assertEqual(
            resolved,
            REPO_ROOT / "docs" / "developer" / "documentation_governance_typo.md",
        )
        self.assertFalse(resolved.exists())

    def test_metadata_issues_report_missing_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "doc.md"
            doc_path.write_text(
                "# Example\n\nStatus: active\nLast updated: 2026-03-17\n",
                encoding="utf-8",
            )

            issues = _metadata_issues(doc_path)

        self.assertIn(
            {"code": "MISSING_METADATA_FIELD", "field": "Role"},
            issues,
        )

    def test_metadata_issues_report_invalid_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "doc.md"
            doc_path.write_text(
                ("# Example\n\nStatus: active\nRole: Current-ish\nLast updated: 2026-03-17\n"),
                encoding="utf-8",
            )

            issues = _metadata_issues(doc_path)

        self.assertIn(
            {"code": "INVALID_ROLE", "field": "Role", "value": "Current-ish"},
            issues,
        )


if __name__ == "__main__":
    unittest.main()
