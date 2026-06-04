from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from i18n import set_locale
from pack_download_failures import PackDownloadFailure, serialize_pack_download_failure
from settings_language_packs import LanguagePackPanel


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_language_pack_failure_handler_does_not_access_embedding_only_fields() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()
    pack_id = next(iter(panel._language_pack_rows.keys()))
    panel._on_language_pack_failed(pack_id, "network error")


def test_language_pack_offline_failure_uses_connectivity_copy_without_archive_link() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()
    pack_id = next(iter(panel._language_pack_rows.keys()))
    panel._on_language_pack_failed(
        pack_id,
        serialize_pack_download_failure(
            PackDownloadFailure(kind="offline", detail="Name or service not known")
        ),
    )

    assert "internet connection" in panel.language_pack_status.text()
    assert "archive mirror" not in panel.language_pack_status.text().lower()
    assert "Name or service not known" in panel.language_pack_status.toolTip()


def test_language_pack_not_found_failure_offers_archive_link() -> None:
    _app()
    set_locale("en")
    panel = LanguagePackPanel()
    pack_id = next(
        candidate
        for candidate, pack in panel._language_pack_info.items()
        if candidate in panel._language_pack_rows and pack.wayback_url
    )
    pack = panel._language_pack_info[pack_id]
    panel._on_language_pack_failed(
        pack_id,
        serialize_pack_download_failure(
            PackDownloadFailure(kind="not_found", detail="HTTP Error 404: Not Found")
        ),
    )

    assert "was not found" in panel.language_pack_status.text()
    assert pack.wayback_url in panel.language_pack_status.text()
