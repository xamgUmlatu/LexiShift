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
from lexishift_core.helper.pack_provenance import (  # noqa: E402
    PACK_PROVENANCE_FILENAME,
    validate_pack_provenance_file,
)
from pack_lifecycle_provenance_backfill import (  # noqa: E402
    backfill_installed_pack_provenance,
    render_provenance_backfill_markdown,
)


class PackLifecycleProvenanceBackfillTests(unittest.TestCase):
    def test_dry_run_reports_catalog_backed_missing_sidecars_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            pack_roots = _write_backfill_fixture(data_root)

            report = backfill_installed_pack_provenance(
                data_root=data_root,
                generated_at="2026-05-15T00:00:00+00:00",
            )
            markdown = render_provenance_backfill_markdown(report)
            sidecars_exist = [
                (pack_root / PACK_PROVENANCE_FILENAME).exists() for pack_root in pack_roots
            ]

        self.assertEqual(report["status"], "would_update")
        self.assertEqual(report["summary"]["backfillable_count"], 4)
        self.assertEqual(report["summary"]["written_count"], 0)
        self.assertFalse(any(sidecars_exist))
        self.assertIn("would_write", markdown)

    def test_apply_writes_conservative_sidecars_for_catalog_backed_installs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            pack_roots = _write_backfill_fixture(data_root)

            report = backfill_installed_pack_provenance(
                data_root=data_root,
                apply_changes=True,
                generated_at="2026-05-15T00:00:00+00:00",
            )
            sidecar_payloads = {
                payload["pack_id"]: payload
                for payload in (
                    json.loads((pack_root / PACK_PROVENANCE_FILENAME).read_text(encoding="utf-8"))
                    for pack_root in pack_roots
                )
            }
            validation_errors = [
                validate_pack_provenance_file(pack_root / PACK_PROVENANCE_FILENAME)
                for pack_root in pack_roots
            ]

        self.assertEqual(report["status"], "applied")
        self.assertEqual(report["summary"]["written_count"], 4)
        self.assertEqual(validation_errors, [(), (), (), ()])
        self.assertEqual(
            set(sidecar_payloads),
            {"freedict-en-es", "freq-es-cde", "freq-de-default", "embed-xling-es"},
        )
        self.assertEqual(
            sidecar_payloads["freedict-en-es"]["source"]["license_status"], "requires_review"
        )
        self.assertEqual(
            sidecar_payloads["freedict-en-es"]["source"]["source_version"],
            "freedict-eng-spa-2025.11.23",
        )
        self.assertEqual(
            sidecar_payloads["freedict-en-es"]["build"]["command"],
            "convert_freedict_tei_to_sqlite",
        )
        self.assertEqual(
            sidecar_payloads["freq-es-cde"]["source"]["license_status"], "requires_review"
        )
        self.assertNotIn("source_version", sidecar_payloads["freq-es-cde"]["source"])
        self.assertNotIn("source_dump", sidecar_payloads["freq-es-cde"]["source"])
        self.assertEqual(
            sidecar_payloads["freq-es-cde"]["build"]["command"],
            "convert_frequency_to_sqlite",
        )
        self.assertTrue(
            sidecar_payloads["freq-es-cde"]["build"]["converter_version"].startswith(
                "source_sha256:lexishift_core.frequency.sqlite:"
            )
        )
        self.assertEqual(
            sidecar_payloads["freq-es-cde"]["build"]["parser_config"]["encoding"], "latin-1"
        )
        self.assertEqual(
            sidecar_payloads["freq-es-cde"]["artifact"]["metrics"],
            {
                "row_count": 3,
                "distinct_lemma_count": 2,
                "pos_rows": 2,
                "topic_domain_rows": 1,
            },
        )
        self.assertIn("source_bundle", sidecar_payloads["freq-de-default"]["source"])
        self.assertEqual(
            sidecar_payloads["freq-de-default"]["source"]["source_bundle"]["bundle_id"],
            "freq-de-default:de_frequency_pipeline",
        )
        self.assertNotIn("source_version", sidecar_payloads["freq-de-default"]["source"])
        self.assertNotIn("source_dump", sidecar_payloads["freq-de-default"]["source"])
        self.assertEqual(
            sidecar_payloads["embed-xling-es"]["source"]["license_status"],
            "requires_review",
        )
        self.assertNotIn("source_version", sidecar_payloads["embed-xling-es"]["source"])
        self.assertNotIn("source_dump", sidecar_payloads["embed-xling-es"]["source"])
        self.assertEqual(
            sidecar_payloads["embed-xling-es"]["build"]["command"],
            "scripts/data/convert_embeddings.py",
        )
        self.assertTrue(
            sidecar_payloads["embed-xling-es"]["build"]["converter_version"].startswith(
                "source_sha256:scripts.data.convert_embeddings:"
            )
        )


def _write_backfill_fixture(data_root: Path) -> tuple[Path, Path, Path, Path]:
    language_root = data_root / "language_packs"
    language_artifact = language_root / "freedict-en-es" / "main.sqlite"
    language_artifact.parent.mkdir(parents=True)
    language_artifact.write_bytes(b"SQLite format 3\x00")
    write_installed_pack_manifest(
        language_root,
        pack_id="freedict-en-es",
        pack_kind="language",
        provider="freedict",
        local_kind="dir",
        build_mode="freedict_tei_to_sqlite",
        artifact_path=language_artifact,
        source_filename="freedict-eng-spa-2025.11.23.src.tar.xz",
        sqlite_filename="main.sqlite",
        required_files=("eng-spa.tei",),
    )

    frequency_root = data_root / "frequency_packs"
    frequency_artifact = frequency_root / "freq-es-cde" / "main.sqlite"
    frequency_artifact.parent.mkdir(parents=True)
    with sqlite3.connect(frequency_artifact) as conn:
        conn.execute(
            """
            CREATE TABLE frequency (
                lemma TEXT,
                freq REAL,
                pos TEXT,
                topics_json TEXT
            );
            """
        )
        conn.executemany(
            "INSERT INTO frequency (lemma, freq, pos, topics_json) VALUES (?, ?, ?, ?);",
            [
                ("gato", 100.0, "n", '["animals"]'),
                ("gato", 50.0, "", ""),
                ("perro", 25.0, "n", None),
            ],
        )
        conn.commit()
    write_installed_pack_manifest(
        frequency_root,
        pack_id="freq-es-cde",
        pack_kind="frequency",
        provider="corpus del espanol",
        local_kind="file",
        build_mode="convert_archive",
        artifact_path=frequency_artifact,
        source_filename="spanish_lemmas20k.txt",
        sqlite_filename="main.sqlite",
    )

    de_frequency_artifact = frequency_root / "freq-de-default" / "main.sqlite"
    de_frequency_artifact.parent.mkdir(parents=True)
    de_frequency_artifact.write_bytes(b"SQLite format 3\x00")
    write_installed_pack_manifest(
        frequency_root,
        pack_id="freq-de-default",
        pack_kind="frequency",
        provider="leipzig + languagetool",
        local_kind="file",
        build_mode="de_frequency_pipeline",
        artifact_path=de_frequency_artifact,
        source_filename="deu_news_2023_1M.tar.gz",
        sqlite_filename="main.sqlite",
    )

    embedding_root = data_root / "embedding_packs"
    embedding_artifact = embedding_root / "embed-xling-es" / "main.sqlite"
    embedding_artifact.parent.mkdir(parents=True)
    embedding_artifact.write_bytes(b"SQLite format 3\x00")
    write_installed_pack_manifest(
        embedding_root,
        pack_id="embed-xling-es",
        pack_kind="embedding",
        provider="fasttext",
        local_kind="file",
        build_mode="convert_to_sqlite",
        artifact_path=embedding_artifact,
        source_filename="wiki.es.align.vec",
        sqlite_filename="main.sqlite",
    )
    return (
        language_artifact.parent,
        frequency_artifact.parent,
        de_frequency_artifact.parent,
        embedding_artifact.parent,
    )


if __name__ == "__main__":
    unittest.main()
