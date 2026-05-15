from __future__ import annotations

import json
from pathlib import Path
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
        self.assertEqual(report["summary"]["backfillable_count"], 2)
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
            sidecar_payloads = [
                json.loads((pack_root / PACK_PROVENANCE_FILENAME).read_text(encoding="utf-8"))
                for pack_root in pack_roots
            ]
            validation_errors = [
                validate_pack_provenance_file(pack_root / PACK_PROVENANCE_FILENAME)
                for pack_root in pack_roots
            ]

        self.assertEqual(report["status"], "applied")
        self.assertEqual(report["summary"]["written_count"], 2)
        self.assertEqual(validation_errors, [(), ()])
        self.assertEqual(
            [payload["source"]["license_status"] for payload in sidecar_payloads],
            ["requires_review", "requires_review"],
        )
        self.assertEqual(sidecar_payloads[0]["pack_id"], "freq-es-cde")
        self.assertEqual(sidecar_payloads[1]["pack_id"], "embed-xling-es")
        self.assertEqual(sidecar_payloads[0]["build"]["command"], "convert_frequency_to_sqlite")
        self.assertEqual(sidecar_payloads[0]["build"]["parser_config"]["encoding"], "latin-1")
        self.assertEqual(
            sidecar_payloads[1]["build"]["command"],
            "scripts/data/convert_embeddings.py",
        )


def _write_backfill_fixture(data_root: Path) -> tuple[Path, Path]:
    frequency_root = data_root / "frequency_packs"
    frequency_artifact = frequency_root / "freq-es-cde" / "main.sqlite"
    frequency_artifact.parent.mkdir(parents=True)
    frequency_artifact.write_bytes(b"SQLite format 3\x00")
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
    return frequency_artifact.parent, embedding_artifact.parent


if __name__ == "__main__":
    unittest.main()
