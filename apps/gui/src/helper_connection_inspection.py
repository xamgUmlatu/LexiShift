from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Callable, Optional, Sequence

from helper_connection_models import (
    HELPER_STATE_CONFIGURED,
    HELPER_STATE_NEEDS_REPAIR,
    HELPER_STATE_NOT_CONFIGURED,
    HelperInstallStatus,
    HOST_MODE_BUNDLED,
    HOST_MODE_WORKSPACE,
    REPAIR_REASON_ALLOWED_ORIGINS_MISSING,
    REPAIR_REASON_BUNDLED_CORE_STALE,
    REPAIR_REASON_BUNDLED_HOST_STALE,
    REPAIR_REASON_HOST_PATH_MISSING,
    REPAIR_REASON_MANIFEST_MISSING_HOST_PATH,
    REPAIR_REASON_MANIFEST_UNREADABLE,
    REPAIR_REASON_WORKSPACE_LEGACY_DIRECT_SCRIPT,
    REPAIR_REASON_WORKSPACE_PYTHON_MISSING,
    REPAIR_REASON_WORKSPACE_WRAPPER_STALE,
    REPAIR_REASON_WORKSPACE_WRAPPER_UNREADABLE,
)


def bundled_freshness_issue(
    host_path: Path,
    *,
    bundled_source_host: Callable[[], Optional[Path]],
    stable_bundled_host_path: Callable[[], Path],
    hash_file: Callable[[Path], Optional[str]],
    stable_bundled_core_path: Callable[[], Path],
    find_core_dir: Callable[[Path], Optional[Path]],
    hash_directory: Callable[[Path], Optional[str]],
    is_windows: bool,
) -> Optional[tuple[str, str]]:
    source_host = bundled_source_host()
    if source_host is None:
        return None
    stable_path = stable_bundled_host_path()
    try:
        if host_path.resolve() != stable_path.resolve():
            return None
    except OSError:
        if host_path != stable_path:
            return None
    source_digest = hash_file(source_host)
    installed_digest = hash_file(host_path)
    if source_digest and installed_digest and source_digest != installed_digest:
        return REPAIR_REASON_BUNDLED_HOST_STALE, "Bundled host copy is stale."
    if is_windows:
        return None
    source_core = find_core_dir(source_host)
    installed_core = stable_bundled_core_path()
    if source_core and installed_core.exists():
        source_core_digest = hash_directory(source_core)
        installed_core_digest = hash_directory(installed_core)
        if (
            source_core_digest
            and installed_core_digest
            and source_core_digest != installed_core_digest
        ):
            return REPAIR_REASON_BUNDLED_CORE_STALE, "Bundled lexishift_core copy is stale."
    return None


def workspace_wrapper_issue(
    host_path: Path,
    *,
    workspace_host_script: Callable[[], Optional[Path]],
    workspace_host_wrapper_path: Callable[[], Path],
    resolve_workspace_python: Callable[..., Optional[Path]],
    build_workspace_wrapper_script: Callable[[Path, Path], str],
) -> Optional[tuple[str, str]]:
    workspace = workspace_host_script()
    if workspace is None:
        return REPAIR_REASON_WORKSPACE_PYTHON_MISSING, "Workspace host could not be resolved."
    wrapper_path = workspace_host_wrapper_path()
    try:
        resolved = host_path.resolve()
    except OSError:
        resolved = host_path
    try:
        if resolved == workspace.resolve():
            return (
                REPAIR_REASON_WORKSPACE_LEGACY_DIRECT_SCRIPT,
                "Workspace host uses a legacy direct script path. Repair to install the pinned Python wrapper.",
            )
    except OSError:
        if resolved == workspace:
            return (
                REPAIR_REASON_WORKSPACE_LEGACY_DIRECT_SCRIPT,
                "Workspace host uses a legacy direct script path. Repair to install the pinned Python wrapper.",
            )
    try:
        if resolved != wrapper_path.resolve():
            return None
    except OSError:
        if resolved != wrapper_path:
            return None
    python_path = resolve_workspace_python(workspace, validate=False)
    if python_path is None or not python_path.exists():
        return (
            REPAIR_REASON_WORKSPACE_PYTHON_MISSING,
            "Workspace host wrapper is missing its Python interpreter.",
        )
    expected = build_workspace_wrapper_script(workspace, python_path)
    try:
        actual = host_path.read_text(encoding="utf-8")
    except OSError:
        return (
            REPAIR_REASON_WORKSPACE_WRAPPER_UNREADABLE,
            "Workspace host wrapper could not be read.",
        )
    if actual != expected:
        return REPAIR_REASON_WORKSPACE_WRAPPER_STALE, "Workspace host wrapper is stale."
    return None


def inspect_helper_installation(
    *,
    browser: str = "chrome",
    expected_extension_ids: Sequence[str] = (),
    read_windows_manifest: Callable[[str], Optional[Path]],
    manifest_path: Callable[[str], Optional[Path]],
    normalize_extension_ids: Callable[[Sequence[str]], tuple[str, ...]],
    extension_id_from_origin: Callable[[object], Optional[str]],
    infer_host_mode: Callable[[Optional[Path]], Optional[str]],
    bundled_freshness_issue: Callable[[Path], Optional[tuple[str, str]]],
    workspace_wrapper_issue: Callable[[Path], Optional[tuple[str, str]]],
) -> HelperInstallStatus:
    manifest = (
        read_windows_manifest(browser) if sys.platform.startswith("win") else manifest_path(browser)
    )
    expected_ids = normalize_extension_ids(expected_extension_ids)
    if not manifest or not manifest.exists():
        return HelperInstallStatus(
            browser=browser,
            state=HELPER_STATE_NOT_CONFIGURED,
            manifest_path=manifest,
            expected_extension_ids=expected_ids,
            message="Native-messaging manifest is missing.",
        )
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return HelperInstallStatus(
            browser=browser,
            state=HELPER_STATE_NEEDS_REPAIR,
            manifest_path=manifest,
            expected_extension_ids=expected_ids,
            repair_reasons=(REPAIR_REASON_MANIFEST_UNREADABLE,),
            message="Native-messaging manifest could not be read.",
        )
    allowed_ids = normalize_extension_ids(
        extension_id
        for extension_id in (
            extension_id_from_origin(origin) for origin in (data.get("allowed_origins") or [])
        )
        if extension_id
    )
    missing_ids = tuple(
        extension_id for extension_id in expected_ids if extension_id not in allowed_ids
    )
    unexpected_ids = tuple(
        extension_id for extension_id in allowed_ids if extension_id not in expected_ids
    )
    raw_host_path = str(data.get("path", "") or "").strip()
    host_path = Path(raw_host_path) if raw_host_path else None
    host_mode = infer_host_mode(host_path)
    repair_messages: list[str] = []
    repair_reasons: list[str] = []

    def add_repair(reason: str, message: str) -> None:
        if reason not in repair_reasons:
            repair_reasons.append(reason)
        repair_messages.append(message)

    if host_path is None:
        add_repair(REPAIR_REASON_MANIFEST_MISSING_HOST_PATH, "Manifest is missing a host path.")
    elif not host_path.exists():
        add_repair(REPAIR_REASON_HOST_PATH_MISSING, f"Host path is missing: {host_path}")
    if missing_ids:
        add_repair(
            REPAIR_REASON_ALLOWED_ORIGINS_MISSING,
            "Manifest is missing allowed origins for: " + ", ".join(missing_ids),
        )
    if host_path is not None and host_path.exists() and host_mode == HOST_MODE_BUNDLED:
        issue = bundled_freshness_issue(host_path)
        if issue:
            add_repair(*issue)
    if host_path is not None and host_path.exists() and host_mode == HOST_MODE_WORKSPACE:
        issue = workspace_wrapper_issue(host_path)
        if issue:
            add_repair(*issue)
    state = HELPER_STATE_NEEDS_REPAIR if repair_messages else HELPER_STATE_CONFIGURED
    message = " ".join(repair_messages) if repair_messages else "Browser connection is configured."
    return HelperInstallStatus(
        browser=browser,
        state=state,
        manifest_path=manifest,
        host_path=host_path,
        host_mode=host_mode,
        allowed_extension_ids=allowed_ids,
        expected_extension_ids=expected_ids,
        missing_extension_ids=missing_ids,
        unexpected_extension_ids=unexpected_ids,
        repair_reasons=tuple(repair_reasons),
        message=message,
    )
