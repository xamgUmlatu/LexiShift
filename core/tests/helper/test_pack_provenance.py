from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.pack_provenance import (  # noqa: E402
    PACK_PROVENANCE_FILENAME,
    validate_pack_provenance_file,
    validate_pack_provenance_payload,
    write_app_managed_pack_provenance,
)


class TestPackProvenance(unittest.TestCase):
    def test_accepts_frequency_pack_provenance_contract(self) -> None:
        errors = validate_pack_provenance_payload(_valid_frequency_payload())

        self.assertEqual(errors, ())

    def test_requires_explicit_identity_license_and_source_pointer(self) -> None:
        payload = _valid_frequency_payload()
        payload["pack_id"] = " "
        payload["source"] = {
            "source_name": "Corpus del Espanol sample",
            "raw_artifacts": [{"filename": "spanish_lemmas20k.txt"}],
        }

        errors = validate_pack_provenance_payload(payload)

        self.assertIn("pack_id is required", errors)
        self.assertIn("source.license_status is required", errors)
        self.assertIn("source must include source_url or local_source_path", errors)

    def test_rejects_invalid_checksums_and_metrics(self) -> None:
        payload = _valid_frequency_payload()
        payload["source"]["raw_artifacts"][0]["sha1"] = "not-a-sha"
        payload["artifact"]["sha256"] = "abc"
        payload["artifact"]["metrics"] = {
            "row_count": 2,
            "distinct_lemma_count": 3,
            "pos_rows": 4,
            "topic_domain_rows": -1,
        }

        errors = validate_pack_provenance_payload(payload)

        self.assertIn(
            "source.raw_artifacts[0].sha1 must be 40 hex characters",
            errors,
        )
        self.assertIn("artifact.sha256 must be 64 hex characters", errors)
        self.assertIn("artifact.metrics.distinct_lemma_count cannot exceed row_count", errors)
        self.assertIn("artifact.metrics.pos_rows cannot exceed row_count", errors)
        self.assertIn(
            "artifact.metrics.topic_domain_rows must be a non-negative integer",
            errors,
        )

    def test_validates_provenance_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / PACK_PROVENANCE_FILENAME
            path.write_text(
                json.dumps(_valid_frequency_payload(), ensure_ascii=False),
                encoding="utf-8",
            )

            errors = validate_pack_provenance_file(path)

        self.assertEqual(errors, ())

    def test_writes_app_managed_pack_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack_root = Path(tmp) / "frequency_packs" / "freq-es-expanded-v1"
            pack_root.mkdir(parents=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")

            provenance_path = write_app_managed_pack_provenance(
                pack_root=pack_root,
                pack_id="freq-es-expanded-v1",
                pack_kind="frequency",
                provider="corpus-del-espanol",
                source_name="Corpus del Espanol",
                source_url="https://example.com/spanish_lemmas20k.txt",
                wayback_url="https://web.archive.org/web/*/https://example.com/spanish_lemmas20k.txt",
                build_mode="convert_archive",
                artifact_path=artifact,
                source_filename="spanish_lemmas20k.txt",
                sqlite_filename="main.sqlite",
            )

            payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        self.assertEqual(validate_pack_provenance_payload(payload), ())
        self.assertEqual(payload["source"]["license_status"], "requires_review")
        self.assertEqual(payload["artifact"]["artifact_relpath"], "main.sqlite")
        self.assertEqual(payload["artifact"]["artifact_kind"], "sqlite")


def _valid_frequency_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pack_id": "freq-es-expanded-v1",
        "pack_kind": "frequency",
        "provider": "corpus-del-espanol",
        "source": {
            "source_name": "Corpus del Espanol frequency sample",
            "source_url": "https://www.wordfrequency.info/files/spanish/spanish_lemmas20k.txt",
            "license_status": "requires_review",
            "source_version": "spanish_lemmas20k",
            "raw_artifacts": [
                {
                    "filename": "spanish_lemmas20k.txt",
                    "sha1": "0" * 40,
                }
            ],
        },
        "build": {
            "build_mode": "convert_archive",
            "command": "convert_frequency_to_sqlite",
            "parser_profile": "freq-es-cde",
        },
        "artifact": {
            "artifact_relpath": "main.sqlite",
            "artifact_kind": "sqlite",
            "sha1": "1" * 40,
            "sha256": "2" * 64,
            "metrics": {
                "row_count": 2000,
                "distinct_lemma_count": 1984,
                "pos_rows": 2000,
                "topic_domain_rows": 0,
            },
        },
    }


if __name__ == "__main__":
    unittest.main()
