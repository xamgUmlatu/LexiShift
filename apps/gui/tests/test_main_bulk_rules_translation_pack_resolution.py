from __future__ import annotations

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = REPO_ROOT / "core"
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
for candidate in (str(CORE_ROOT), str(GUI_SRC)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.installed_packs import (  # noqa: E402
    write_installed_pack_manifest,
)
from lexishift_core.helper.translation_packs import (  # noqa: E402
    resolve_configured_language_pack_paths,
)
from lexishift_core import SynonymSourceSettings  # noqa: E402
from main_bulk_rules_mixin import (  # noqa: E402
    MainWindowBulkRulesMixin,
    _resolve_translation_pack_path,
)


def test_resolve_translation_pack_path_prefers_manifest_backed_sqlite() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_root = root / "freedict-de-en"
        pack_root.mkdir(parents=True, exist_ok=True)
        artifact = pack_root / "main.sqlite"
        artifact.write_text("placeholder", encoding="utf-8")
        write_installed_pack_manifest(
            root,
            pack_id="freedict-de-en",
            pack_kind="language",
            provider="freedict",
            local_kind="dir",
            build_mode="freedict_tei_to_sqlite",
            artifact_path=artifact,
            sqlite_filename="main.sqlite",
        )

        resolved = _resolve_translation_pack_path(
            str(pack_root),
            sqlite_artifact_names=("freedict-de-en.sqlite", "deu-eng.sqlite"),
        )

    assert resolved == str(artifact)


def test_resolve_translation_pack_path_accepts_legacy_sqlite_directory_artifact() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_root = root / "freedict-de-en"
        pack_root.mkdir(parents=True, exist_ok=True)
        artifact = pack_root / "deu-eng.sqlite"
        artifact.write_text("placeholder", encoding="utf-8")

        resolved = _resolve_translation_pack_path(
            str(pack_root),
            sqlite_artifact_names=("freedict-de-en.sqlite", "deu-eng.sqlite"),
        )

    assert resolved == str(artifact)


def test_resolve_translation_pack_path_rejects_raw_tei_directory_fallback() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_root = root / "freedict-de-en"
        pack_root.mkdir(parents=True, exist_ok=True)
        tei = pack_root / "deu-eng.tei"
        tei.write_text("<TEI/>", encoding="utf-8")

        resolved = _resolve_translation_pack_path(
            str(pack_root),
            sqlite_artifact_names=("freedict-de-en.sqlite", "deu-eng.sqlite"),
        )

    assert resolved is None


def test_resolve_translation_pack_path_preserves_manual_file_paths() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        tei = root / "deu-eng.tei"
        tei.write_text("<TEI/>", encoding="utf-8")

        resolved = _resolve_translation_pack_path(
            str(tei),
            sqlite_artifact_names=("freedict-de-en.sqlite", "deu-eng.sqlite"),
        )

    assert resolved == str(tei)


def test_configured_language_pack_paths_include_managed_translation_pack_ids() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_root = root / "language_packs" / "freedict-en-es"
        pack_root.mkdir(parents=True, exist_ok=True)
        artifact = pack_root / "main.sqlite"
        artifact.write_text("placeholder", encoding="utf-8")
        write_installed_pack_manifest(
            root / "language_packs",
            pack_id="freedict-en-es",
            pack_kind="language",
            provider="freedict",
            local_kind="dir",
            build_mode="freedict_tei_to_sqlite",
            artifact_path=artifact,
            sqlite_filename="main.sqlite",
        )
        settings = SynonymSourceSettings(
            managed_language_pack_ids=("freedict-en-es",),
            language_pack_paths={"wordnet-en": "/tmp/wordnet"},
        )

        resolved = resolve_configured_language_pack_paths(
            language_packs_dir=root / "language_packs",
            settings_language_pack_paths=settings.language_pack_paths,
            managed_language_pack_ids=settings.managed_language_pack_ids,
        )

    assert resolved["freedict-en-es"] == str(artifact)
    assert resolved["wordnet-en"] == "/tmp/wordnet"


def test_configured_language_pack_paths_prefer_managed_artifact_over_same_key_manual_entry() -> (
    None
):
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_root = root / "language_packs" / "freedict-en-es"
        pack_root.mkdir(parents=True, exist_ok=True)
        artifact = pack_root / "main.sqlite"
        artifact.write_text("placeholder", encoding="utf-8")
        stale = root / "manual.sqlite"
        stale.write_text("placeholder", encoding="utf-8")
        write_installed_pack_manifest(
            root / "language_packs",
            pack_id="freedict-en-es",
            pack_kind="language",
            provider="freedict",
            local_kind="dir",
            build_mode="freedict_tei_to_sqlite",
            artifact_path=artifact,
            sqlite_filename="main.sqlite",
        )
        settings = SynonymSourceSettings(
            managed_language_pack_ids=("freedict-en-es",),
            language_pack_paths={"freedict-en-es": str(stale)},
        )

        resolved = resolve_configured_language_pack_paths(
            language_packs_dir=root / "language_packs",
            settings_language_pack_paths=settings.language_pack_paths,
            managed_language_pack_ids=settings.managed_language_pack_ids,
        )

    assert resolved["freedict-en-es"] == str(artifact)


def test_default_bulk_pack_ids_include_secondary_binding_map_entries_without_legacy_fields() -> (
    None
):
    dummy = type("Dummy", (MainWindowBulkRulesMixin,), {})()
    dummy.state = type(
        "State",
        (),
        {
            "settings": type(
                "Settings",
                (),
                {
                    "synonyms": SynonymSourceSettings(
                        language_pack_paths={
                            "wordnet-en": "/tmp/wordnet-binding",
                            "moby-en": "/tmp/moby-binding.txt",
                        }
                    )
                },
            )()
        },
    )()

    resolved = MainWindowBulkRulesMixin._default_bulk_pack_ids(dummy)

    assert resolved == {"wordnet-en", "moby-en"}
