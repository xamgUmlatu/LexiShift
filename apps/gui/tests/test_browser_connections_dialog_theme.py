from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel, QScrollArea

from helper_connections_dialog import BrowserConnectionsDialog
from helper_connection_models import (
    BrowserConnectionConfig,
    BrowserConnectionTarget,
    ExtensionEnvironment,
    HELPER_STATE_CONFIGURED,
    HELPER_STATE_NEEDS_REPAIR,
    HOST_MODE_WORKSPACE,
    HelperInstallStatus,
    TARGET_KIND_UNPACKED,
)
from theme_manager import build_browser_connection_styles, resolve_theme


class _FakeSettings:
    def value(self, _key: str, default=None):  # noqa: ANN001
        return default

    def setValue(self, _key: str, _value) -> None:  # noqa: ANN001
        return None


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_browser_connection_styles_cover_dialog_panels_and_badges() -> None:
    styles = build_browser_connection_styles(resolve_theme("light_sand"))

    assert 'QScrollArea[browserConnectionsScroll="true"]' in styles
    assert 'QWidget[browserConnectionsCanvas="true"]' in styles
    assert 'QFrame[browserConnectionPanel="true"]' in styles
    assert 'QFrame[browserConnectionCard="true"]' in styles
    assert 'QLabel[browserConnectionSectionTitle="true"]' in styles
    assert 'QLabel[browserConnectionStatusBadge="true"][statusState="configured"]' in styles


def test_browser_connections_dialog_marks_themeable_frames_and_badges() -> None:
    _app()
    unpacked_target = BrowserConnectionTarget(
        key="chromium_unpacked_abcd",
        label="Chromium (Unpacked Dev)",
        extension_id="abcdabcdabcdabcdabcdabcdabcdabcd",
        kind=TARGET_KIND_UNPACKED,
        fixed=False,
    )
    config = BrowserConnectionConfig(
        browser="chromium",
        host_mode=HOST_MODE_WORKSPACE,
        host_override_path="/repo/scripts/helper/lexishift_native_host.py",
        targets=(unpacked_target,),
    )
    fixed_env = ExtensionEnvironment(
        key="chrome_prod",
        label="Chrome (Web Store)",
        browser="chrome",
        extension_id="prodprodprodprodprodprodprodprod",
        fixed=True,
    )
    statuses = [
        HelperInstallStatus(
            browser="chrome",
            state=HELPER_STATE_CONFIGURED,
            manifest_path=Path("/tmp/chrome-manifest.json"),
            host_path=Path("/tmp/chrome-host.py"),
            host_mode=HOST_MODE_WORKSPACE,
            allowed_extension_ids=("prodprodprodprodprodprodprodprod",),
        ),
        HelperInstallStatus(
            browser="chromium",
            state=HELPER_STATE_NEEDS_REPAIR,
            manifest_path=Path("/tmp/chromium-manifest.json"),
            host_path=Path("/tmp/chromium-host.py"),
            host_mode=HOST_MODE_WORKSPACE,
            allowed_extension_ids=(unpacked_target.extension_id,),
            message="host copy is stale",
        ),
    ]

    with (
        patch(
            "helper_connections_dialog.load_extension_environments", return_value=([fixed_env], "")
        ),
        patch("helper_connections_dialog.load_browser_connections", return_value=[config]),
        patch("helper_connections_dialog.inspect_helper_installation", side_effect=statuses),
    ):
        dialog = BrowserConnectionsDialog(None, _FakeSettings())

    scroll = dialog.findChild(QScrollArea)
    assert scroll is not None
    assert scroll.property("browserConnectionsScroll") is True
    assert dialog._content_widget.property("browserConnectionsCanvas") is True

    themed_panels = [
        frame for frame in dialog.findChildren(QFrame) if frame.property("browserConnectionPanel")
    ]
    themed_cards = [
        frame for frame in dialog.findChildren(QFrame) if frame.property("browserConnectionCard")
    ]
    section_titles = [
        label
        for label in dialog.findChildren(QLabel)
        if label.property("browserConnectionSectionTitle")
    ]
    status_badges = [
        label
        for label in dialog.findChildren(QLabel)
        if label.property("browserConnectionStatusBadge")
    ]

    assert len(themed_panels) >= 3
    assert len(themed_cards) >= 2
    assert len(section_titles) == 2
    assert all(label.text().strip() for label in section_titles)
    assert {label.property("statusState") for label in status_badges} == {
        HELPER_STATE_CONFIGURED,
        HELPER_STATE_NEEDS_REPAIR,
    }
