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
from lexishift_core.replacement.core import VocabRule  # noqa: E402


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
                    "triggers": {"en-es:trigger:ball": {}},
                    "senses": {},
                    "competition_sets": {},
                    "phrase_sets": {},
                },
            )

            inventory_path = paths.semantic_inventory_path("en-es")
            self.assertTrue(inventory_path.exists())
            payload = json.loads(inventory_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["pair"], "en-es")
            self.assertEqual(payload["schema_version"], 1)

    def test_write_rulegen_outputs_removes_stale_semantic_inventory_when_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            inventory_path = paths.semantic_inventory_path("en-es")
            inventory_path.write_text('{"schema_version":1}', encoding="utf-8")

            write_rulegen_outputs(
                paths=paths,
                pair="en-es",
                rules=(VocabRule(source_phrase="ball", replacement="pelota"),),
                snapshot={"version": 1, "pair": "en-es", "targets": [], "stats": {}},
            )

            self.assertFalse(inventory_path.exists())


if __name__ == "__main__":
    unittest.main()
