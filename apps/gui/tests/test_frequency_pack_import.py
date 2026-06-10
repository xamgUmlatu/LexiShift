from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import zipfile

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


def _freq_es_spalex_pack():
    catalogs = build_pack_catalogs(source_overrides={})
    return next(pack for pack in catalogs.frequency_packs if pack.pack_id == "freq-es-spalex-v1")


def _freq_ja_bccwj_pack():
    catalogs = build_pack_catalogs(source_overrides={})
    return next(pack for pack in catalogs.frequency_packs if pack.pack_id == "freq-ja-bccwj")


def _write_cde_source(path: Path) -> None:
    path.write_text(
        "ID\tfreq\tlemma\tpos\n1\t100\tgato\tn\n2\t80\tverde\tj\n",
        encoding="latin-1",
    )


def _write_spalex_source(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "spelling,count_total,percent_total,prevalence_total,count_nts,percent_nts,"
                "prevalence_nts,count_ntl,percent_ntl,prevalence_ntl,freq,zipf",
                "que,100,1.0,98,50,1.0,90,50,1.0,90,7.4,7.1",
                "casa,80,0.8,88,40,0.8,80,40,0.8,80,6.0,6.3",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_bccwj_source(path: Path) -> None:
    path.write_text(
        "rank\tlemma\tfrequency\tpos\n1\tsekai\t100\tnoun\n2\tmiru\t80\tverb\n",
        encoding="utf-8",
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


def test_import_spalex_frequency_source_file_writes_clean_managed_pack() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        user_source = root / "Downloads" / "word_info.csv"
        user_source.parent.mkdir()
        _write_spalex_source(user_source)
        frequency_dir = root / "frequency_packs"

        sqlite_path = import_frequency_source_file(
            _freq_es_spalex_pack(),
            user_source,
            frequency_pack_dir=frequency_dir,
        )

        pack_root = frequency_dir / "freq-es-spalex-v1"
        provenance_path = pack_root / PACK_PROVENANCE_FILENAME
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        assert user_source.exists()
        assert sqlite_path == pack_root / "main.sqlite"
        assert validate_pack_provenance_file(provenance_path) == ()
        with sqlite3.connect(sqlite_path) as conn:
            row_count = conn.execute("select count(*) from frequency").fetchone()[0]
            lemmas = [row[0] for row in conn.execute("select lemma from frequency order by id")]

        assert row_count == 2
        assert lemmas == ["que", "casa"]
        assert payload["pack_id"] == "freq-es-spalex-v1"
        assert payload["provider"] == "freq-es-spalex-v1"
        assert payload["source"]["license_status"] == "confirmed"
        assert payload["source"]["source_version"] == "10.6084/m9.figshare.5924794.v4"


def test_import_bccwj_zip_source_file_preserves_archive_handling() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source_tsv = root / "BCCWJ_frequencylist_suw_ver1_0.tsv"
        source_zip = root / "Downloads" / "BCCWJ_frequencylist_suw_ver1_0.zip"
        source_zip.parent.mkdir()
        _write_bccwj_source(source_tsv)
        with zipfile.ZipFile(source_zip, "w") as archive:
            archive.write(source_tsv, source_tsv.name)
        frequency_dir = root / "frequency_packs"

        sqlite_path = import_frequency_source_file(
            _freq_ja_bccwj_pack(),
            source_zip,
            frequency_pack_dir=frequency_dir,
        )

        pack_root = frequency_dir / "freq-ja-bccwj"
        provenance_path = pack_root / PACK_PROVENANCE_FILENAME
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
        staged_files = tuple(pack_root.glob(".import-*"))

        assert source_zip.exists()
        assert sqlite_path == pack_root / "main.sqlite"
        assert validate_pack_provenance_file(provenance_path) == ()
        assert staged_files == ()
        with sqlite3.connect(sqlite_path) as conn:
            row_count = conn.execute("select count(*) from frequency").fetchone()[0]

        assert row_count == 2
        assert payload["pack_id"] == "freq-ja-bccwj"
        assert payload["source"]["raw_artifacts"][0]["filename"] == (
            "BCCWJ_frequencylist_suw_ver1_0.tsv"
        )


def test_frequency_pack_panel_imports_spalex_raw_source_as_managed_pack(monkeypatch) -> None:
    _app()
    set_locale("en")
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        user_source = root / "Downloads" / "word_info.csv"
        user_source.parent.mkdir()
        _write_spalex_source(user_source)
        panel = LanguagePackPanel(pack_source_overrides={})
        panel._frequency_pack_dir = str(root / "frequency_packs")

        monkeypatch.setattr(
            "settings_language_packs.QFileDialog.getOpenFileName",
            lambda *_args, **_kwargs: (str(user_source), ""),
        )

        panel._select_frequency_pack_path("freq-es-spalex-v1")

        sqlite_path = root / "frequency_packs" / "freq-es-spalex-v1" / "main.sqlite"
        assert user_source.exists()
        assert sqlite_path.exists()
        assert "freq-es-spalex-v1" in panel._managed_frequency_pack_ids
        assert "freq-es-spalex-v1" not in panel._frequency_pack_paths


def test_frequency_pack_panel_starts_import_picker_at_downloaded_source(monkeypatch) -> None:
    _app()
    set_locale("en")
    with TemporaryDirectory() as temp_dir:
        downloads = Path(temp_dir) / "Downloads"
        downloads.mkdir()
        source = downloads / "word_info.csv"
        source.write_text("spelling,count_total,percent_total,prevalence_total\n", encoding="utf-8")
        panel = LanguagePackPanel(pack_source_overrides={})
        pack = panel._frequency_pack_info["freq-es-spalex-v1"]

        monkeypatch.setattr(
            "settings_language_packs.QStandardPaths.writableLocation",
            lambda _location: str(downloads),
        )

        assert panel._frequency_pack_file_picker_start(pack) == str(source)

        source.unlink()

        assert panel._frequency_pack_file_picker_start(pack) == str(downloads)


def test_frequency_pack_panel_detects_bccwj_manual_source_in_downloads(monkeypatch) -> None:
    _app()
    set_locale("en")
    with TemporaryDirectory() as temp_dir:
        downloads = Path(temp_dir) / "Downloads"
        downloads.mkdir()
        source = downloads / "BCCWJ_frequencylist_suw_ver1_0.zip"
        source.write_bytes(b"zip fixture")
        panel = LanguagePackPanel(pack_source_overrides={})
        pack = panel._frequency_pack_info["freq-ja-bccwj"]

        monkeypatch.setattr(
            "settings_language_packs.QStandardPaths.writableLocation",
            lambda _location: str(downloads),
        )

        assert panel._manual_frequency_source_candidate_path(pack) == str(source)
        assert panel._frequency_pack_file_picker_start(pack) == str(source)


def test_frequency_pack_panel_detects_manual_source_in_remembered_import_folder(
    monkeypatch,
) -> None:
    _app()
    set_locale("en")
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        os_downloads = root / "Downloads"
        chrome_downloads = root / "Documents" / "ChromeDownloads"
        os_downloads.mkdir()
        chrome_downloads.mkdir(parents=True)
        source = chrome_downloads / "BCCWJ_frequencylist_suw_ver1_0.zip"
        source.write_bytes(b"zip fixture")
        panel = LanguagePackPanel(pack_source_overrides={})
        pack = panel._frequency_pack_info["freq-ja-bccwj"]

        monkeypatch.setattr(
            "settings_language_packs.QStandardPaths.writableLocation",
            lambda _location: str(os_downloads),
        )

        assert panel._manual_frequency_source_candidate_path(pack) is None

        panel._remember_manual_source_import_dir(source)

        assert panel._manual_frequency_source_candidate_path(pack) == str(source)
        assert panel._frequency_pack_file_picker_start(pack) == str(source)


def test_frequency_pack_panel_uses_pack_specific_source_file_filters() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel(pack_source_overrides={})
    bccwj_pack = panel._frequency_pack_info["freq-ja-bccwj"]
    spalex_pack = panel._frequency_pack_info["freq-es-spalex-v1"]

    bccwj_filter = panel._frequency_pack_file_filters(bccwj_pack)
    spalex_filter = panel._frequency_pack_file_filters(spalex_pack)

    assert "*.zip" in bccwj_filter
    assert "*.tsv" in bccwj_filter
    assert "*.sqlite" in bccwj_filter
    assert "*.csv" in spalex_filter
    assert "*.zip" not in spalex_filter.split(";;", maxsplit=1)[0]


def test_frequency_pack_panel_offers_source_import_for_supported_frequency_builds() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel(pack_source_overrides={})

    assert (
        panel._supports_frequency_source_import(panel._frequency_pack_info["freq-es-cde"]) is True
    )
    assert (
        panel._supports_frequency_source_import(panel._frequency_pack_info["freq-es-spalex-v1"])
        is True
    )
    assert (
        panel._supports_frequency_source_import(panel._frequency_pack_info["freq-ja-bccwj"]) is True
    )
    assert (
        panel._supports_frequency_source_import(panel._frequency_pack_info["freq-de-default"])
        is False
    )
