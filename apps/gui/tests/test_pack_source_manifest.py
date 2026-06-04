from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from language_packs_catalog import PackTransportOverride  # noqa: E402
from pack_source_manifest import (  # noqa: E402
    PackSourceManifestSnapshot,
    PackSourceManifestValidationError,
    load_pack_source_overrides,
    pack_source_manifest_snapshot_from_payload,
    resolve_pack_source_manifest,
    write_pack_source_manifest_cache,
)
from settings_language_packs import LanguagePackPanel  # noqa: E402


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _snapshot(*, fetched_at: datetime, ttl_hours: int = 24) -> PackSourceManifestSnapshot:
    return PackSourceManifestSnapshot(
        source_url="https://example.com/pack_source_manifest.json",
        fetched_at=fetched_at,
        ttl_hours=ttl_hours,
        generated_at=_utc("2026-04-19T00:00:00Z"),
        overrides={
            "freedict-en-es": PackTransportOverride(
                url="https://example.com/freedict-eng-spa.tar.xz",
                filename="freedict-eng-spa.tar.xz",
                expected_content_type="application/x-xz",
                disabled=True,
                disabled_reason="Upstream source temporarily disabled.",
            )
        },
    )


def test_resolve_pack_source_manifest_uses_fresh_cache_without_fetch() -> None:
    with TemporaryDirectory() as temp_dir:
        cache_path = Path(temp_dir) / "pack_source_manifest_cache.json"
        snapshot = _snapshot(fetched_at=_utc("2026-04-19T00:00:00Z"), ttl_hours=24)
        write_pack_source_manifest_cache(snapshot, cache_path=cache_path)

        with patch("pack_source_manifest.fetch_pack_source_manifest") as fetch_mock:
            resolved = resolve_pack_source_manifest(
                manifest_url=snapshot.source_url,
                cache_path=cache_path,
                refresh_remote=True,
                now=_utc("2026-04-19T06:00:00Z"),
            )

    fetch_mock.assert_not_called()
    assert resolved is not None
    assert resolved.overrides["freedict-en-es"].filename == "freedict-eng-spa.tar.xz"
    assert resolved.overrides["freedict-en-es"].expected_content_type == "application/x-xz"
    assert resolved.overrides["freedict-en-es"].disabled is True
    assert (
        resolved.overrides["freedict-en-es"].disabled_reason
        == "Upstream source temporarily disabled."
    )


def test_resolve_pack_source_manifest_fetches_and_writes_cache_when_missing() -> None:
    with TemporaryDirectory() as temp_dir:
        cache_path = Path(temp_dir) / "pack_source_manifest_cache.json"
        fetched_snapshot = PackSourceManifestSnapshot(
            source_url="https://example.com/pack_source_manifest.json",
            fetched_at=_utc("2026-04-19T01:00:00Z"),
            ttl_hours=24,
            generated_at=_utc("2026-04-19T00:00:00Z"),
            overrides={
                "freq-en-coca": PackTransportOverride(
                    url="https://example.com/lemmas.txt",
                    filename="lemmas.txt",
                    expected_content_type="text/plain",
                )
            },
        )

        with patch(
            "pack_source_manifest.fetch_pack_source_manifest",
            return_value=fetched_snapshot,
        ) as fetch_mock:
            resolved = resolve_pack_source_manifest(
                manifest_url=fetched_snapshot.source_url,
                cache_path=cache_path,
                refresh_remote=True,
                now=_utc("2026-04-19T01:00:00Z"),
            )

        cached = resolve_pack_source_manifest(
            manifest_url=fetched_snapshot.source_url,
            cache_path=cache_path,
            refresh_remote=False,
            now=_utc("2026-04-19T01:30:00Z"),
        )

    fetch_mock.assert_called_once()
    assert resolved is not None
    assert resolved.overrides["freq-en-coca"].url == "https://example.com/lemmas.txt"
    assert cached is not None
    assert cached.overrides["freq-en-coca"].filename == "lemmas.txt"
    assert cached.overrides["freq-en-coca"].expected_content_type == "text/plain"


def test_resolve_pack_source_manifest_falls_back_to_stale_cache_when_fetch_fails() -> None:
    with TemporaryDirectory() as temp_dir:
        cache_path = Path(temp_dir) / "pack_source_manifest_cache.json"
        stale_snapshot = _snapshot(fetched_at=_utc("2026-04-10T00:00:00Z"), ttl_hours=24)
        write_pack_source_manifest_cache(stale_snapshot, cache_path=cache_path)

        with patch(
            "pack_source_manifest.fetch_pack_source_manifest",
            side_effect=OSError("network down"),
        ):
            resolved = resolve_pack_source_manifest(
                manifest_url=stale_snapshot.source_url,
                cache_path=cache_path,
                refresh_remote=True,
                now=_utc("2026-04-19T00:00:00Z"),
            )

    assert resolved is not None
    assert resolved.overrides["freedict-en-es"].url == "https://example.com/freedict-eng-spa.tar.xz"


def test_pack_source_manifest_snapshot_from_payload_rejects_invalid_schema_version() -> None:
    try:
        pack_source_manifest_snapshot_from_payload(
            {
                "schema_version": 99,
                "ttl_hours": 24,
                "packs": {},
            },
            source_url="https://example.com/pack_source_manifest.json",
            fetched_at=_utc("2026-04-19T00:00:00Z"),
        )
    except PackSourceManifestValidationError as exc:
        assert "schema_version" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected PackSourceManifestValidationError")


def test_load_pack_source_overrides_applies_builtin_freq_es_manual_policy() -> None:
    with patch("pack_source_manifest.resolve_pack_source_manifest", return_value=None):
        overrides = load_pack_source_overrides(refresh_remote=False)

    assert overrides["freq-es-cde"].disabled is True
    assert "license-restricted" in str(overrides["freq-es-cde"].disabled_reason)


class _DummySignal:
    def connect(self, _callback) -> None:
        return None


class _DummyFrequencyThread:
    def __init__(self, pack, archive_path: str, sqlite_path: str, parent=None) -> None:
        self.pack = pack
        self.archive_path = archive_path
        self.sqlite_path = sqlite_path
        self.parent = parent
        self.progress = _DummySignal()
        self.completed = _DummySignal()
        self.failed = _DummySignal()
        self.finished = _DummySignal()

    def start(self) -> None:
        return None


def test_language_pack_panel_refreshes_dynamic_pack_source_overrides_before_download() -> None:
    _app()
    with (
        patch(
            "settings_language_packs.load_pack_source_overrides",
            side_effect=[
                {},
                {
                    "freq-en-coca": PackTransportOverride(
                        url="https://example.com/lemmas_override.txt",
                        filename="lemmas_override.txt",
                    )
                },
            ],
        ) as load_mock,
        patch(
            "settings_language_packs.FrequencyPackDownloadThread",
            _DummyFrequencyThread,
        ),
    ):
        panel = LanguagePackPanel()
        panel._download_frequency_pack("freq-en-coca")

    thread = panel._frequency_pack_threads[0]
    assert load_mock.call_count == 2
    assert thread.pack.url == "https://example.com/lemmas_override.txt"
    assert thread.archive_path.endswith("lemmas_override.txt")
    assert thread.sqlite_path.endswith("main.sqlite")
