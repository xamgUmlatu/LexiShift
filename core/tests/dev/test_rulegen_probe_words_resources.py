from __future__ import annotations

import importlib
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = REPO_ROOT / "core"
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

installed_packs = importlib.import_module("lexishift_core.helper.installed_packs")
probe_words_support = importlib.import_module("rulegen_probe_words_support")


class TestRulegenProbeWordsResources(unittest.TestCase):
    def test_build_pair_resources_payload_reports_installed_pack_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            language_packs_dir = tmp_root / "language_packs"
            frequency_packs_dir = tmp_root / "frequency_packs"

            translation_artifact = self._write_manifest_backed_pack(
                base_dir=language_packs_dir,
                pack_id="freedict_de_en",
                provider="freedict",
            )
            reverse_translation_artifact = self._write_manifest_backed_pack(
                base_dir=language_packs_dir,
                pack_id="freedict_en_de",
                provider="freedict",
            )
            source_frequency_artifact = self._write_manifest_backed_pack(
                base_dir=frequency_packs_dir,
                pack_id="freq-en-coca",
                provider="freq-en-coca",
            )

            payload = probe_words_support.build_pair_resources_payload(
                pair="en-de",
                jmdict_path=None,
                translation_dict_path=translation_artifact,
                reverse_translation_dict_path=reverse_translation_artifact,
                source_frequency_db_path=source_frequency_artifact,
            )

            self.assertEqual(payload["translation_pack_id"], "freedict_de_en")
            self.assertEqual(payload["translation_pack_provider"], "freedict")
            self.assertEqual(payload["translation_pack_pos_source_profile"], "freedict")
            self.assertEqual(
                payload["reverse_translation_pack_id"],
                "freedict_en_de",
            )
            self.assertEqual(payload["reverse_translation_pack_provider"], "freedict")
            self.assertEqual(payload["source_frequency_pack_id"], "freq-en-coca")
            self.assertEqual(payload["source_frequency_pack_provider"], "freq-en-coca")
            self.assertEqual(
                payload["source_frequency_pack_pos_source_profile"],
                "compact-latin",
            )
            self.assertEqual(payload["translation_dict_path"], str(translation_artifact))
            self.assertEqual(
                payload["reverse_translation_dict_path"],
                str(reverse_translation_artifact),
            )
            self.assertEqual(
                payload["source_frequency_db_path"],
                str(source_frequency_artifact),
            )

    def test_build_pair_resources_payload_keeps_manual_override_identity_generic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            translation_artifact = tmp_root / "wiktionary-de-en.sqlite"
            reverse_translation_artifact = tmp_root / "wiktionary-en-de.sqlite"
            translation_artifact.touch()
            reverse_translation_artifact.touch()

            payload = probe_words_support.build_pair_resources_payload(
                pair="en-de",
                jmdict_path=None,
                translation_dict_path=translation_artifact,
                reverse_translation_dict_path=reverse_translation_artifact,
            )

            self.assertEqual(payload["translation_pack_id"], "wiktionary_de_en")
            self.assertEqual(payload["translation_pack_provider"], "wiktionary")
            self.assertEqual(
                payload["reverse_translation_pack_id"],
                "wiktionary_en_de",
            )
            self.assertEqual(payload["reverse_translation_pack_provider"], "wiktionary")
            self.assertEqual(payload["translation_dict_path"], str(translation_artifact))
            self.assertEqual(
                payload["reverse_translation_dict_path"],
                str(reverse_translation_artifact),
            )

    @staticmethod
    def _write_manifest_backed_pack(
        *,
        base_dir: Path,
        pack_id: str,
        provider: str,
    ) -> Path:
        pack_root = base_dir / pack_id
        pack_root.mkdir(parents=True, exist_ok=True)
        artifact_path = pack_root / "main.sqlite"
        artifact_path.touch()
        installed_packs.write_installed_pack_manifest(
            base_dir,
            pack_id=pack_id,
            pack_kind="language",
            provider=provider,
            local_kind="file",
            build_mode="compiled_sqlite",
            artifact_path=artifact_path,
            sqlite_filename="main.sqlite",
        )
        return artifact_path


if __name__ == "__main__":
    unittest.main()
