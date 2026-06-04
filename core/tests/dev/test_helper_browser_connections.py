from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
if str(GUI_SRC) not in sys.path:
    sys.path.insert(0, str(GUI_SRC))

import helper_ui  # noqa: E402
from helper_installer import (  # noqa: E402
    BrowserConnectionConfig,
    BrowserConnectionTarget,
    HELPER_STATE_CONFIGURED,
    HELPER_STATE_NEEDS_REPAIR,
    HELPER_STATE_NOT_CONFIGURED,
    HOST_MODE_WORKSPACE,
    HOST_MODE_BUNDLED,
    HOST_MODE_CUSTOM,
    TARGET_KIND_UNPACKED,
    HelperInstallStatus,
)
from helper_connection_models import (  # noqa: E402
    REPAIR_REASON_ALLOWED_ORIGINS_MISSING,
    REPAIR_REASON_BUNDLED_HOST_STALE,
)


class _FakeSettings:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def value(self, key: str, default=None):
        return self.values.get(key, default)

    def setValue(self, key: str, value) -> None:  # noqa: ANN001
        self.values[key] = value

    def remove(self, key: str) -> None:
        self.values.pop(key, None)


class TestHelperBrowserConnections(unittest.TestCase):
    def test_save_and_load_browser_connections_round_trip(self) -> None:
        settings = _FakeSettings()
        configs = [
            BrowserConnectionConfig(
                browser="chromium",
                host_mode=HOST_MODE_WORKSPACE,
                host_override_path="/repo/scripts/helper/lexishift_native_host.py",
                targets=(
                    BrowserConnectionTarget(
                        key="chromium_unpacked_abcd",
                        label="Chromium (Unpacked Dev)",
                        extension_id="abcdabcdabcdabcdabcdabcdabcdabcd",
                        kind=TARGET_KIND_UNPACKED,
                        fixed=False,
                    ),
                ),
            )
        ]

        helper_ui.save_browser_connections(settings, configs)
        loaded = helper_ui.load_browser_connections(settings)

        self.assertEqual(loaded, configs)

    def test_load_browser_connections_migrates_legacy_settings(self) -> None:
        settings = _FakeSettings()
        settings.setValue("helper/extension_env", "chromium_dev")
        settings.setValue(
            "helper/extension_id/chromium_dev",
            "abcdabcdabcdabcdabcdabcdabcdabcd",
        )
        settings.setValue(
            "helper/host_path",
            "/repo/scripts/helper/lexishift_native_host.py",
        )
        envs = [
            helper_ui.ExtensionEnvironment(
                key="chromium_dev",
                label="Chromium (Unpacked Dev)",
                browser="chromium",
                extension_id="",
                fixed=False,
            )
        ]

        with (
            mock.patch.object(
                helper_ui, "load_extension_environments", return_value=(envs, "chromium_dev")
            ),
            mock.patch.object(helper_ui, "infer_host_mode", return_value=HOST_MODE_WORKSPACE),
        ):
            loaded = helper_ui.load_browser_connections(settings)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].browser, "chromium")
        self.assertEqual(loaded[0].host_mode, HOST_MODE_WORKSPACE)
        self.assertEqual(
            loaded[0].targets[0].extension_id,
            "abcdabcdabcdabcdabcdabcdabcdabcd",
        )

    def test_helper_connection_overall_state_uses_saved_connections(self) -> None:
        settings = _FakeSettings()
        helper_ui.save_browser_connections(
            settings,
            [
                BrowserConnectionConfig(
                    browser="chrome",
                    host_mode=HOST_MODE_WORKSPACE,
                    host_override_path="/repo/scripts/helper/lexishift_native_host.py",
                    targets=(
                        BrowserConnectionTarget(
                            key="chrome_unpacked_abcd",
                            label="Chrome (Unpacked Dev)",
                            extension_id="abcdabcdabcdabcdabcdabcdabcdabcd",
                            kind=TARGET_KIND_UNPACKED,
                            fixed=False,
                        ),
                    ),
                )
            ],
        )

        with mock.patch.object(
            helper_ui,
            "inspect_helper_installation",
            return_value=type("Status", (), {"state": HELPER_STATE_CONFIGURED})(),
        ):
            self.assertEqual(
                helper_ui.helper_connection_overall_state(settings),
                HELPER_STATE_CONFIGURED,
            )

        with mock.patch.object(
            helper_ui,
            "inspect_helper_installation",
            return_value=type("Status", (), {"state": HELPER_STATE_NOT_CONFIGURED})(),
        ):
            self.assertEqual(
                helper_ui.helper_connection_overall_state(settings),
                HELPER_STATE_NOT_CONFIGURED,
            )

    def test_remove_browser_target_preserves_other_targets(self) -> None:
        prod_target = BrowserConnectionTarget(
            key="chrome_prod",
            label="Chrome (Web Store)",
            extension_id="prodprodprodprodprodprodprodprod",
            kind="prod",
            fixed=True,
        )
        unpacked_target = BrowserConnectionTarget(
            key="chrome_unpacked_abcd",
            label="Chrome (Unpacked Dev)",
            extension_id="abcdabcdabcdabcdabcdabcdabcdabcd",
            kind=TARGET_KIND_UNPACKED,
            fixed=False,
        )
        configs = [
            BrowserConnectionConfig(
                browser="chrome",
                host_mode=HOST_MODE_WORKSPACE,
                host_override_path="/repo/scripts/helper/lexishift_native_host.py",
                targets=(prod_target, unpacked_target),
            )
        ]

        updated = helper_ui._remove_browser_target(
            configs,
            browser="chrome",
            target_key="chrome_unpacked_abcd",
        )

        self.assertEqual(len(updated), 1)
        self.assertEqual(updated[0].targets, (prod_target,))

    def test_host_path_for_config_does_not_open_picker_when_workspace_host_missing(self) -> None:
        config = BrowserConnectionConfig(
            browser="chromium",
            host_mode=HOST_MODE_WORKSPACE,
            host_override_path=None,
            targets=(
                BrowserConnectionTarget(
                    key="chromium_unpacked_abcd",
                    label="Chromium (Unpacked Dev)",
                    extension_id="abcdabcdabcdabcdabcdabcdabcdabcd",
                    kind=TARGET_KIND_UNPACKED,
                    fixed=False,
                ),
            ),
        )

        with (
            mock.patch.object(helper_ui, "resolve_host_path_for_mode", return_value=None),
            mock.patch.object(
                helper_ui.QFileDialog,
                "getOpenFileName",
                side_effect=AssertionError("unexpected file picker"),
            ),
        ):
            self.assertIsNone(helper_ui._host_path_for_config(config))

    def test_auto_repair_browser_connections_repairs_safe_saved_state(self) -> None:
        settings = _FakeSettings()
        config = BrowserConnectionConfig(
            browser="chrome",
            host_mode=HOST_MODE_BUNDLED,
            targets=(
                BrowserConnectionTarget(
                    key="chrome_prod",
                    label="Chrome (Web Store)",
                    extension_id="prodprodprodprodprodprodprodprod",
                    kind="prod",
                    fixed=True,
                ),
            ),
        )
        helper_ui.save_browser_connections(settings, [config])
        status = HelperInstallStatus(
            browser="chrome",
            state=HELPER_STATE_NEEDS_REPAIR,
            repair_reasons=(
                REPAIR_REASON_BUNDLED_HOST_STALE,
                REPAIR_REASON_ALLOWED_ORIGINS_MISSING,
            ),
        )

        with (
            mock.patch.object(helper_ui, "inspect_helper_installation", return_value=status),
            mock.patch.object(
                helper_ui,
                "_host_path_for_config",
                return_value=(config, Path("/tmp/lexishift_native_host.py")),
            ),
            mock.patch.object(
                helper_ui,
                "install_helper",
                return_value=type("Result", (), {"installed": True, "message": "ok"})(),
            ) as install_mock,
            mock.patch.object(helper_ui, "ensure_helper_autostart") as autostart_mock,
        ):
            repaired = helper_ui.auto_repair_browser_connections(settings)

        self.assertTrue(repaired)
        install_mock.assert_called_once()
        autostart_mock.assert_called_once()

    def test_auto_repair_browser_connections_skips_custom_and_unexpected_origin_state(self) -> None:
        settings = _FakeSettings()
        custom_config = BrowserConnectionConfig(
            browser="chrome",
            host_mode=HOST_MODE_CUSTOM,
            host_override_path="/tmp/custom-host.py",
            targets=(
                BrowserConnectionTarget(
                    key="chrome_unpacked_abcd",
                    label="Chrome (Unpacked Dev)",
                    extension_id="abcdabcdabcdabcdabcdabcdabcdabcd",
                    kind=TARGET_KIND_UNPACKED,
                    fixed=False,
                ),
            ),
        )
        bundled_config = BrowserConnectionConfig(
            browser="brave",
            host_mode=HOST_MODE_BUNDLED,
            targets=(
                BrowserConnectionTarget(
                    key="brave_prod",
                    label="Brave (Web Store)",
                    extension_id="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                    kind="prod",
                    fixed=True,
                ),
            ),
        )
        helper_ui.save_browser_connections(settings, [custom_config, bundled_config])
        statuses = [
            HelperInstallStatus(
                browser="chrome",
                state=HELPER_STATE_NEEDS_REPAIR,
                repair_reasons=(REPAIR_REASON_ALLOWED_ORIGINS_MISSING,),
            ),
            HelperInstallStatus(
                browser="brave",
                state=HELPER_STATE_NEEDS_REPAIR,
                repair_reasons=(REPAIR_REASON_ALLOWED_ORIGINS_MISSING,),
                unexpected_extension_ids=("manualmanualmanualmanualmanualmanua",),
            ),
        ]

        with (
            mock.patch.object(helper_ui, "inspect_helper_installation", side_effect=statuses),
            mock.patch.object(helper_ui, "_host_path_for_config") as resolve_mock,
            mock.patch.object(helper_ui, "install_helper") as install_mock,
            mock.patch.object(helper_ui, "ensure_helper_autostart") as autostart_mock,
        ):
            repaired = helper_ui.auto_repair_browser_connections(settings)

        self.assertFalse(repaired)
        resolve_mock.assert_not_called()
        install_mock.assert_not_called()
        autostart_mock.assert_not_called()

    def test_auto_install_helper_returns_true_when_auto_repair_succeeds(self) -> None:
        settings = _FakeSettings()

        with (
            mock.patch.object(helper_ui, "auto_repair_browser_connections", return_value=True),
            mock.patch.object(helper_ui, "load_extension_environments") as load_mock,
        ):
            installed = helper_ui.auto_install_helper(settings)

        self.assertTrue(installed)
        load_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
