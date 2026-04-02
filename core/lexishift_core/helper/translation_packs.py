from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from lexishift_core.helper.installed_packs import load_installed_pack_manifest_for_artifact
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
    name = path.name.strip().lower()
    if "wiktionary" in name or "kaikki" in name:
        return "wiktionary"
    return "freedict"


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
        else infer_translation_pack_provider(candidate) or "freedict"
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
