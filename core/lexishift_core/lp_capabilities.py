from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class PairCapability:
    pair: str
    rulegen_mode: Optional[str] = None
    default_frequency_db: Optional[str] = None
    requires_jmdict_for_seed: bool = False
    requires_jmdict_for_rulegen: bool = False
    requires_freedict_de_en_for_rulegen: bool = False


_PAIR_CAPABILITIES: dict[str, PairCapability] = {
    "en-ja": PairCapability(
        pair="en-ja",
        rulegen_mode="ja_en",
        default_frequency_db="freq-ja-bccwj.sqlite",
        requires_jmdict_for_seed=True,
        requires_jmdict_for_rulegen=True,
    ),
    "ja-ja": PairCapability(
        pair="ja-ja",
        default_frequency_db="freq-ja-bccwj.sqlite",
    ),
    "en-en": PairCapability(
        pair="en-en",
        default_frequency_db="freq-en-coca.sqlite",
    ),
    "de-en": PairCapability(
        pair="de-en",
        default_frequency_db="freq-en-coca.sqlite",
    ),
    "en-de": PairCapability(
        pair="en-de",
        rulegen_mode="en_de",
        requires_freedict_de_en_for_rulegen=True,
    ),
    "de-de": PairCapability(pair="de-de"),
    "en-zh": PairCapability(pair="en-zh"),
}


def normalize_pair_key(pair: str, *, default: str = "en-ja") -> str:
    normalized = str(pair or "").strip().lower()
    return normalized or default


def _target_language(pair: str) -> str:
    normalized = normalize_pair_key(pair)
    parts = normalized.split("-", 1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip().lower()
    return ""


def resolve_pair_capability(pair: str) -> PairCapability:
    normalized = normalize_pair_key(pair)
    return _PAIR_CAPABILITIES.get(normalized, PairCapability(pair=normalized))


def supports_rulegen(pair: str) -> bool:
    capability = resolve_pair_capability(pair)
    return capability.rulegen_mode is not None


def default_frequency_db_path(
    pair: str,
    *,
    frequency_packs_dir: Path,
) -> Optional[Path]:
    capability = resolve_pair_capability(pair)
    if capability.default_frequency_db:
        return frequency_packs_dir / capability.default_frequency_db
    target_lang = _target_language(capability.pair)
    if not target_lang:
        return None
    # Fallback convention for LPs that have not yet declared a concrete corpus filename.
    return frequency_packs_dir / f"freq-{target_lang}-default.sqlite"


def default_jmdict_path(
    pair: str,
    *,
    language_packs_dir: Path,
) -> Optional[Path]:
    capability = resolve_pair_capability(pair)
    if not (
        capability.requires_jmdict_for_seed or capability.requires_jmdict_for_rulegen
    ):
        return None
    return language_packs_dir / "JMdict_e"


def default_freedict_de_en_path(
    pair: str,
    *,
    language_packs_dir: Path,
) -> Optional[Path]:
    capability = resolve_pair_capability(pair)
    if not capability.requires_freedict_de_en_for_rulegen:
        return None
    direct_candidates = (
        language_packs_dir / "deu-eng.tei",
        language_packs_dir / "freedict-de-en" / "deu-eng.tei",
    )
    for candidate in direct_candidates:
        if candidate.exists():
            return candidate
    discovered = sorted(language_packs_dir.rglob("deu-eng.tei"))
    if discovered:
        return discovered[0]
    return language_packs_dir / "deu-eng.tei"


def pair_requirements(pair: str) -> dict[str, object]:
    capability = resolve_pair_capability(pair)
    fallback_frequency = capability.default_frequency_db
    if not fallback_frequency:
        target_lang = _target_language(capability.pair)
        fallback_frequency = f"freq-{target_lang}-default.sqlite" if target_lang else None
    return {
        "pair": capability.pair,
        "rulegen_mode": capability.rulegen_mode,
        "supports_rulegen": supports_rulegen(capability.pair),
        "default_frequency_db": fallback_frequency,
        "requires_jmdict_for_seed": capability.requires_jmdict_for_seed,
        "requires_jmdict_for_rulegen": capability.requires_jmdict_for_rulegen,
        "requires_freedict_de_en_for_rulegen": capability.requires_freedict_de_en_for_rulegen,
    }
