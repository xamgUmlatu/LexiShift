from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys


def _platform_data_root() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(home / "AppData" / "Roaming")
        return Path(base) / "LexiShift" / "LexiShift"
    return home / ".local" / "share" / "LexiShift" / "LexiShift"


def resolve_data_root() -> Path:
    override = os.environ.get("LEXISHIFT_DATA_DIR")
    root = Path(override) if override else _platform_data_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


@dataclass(frozen=True)
class HelperPaths:
    data_root: Path
    srs_dir: Path
    srs_store_path: Path
    srs_settings_path: Path
    srs_status_path: Path
    srs_signal_queue_path: Path
    language_packs_dir: Path
    frequency_packs_dir: Path

    def snapshot_path(self, pair: str) -> Path:
        safe_pair = pair.replace("/", "-").replace(":", "-")
        return self.srs_dir / f"srs_rulegen_snapshot_{safe_pair}.json"

    def ruleset_path(self, pair: str) -> Path:
        safe_pair = pair.replace("/", "-").replace(":", "-")
        return self.srs_dir / f"srs_ruleset_{safe_pair}.json"


def build_helper_paths(root: Path | None = None) -> HelperPaths:
    data_root = root or resolve_data_root()
    srs_dir = data_root / "srs"
    srs_dir.mkdir(parents=True, exist_ok=True)
    language_packs_dir = data_root / "language_packs"
    frequency_packs_dir = data_root / "frequency_packs"
    return HelperPaths(
        data_root=data_root,
        srs_dir=srs_dir,
        srs_store_path=srs_dir / "srs_store.json",
        srs_settings_path=srs_dir / "srs_settings.json",
        srs_status_path=srs_dir / "srs_status.json",
        srs_signal_queue_path=srs_dir / "srs_signal_queue.json",
        language_packs_dir=language_packs_dir,
        frequency_packs_dir=frequency_packs_dir,
    )
