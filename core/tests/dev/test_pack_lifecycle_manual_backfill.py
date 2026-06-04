from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (CORE_ROOT, SCRIPTS_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from lexishift_core.helper.installed_packs import write_installed_pack_manifest  # noqa: E402
from pack_lifecycle_manual_backfill import (  # noqa: E402
    backfill_manual_resource_settings,
    render_backfill_markdown,
)


class PackLifecycleManualBackfillTests(unittest.TestCase):
    def test_dry_run_promotes_only_app_managed_sqlite_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            settings_path, paths = _write_backfill_fixture(data_root)
            original_settings = settings_path.read_text(encoding="utf-8")

            report = backfill_manual_resource_settings(
                settings_path,
                generated_at="2026-05-15T00:00:00+00:00",
            )
            markdown = render_backfill_markdown(report)
            current_settings = settings_path.read_text(encoding="utf-8")

        self.assertEqual(report["status"], "would_update")
        self.assertTrue(report["changed"])
        self.assertEqual(current_settings, original_settings)
        self.assertEqual(len(report["changes"]), 4)
        self.assertIn("migrate_manual_path_to_managed_id", markdown)
        self.assertIn("embed-xling-es", markdown)
        self.assertEqual(paths["external_frequency"].name, "manual-frequency.sqlite")

    def test_apply_rewrites_managed_paths_and_leaves_external_paths_manual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            settings_path, paths = _write_backfill_fixture(data_root)

            report = backfill_manual_resource_settings(
                settings_path,
                apply_changes=True,
                generated_at="2026-05-15T00:00:00+00:00",
            )
            updated = json.loads(settings_path.read_text(encoding="utf-8"))
            backup_path = Path(report["backup_path"])
            backup_exists = backup_path.is_file()

        synonyms = updated["synonyms"]
        self.assertEqual(report["status"], "applied")
        self.assertTrue(backup_exists)
        self.assertEqual(synonyms["managed_language_pack_ids"], ["freedict-en-es"])
        self.assertNotIn("freedict-en-es", synonyms.get("language_pack_paths", {}))
        self.assertEqual(
            synonyms["language_pack_paths"]["wordnet-en"],
            str(paths["external_wordnet"]),
        )
        self.assertEqual(synonyms["managed_frequency_pack_ids"], ["freq-es-cde"])
        self.assertEqual(
            synonyms["frequency_pack_paths"]["freq-manual"],
            str(paths["external_frequency"]),
        )
        self.assertNotIn("embed-xling-es", synonyms.get("embedding_pack_paths", {}))
        self.assertEqual(
            synonyms["embedding_pack_paths"]["embed-manual"],
            str(paths["external_embedding"]),
        )
        self.assertEqual(synonyms["embedding_pair_pack_ids"]["en-es"], ["embed-xling-es"])
        self.assertEqual(
            synonyms["embedding_pair_paths"]["en-es"],
            [str(paths["external_embedding"])],
        )
        self.assertTrue(synonyms["embedding_pair_enabled"]["en-es"])


def _write_backfill_fixture(data_root: Path) -> tuple[Path, dict[str, Path]]:
    language_artifact = _write_managed_sqlite_pack(
        data_root,
        family_dir="language_packs",
        pack_id="freedict-en-es",
        pack_kind="language",
    )
    frequency_artifact = _write_managed_sqlite_pack(
        data_root,
        family_dir="frequency_packs",
        pack_id="freq-es-cde",
        pack_kind="frequency",
    )
    embedding_artifact = _write_managed_sqlite_pack(
        data_root,
        family_dir="embedding_packs",
        pack_id="embed-xling-es",
        pack_kind="embedding",
    )
    external_dir = data_root / "manual_imports"
    external_dir.mkdir(parents=True)
    external_frequency = external_dir / "manual-frequency.sqlite"
    external_frequency.write_bytes(b"SQLite format 3\x00")
    external_embedding = external_dir / "manual.vec"
    external_embedding.write_text("hola 0.1 0.2\n", encoding="utf-8")
    external_wordnet = external_dir / "wordnet"
    external_wordnet.mkdir()
    settings_path = data_root / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "synonyms": {
                    "language_pack_paths": {
                        "freedict-en-es": str(language_artifact),
                        "wordnet-en": str(external_wordnet),
                    },
                    "frequency_pack_paths": {
                        "freq-es-cde": str(frequency_artifact),
                        "freq-manual": str(external_frequency),
                    },
                    "embedding_pack_paths": {
                        "embed-xling-es": str(embedding_artifact),
                        "embed-manual": str(external_embedding),
                    },
                    "embedding_pair_paths": {
                        "en-es": [str(embedding_artifact), str(external_embedding)]
                    },
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return settings_path, {
        "external_frequency": external_frequency,
        "external_embedding": external_embedding,
        "external_wordnet": external_wordnet,
    }


def _write_managed_sqlite_pack(
    data_root: Path,
    *,
    family_dir: str,
    pack_id: str,
    pack_kind: str,
) -> Path:
    base_dir = data_root / family_dir
    artifact = base_dir / pack_id / "main.sqlite"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"SQLite format 3\x00")
    write_installed_pack_manifest(
        base_dir,
        pack_id=pack_id,
        pack_kind=pack_kind,
        provider="fixture",
        local_kind="file",
        build_mode="fixture",
        artifact_path=artifact,
        source_filename=f"{pack_id}.source",
        sqlite_filename="main.sqlite",
    )
    return artifact


if __name__ == "__main__":
    unittest.main()
