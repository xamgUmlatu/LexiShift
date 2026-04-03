from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.translation_packs import (  # noqa: E402
    FORWARD_PACK_DIRECTION,
    REVERSE_PACK_DIRECTION,
    build_translation_pack_ref,
    resolve_configured_language_pack_paths,
)


class TestTranslationPacks(unittest.TestCase):
    def test_builds_forward_wiktionary_pack_ref_for_en_de(self) -> None:
        ref = build_translation_pack_ref(
            "en-de",
            Path("/tmp/wiktionary-de-en.sqlite"),
            direction=FORWARD_PACK_DIRECTION,
        )
        assert ref is not None
        self.assertEqual(ref.provider, "wiktionary")
        self.assertEqual(ref.pack_id, "wiktionary_de_en")
        self.assertEqual(ref.pos_source_profile, "wiktionary")

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

    def test_builds_manifest_backed_wiktionary_pack_ref_from_generic_sqlite_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = base_dir / "wiktionary-es-en"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="wiktionary-es-en",
                pack_kind="language",
                provider="wiktionary",
                local_kind="file",
                build_mode="kaikki_jsonl_to_sqlite",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )

            ref = build_translation_pack_ref(
                "en-es",
                artifact,
                direction=FORWARD_PACK_DIRECTION,
            )

        assert ref is not None
        self.assertEqual(ref.provider, "wiktionary")
        self.assertEqual(ref.pack_id, "wiktionary_es_en")
        self.assertEqual(ref.pos_source_profile, "wiktionary")

    def test_resolve_configured_language_pack_paths_prefers_managed_pack_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            pack_root = base_dir / "freedict-en-es"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                base_dir,
                pack_id="freedict-en-es",
                pack_kind="language",
                provider="freedict",
                local_kind="file",
                build_mode="freedict_tei_to_sqlite",
                artifact_path=artifact,
                sqlite_filename="main.sqlite",
            )

            resolved = resolve_configured_language_pack_paths(
                language_packs_dir=base_dir,
                settings_language_pack_paths={"wordnet-en": "/tmp/wordnet"},
                managed_language_pack_ids=("freedict-en-es",),
            )

        self.assertEqual(resolved["freedict-en-es"], str(artifact))
        self.assertEqual(resolved["wordnet-en"], "/tmp/wordnet")
