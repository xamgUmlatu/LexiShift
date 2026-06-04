from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib import error as url_error

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pack_source_url_audit_support import (  # noqa: E402
    PackSourceAuditRow,
    PackSourceUrlAuditReport,
    UrlProbe,
    build_pack_source_url_audit_report,
    probe_url,
    render_markdown,
)


class _FakeResponse:
    def __init__(self, *, url: str, status: int, headers: dict[str, str]) -> None:
        self._url = url
        self.status = status
        self.headers = headers

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def geturl(self) -> str:
        return self._url


class TestPackSourceUrlAudit(unittest.TestCase):
    def test_probe_url_falls_back_to_get_when_head_is_rejected(self) -> None:
        def opener(request, timeout: float):  # noqa: ANN001
            self.assertGreater(timeout, 0)
            if request.get_method() == "HEAD":
                raise url_error.HTTPError(
                    url=request.full_url,
                    code=405,
                    msg="Method Not Allowed",
                    hdrs={"Content-Length": "0"},
                    fp=None,
                )
            return _FakeResponse(
                url=request.full_url,
                status=206,
                headers={
                    "Content-Type": "application/x-xz",
                    "Content-Length": "1",
                },
            )

        probe = probe_url(
            "https://example.com/freedict-eng-deu.tar.xz",
            timeout_seconds=5.0,
            opener=opener,
        )

        self.assertTrue(probe.ok)
        self.assertEqual(probe.method, "GET")
        self.assertEqual(probe.status_code, 206)
        self.assertEqual(probe.content_type, "application/x-xz")

    def test_build_report_uses_manifest_override_for_selected_pack(self) -> None:
        def opener(request, timeout: float):  # noqa: ANN001
            return _FakeResponse(
                url=request.full_url,
                status=200,
                headers={
                    "Content-Type": "text/plain",
                    "Content-Length": "123",
                },
            )

        manifest_payload = {
            "schema_version": 1,
            "generated_at": "2026-04-19T00:00:00Z",
            "ttl_hours": 24,
            "packs": {
                "freq-en-coca": {
                    "url": "https://example.com/freq-en-coca.txt",
                    "filename": "freq-en-coca.txt",
                    "expected_content_type": "text/plain",
                }
            },
        }

        with TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "pack_source_manifest.json"
            manifest_path.write_text(
                json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report = build_pack_source_url_audit_report(
                manifest_path=manifest_path,
                manifest_url=None,
                pack_ids=("freq-en-coca",),
                pack_kinds=("frequency",),
                include_archive=False,
                timeout_seconds=5.0,
                opener=opener,
            )

        self.assertEqual(report.overall_status, "PASS")
        self.assertEqual(report.manifest_override_count, 1)
        self.assertEqual(report.pack_count, 1)
        self.assertEqual(report.primary_ok_count, 1)
        self.assertEqual(report.rows[0].pack_id, "freq-en-coca")
        self.assertEqual(report.rows[0].transport_origin, "manifest_override")
        self.assertEqual(report.rows[0].primary_probe.url, "https://example.com/freq-en-coca.txt")
        self.assertEqual(report.rows[0].expected_content_type, "text/plain")
        self.assertTrue(report.rows[0].primary_content_type_matches)

    def test_build_report_fails_on_primary_content_type_mismatch(self) -> None:
        def opener(request, timeout: float):  # noqa: ANN001
            return _FakeResponse(
                url=request.full_url,
                status=200,
                headers={
                    "Content-Type": "text/html",
                    "Content-Length": "123",
                },
            )

        manifest_payload = {
            "schema_version": 1,
            "generated_at": "2026-04-19T00:00:00Z",
            "ttl_hours": 24,
            "packs": {
                "freedict-en-de": {
                    "expected_content_type": "application/x-xz",
                }
            },
        }

        with TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "pack_source_manifest.json"
            manifest_path.write_text(
                json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report = build_pack_source_url_audit_report(
                manifest_path=manifest_path,
                manifest_url=None,
                pack_ids=("freedict-en-de",),
                pack_kinds=("language",),
                include_archive=False,
                timeout_seconds=5.0,
                opener=opener,
            )

        self.assertEqual(report.overall_status, "FAIL")
        self.assertEqual(report.primary_content_type_mismatch_count, 1)
        self.assertFalse(report.rows[0].primary_content_type_matches)

    def test_render_markdown_surfaces_archive_warning_findings(self) -> None:
        report = PackSourceUrlAuditReport(
            generated_at="2026-04-19T00:00:00+00:00",
            overall_status="WARN",
            manifest_source="file:///tmp/pack_source_manifest.json",
            manifest_schema_version=1,
            manifest_override_count=0,
            manifest_generated_at="2026-04-19T00:00:00+00:00",
            pack_count=1,
            primary_ok_count=1,
            primary_fail_count=0,
            archive_ok_count=0,
            archive_fail_count=1,
            archive_skipped_count=0,
            primary_content_type_mismatch_count=0,
            archive_content_type_mismatch_count=0,
            include_archive=True,
            pack_kinds=["language"],
            pack_id_filter=[],
            rows=[
                PackSourceAuditRow(
                    pack_id="wordnet-en",
                    pack_kind="language",
                    display_name="WordNet",
                    source="Princeton",
                    filename="english-wordnet-2025-json.zip",
                    transport_origin="bundled",
                    expected_content_type="application/zip",
                    primary_probe=UrlProbe(
                        url="https://example.com/wordnet.zip",
                        ok=True,
                        method="HEAD",
                        status_code=200,
                        final_url="https://example.com/wordnet.zip",
                        content_type="application/zip",
                        content_length="123",
                    ),
                    archive_probe=UrlProbe(
                        url="https://web.archive.org/example.com/wordnet.zip",
                        ok=False,
                        method="HEAD",
                        status_code=404,
                        final_url="https://web.archive.org/example.com/wordnet.zip",
                        content_type="text/html",
                        content_length="321",
                        error="HTTP Error 404: Not Found",
                    ),
                    primary_content_type_matches=True,
                    archive_content_type_matches=None,
                )
            ],
            issues=[],
        )

        markdown = render_markdown(report)

        self.assertIn("- Status: WARN", markdown)
        self.assertIn("[WARN] `wordnet-en`", markdown)
        self.assertIn("FAIL (HEAD 404)", markdown)
        self.assertIn("- Content-type mismatches: primary=0 archive=0", markdown)


if __name__ == "__main__":
    unittest.main()
