from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = REPO_ROOT / "core"
SCRIPTS_TESTING = REPO_ROOT / "scripts" / "testing"
for candidate in (CORE_ROOT, SCRIPTS_TESTING):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from rulegen_benchmark import (  # noqa: E402
    _build_pair_resources_payload,
    _resolve_pair_resources_for_benchmark,
)


class TestRulegenResourceContracts(unittest.TestCase):
    def test_benchmark_translation_contract_matches_runtime_helper_for_manifest_installs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            forward = self._write_manifest_backed_translation_pack(
                paths.language_packs_dir,
                pack_id="wiktionary-es-en",
                provider="wiktionary",
            )
            reverse = self._write_manifest_backed_translation_pack(
                paths.language_packs_dir,
                pack_id="wiktionary-en-es",
                provider="wiktionary",
            )

            _resolved_jmdict, translation_path, reverse_path = (
                _resolve_pair_resources_for_benchmark(
                    paths=paths,
                    pair="en-es",
                    jmdict_override=None,
                    translation_dict_override=None,
                    reverse_translation_dict_override=None,
                )
            )

            forward_pack, reverse_pack = resolve_pair_translation_packs(paths, pair="en-es")

            self.assertEqual(translation_path, forward)
            self.assertEqual(reverse_path, reverse)
            self.assertIsNotNone(forward_pack)
            self.assertIsNotNone(reverse_pack)
            assert forward_pack is not None
            assert reverse_pack is not None
            self.assertEqual(translation_path, forward_pack.path)
            self.assertEqual(reverse_path, reverse_pack.path)

            payload = _build_pair_resources_payload(
                pair="en-es",
                jmdict_path=None,
                translation_dict_path=translation_path,
                reverse_translation_dict_path=reverse_path,
            )

            self.assertEqual(payload["translation_pack_id"], forward_pack.pack_id)
            self.assertEqual(payload["translation_pack_provider"], forward_pack.provider)
            self.assertEqual(
                payload["translation_pack_pos_source_profile"],
                forward_pack.pos_source_profile,
            )
            self.assertEqual(payload["reverse_translation_pack_id"], reverse_pack.pack_id)
            self.assertEqual(payload["reverse_translation_pack_provider"], reverse_pack.provider)
            self.assertEqual(
                payload["reverse_translation_pack_pos_source_profile"],
                reverse_pack.pos_source_profile,
            )

    def test_benchmark_translation_contract_matches_runtime_helper_for_legacy_defaults(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = build_helper_paths(Path(tmp))
            forward = paths.language_packs_dir / "wiktionary-es-en.sqlite"
            reverse = paths.language_packs_dir / "wiktionary-en-es.sqlite"
            forward.parent.mkdir(parents=True, exist_ok=True)
            forward.write_bytes(b"SQLite format 3\x00")
            reverse.write_bytes(b"SQLite format 3\x00")

            _resolved_jmdict, translation_path, reverse_path = (
                _resolve_pair_resources_for_benchmark(
                    paths=paths,
                    pair="en-es",
                    jmdict_override=None,
                    translation_dict_override=None,
                    reverse_translation_dict_override=None,
                )
            )

            forward_pack, reverse_pack = resolve_pair_translation_packs(paths, pair="en-es")

            self.assertEqual(translation_path, forward)
            self.assertEqual(reverse_path, reverse)
            self.assertIsNotNone(forward_pack)
            self.assertIsNotNone(reverse_pack)
            assert forward_pack is not None
            assert reverse_pack is not None
            self.assertEqual(translation_path, forward_pack.path)
            self.assertEqual(reverse_path, reverse_pack.path)

            payload = _build_pair_resources_payload(
                pair="en-es",
                jmdict_path=None,
                translation_dict_path=translation_path,
                reverse_translation_dict_path=reverse_path,
            )

            self.assertEqual(payload["translation_pack_id"], forward_pack.pack_id)
            self.assertEqual(payload["translation_pack_provider"], forward_pack.provider)
            self.assertEqual(payload["reverse_translation_pack_id"], reverse_pack.pack_id)
            self.assertEqual(payload["reverse_translation_pack_provider"], reverse_pack.provider)

    def _write_manifest_backed_translation_pack(
        self,
        language_packs_dir: Path,
        *,
        pack_id: str,
        provider: str,
    ) -> Path:
        pack_root = language_packs_dir / pack_id
        pack_root.mkdir(parents=True, exist_ok=True)
        artifact = pack_root / "main.sqlite"
        artifact.write_bytes(b"SQLite format 3\x00")
        write_installed_pack_manifest(
            language_packs_dir,
            pack_id=pack_id,
            pack_kind="language",
            provider=provider,
            local_kind="file",
            build_mode="kaikki_jsonl_to_sqlite",
            artifact_path=artifact,
            sqlite_filename="main.sqlite",
        )
        return artifact


if __name__ == "__main__":
    unittest.main()
