from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import re


DEFAULT_PROFILE_ID = "default"
DEFAULT_STOPWORDS_DE = (
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "ein",
    "eine",
    "einer",
    "einem",
    "einen",
    "und",
    "oder",
    "aber",
    "auch",
    "nicht",
    "kein",
    "keine",
    "ich",
    "du",
    "er",
    "sie",
    "es",
    "wir",
    "ihr",
    "sie",
    "im",
    "in",
    "am",
    "an",
    "zu",
    "von",
    "mit",
    "für",
    "auf",
    "aus",
    "bei",
    "nach",
    "vor",
    "über",
    "unter",
)


def _sanitize_profile_id(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return DEFAULT_PROFILE_ID
    # Keep profile directory segments deterministic and filesystem-safe.
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", raw)
    return normalized or DEFAULT_PROFILE_ID


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
    app_settings_path: Path
    srs_store_path: Path
    srs_settings_path: Path
    srs_status_path: Path
    srs_signal_queue_path: Path
    language_packs_dir: Path
    frequency_packs_dir: Path

    def normalize_profile_id(self, profile_id: str | None) -> str:
        return _sanitize_profile_id(profile_id or DEFAULT_PROFILE_ID)

    def profile_srs_dir(self, profile_id: str | None = None) -> Path:
        safe_profile = self.normalize_profile_id(profile_id)
        directory = self.srs_dir / "profiles" / safe_profile
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def srs_store_path_for(self, profile_id: str | None = None) -> Path:
        return self.profile_srs_dir(profile_id) / "srs_store.json"

    def srs_status_path_for(self, profile_id: str | None = None) -> Path:
        return self.profile_srs_dir(profile_id) / "srs_status.json"

    def srs_signal_queue_path_for(self, profile_id: str | None = None) -> Path:
        return self.profile_srs_dir(profile_id) / "srs_signal_queue.json"

    def snapshot_path(self, pair: str, profile_id: str | None = None) -> Path:
        safe_pair = pair.replace("/", "-").replace(":", "-")
        return self.profile_srs_dir(profile_id) / f"srs_rulegen_snapshot_{safe_pair}.json"

    def ruleset_path(self, pair: str, profile_id: str | None = None) -> Path:
        safe_pair = pair.replace("/", "-").replace(":", "-")
        return self.profile_srs_dir(profile_id) / f"srs_ruleset_{safe_pair}.json"


def build_helper_paths(root: Path | None = None) -> HelperPaths:
    data_root = root or resolve_data_root()
    srs_dir = data_root / "srs"
    srs_dir.mkdir(parents=True, exist_ok=True)
    default_profile_dir = srs_dir / "profiles" / DEFAULT_PROFILE_ID
    default_profile_dir.mkdir(parents=True, exist_ok=True)
    language_packs_dir = data_root / "language_packs"
    frequency_packs_dir = data_root / "frequency_packs"
    _ensure_default_stopwords(srs_dir)
    return HelperPaths(
        data_root=data_root,
        srs_dir=srs_dir,
        app_settings_path=data_root / "settings.json",
        srs_store_path=default_profile_dir / "srs_store.json",
        srs_settings_path=srs_dir / "srs_settings.json",
        srs_status_path=default_profile_dir / "srs_status.json",
        srs_signal_queue_path=default_profile_dir / "srs_signal_queue.json",
        language_packs_dir=language_packs_dir,
        frequency_packs_dir=frequency_packs_dir,
    )


def _ensure_default_stopwords(srs_dir: Path) -> None:
    stopwords_dir = srs_dir / "stopwords"
    stopwords_dir.mkdir(parents=True, exist_ok=True)
    de_path = stopwords_dir / "stopwords-de.json"
    if not de_path.exists():
        payload = json.dumps(list(DEFAULT_STOPWORDS_DE), ensure_ascii=False, indent=2)
        de_path.write_text(payload + "\n", encoding="utf-8")
