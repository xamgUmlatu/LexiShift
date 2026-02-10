from __future__ import annotations

from pathlib import Path
from typing import Optional

from lexishift_core.helper.lp_capabilities import (
    default_freedict_de_en_path,
    default_frequency_db_path,
    default_jmdict_path,
    resolve_pair_capability,
)
from lexishift_core.helper.paths import HelperPaths


def target_language_from_pair(pair: str) -> str:
    normalized = str(pair or "").strip()
    parts = normalized.split("-", 1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip().lower()
    return ""


def resolve_stopwords_path(paths: HelperPaths, *, pair: str) -> Optional[Path]:
    target_lang = target_language_from_pair(pair)
    if not target_lang:
        return None
    candidates = (
        paths.srs_dir / f"stopwords-{target_lang}.json",
        paths.srs_dir / "stopwords" / f"stopwords-{target_lang}.json",
        paths.data_root / "stopwords" / f"stopwords-{target_lang}.json",
        paths.language_packs_dir / f"stopwords-{target_lang}.json",
    )
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def resolve_pair_resources(
    paths: HelperPaths,
    *,
    pair: str,
    jmdict_path: Optional[Path],
    freedict_de_en_path: Optional[Path],
    set_source_db: Optional[Path],
) -> tuple[Optional[Path], Optional[Path], Optional[Path]]:
    capability = resolve_pair_capability(pair)
    resolved_jmdict = (
        Path(jmdict_path)
        if jmdict_path is not None
        else default_jmdict_path(capability.pair, language_packs_dir=paths.language_packs_dir)
    )
    resolved_freedict_de_en = (
        Path(freedict_de_en_path)
        if freedict_de_en_path is not None
        else default_freedict_de_en_path(
            capability.pair,
            language_packs_dir=paths.language_packs_dir,
        )
    )
    resolved_frequency_db = (
        Path(set_source_db)
        if set_source_db is not None
        else default_frequency_db_path(capability.pair, frequency_packs_dir=paths.frequency_packs_dir)
    )
    return resolved_jmdict, resolved_freedict_de_en, resolved_frequency_db
