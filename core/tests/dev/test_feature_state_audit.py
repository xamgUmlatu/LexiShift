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

from feature_state_audit import audit_feature_state_matrix  # noqa: E402


class TestFeatureStateAudit(unittest.TestCase):
    def test_audit_accepts_well_formed_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            evidence = root / "docs" / "proof.md"
            evidence.write_text("ok\n", encoding="utf-8")
            matrix = root / "feature_state_matrix.md"
            matrix.write_text(
                textwrap.dedent(
                    """
                    # Feature State Matrix

                    ## Example Feature
                    - Status: `implemented`, `verified`
                    - Last documented checkpoint: `2026-03-12`
                    - Last verified: `2026-03-12` audit run
                    - Default behavior:
                      - does a thing
                    - Evidence:
                      - `docs/proof.md`
                    - Known gaps:
                      - still missing stricter gating
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            report = audit_feature_state_matrix(matrix)
            self.assertEqual(report.issue_count, 0)
            self.assertEqual(report.section_count, 1)

    def test_audit_reports_missing_fields_and_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix = root / "feature_state_matrix.md"
            matrix.write_text(
                textwrap.dedent(
                    """
                    # Feature State Matrix

                    ## Broken Feature
                    - Status: pending
                    - Last documented checkpoint: recent
                    - Default behavior:
                      - unclear
                    - Evidence:
                      - `docs/missing.md`
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            report = audit_feature_state_matrix(matrix)
            codes = {issue["code"] for issue in report.issues}
            self.assertIn("INVALID_STATUS", codes)
            self.assertIn("MISSING_DATE", codes)
            self.assertIn("MISSING_FIELD", codes)
            self.assertIn("MISSING_EVIDENCE_PATH", codes)


if __name__ == "__main__":
    unittest.main()
