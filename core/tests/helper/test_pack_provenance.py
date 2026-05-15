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

    def test_rejects_blank_optional_lineage_fields(self) -> None:
        payload = _valid_frequency_payload()
        payload["source"]["source_version"] = " "
        payload["build"]["command"] = ""
        payload["build"]["parser_config"] = "freq-es-cde"

        errors = validate_pack_provenance_payload(payload)

        self.assertIn("source.source_version must not be blank when present", errors)
        self.assertIn("build.command must not be blank when present", errors)
        self.assertIn("build.parser_config must be a JSON object", errors)

    def test_validates_source_bundle_lineage(self) -> None:
        payload = _valid_frequency_payload()
        payload["source"]["source_bundle"] = {
            "bundle_id": "freq-de-default:de_frequency_pipeline",
            "bundle_kind": "generated_frequency_pipeline",
            "components": [
                {
                    "role": "corpus",
                    "source_name": "Leipzig Wortschatz",
                    "source_url": "https://example.com/deu_news_2023_1M.tar.gz",
                    "filename": "deu_news_2023_1M.tar.gz",
                },
                {
                    "role": "pos_tooling",
                    "source_name": "Morfologik tools",
                    "build_ref": "morfologik-tools-2.1.9.jar",
                },
            ],
        }

        errors = validate_pack_provenance_payload(payload)

        self.assertEqual(errors, ())

    def test_rejects_invalid_source_bundle_lineage(self) -> None:
        payload = _valid_frequency_payload()
        payload["source"]["source_bundle"] = {
            "bundle_id": "freq-de-default:de_frequency_pipeline",
            "bundle_kind": "generated_frequency_pipeline",
            "components": [
                {
                    "role": "corpus",
                    "source_name": "Leipzig Wortschatz",
                }
            ],
        }

        errors = validate_pack_provenance_payload(payload)

        self.assertIn(
            "source.source_bundle.components[0] must include source_url, "
            "local_source_path, or build_ref",
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
                build_command="convert_frequency_to_sqlite",
                parser_profile="freq-es-cde",
                parser_config={"delimiter": "\t", "header_starts_with": "ID"},
                source_bundle={
                    "bundle_id": "freq-es-expanded-v1:fixture",
                    "bundle_kind": "test_fixture",
                    "components": [
                        {
                            "role": "corpus",
                            "source_name": "Corpus del Espanol sample",
                            "source_url": "https://example.com/spanish_lemmas20k.txt",
                        }
                    ],
                },
                artifact_path=artifact,
                source_filename="spanish_lemmas20k.txt",
                sqlite_filename="main.sqlite",
                artifact_metrics={
                    "row_count": 2,
                    "distinct_lemma_count": 2,
                    "pos_rows": 1,
                    "topic_domain_rows": 0,
                },
            )

            payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        self.assertEqual(validate_pack_provenance_payload(payload), ())
        self.assertEqual(payload["source"]["license_status"], "requires_review")
        self.assertEqual(payload["build"]["command"], "convert_frequency_to_sqlite")
        self.assertEqual(payload["build"]["parser_profile"], "freq-es-cde")
        self.assertEqual(payload["build"]["parser_config"]["header_starts_with"], "ID")
        self.assertEqual(payload["source"]["source_bundle"]["bundle_kind"], "test_fixture")
        self.assertEqual(payload["artifact"]["artifact_relpath"], "main.sqlite")
        self.assertEqual(payload["artifact"]["artifact_kind"], "sqlite")
        self.assertEqual(payload["artifact"]["metrics"]["row_count"], 2)
        self.assertEqual(payload["artifact"]["metrics"]["pos_rows"], 1)


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
