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

from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.pack_provenance import (  # noqa: E402
    PACK_PROVENANCE_FILENAME,
    validate_pack_provenance_file,
)
from lexishift_core.helper.use_cases.semantic_pack_install import (  # noqa: E402
    DEFAULT_PACK_ID,
    SemanticPackInstallConfig,
    install_semantic_pack,
    resolve_semantic_pack_inventory_path,
)


class TestSemanticPackInstall(unittest.TestCase):
    def test_dry_run_reports_targets_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            report = install_semantic_pack(
                paths,
                config=SemanticPackInstallConfig(
                    pair="en-es",
                    profile_id="alpha test",
                    semantic_inventory=_sample_inventory(),
                    pack_id="en-es-active-only-v1",
                    dry_run=True,
                    generated_at="2026-05-10T00:00:00Z",
                ),
            )

            self.assertEqual(report["status"], "dry_run")
            self.assertEqual(report["profile_id"], "alpha_test")
            self.assertEqual(report["summary"]["rule_count"], 1)
            self.assertFalse(
                paths.semantic_inventory_path("en-es", profile_id="alpha_test").exists()
            )

    def test_installs_pack_copy_and_profile_publication_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_inventory = Path(tmp) / "source_inventory.json"
            source_inventory.write_text(
                json.dumps(_sample_inventory(), ensure_ascii=False), encoding="utf-8"
            )
            paths = build_helper_paths(Path(tmp) / "data-root")

            report = install_semantic_pack(
                paths,
                config=SemanticPackInstallConfig(
                    pair="en-es",
                    profile_id="semantic-alpha",
                    semantic_inventory_path=source_inventory,
                    pack_id="en-es-active-only-v1",
                    generated_at="2026-05-10T00:00:00Z",
                ),
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["summary"]["rule_count"], 1)
            self.assertTrue(report["written"]["ruleset"])
            inventory_path = paths.semantic_inventory_path("en-es", profile_id="semantic-alpha")
            manifest_path = paths.publication_manifest_path("en-es", profile_id="semantic-alpha")
            self.assertTrue(inventory_path.exists())
            self.assertTrue(manifest_path.exists())
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(inventory["profile_id"], "semantic-alpha")
            self.assertEqual(inventory["capability"]["competition_mode"], "active_only_anchor_cue")
            self.assertEqual(inventory["generation_id"], manifest["generation_id"])

            pack_inventory = (
                paths.language_packs_dir
                / "en-es"
                / "semantic_packs"
                / "en-es-active-only-v1"
                / "semantic_inventory.json"
            )
            pack_manifest = pack_inventory.with_name("manifest.json")
            pack_provenance = pack_inventory.with_name(PACK_PROVENANCE_FILENAME)
            self.assertTrue(pack_inventory.exists())
            self.assertTrue(pack_manifest.exists())
            self.assertTrue(pack_provenance.exists())
            pack_manifest_payload = json.loads(pack_manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                pack_manifest_payload["lineage"]["source_inventory_sha1"],
                report["source"]["semantic_inventory_sha1"],
            )
            self.assertEqual(
                pack_manifest_payload["artifacts"]["provenance"]["path"],
                str(pack_provenance),
            )
            self.assertEqual(validate_pack_provenance_file(pack_provenance), ())
            self.assertEqual(
                report["source"]["source_pack_provenance_path"],
                str(pack_provenance),
            )

    def test_installs_named_pack_from_existing_pack_copy_without_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp) / "data-root")
            pack_inventory = (
                paths.language_packs_dir
                / "en-es"
                / "semantic_packs"
                / "en-es-installed-pack-v1"
                / "semantic_inventory.json"
            )
            pack_inventory.parent.mkdir(parents=True, exist_ok=True)
            pack_inventory.write_text(
                json.dumps(_sample_inventory(), ensure_ascii=False),
                encoding="utf-8",
            )

            report = install_semantic_pack(
                paths,
                config=SemanticPackInstallConfig(
                    pair="en-es",
                    profile_id="semantic-alpha",
                    pack_id="en-es-installed-pack-v1",
                    generated_at="2026-05-10T00:00:00Z",
                    copy_pack=False,
                ),
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["summary"]["rule_count"], 1)
            self.assertEqual(
                report["source"]["semantic_inventory_path"],
                str(pack_inventory),
            )
            self.assertTrue(
                paths.semantic_inventory_path("en-es", profile_id="semantic-alpha").exists()
            )

    def test_default_dev_pack_resolves_to_current_tranche_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp) / "data-root")

            resolved = resolve_semantic_pack_inventory_path(
                paths=paths,
                pair="en-es",
                pack_id=DEFAULT_PACK_ID,
            )

            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertTrue(resolved.exists())
            self.assertEqual(
                resolved.name,
                "en-es-active-only-combined-full-v1-tranche-011_semantic_inventory.json",
            )


def _sample_inventory() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "triggers": {
            "family:bank:trigger": {
                "trigger_id": "family:bank:trigger",
                "source_phrase": "bank",
            }
        },
        "senses": {
            "family:bank:active": {
                "sense_id": "family:bank:active",
                "target_lemma": "banco",
                "evidence_views": {
                    "sense_label": "financial institution",
                    "all_evidence_text": "The bank approved the loan.",
                },
            },
            "family:bank:shadow": {
                "sense_id": "family:bank:shadow",
                "target_lemma": "orilla",
                "evidence_views": {
                    "sense_label": "river edge",
                    "all_evidence_text": "They sat on the bank of the river.",
                },
            },
        },
        "competition_sets": {
            "family:bank:banco:v1": {
                "competition_set_id": "family:bank:banco:v1",
                "trigger_id": "family:bank:trigger",
                "active_sense_id": "family:bank:active",
                "shadow_sense_ids": ["family:bank:shadow"],
            }
        },
        "phrase_sets": {},
    }


if __name__ == "__main__":
    unittest.main()
