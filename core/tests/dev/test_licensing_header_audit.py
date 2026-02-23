from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from licensing_header_audit import (  # noqa: E402
    build_license_audit_report,
    parse_pack_ids,
    parse_register_table,
    parse_url_registry,
    resolve_source_url,
)


class TestLicensingHeaderAudit(unittest.TestCase):
    def test_parse_pack_ids_expands_embed_xling_family(self) -> None:
        pack_cell = "`embed-xling-en/de/es/ja`"
        self.assertEqual(
            parse_pack_ids(pack_cell),
            [
                "embed-xling-en",
                "embed-xling-de",
                "embed-xling-es",
                "embed-xling-ja",
            ],
        )

    def test_parse_url_registry_and_alias_source_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "language_pack_urls.txt"
            registry_path.write_text(
                "\n".join(
                    [
                        "pack_id: align-en-cc",
                        "url: https://example.org/cc.en.300.vec.gz",
                        "pack_id: jmdict-ja-en",
                        "url: https://example.org/JMdict_e.gz",
                    ]
                ),
                encoding="utf-8",
            )
            mapping = parse_url_registry(registry_path)
            self.assertEqual(
                mapping["align-en-cc"],
                "https://example.org/cc.en.300.vec.gz",
            )
            source_url, note = resolve_source_url("embed-en-cc", mapping)
            self.assertEqual(source_url, "https://example.org/cc.en.300.vec.gz")
            self.assertEqual(note, "alias:align-en-cc")

    def test_build_report_skip_remote_uses_local_artifact_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            register_path = tmp_root / "register.md"
            url_registry = tmp_root / "language_pack_urls.txt"
            data_root = tmp_root / "data_root"
            artifact_path = data_root / "language_packs" / "eng-deu.tei"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(
                (
                    "<availability status=\"free\">"
                    "Licensed under GPL v2 or later."
                    "</availability>"
                ),
                encoding="utf-8",
            )

            register_path.write_text(
                "\n".join(
                    [
                        "# Header",
                        "## Pack Register",
                        "| Pack ID | Type | Post-download/post-conversion artifact | "
                        "License/copyright status | Evidence Details | Evidence URL | "
                        "Verified On | Recommended distribution mode | Manual-supply UX |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| `freedict-en-de` | translation | "
                        "`$DATA_ROOT/language_packs/eng-deu.tei` | "
                        "expected-not-verified | sample | "
                        "`https://example.org/license` | 2026-02-22 | "
                        "`manual-supply` | available |",
                    ]
                ),
                encoding="utf-8",
            )
            url_registry.write_text(
                "\n".join(
                    [
                        "pack_id: freedict-en-de",
                        "url: https://example.org/freedict-eng-deu.tar.xz",
                    ]
                ),
                encoding="utf-8",
            )

            parsed_rows = parse_register_table(register_path)
            self.assertEqual(len(parsed_rows), 1)

            report = build_license_audit_report(
                register_path=register_path,
                url_registry_path=url_registry,
                data_root=data_root,
                status_filter={"expected-not-verified"},
                max_bytes=1024,
                max_lines=5,
                timeout_seconds=5.0,
                skip_remote=True,
            )
            self.assertEqual(len(report.rows), 1)
            row = report.rows[0]
            self.assertEqual(row.pack_id, "freedict-en-de")
            self.assertTrue(row.local_artifact.exists)
            self.assertIn("Licensed under GPL v2 or later.", row.local_artifact.license_hits[0])
            self.assertIsNone(row.source_probe)
            self.assertEqual(row.source_url, "https://example.org/freedict-eng-deu.tar.xz")


if __name__ == "__main__":
    unittest.main()
