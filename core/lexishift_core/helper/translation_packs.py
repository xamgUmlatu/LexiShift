from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.helper.installed_packs import (
    load_installed_pack_manifest_for_artifact,
    resolve_installed_pack_artifact,
)
from lexishift_core.helper.lp_capabilities import normalize_pair_key

FORWARD_PACK_DIRECTION = "forward"
REVERSE_PACK_DIRECTION = "reverse"


@dataclass(frozen=True)
class TranslationPackRef:
    pair: str
    direction: str
    path: Path
    provider: str
    pack_id: str
    pos_source_profile: str


def infer_translation_pack_provider(path: Path | None) -> str | None:
    if path is None:
        return None
    for candidate_text in _provider_hint_texts(path):
        if "wiktionary" in candidate_text or "kaikki" in candidate_text:
            return "wiktionary"
        if any(marker in candidate_text for marker in _FREEDICT_HINTS):
            return "freedict"
    return None


_FREEDICT_HINTS = (
    "freedict",
    "eng-deu",
    "deu-eng",
    "eng-spa",
    "spa-eng",
)


def _provider_hint_texts(path: Path) -> tuple[str, ...]:
    candidate = Path(path)
    values: list[str] = []
    for raw_value in (
        candidate.name,
        candidate.stem,
        candidate.parent.name,
    ):
        normalized = str(raw_value or "").strip().lower()
        if normalized and normalized not in values:
            values.append(normalized)
    return tuple(values)


def build_translation_pack_ref(
    pair: str,
    path: Path | None,
    *,
    direction: str = FORWARD_PACK_DIRECTION,
) -> Optional[TranslationPackRef]:
    if path is None:
        return None
    normalized_pair = normalize_pair_key(pair)
    candidate = Path(path)
    manifest = load_installed_pack_manifest_for_artifact(candidate)
    provider = (
        str(manifest.provider).strip().lower()
        if manifest is not None and str(manifest.provider).strip()
        else infer_translation_pack_provider(candidate) or "translation"
    )
    pack_id = build_translation_pack_id(
        normalized_pair,
        provider=provider,
        direction=direction,
    )
    return TranslationPackRef(
        pair=normalized_pair,
        direction=direction,
        path=candidate,
        provider=provider,
        pack_id=pack_id,
        pos_source_profile=provider,
    )


def resolve_configured_language_pack_paths(
    *,
    language_packs_dir: Path,
    settings_language_pack_paths: Mapping[str, str] | None = None,
    managed_language_pack_ids: Sequence[str] = (),
) -> dict[str, str]:
    configured = {
        str(pack_id).strip(): str(raw_path).strip()
        for pack_id, raw_path in dict(settings_language_pack_paths or {}).items()
        if str(pack_id).strip() and str(raw_path).strip()
    }
    for pack_id in tuple(managed_language_pack_ids or ()):
        pack_key = str(pack_id or "").strip()
        if not pack_key:
            continue
        resolved = resolve_installed_pack_artifact(language_packs_dir, pack_key)
        if resolved is not None and resolved.is_file():
            configured[pack_key] = str(resolved)
    return configured


def build_translation_pack_id(
    pair: str,
    *,
    provider: str,
    direction: str = FORWARD_PACK_DIRECTION,
) -> str:
    source_lang, target_lang = _split_pair_languages(pair)
    if direction == REVERSE_PACK_DIRECTION:
        left, right = source_lang, target_lang
    else:
        left, right = target_lang, source_lang
    provider_text = str(provider or "").strip().lower() or "translation"
    return f"{provider_text}_{left}_{right}"


def _split_pair_languages(pair: str) -> tuple[str, str]:
    normalized = normalize_pair_key(pair)
    left, sep, right = normalized.partition("-")
    if not sep or not left or not right:
        raise ValueError(f"Invalid language pair '{pair}'.")
    return left, right
