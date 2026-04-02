from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.pair_resources import (  # noqa: E402
    resolve_pair_resources,
    resolve_pair_translation_packs,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402


class TestPairResources(unittest.TestCase):
    def test_resolve_pair_translation_packs_uses_en_es_kaikki_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            forward, reverse = resolve_pair_translation_packs(paths, pair="en-es")
        assert forward is not None
        assert reverse is not None
        self.assertEqual(forward.provider, "wiktionary")
        self.assertEqual(forward.pack_id, "wiktionary_es_en")
        self.assertTrue(str(forward.path).endswith("wiktionary-es-en.sqlite"))
        self.assertEqual(reverse.provider, "wiktionary")
        self.assertEqual(reverse.pack_id, "wiktionary_en_es")
        self.assertTrue(str(reverse.path).endswith("wiktionary-en-es.sqlite"))

    def test_resolve_pair_translation_packs_uses_en_de_freedict_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            forward, reverse = resolve_pair_translation_packs(paths, pair="en-de")
        assert forward is not None
        assert reverse is not None
        self.assertEqual(forward.provider, "freedict")
        self.assertEqual(forward.pack_id, "freedict_de_en")
        self.assertTrue(str(forward.path).endswith("freedict-de-en.sqlite"))
        self.assertEqual(reverse.provider, "freedict")
        self.assertEqual(reverse.pack_id, "freedict_en_de")
        self.assertTrue(str(reverse.path).endswith("freedict-en-de.sqlite"))

    def test_resolve_pair_translation_packs_uses_de_en_freedict_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            forward, reverse = resolve_pair_translation_packs(paths, pair="de-en")
        assert forward is not None
        assert reverse is not None
        self.assertEqual(forward.provider, "freedict")
        self.assertEqual(forward.pack_id, "freedict_en_de")
        self.assertTrue(str(forward.path).endswith("freedict-en-de.sqlite"))
        self.assertEqual(reverse.provider, "freedict")
        self.assertEqual(reverse.pack_id, "freedict_de_en")
        self.assertTrue(str(reverse.path).endswith("freedict-de-en.sqlite"))

    def test_resolve_pair_resources_prefers_manifest_backed_frequency_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            pack_root = paths.frequency_packs_dir / "freq-es-cde"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "freq-es-cde.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                paths.frequency_packs_dir,
                pack_id="freq-es-cde",
                pack_kind="frequency",
                provider="freq-es-cde",
                local_kind="file",
                build_mode="convert_archive",
                artifact_path=artifact,
                sqlite_filename="freq-es-cde.sqlite",
            )
            _resolved_jmdict, _resolved_translation, resolved_frequency = resolve_pair_resources(
                paths,
                pair="en-es",
                jmdict_path=None,
                translation_dict_path=None,
                freedict_de_en_path=None,
                set_source_db=None,
            )
        self.assertEqual(resolved_frequency, artifact)
