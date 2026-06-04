from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.frequency.de.build_support import (  # noqa: E402
    discover_dictionary_paths,
    load_freedict_headwords,
)
from lexishift_core.frequency.de.pipeline import _ensure_freedict_de_en  # noqa: E402
from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402


class TestDeBuildSupport(unittest.TestCase):
    def test_load_freedict_headwords_accepts_sqlite_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "freedict-de-en.sqlite"
            conn = sqlite3.connect(path)
            try:
                conn.execute(
                    "CREATE TABLE entries ("
                    "headword TEXT, "
                    "headword_lc TEXT, "
                    "translation TEXT, "
                    "translation_lc TEXT, "
                    "rank INTEGER, "
                    "pos TEXT, "
                    "entry_ord INTEGER, "
                    "gloss_ord INTEGER"
                    ")"
                )
                conn.execute(
                    "INSERT INTO entries (headword, headword_lc, translation, translation_lc, rank, pos, entry_ord, gloss_ord) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("Häuser", "häuser", "houses", "houses", 1, "noun", 1, 0),
                )
                conn.commit()
            finally:
                conn.close()

            lemmas = load_freedict_headwords(path)

        self.assertEqual(lemmas, {"häuser"})

    def test_discover_dictionary_paths_prefers_manifest_backed_freedict_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            pack_root = language_packs_dir / "freedict-de-en"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="freedict-de-en",
                pack_kind="language",
                provider="freedict",
                local_kind="dir",
                build_mode="freedict_tei_to_sqlite",
                artifact_path=artifact,
                source_filename="freedict-deu-eng-1.9-fd1.src.tar.xz",
                sqlite_filename="main.sqlite",
                required_files=("deu-eng.tei",),
            )

            resolved_freedict, resolved_odenet, resolved_open = discover_dictionary_paths(
                language_packs_dir=language_packs_dir,
                freedict_de_en_path=None,
                odenet_path=None,
                openthesaurus_path=None,
            )

        self.assertEqual(resolved_freedict, artifact)
        self.assertIsNone(resolved_odenet)
        self.assertIsNone(resolved_open)

    def test_ensure_freedict_de_en_reuses_manifest_backed_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp) / "language_packs"
            workspace_dir = Path(tmp) / "workspace"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            pack_root = language_packs_dir / "freedict-de-en"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")
            write_installed_pack_manifest(
                language_packs_dir,
                pack_id="freedict-de-en",
                pack_kind="language",
                provider="freedict",
                local_kind="dir",
                build_mode="freedict_tei_to_sqlite",
                artifact_path=artifact,
                source_filename="freedict-deu-eng-1.9-fd1.src.tar.xz",
                sqlite_filename="main.sqlite",
                required_files=("deu-eng.tei",),
            )

            resolved = _ensure_freedict_de_en(
                language_packs_dir=language_packs_dir,
                workspace_dir=workspace_dir,
            )

        self.assertEqual(resolved, artifact)

    def test_discover_dictionary_paths_accepts_main_sqlite_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            language_packs_dir = Path(tmp)
            pack_root = language_packs_dir / "freedict-de-en"
            pack_root.mkdir(parents=True, exist_ok=True)
            artifact = pack_root / "main.sqlite"
            artifact.write_bytes(b"SQLite format 3\x00")

            resolved_freedict, resolved_odenet, resolved_open = discover_dictionary_paths(
                language_packs_dir=language_packs_dir,
                freedict_de_en_path=None,
                odenet_path=None,
                openthesaurus_path=None,
            )

        self.assertEqual(resolved_freedict, artifact)
        self.assertIsNone(resolved_odenet)
        self.assertIsNone(resolved_open)


if __name__ == "__main__":
    unittest.main()
