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
    resolve_pair_translation_packs,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402


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
        self.assertTrue(str(forward.path).endswith("deu-eng.tei"))
        self.assertEqual(reverse.provider, "freedict")
        self.assertEqual(reverse.pack_id, "freedict_en_de")
