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
    audit_manual_resource_settings,
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

    def test_report_surfaces_manual_resource_settings_for_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            language_root = data_root / "language_packs"
            pack_root = language_root / "freedict-en-es"
            pack_root.mkdir(parents=True)
            managed_artifact = pack_root / "main.sqlite"
            managed_artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                language_root,
                pack_id="freedict-en-es",
                pack_kind="language",
                provider="freedict",
                local_kind="file",
                build_mode="freedict_tei_to_sqlite",
                artifact_path=managed_artifact,
                source_filename="eng-spa.tei",
                sqlite_filename="main.sqlite",
            )
            (pack_root / PACK_PROVENANCE_FILENAME).write_text(
                json.dumps(_valid_provenance(pack_id="freedict-en-es", pack_kind="language")),
                encoding="utf-8",
            )
            manual_freq = data_root / "imports" / "manual-frequency.sqlite"
            manual_freq.parent.mkdir(parents=True)
            with sqlite3.connect(manual_freq) as conn:
                conn.execute("CREATE TABLE frequency (lemma TEXT, rank INTEGER)")
            manual_embedding = data_root / "imports" / "manual.vec"
            manual_embedding.write_text("hola 0.1 0.2\n", encoding="utf-8")
            unsupported_embedding = data_root / "imports" / "not-embeddings.pdf"
            unsupported_embedding.write_bytes(b"%PDF-1.7\n")
            settings_path = data_root / "settings.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "synonyms": {
                            "managed_language_pack_ids": ["freedict-en-es"],
                            "language_pack_paths": {
                                "freedict-en-es": str(managed_artifact),
                                "wordnet-en": str(data_root / "missing-wordnet"),
                            },
                            "frequency_pack_paths": {"freq-manual": str(manual_freq)},
                            "embedding_pack_paths": {"embed-bad": str(unsupported_embedding)},
                            "embedding_pair_paths": {"en-es": [str(manual_embedding)]},
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manual_report = audit_manual_resource_settings(settings_path)
            report = build_pack_lifecycle_audit_report(
                data_root=data_root,
                generated_at="2026-05-15T00:00:00+00:00",
            )
            markdown = render_pack_lifecycle_markdown(report)

        self.assertEqual(manual_report["status"], "review")
        self.assertEqual(manual_report["manual_path_count"], 5)
        self.assertEqual(manual_report["manual_path_missing_count"], 1)
        self.assertEqual(manual_report["managed_artifact_manual_path_count"], 1)
        self.assertEqual(report["summary"]["status"], "review")
        self.assertEqual(report["summary"]["manual_resource_path_count"], 5)
        self.assertEqual(report["summary"]["manual_resource_review_count"], 3)
        self.assertTrue(
            any(
                "unsupported_manual_artifact_format" in row["issues"]
                for row in manual_report["manual_paths"]
            )
        )
        self.assertIn("Manual Resource Settings", markdown)
        self.assertIn("migrate_to_managed_pack_id", markdown)
        self.assertIn("SQLite embedding database or .vec/.txt/.bin vector file", markdown)

    def test_report_surfaces_publication_manifest_source_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            manifest_path = (
                data_root / "srs" / "profiles" / "default" / ("srs_publication_manifest_en-es.json")
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "pair": "en-es",
                        "profile_id": "default",
                        "generated_at": "2026-05-15T00:00:00Z",
                        "published_at": "2026-05-15T00:00:00Z",
                        "generation_id": "en-es:default:abc123",
                        "artifacts": {},
                        "validation": {"family_valid": True, "errors": []},
                        "source_lineage": {
                            "pack_id": "en-es-active-only-v1",
                            "source_batches": ["batch-a", "batch-b"],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_pack_lifecycle_audit_report(
                data_root=data_root,
                generated_at="2026-05-15T00:00:00+00:00",
            )
            markdown = render_pack_lifecycle_markdown(report)

        publication = report["publication_manifests"]
        row = publication["manifests"][0]
        self.assertEqual(publication["source_lineage_count"], 1)
        self.assertTrue(row["source_lineage_exists"])
        self.assertEqual(row["source_lineage_pack_id"], "en-es-active-only-v1")
        self.assertEqual(row["source_lineage_source_batch_count"], 2)
        self.assertIn("Source lineage count", markdown)


def _valid_provenance(
    *,
    pack_id: str = "freq-es-expanded-v1",
    pack_kind: str = "frequency",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pack_id": pack_id,
        "pack_kind": pack_kind,
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
