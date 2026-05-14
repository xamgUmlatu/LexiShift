from __future__ import annotations

import json
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

from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.pack_provenance import PACK_PROVENANCE_FILENAME  # noqa: E402
from pack_lifecycle_audit import (  # noqa: E402
    audit_candidate_sqlite,
    build_pack_lifecycle_audit_report,
    render_pack_lifecycle_markdown,
)


class PackLifecycleAuditTests(unittest.TestCase):
    def test_report_accepts_manifest_backed_pack_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            frequency_root = data_root / "frequency_packs"
            pack_root = frequency_root / "freq-es-expanded-v1"
            pack_root.mkdir(parents=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                frequency_root,
                pack_id="freq-es-expanded-v1",
                pack_kind="frequency",
                provider="corpus-del-espanol",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=artifact,
                source_filename="spanish_lemmas20k.txt",
                sqlite_filename="main.sqlite",
            )
            (pack_root / PACK_PROVENANCE_FILENAME).write_text(
                json.dumps(_valid_provenance(), ensure_ascii=False),
                encoding="utf-8",
            )

            report = build_pack_lifecycle_audit_report(
                data_root=data_root,
                generated_at="2026-05-15T00:00:00+00:00",
            )

        self.assertEqual(report["summary"]["status"], "ok")
        self.assertEqual(report["summary"]["installed_pack_count"], 1)
        self.assertEqual(report["summary"]["missing_provenance_count"], 0)
        frequency = report["installed_pack_families"]["frequency"]
        self.assertEqual(frequency["pack_count"], 1)
        self.assertTrue(frequency["packs"][0]["provenance_valid"])

    def test_report_flags_missing_artifact_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            frequency_root = data_root / "frequency_packs"
            pack_root = frequency_root / "freq-es-expanded-v1"
            pack_root.mkdir(parents=True)
            missing_artifact = pack_root / "main.sqlite"
            write_installed_pack_manifest(
                frequency_root,
                pack_id="freq-es-expanded-v1",
                pack_kind="frequency",
                provider="corpus-del-espanol",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=missing_artifact,
                source_filename="spanish_lemmas20k.txt",
                sqlite_filename="main.sqlite",
            )

            report = build_pack_lifecycle_audit_report(data_root=data_root)

        self.assertEqual(report["summary"]["status"], "error")
        self.assertEqual(report["summary"]["missing_artifact_count"], 1)
        self.assertEqual(report["summary"]["missing_provenance_count"], 1)
        issues = report["installed_pack_families"]["frequency"]["packs"][0]["issues"]
        self.assertIn("missing_artifact", issues)
        self.assertIn("missing_provenance", issues)

    def test_candidate_sqlite_and_markdown_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            candidate_db = Path(tmp) / "candidate.sqlite"
            _write_candidate_db(candidate_db)

            report = build_pack_lifecycle_audit_report(
                data_root=data_root,
                candidate_dbs=(candidate_db,),
                generated_at="2026-05-15T00:00:00+00:00",
            )
            audit = audit_candidate_sqlite(candidate_db)
            markdown = render_pack_lifecycle_markdown(report)

        self.assertEqual(audit["status"], "ok")
        self.assertEqual(audit["primary_table"], "frequency")
        self.assertEqual(audit["row_count"], 2)
        self.assertEqual(audit["meta"]["source"], "fixture")
        self.assertIn("Candidate SQLite", markdown)
        self.assertIn("candidate.sqlite", markdown)


def _valid_provenance() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pack_id": "freq-es-expanded-v1",
        "pack_kind": "frequency",
        "provider": "corpus-del-espanol",
        "source": {
            "source_name": "Corpus del Espanol frequency sample",
            "source_url": "https://www.wordfrequency.info/files/spanish/spanish_lemmas20k.txt",
            "license_status": "requires_review",
            "raw_artifacts": [
                {
                    "filename": "spanish_lemmas20k.txt",
                    "sha1": "0" * 40,
                }
            ],
        },
        "build": {"build_mode": "convert_archive"},
        "artifact": {
            "artifact_relpath": "main.sqlite",
            "artifact_kind": "sqlite",
            "sha1": "1" * 40,
            "metrics": {
                "row_count": 2,
                "distinct_lemma_count": 2,
                "pos_rows": 2,
                "topic_domain_rows": 0,
            },
        },
    }


def _write_candidate_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE frequency (lemma TEXT, rank INTEGER, freq REAL, pos TEXT)")
        conn.executemany(
            "INSERT INTO frequency (lemma, rank, freq, pos) VALUES (?, ?, ?, ?)",
            [
                ("banco", 1, 100.0, "n"),
                ("hablar", 2, 80.0, "v"),
            ],
        )
        conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
        conn.execute("INSERT INTO meta (key, value) VALUES (?, ?)", ("source", "fixture"))


if __name__ == "__main__":
    unittest.main()
