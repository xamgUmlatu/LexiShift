from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_ID_PLACEHOLDERS = {"", "__FILL_ME__", "<FILL_ME>"}
HOST_MODE_BUNDLED = "bundled"
HOST_MODE_WORKSPACE = "workspace"
HOST_MODE_CUSTOM = "custom"
TARGET_KIND_PROD = "prod"
TARGET_KIND_UNPACKED = "unpacked"
HELPER_STATE_CONFIGURED = "configured"
HELPER_STATE_NEEDS_REPAIR = "needs_repair"
HELPER_STATE_NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True)
class ExtensionEnvironment:
    key: str
    label: str
    browser: str
    extension_id: str
    fixed: bool


@dataclass(frozen=True)
class BrowserConnectionTarget:
    key: str
    label: str
    extension_id: str
    kind: str
    fixed: bool = False


@dataclass(frozen=True)
class BrowserConnectionConfig:
    browser: str
    host_mode: str
    host_override_path: Optional[str] = None
    targets: tuple[BrowserConnectionTarget, ...] = ()


@dataclass(frozen=True)
class HelperInstallStatus:
    browser: str
    state: str
    manifest_path: Optional[Path] = None
    host_path: Optional[Path] = None
    host_mode: Optional[str] = None
    allowed_extension_ids: tuple[str, ...] = ()
    expected_extension_ids: tuple[str, ...] = ()
    missing_extension_ids: tuple[str, ...] = ()
    message: str = ""


def default_extension_environments() -> tuple[list[ExtensionEnvironment], str]:
    envs = [
        ExtensionEnvironment(
            key="chrome_prod",
            label="Chrome (Web Store)",
            browser="chrome",
            extension_id="",
            fixed=True,
        ),
        ExtensionEnvironment(
            key="chrome_dev",
            label="Chrome (Unpacked Dev)",
            browser="chrome",
            extension_id="",
            fixed=False,
        ),
        ExtensionEnvironment(
            key="brave_prod",
            label="Brave (Web Store)",
            browser="brave",
            extension_id="",
            fixed=True,
        ),
        ExtensionEnvironment(
            key="chromium_dev",
            label="Chromium (Unpacked Dev)",
            browser="chromium",
            extension_id="",
            fixed=False,
        ),
    ]
    return envs, "chrome_prod"
