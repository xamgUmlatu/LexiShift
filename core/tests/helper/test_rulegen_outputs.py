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
from lexishift_core.helper.rulegen_outputs import write_rulegen_outputs  # noqa: E402
from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402


class TestRulegenOutputs(unittest.TestCase):
    def test_write_rulegen_outputs_writes_semantic_inventory_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            write_rulegen_outputs(
                paths=paths,
                pair="en-es",
                rules=(VocabRule(source_phrase="ball", replacement="pelota"),),
                snapshot={"version": 1, "pair": "en-es", "targets": [], "stats": {}},
                semantic_inventory={
                    "schema_version": 1,
                    "pair": "en-es",
                    "profile_id": "default",
                    "generated_at": "2026-04-10T00:00:00Z",
                    "capability": {
                        "pointer_modes": ["sense_provenance", "translation_gloss"],
                        "default_unavailable_reason_code": "missing_source_sense_locator",
                        "competition_mode": "not_published",
                        "competition_reason_code": "missing_shadow_selection",
                        "phrase_mode": "not_published",
                        "phrase_reason_code": "missing_phrase_inventory",
                    },
                    "triggers": {"en-es:trigger:ball": {}},
                    "senses": {},
                    "competition_sets": {},
                    "phrase_sets": {},
                },
            )

            inventory_path = paths.semantic_inventory_path("en-es")
            manifest_path = paths.publication_manifest_path("en-es")
            snapshot_path = paths.snapshot_path("en-es")
            self.assertTrue(inventory_path.exists())
            self.assertTrue(manifest_path.exists())
            payload = json.loads(inventory_path.read_text(encoding="utf-8"))
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["pair"], "en-es")
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["generation_id"], manifest_payload["generation_id"])
            self.assertEqual(snapshot_payload["generation_id"], manifest_payload["generation_id"])
            self.assertTrue(manifest_payload["validation"]["family_valid"])
            self.assertEqual(
                payload["capability"]["default_unavailable_reason_code"],
                "missing_source_sense_locator",
            )

    def test_write_rulegen_outputs_removes_stale_semantic_inventory_when_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            inventory_path = paths.semantic_inventory_path("en-es")
            manifest_path = paths.publication_manifest_path("en-es")
            inventory_path.write_text('{"schema_version":1}', encoding="utf-8")

            write_rulegen_outputs(
                paths=paths,
                pair="en-es",
                rules=(VocabRule(source_phrase="ball", replacement="pelota"),),
                snapshot={"version": 1, "pair": "en-es", "targets": [], "stats": {}},
            )

            self.assertFalse(inventory_path.exists())
            self.assertTrue(manifest_path.exists())
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertFalse(manifest_payload["artifacts"]["semantic_inventory"]["exists"])
            self.assertTrue(manifest_payload["validation"]["family_valid"])

    def test_write_rulegen_outputs_rejects_ready_semantic_pointer_without_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            rule = VocabRule(
                source_phrase="ball",
                replacement="pelota",
                metadata=RuleMetadata(
                    semantic_admission={
                        "schema_version": 1,
                        "status": "ready",
                        "trigger_id": "en-es:trigger:ball",
                        "sense_id": "en-es:test:pelota:1",
                        "competition_set_id": "en-es:ball:pelota:v1",
                    }
                ),
            )

            with self.assertRaisesRegex(
                ValueError,
                "status=ready semantic_admission but no semantic inventory was published",
            ):
                write_rulegen_outputs(
                    paths=paths,
                    pair="en-es",
                    rules=(rule,),
                    snapshot={"version": 1, "pair": "en-es", "targets": [], "stats": {}},
                )

            self.assertFalse(paths.ruleset_path("en-es").exists())
            self.assertFalse(paths.snapshot_path("en-es").exists())
            self.assertFalse(paths.publication_manifest_path("en-es").exists())


if __name__ == "__main__":
    unittest.main()
