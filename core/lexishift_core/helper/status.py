from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class HelperStatus:
    version: int = 1
    helper_version: str = "0.1.1"
    last_run_at: Optional[str] = None
    last_error: Optional[str] = None
    last_pair: Optional[str] = None
    last_rule_count: int = 0
    last_target_count: int = 0


def status_from_dict(data: Mapping[str, Any]) -> HelperStatus:
    return HelperStatus(
        version=int(data.get("version", 1)),
        helper_version=str(data.get("helper_version", "0.1.1")),
        last_run_at=data.get("last_run_at"),
        last_error=data.get("last_error"),
        last_pair=data.get("last_pair"),
        last_rule_count=int(data.get("last_rule_count", 0)),
        last_target_count=int(data.get("last_target_count", 0)),
    )


def status_to_dict(status: HelperStatus) -> dict[str, Any]:
    return {
        "version": status.version,
        "helper_version": status.helper_version,
        "last_run_at": status.last_run_at,
        "last_error": status.last_error,
        "last_pair": status.last_pair,
        "last_rule_count": status.last_rule_count,
        "last_target_count": status.last_target_count,
    }


def load_status(path: str | Path) -> HelperStatus:
    status_path = Path(path)
    if not status_path.exists():
        return HelperStatus()
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return HelperStatus()
    if not isinstance(payload, Mapping):
        return HelperStatus()
    try:
        return status_from_dict(payload)
    except (TypeError, ValueError):
        return HelperStatus()


def save_status(status: HelperStatus, path: str | Path) -> None:
    status_path = Path(path)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=status_path.parent,
            prefix=f".{status_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(status_to_dict(status), handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, status_path)
    finally:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
