from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from pack_lifecycle_policy import audit_provenance_policy  # noqa: E402


class PackLifecyclePolicyTests(unittest.TestCase):
    def test_confirmed_frequency_provenance_is_promotion_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "provenance.json"
            path.write_text(
                json.dumps(_provenance_payload(), ensure_ascii=False),
                encoding="utf-8",
            )

            policy = audit_provenance_policy(provenance_path=path, pack_kind="frequency")

        self.assertEqual(policy["status"], "ok")
        self.assertTrue(policy["promotion_ready"])
        self.assertFalse(policy["review_required"])
        self.assertEqual(policy["source_identity_kind"], "source_version")
        self.assertEqual(policy["artifact_metric_keys"], list(_frequency_metrics()))

    def test_unconfirmed_or_incomplete_evidence_requires_review(self) -> None:
        payload = _provenance_payload(
            license_status="requires_review",
            source_version="",
            raw_sha1="",
            artifact_sha1="",
            metrics={},
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "provenance.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            policy = audit_provenance_policy(provenance_path=path, pack_kind="frequency")

        self.assertEqual(policy["status"], "review")
        self.assertFalse(policy["promotion_ready"])
        self.assertIn("license_status_requires_review", policy["review_reasons"])
        self.assertIn("missing_source_identity", policy["review_reasons"])
        self.assertIn("raw_artifact_checksum_missing", policy["review_reasons"])
        self.assertIn("generated_artifact_checksum_missing", policy["review_reasons"])
        self.assertIn("frequency_metrics_missing", policy["review_reasons"])

    def test_source_bundle_component_checksums_are_policy_checked(self) -> None:
        payload = _provenance_payload(source_version="")
        payload["source"]["source_bundle"] = {
            "bundle_id": "freq-de-default:de_frequency_pipeline",
            "bundle_kind": "generated_frequency_pipeline",
            "components": [
                {
                    "role": "corpus",
                    "source_name": "Leipzig",
                    "source_url": "https://example.com/deu_news_2023_1M.tar.gz",
                    "filename": "deu_news_2023_1M.tar.gz",
                    "sha256": "a" * 64,
                },
                {
                    "role": "pos_lexicon_primary",
                    "source_name": "german-pos-dict",
                    "source_url": "https://example.com/german.dict",
                    "filename": "german.dict",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "provenance.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            policy = audit_provenance_policy(provenance_path=path, pack_kind="frequency")

        self.assertEqual(policy["source_identity_kind"], "source_bundle")
        self.assertEqual(policy["source_bundle_component_count"], 2)
        self.assertEqual(policy["source_bundle_component_checksum_count"], 1)
        self.assertIn("source_bundle_component_checksum_missing", policy["review_reasons"])

    def test_missing_or_invalid_provenance_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            invalid = Path(tmp) / "invalid.json"
            invalid.write_text("{not json", encoding="utf-8")

            missing_policy = audit_provenance_policy(
                provenance_path=missing,
                pack_kind="frequency",
            )
            invalid_policy = audit_provenance_policy(
                provenance_path=invalid,
                pack_kind="frequency",
            )

        self.assertEqual(missing_policy["status"], "error")
        self.assertEqual(invalid_policy["status"], "error")
        self.assertIn("missing_provenance", missing_policy["review_reasons"])
        self.assertIn("invalid_provenance", invalid_policy["review_reasons"])


def _frequency_metrics() -> dict[str, int]:
    return {
        "distinct_lemma_count": 2,
        "pos_rows": 2,
        "row_count": 2,
        "topic_domain_rows": 0,
    }


def _provenance_payload(
    *,
    license_status: str = "confirmed",
    source_version: str = "spanish_lemmas20k:fixture",
    raw_sha1: str = "0" * 40,
    artifact_sha1: str = "1" * 40,
    metrics: dict[str, int] | None = None,
) -> dict[str, object]:
    raw_artifact = {"filename": "spanish_lemmas20k.txt"}
    if raw_sha1:
        raw_artifact["sha1"] = raw_sha1
    artifact = {
        "artifact_relpath": "main.sqlite",
        "artifact_kind": "sqlite",
    }
    if artifact_sha1:
        artifact["sha1"] = artifact_sha1
    if metrics is not None:
        artifact["metrics"] = dict(metrics)
    else:
        artifact["metrics"] = _frequency_metrics()
    source: dict[str, object] = {
        "source_name": "Corpus del Espanol",
        "source_url": "https://example.com/spanish_lemmas20k.txt",
        "license_status": license_status,
        "raw_artifacts": [raw_artifact],
    }
    if source_version:
        source["source_version"] = source_version
    return {
        "schema_version": 1,
        "pack_id": "freq-es-expanded-v1",
        "pack_kind": "frequency",
        "provider": "corpus-del-espanol",
        "source": source,
        "build": {
            "build_mode": "convert_archive",
            "command": "convert_frequency_to_sqlite",
        },
        "artifact": artifact,
    }


if __name__ == "__main__":
    unittest.main()
