from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from i18n import set_locale
from language_packs import PackTransportOverride
from settings_language_packs import LanguagePackPanel
from settings_language_packs_support import (
    LANGUAGE_RESOURCE_FAMILY_SECONDARY,
    LANGUAGE_RESOURCE_FAMILY_TRANSLATION,
    LANGUAGE_RESOURCE_ORIGIN_MANAGED,
    LANGUAGE_RESOURCE_ORIGIN_MANUAL,
    LanguageResourceBinding,
)


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _write_sqlite_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"SQLite format 3\x00")


def _write_frequency_sqlite(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as conn:
        conn.execute("CREATE TABLE frequency (lemma TEXT, rank INTEGER)")
        conn.commit()


def test_language_pack_table_marks_managed_artifact_as_installed() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        panel._language_pack_dir = str(root / "language_packs")
        managed = root / "language_packs" / "freedict-en-es" / "main.sqlite"
        _write_sqlite_header(managed)
        panel._language_resource_bindings = {
            "freedict-en-es": LanguageResourceBinding(
                pack_id="freedict-en-es",
                family=LANGUAGE_RESOURCE_FAMILY_TRANSLATION,
                origin=LANGUAGE_RESOURCE_ORIGIN_MANAGED,
                effective_path=str(managed),
            )
        }

        panel._refresh_language_pack_table()

        row = panel._language_pack_rows["freedict-en-es"]
        assert row.status_item.text() == "Installed"
        assert row.status_item.toolTip() == str(managed)


def test_language_pack_table_marks_external_translation_source_as_manual() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        panel._language_pack_dir = str(root / "language_packs")
        manual = root / "manual" / "eng-spa.tei"
        manual.parent.mkdir(parents=True, exist_ok=True)
        manual.write_text("<tei/>", encoding="utf-8")
        panel._language_resource_bindings = {
            "freedict-en-es": LanguageResourceBinding(
                pack_id="freedict-en-es",
                family=LANGUAGE_RESOURCE_FAMILY_TRANSLATION,
                origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                effective_path=str(manual),
            )
        }

        panel._refresh_language_pack_table()

        row = panel._language_pack_rows["freedict-en-es"]
        assert row.status_item.text() == "Manual"
        assert row.status_item.toolTip() == str(manual)


def test_language_pack_table_marks_secondary_source_as_manual_from_binding() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()

    with TemporaryDirectory() as temp_dir:
        wordnet_dir = Path(temp_dir) / "wordnet"
        wordnet_dir.mkdir(parents=True, exist_ok=True)
        (wordnet_dir / "entries-a.json").write_text("[]", encoding="utf-8")
        panel._language_resource_bindings = {
            "wordnet-en": LanguageResourceBinding(
                pack_id="wordnet-en",
                family=LANGUAGE_RESOURCE_FAMILY_SECONDARY,
                origin=LANGUAGE_RESOURCE_ORIGIN_MANUAL,
                effective_path=str(wordnet_dir),
            )
        }

        panel._refresh_language_pack_table()

        row = panel._language_pack_rows["wordnet-en"]
        assert row.status_item.text() == "Manual"
        assert row.status_item.toolTip() == str(wordnet_dir)


def test_embedding_manual_selection_rejects_unsupported_file_format() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()
    pack = panel._embedding_pack_info["embed-en-cc"]

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        vector = root / "manual.vec"
        vector.write_text("hello 0.1 0.2\n", encoding="utf-8")
        unsupported = root / "not-embeddings.pdf"
        unsupported.write_bytes(b"%PDF-1.7\n")

        valid_vector, _vector_message = panel._validate_embedding_pack_path(pack, str(vector))
        valid_unsupported, unsupported_message = panel._validate_embedding_pack_path(
            pack,
            str(unsupported),
        )

    assert valid_vector is True
    assert valid_unsupported is False
    assert "expects a SQLite embedding database" in unsupported_message


def test_frequency_pack_table_marks_managed_artifact_as_installed() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        panel._frequency_pack_dir = str(root / "frequency_packs")
        managed = root / "frequency_packs" / "freq-en-coca" / "main.sqlite"
        _write_frequency_sqlite(managed)
        panel._frequency_pack_paths = {"freq-en-coca": str(managed)}

        panel._refresh_frequency_pack_table()

        row = panel._frequency_pack_rows["freq-en-coca"]
        assert row.status_item.text() == "Installed"
        assert row.status_item.toolTip() == str(managed)


def test_frequency_pack_table_marks_manifest_disabled_source_as_disabled() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel(
        pack_source_overrides={
            "freq-en-coca": PackTransportOverride(
                disabled=True,
                disabled_reason="Temporarily unavailable",
            )
        }
    )

    row = panel._frequency_pack_rows["freq-en-coca"]
    assert row.status_item.text() == "Disabled"
    assert row.status_item.toolTip() == "Temporarily unavailable"
    assert not row.download_button.isEnabled()
    assert row.download_button.toolTip() == "Temporarily unavailable"


def test_embedding_pack_table_distinguishes_active_manual_and_installed() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        panel._embedding_pack_dir = str(root / "embedding_packs")

        managed = root / "embedding_packs" / "embed-xling-es" / "main.sqlite"
        manual = root / "manual" / "embed-xling-es.sqlite"
        _write_sqlite_header(managed)
        _write_sqlite_header(manual)

        panel._embedding_pack_paths = {"embed-xling-es": str(manual)}
        panel._embedding_pair_paths = {"en-es": [str(manual)]}
        panel._embedding_pair_pack_ids = {}
        panel._embedding_pair_enabled = {"en-es": True}
        panel._refresh_cross_embedding_pack_table()

        row = panel._cross_embedding_pack_rows["embed-xling-es"]
        assert row.status_item.text() == "Active (Manual)"
        assert row.status_item.toolTip() == str(manual)

        panel._embedding_pack_paths = {"embed-xling-es": str(managed)}
        panel._embedding_pair_paths = {}
        panel._embedding_pair_pack_ids = {"en-es": ["embed-xling-es"]}
        panel._embedding_pair_enabled = {"en-es": True}
        panel._refresh_cross_embedding_pack_table()

        row = panel._cross_embedding_pack_rows["embed-xling-es"]
        assert row.status_item.text() == "Active (Installed)"
        assert row.status_item.toolTip() == str(managed)
