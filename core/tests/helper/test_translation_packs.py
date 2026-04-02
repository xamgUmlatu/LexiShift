from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.translation_packs import (  # noqa: E402
    FORWARD_PACK_DIRECTION,
    REVERSE_PACK_DIRECTION,
    build_translation_pack_ref,
)


class TestTranslationPacks(unittest.TestCase):
    def test_builds_forward_wiktionary_pack_ref_for_en_es(self) -> None:
        ref = build_translation_pack_ref(
            "en-es",
            Path("/tmp/wiktionary-es-en.sqlite"),
            direction=FORWARD_PACK_DIRECTION,
        )
        assert ref is not None
        self.assertEqual(ref.provider, "wiktionary")
        self.assertEqual(ref.pack_id, "wiktionary_es_en")
        self.assertEqual(ref.pos_source_profile, "wiktionary")

    def test_builds_reverse_freedict_pack_ref_for_en_de(self) -> None:
        ref = build_translation_pack_ref(
            "en-de",
            Path("/tmp/eng-deu.sqlite"),
            direction=REVERSE_PACK_DIRECTION,
        )
        assert ref is not None
        self.assertEqual(ref.provider, "freedict")
        self.assertEqual(ref.pack_id, "freedict_en_de")
        self.assertEqual(ref.pos_source_profile, "freedict")

    def test_builds_forward_freedict_pack_ref_for_de_en(self) -> None:
        ref = build_translation_pack_ref(
            "de-en",
            Path("/tmp/eng-deu.tei"),
            direction=FORWARD_PACK_DIRECTION,
        )
        assert ref is not None
        self.assertEqual(ref.provider, "freedict")
        self.assertEqual(ref.pack_id, "freedict_en_de")
        self.assertEqual(ref.pos_source_profile, "freedict")
