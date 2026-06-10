from __future__ import annotations

import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from language_packs_catalog import (  # noqa: E402
    AUTO_DOWNLOAD_MODE,
    FREQUENCY_PACKS,
    LANGUAGE_PACKS,
    MANUAL_SUPPLY_MODE,
    POS_OVERLAY_PACKS,
    SEMANTIC_PACKS,
    PackTransportOverride,
    build_pack_catalogs,
)
from scripts.data.generate_third_party_data_notices import render_notices  # noqa: E402
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


def _pos_overlay_pack(pack_id: str):
    return next(pack for pack in POS_OVERLAY_PACKS if pack.pack_id == pack_id)


def _semantic_pack(pack_id: str):
    return next(pack for pack in SEMANTIC_PACKS if pack.pack_id == pack_id)


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


def test_build_pack_catalogs_keeps_metadata_only_override_from_mutating_pack_fields() -> None:
    snapshot = build_pack_catalogs(
        source_overrides={
            "freq-en-coca": {
                "url": "   ",
                "disabled": True,
                "disabled_reason": "Temporarily unavailable",
            }
        }
    )

    overridden = next(pack for pack in snapshot.frequency_packs if pack.pack_id == "freq-en-coca")
    baseline = _frequency_pack("freq-en-coca")

    assert overridden is baseline


def test_build_pack_catalogs_includes_ud_ancora_pos_overlay_pack() -> None:
    snapshot = build_pack_catalogs(source_overrides={})

    pack = next(
        pack for pack in snapshot.pos_overlay_packs if pack.pack_id == "pos-es-ud-ancora-v1"
    )
    baseline = _pos_overlay_pack("pos-es-ud-ancora-v1")

    assert pack is baseline
    assert pack.build_mode == "ud_ancora_pos_overlay"
    assert pack.sqlite_filename == "main.sqlite"
    assert len(pack.source_urls) == 3


def test_build_pack_catalogs_includes_en_es_semantic_pack() -> None:
    snapshot = build_pack_catalogs(source_overrides={})

    pack = next(
        pack
        for pack in snapshot.semantic_packs
        if pack.pack_id == "en-es-active-only-combined-full-v1-tranche-011"
    )
    baseline = _semantic_pack("en-es-active-only-combined-full-v1-tranche-011")

    assert pack is baseline
    assert pack.pair == "en-es"
    assert pack.distribution_mode == "local-copy"
    assert "local reference inventory" in "\n".join(pack.license_notes)


def test_catalog_records_license_posture_for_auto_and_manual_sources() -> None:
    spalex = _frequency_pack("freq-es-spalex-v1")
    ud_ancora = _pos_overlay_pack("pos-es-ud-ancora-v1")
    wordfrequency = _frequency_pack("freq-es-cde")
    german_frequency = _frequency_pack("freq-de-default")
    english_leipzig = _frequency_pack("freq-en-leipzig-default")

    assert spalex.license_name == "CC BY 4.0"
    assert spalex.distribution_mode == AUTO_DOWNLOAD_MODE
    assert ud_ancora.license_name == "CC BY 4.0"
    assert ud_ancora.distribution_mode == AUTO_DOWNLOAD_MODE
    assert wordfrequency.distribution_mode == MANUAL_SUPPLY_MODE
    assert wordfrequency.license_status == "manual-review-required"
    assert german_frequency.distribution_mode == AUTO_DOWNLOAD_MODE
    assert "Bundled or hosted composite artifacts" in "\n".join(german_frequency.license_notes)
    assert english_leipzig.build_mode == "en_frequency_pipeline"
    assert english_leipzig.distribution_mode == AUTO_DOWNLOAD_MODE
    assert english_leipzig.license_status == "expected-not-verified"


def test_third_party_data_notices_render_from_catalog_metadata() -> None:
    notices = render_notices(as_of="2026-06-08")

    assert "freq-es-spalex-v1" in notices
    assert "Semantic Packs" in notices
    assert "en-es-active-only-combined-full-v1-tranche-011" in notices
    assert "CC BY 4.0" in notices
    assert "pos-es-ud-ancora-v1" in notices
    assert "freq-es-cde" in notices
    assert "manual-supply" in notices


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


def test_frequency_pack_download_is_blocked_when_manifest_disables_source() -> None:
    _app()
    panel = LanguagePackPanel(
        pack_source_overrides={
            "freq-en-coca": PackTransportOverride(
                disabled=True,
                disabled_reason="Temporarily unavailable",
            )
        }
    )

    with patch("settings_language_packs.FrequencyPackDownloadThread") as thread_cls:
        panel._download_frequency_pack("freq-en-coca")

    thread_cls.assert_not_called()
    assert panel.language_pack_status.text() == "Temporarily unavailable"
    assert panel.language_pack_status.toolTip() == "Temporarily unavailable"
