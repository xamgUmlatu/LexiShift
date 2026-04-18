from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from language_packs_catalog import (  # noqa: E402
    FREQUENCY_PACKS,
    LANGUAGE_PACKS,
    PackTransportOverride,
    build_pack_catalogs,
)
from settings_language_packs import LanguagePackPanel  # noqa: E402


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _language_pack(pack_id: str):
    return next(pack for pack in LANGUAGE_PACKS if pack.pack_id == pack_id)


def _frequency_pack(pack_id: str):
    return next(pack for pack in FREQUENCY_PACKS if pack.pack_id == pack_id)


def test_build_pack_catalogs_applies_transport_override_only_to_target_pack() -> None:
    snapshot = build_pack_catalogs(
        source_overrides={
            "freedict-en-es": {
                "url": " https://example.com/custom-eng-spa.tar.xz ",
                "wayback_url": "https://web.archive.org/web/*/https://example.com/custom-eng-spa.tar.xz",
                "filename": " custom-eng-spa.tar.xz ",
            }
        }
    )

    overridden = next(pack for pack in snapshot.language_packs if pack.pack_id == "freedict-en-es")
    baseline = _language_pack("freedict-en-es")
    untouched = next(pack for pack in snapshot.language_packs if pack.pack_id == "freedict-en-de")

    assert overridden.url == "https://example.com/custom-eng-spa.tar.xz"
    assert (
        overridden.wayback_url
        == "https://web.archive.org/web/*/https://example.com/custom-eng-spa.tar.xz"
    )
    assert overridden.filename == "custom-eng-spa.tar.xz"
    assert overridden.build_mode == baseline.build_mode
    assert overridden.required_files == baseline.required_files
    assert untouched is _language_pack("freedict-en-de")


def test_build_pack_catalogs_ignores_blank_and_unknown_override_fields() -> None:
    snapshot = build_pack_catalogs(
        source_overrides={
            "freq-en-coca": {
                "url": "   ",
                "disabled_reason": "ignored in this slice",
            }
        }
    )

    overridden = next(pack for pack in snapshot.frequency_packs if pack.pack_id == "freq-en-coca")
    baseline = _frequency_pack("freq-en-coca")

    assert overridden is baseline


def test_language_pack_panel_accepts_pack_source_overrides() -> None:
    _app()
    panel = LanguagePackPanel(
        pack_source_overrides={
            "freq-en-coca": PackTransportOverride(
                filename="lemmas_60k_override.txt",
                url="https://example.com/lemmas_60k_override.txt",
            )
        }
    )

    pack = panel._frequency_pack_info["freq-en-coca"]
    archive_path = panel._frequency_archive_path(pack)

    assert pack.filename == "lemmas_60k_override.txt"
    assert pack.url == "https://example.com/lemmas_60k_override.txt"
    assert archive_path.endswith("lemmas_60k_override.txt")
