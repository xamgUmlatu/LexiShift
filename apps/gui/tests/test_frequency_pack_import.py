from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from frequency_pack_import import import_frequency_source_file  # noqa: E402
from i18n import set_locale  # noqa: E402
from language_packs import build_pack_catalogs  # noqa: E402
from lexishift_core.helper.pack_provenance import PACK_PROVENANCE_FILENAME  # noqa: E402
from lexishift_core.helper.pack_provenance import validate_pack_provenance_file  # noqa: E402
from settings_language_packs import LanguagePackPanel  # noqa: E402


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _freq_es_pack():
    catalogs = build_pack_catalogs(source_overrides={})
    return next(pack for pack in catalogs.frequency_packs if pack.pack_id == "freq-es-cde")


def _write_cde_source(path: Path) -> None:
    path.write_text(
        "ID\tfreq\tlemma\tpos\n1\t100\tgato\tn\n2\t80\tverde\tj\n",
        encoding="latin-1",
    )


def test_import_frequency_source_file_converts_managed_pack_without_deleting_user_file() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        user_source = root / "Downloads" / "spanish_lemmas20k.txt"
        user_source.parent.mkdir()
        _write_cde_source(user_source)
        frequency_dir = root / "frequency_packs"

        sqlite_path = import_frequency_source_file(
            _freq_es_pack(),
            user_source,
            frequency_pack_dir=frequency_dir,
        )

        pack_root = frequency_dir / "freq-es-cde"
        provenance_path = pack_root / PACK_PROVENANCE_FILENAME
        manifest_path = pack_root / "manifest.json"
        staged_files = tuple(pack_root.glob(".import-*"))

        assert user_source.exists()
        assert sqlite_path == pack_root / "main.sqlite"
        assert manifest_path.exists()
        assert validate_pack_provenance_file(provenance_path) == ()
        assert staged_files == ()

        with sqlite3.connect(sqlite_path) as conn:
            row_count = conn.execute("select count(*) from frequency").fetchone()[0]
            metadata = json.loads(
                conn.execute("select value from meta where key='metadata'").fetchone()[0]
            )
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        assert row_count == 2
        assert metadata["rows_with_pos"] == 2
        assert payload["pack_id"] == "freq-es-cde"
        assert payload["source"]["raw_artifacts"][0]["filename"] == "spanish_lemmas20k.txt"
        assert payload["artifact"]["metrics"]["row_count"] == 2


def test_frequency_pack_panel_imports_freq_es_raw_source_as_managed_pack(monkeypatch) -> None:
    _app()
    set_locale("en")
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        user_source = root / "Downloads" / "spanish_lemmas20k.txt"
        user_source.parent.mkdir()
        _write_cde_source(user_source)
        panel = LanguagePackPanel(pack_source_overrides={})
        panel._frequency_pack_dir = str(root / "frequency_packs")

        monkeypatch.setattr(
            "settings_language_packs.QFileDialog.getOpenFileName",
            lambda *_args, **_kwargs: (str(user_source), ""),
        )
        monkeypatch.setattr(panel, "_confirm_frequency_import_rights", lambda _pack: True)

        panel._select_frequency_pack_path("freq-es-cde")

        sqlite_path = root / "frequency_packs" / "freq-es-cde" / "main.sqlite"
        assert user_source.exists()
        assert sqlite_path.exists()
        assert "freq-es-cde" in panel._managed_frequency_pack_ids
        assert "freq-es-cde" not in panel._frequency_pack_paths


def test_frequency_pack_panel_starts_import_picker_at_downloaded_source(monkeypatch) -> None:
    _app()
    set_locale("en")
    with TemporaryDirectory() as temp_dir:
        downloads = Path(temp_dir) / "Downloads"
        downloads.mkdir()
        source = downloads / "spanish_lemmas20k.txt"
        source.write_text("ID\tfreq\tlemma\tpos\n", encoding="latin-1")
        panel = LanguagePackPanel(pack_source_overrides={})
        pack = panel._frequency_pack_info["freq-es-cde"]

        monkeypatch.setattr(
            "settings_language_packs.QStandardPaths.writableLocation",
            lambda _location: str(downloads),
        )

        assert panel._frequency_pack_file_picker_start(pack) == str(source)

        source.unlink()

        assert panel._frequency_pack_file_picker_start(pack) == str(downloads)
