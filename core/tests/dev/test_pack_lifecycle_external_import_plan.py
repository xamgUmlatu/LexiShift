from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (CORE_ROOT, SCRIPTS_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from pack_lifecycle_external_import_plan import (  # noqa: E402
    build_external_import_plan,
    render_external_import_plan_markdown,
)


class PackLifecycleExternalImportPlanTests(unittest.TestCase):
    def test_frequency_sqlite_can_be_manual_linked_but_needs_license_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "manual-frequency.sqlite"
            with sqlite3.connect(db_path) as conn:
                conn.execute("CREATE TABLE frequency (lemma TEXT, freq REAL)")

            report = build_external_import_plan(
                family="frequency",
                pack_id="freq-es-manual",
                path=db_path,
                source_name="Manual Spanish frequency source",
                source_url="https://example.com/manual-frequency.zip",
                license_status="requires_review",
                generated_at="2026-05-15T00:00:00+00:00",
            )
            markdown = render_external_import_plan_markdown(report)

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "external_manual_link_ready_import_needs_review")
        self.assertEqual(report["mutation"], "none")
        self.assertTrue(report["manual_link"]["allowed"])
        self.assertEqual(report["managed_import"]["status"], "needs_source_or_license_review")
        self.assertFalse(report["promotion"]["ready"])
        self.assertIn("license_status_requires_review", report["promotion"]["blocked_reasons"])
        self.assertNotIn("missing_raw_artifact_checksum", report["promotion"]["blocked_reasons"])
        self.assertEqual(report["raw_checksum"]["source"], "computed_from_external_path")
        self.assertTrue(report["provenance_preview_valid"])
        self.assertIn("sha256", report["provenance_preview"]["source"]["raw_artifacts"][0])
        self.assertIn("requires_review", markdown)

    def test_unsupported_embedding_artifact_is_blocked_before_link_or_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "not-embeddings.pdf"
            bad_path.write_bytes(b"%PDF-1.7\n")

            report = build_external_import_plan(
                family="embedding",
                pack_id="embed-bad",
                path=bad_path,
                source_name="Bad embedding source",
                license_status="confirmed",
                raw_sha1="0" * 40,
                generated_at="2026-05-15T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["decision"], "external_manual_link_blocked")
        self.assertFalse(report["manual_link"]["allowed"])
        self.assertIn("unsupported_manual_artifact_format", report["issues"])
        self.assertEqual(report["managed_import"]["status"], "blocked")
        self.assertFalse(report["promotion"]["ready"])

    def test_confirmed_supported_artifact_with_checksum_is_preflight_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vec_path = Path(tmp) / "manual.vec"
            vec_path.write_text("hola 0.1 0.2\n", encoding="utf-8")

            report = build_external_import_plan(
                family="embedding",
                pack_id="embed-manual-es",
                path=vec_path,
                source_name="Manual embedding source",
                source_url="https://example.com/manual.vec",
                license_status="confirmed",
                raw_sha256="1" * 64,
                generated_at="2026-05-15T00:00:00+00:00",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "external_import_preflight_ready")
        self.assertTrue(report["manual_link"]["allowed"])
        self.assertEqual(report["managed_import"]["status"], "ready_for_explicit_operator_import")
        self.assertTrue(report["promotion"]["ready"])
        self.assertEqual(report["promotion"]["blocked_reasons"], [])

    def test_supported_artifact_computes_checksum_when_operator_does_not_provide_one(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vec_path = Path(tmp) / "manual.vec"
            vec_bytes = b"hola 0.1 0.2\n"
            vec_path.write_bytes(vec_bytes)

            report = build_external_import_plan(
                family="embedding",
                pack_id="embed-manual-es",
                path=vec_path,
                source_name="Manual embedding source",
                source_url="https://example.com/manual.vec",
                license_status="confirmed",
                generated_at="2026-05-15T00:00:00+00:00",
            )

        raw_checksum = report["raw_checksum"]
        raw_artifact = report["provenance_preview"]["source"]["raw_artifacts"][0]
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "external_import_preflight_ready")
        self.assertEqual(raw_checksum["source"], "computed_from_external_path")
        self.assertEqual(raw_checksum["sha1"], hashlib.sha1(vec_bytes).hexdigest())
        self.assertEqual(raw_checksum["sha256"], hashlib.sha256(vec_bytes).hexdigest())
        self.assertEqual(raw_artifact["sha1"], hashlib.sha1(vec_bytes).hexdigest())
        self.assertEqual(raw_artifact["sha256"], hashlib.sha256(vec_bytes).hexdigest())


if __name__ == "__main__":
    unittest.main()
