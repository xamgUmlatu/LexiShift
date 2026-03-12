from __future__ import annotations

import gzip
import io
from pathlib import Path
import sqlite3
import sys
import tarfile
import tempfile
import unittest
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "dev"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from licensing_source_header_fetch import (  # noqa: E402
    build_report,
    inspect_downloaded_file,
)


class TestLicensingSourceHeaderFetch(unittest.TestCase):
    def test_inspect_gz_detects_sqlite_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sqlite_path = root / "sample.db"
            with sqlite3.connect(sqlite_path) as conn:
                conn.execute("CREATE TABLE t (k TEXT);")
                conn.commit()
            gz_path = root / "sample.db.gz"
            with sqlite_path.open("rb") as source, gzip.open(gz_path, "wb") as target:
                target.write(source.read())

            probes, error = inspect_downloaded_file(
                gz_path,
                target_name="wnjpn.db",
                sample_bytes=8192,
                max_lines=10,
            )
            self.assertIsNone(error)
            self.assertEqual(len(probes), 1)
            self.assertTrue(probes[0].sqlite_header_ok)
            self.assertEqual(probes[0].kind, "sqlite")

    def test_inspect_tar_xz_reads_target_member_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "freedict-eng-deu.src.tar.xz"
            tei_text = (
                '<availability status="free">\n'
                "Licensed under GNU General Public License.\n"
                "</availability>\n"
            ).encode("utf-8")
            with tarfile.open(archive_path, "w:xz") as archive:
                info = tarfile.TarInfo(name="eng-deu.tei")
                info.size = len(tei_text)
                archive.addfile(info, io.BytesIO(tei_text))

            probes, error = inspect_downloaded_file(
                archive_path,
                target_name="eng-deu.tei",
                sample_bytes=8192,
                max_lines=20,
            )
            self.assertIsNone(error)
            self.assertEqual(len(probes), 1)
            self.assertEqual(probes[0].entry_name, "eng-deu.tei")
            self.assertIn("GNU General Public License.", "\n".join(probes[0].preview_lines))
            self.assertTrue(probes[0].license_hits)

    def test_build_report_downloads_file_url_and_inspects_zip_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            register_path = root / "register.md"
            url_registry_path = root / "language_pack_urls.txt"
            cache_dir = root / "cache"
            source_zip = root / "cedict_1_0_ts_utf-8_mdbg.zip"

            with zipfile.ZipFile(source_zip, "w") as archive:
                archive.writestr(
                    "cedict_ts.u8",
                    "# CC-CEDICT is distributed under CC BY-SA 3.0\n",
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
                        "| `cc-cedict-zh-en` | translation | "
                        "`$DATA_ROOT/language_packs/cedict_ts.u8` | "
                        "expected-not-verified | sample | `https://example.org` | "
                        "2026-02-23 | `manual-supply` | available |",
                    ]
                ),
                encoding="utf-8",
            )
            url_registry_path.write_text(
                "\n".join(
                    [
                        "pack_id: cc-cedict-zh-en",
                        f"url: {source_zip.as_uri()}",
                        "filename: cedict_1_0_ts_utf-8_mdbg.zip",
                        "unzipped_name: cedict_ts.u8",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_report(
                register_path=register_path,
                url_registry_path=url_registry_path,
                status_filter={"expected-not-verified"},
                pack_filter=set(),
                cache_dir=cache_dir,
                max_download_bytes=10_000_000,
                sample_bytes=16_384,
                max_lines=20,
                timeout_seconds=10.0,
                force_redownload=False,
            )

            self.assertEqual(len(report.rows), 1)
            row = report.rows[0]
            self.assertEqual(row.pack_id, "cc-cedict-zh-en")
            self.assertEqual(row.status, "inspected")
            self.assertTrue(row.downloaded_path)
            self.assertEqual(len(row.probes), 1)
            self.assertTrue(row.probes[0].license_hits)


if __name__ == "__main__":
    unittest.main()
