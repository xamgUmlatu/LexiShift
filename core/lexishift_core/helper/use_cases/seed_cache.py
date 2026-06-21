from __future__ import annotations

from pathlib import Path
from typing import Optional

from lexishift_core.helper.lp_capabilities import (
    default_japanese_lesson_vocabulary_path,
    default_kanjidic2_path,
    default_kanjivg_path,
    default_jmnedict_path,
    default_jlpt_vocabulary_path,
    resolve_pair_capability,
    selectable_srs_pairs,
)
from lexishift_core.helper.pair_resources import (
    resolve_pair_frequency_pack,
    resolve_pair_resources,
    resolve_stopwords_path,
)
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.srs.pos_overlay import resolve_pair_pos_overlay
from lexishift_core.srs.seed import (
    SeedSelectionConfig,
    prepare_seed_frontier_cache,
    seed_frontier_cache_status,
)


def pairs_for_seed_resource_pack_id(pack_id: str) -> tuple[str, ...]:
    normalized_pack_id = _pack_id_key(pack_id)
    if not normalized_pack_id:
        return ()
    pairs: list[str] = []
    for pair in selectable_srs_pairs():
        capability = resolve_pair_capability(pair)
        if _frequency_pack_id_matches_pair(normalized_pack_id, capability):
            pairs.append(capability.pair)
            continue
        if normalized_pack_id == "jmdict-ja-en" and capability.requires_jmdict_for_seed:
            pairs.append(capability.pair)
            continue
        if normalized_pack_id == "kanjidic2-ja" and capability.pair in {"en-ja", "ja-ja"}:
            pairs.append(capability.pair)
            continue
        if normalized_pack_id == "jmnedict-ja" and capability.pair in {"en-ja", "ja-ja"}:
            pairs.append(capability.pair)
            continue
        if normalized_pack_id == "kanjivg-ja" and capability.pair in {"en-ja", "ja-ja"}:
            pairs.append(capability.pair)
            continue
        if normalized_pack_id == "jlpt-tanos-vocab-ja" and capability.pair in {
            "en-ja",
            "ja-ja",
        }:
            pairs.append(capability.pair)
            continue
        if normalized_pack_id == "sbsjapanese1-ja" and capability.pair in {"en-ja", "ja-ja"}:
            pairs.append(capability.pair)
            continue
        if normalized_pack_id in _default_pos_overlay_pack_ids_for_pair(capability.pair):
            pairs.append(capability.pair)
    return tuple(dict.fromkeys(pairs))


def get_srs_seed_frontier_cache_status(
    paths: HelperPaths,
    *,
    pair: str,
    set_source_db: Optional[Path] = None,
    jmdict_path: Optional[Path] = None,
) -> dict[str, object]:
    resource_payload = _resolve_seed_cache_resources(
        paths,
        pair=pair,
        set_source_db=set_source_db,
        jmdict_path=jmdict_path,
    )
    if not resource_payload["ok"]:
        return resource_payload
    return _public_seed_cache_payload(
        {
            **resource_payload,
            **seed_frontier_cache_status(
                frequency_db=Path(resource_payload["frequency_db"]),
                config=resource_payload["config"],
            ),
        }
    )


def prepare_srs_seed_frontier_cache(
    paths: HelperPaths,
    *,
    pair: str,
    set_source_db: Optional[Path] = None,
    jmdict_path: Optional[Path] = None,
    cleanup: bool = True,
) -> dict[str, object]:
    resource_payload = _resolve_seed_cache_resources(
        paths,
        pair=pair,
        set_source_db=set_source_db,
        jmdict_path=jmdict_path,
    )
    if not resource_payload["ok"]:
        return resource_payload
    return _public_seed_cache_payload(
        {
            **resource_payload,
            **prepare_seed_frontier_cache(
                frequency_db=Path(resource_payload["frequency_db"]),
                config=resource_payload["config"],
                cleanup=cleanup,
            ),
        }
    )


def prepare_srs_seed_frontier_caches_for_pack(
    paths: HelperPaths,
    *,
    pack_id: str,
    cleanup: bool = True,
) -> dict[str, object]:
    pairs = pairs_for_seed_resource_pack_id(pack_id)
    results = [prepare_srs_seed_frontier_cache(paths, pair=pair, cleanup=cleanup) for pair in pairs]
    return {
        "pack_id": str(pack_id or "").strip(),
        "pair_count": len(pairs),
        "pairs": list(pairs),
        "results": [_public_seed_cache_payload(result) for result in results],
        "prepared_count": sum(1 for result in results if result.get("prepared")),
        "blocked_count": sum(1 for result in results if result.get("status") == "blocked"),
    }


def _resolve_seed_cache_resources(
    paths: HelperPaths,
    *,
    pair: str,
    set_source_db: Optional[Path],
    jmdict_path: Optional[Path],
) -> dict[str, object]:
    capability = resolve_pair_capability(pair)
    resolved_jmdict_path, _translation_dict_path, resolved_frequency_db = resolve_pair_resources(
        paths,
        pair=capability.pair,
        jmdict_path=jmdict_path,
        set_source_db=set_source_db,
    )
    if resolved_frequency_db is None or not Path(resolved_frequency_db).is_file():
        return _blocked_payload(
            pair=capability.pair,
            reason="missing_frequency_db",
            frequency_db=resolved_frequency_db,
            jmdict_path=resolved_jmdict_path,
        )
    if capability.requires_jmdict_for_seed and (
        resolved_jmdict_path is None or not Path(resolved_jmdict_path).is_file()
    ):
        return _blocked_payload(
            pair=capability.pair,
            reason="missing_jmdict",
            frequency_db=resolved_frequency_db,
            jmdict_path=resolved_jmdict_path,
        )

    resolved_frequency_pack = resolve_pair_frequency_pack(
        paths,
        pair=capability.pair,
        set_source_db=resolved_frequency_db,
    )
    resolved_pos_overlay = resolve_pair_pos_overlay(paths, pair=capability.pair)
    resolved_kanjidic2_path = default_kanjidic2_path(
        capability.pair,
        language_packs_dir=paths.language_packs_dir,
    )
    if resolved_kanjidic2_path is not None and not Path(resolved_kanjidic2_path).is_file():
        resolved_kanjidic2_path = None
    resolved_jmnedict_path = default_jmnedict_path(
        capability.pair,
        language_packs_dir=paths.language_packs_dir,
    )
    if resolved_jmnedict_path is not None and not Path(resolved_jmnedict_path).is_file():
        resolved_jmnedict_path = None
    resolved_kanjivg_path = default_kanjivg_path(
        capability.pair,
        language_packs_dir=paths.language_packs_dir,
    )
    if resolved_kanjivg_path is not None and not Path(resolved_kanjivg_path).is_file():
        resolved_kanjivg_path = None
    resolved_jlpt_vocabulary_path = default_jlpt_vocabulary_path(
        capability.pair,
        language_packs_dir=paths.language_packs_dir,
    )
    if (
        resolved_jlpt_vocabulary_path is not None
        and not Path(resolved_jlpt_vocabulary_path).exists()
    ):
        resolved_jlpt_vocabulary_path = None
    resolved_lesson_vocabulary_path = default_japanese_lesson_vocabulary_path(
        capability.pair,
        language_packs_dir=paths.language_packs_dir,
    )
    if (
        resolved_lesson_vocabulary_path is not None
        and not Path(resolved_lesson_vocabulary_path).exists()
    ):
        resolved_lesson_vocabulary_path = None
    config = SeedSelectionConfig(
        language_pair=capability.pair,
        top_n=None,
        require_jmdict=capability.requires_jmdict_for_seed,
        jmdict_path=resolved_jmdict_path,
        jmnedict_path=resolved_jmnedict_path,
        kanjidic2_path=resolved_kanjidic2_path,
        kanjivg_path=resolved_kanjivg_path,
        jlpt_vocabulary_path=resolved_jlpt_vocabulary_path,
        lesson_vocabulary_path=resolved_lesson_vocabulary_path,
        stopwords_path=resolve_stopwords_path(paths, pair=capability.pair),
        source_label=resolved_frequency_pack.provider if resolved_frequency_pack else None,
        pos_overlay_path=resolved_pos_overlay.path if resolved_pos_overlay else None,
        cache_dir=paths.srs_seed_frontier_cache_dir(),
    )
    return {
        "ok": True,
        "status": "resolvable",
        "pair": capability.pair,
        "frequency_db": str(resolved_frequency_db),
        "frequency_pack_id": (resolved_frequency_pack.pack_id if resolved_frequency_pack else None),
        "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
        "jmnedict_path": str(resolved_jmnedict_path) if resolved_jmnedict_path else None,
        "kanjidic2_path": str(resolved_kanjidic2_path) if resolved_kanjidic2_path else None,
        "kanjivg_path": str(resolved_kanjivg_path) if resolved_kanjivg_path else None,
        "jlpt_vocabulary_path": (
            str(resolved_jlpt_vocabulary_path) if resolved_jlpt_vocabulary_path else None
        ),
        "lesson_vocabulary_path": (
            str(resolved_lesson_vocabulary_path) if resolved_lesson_vocabulary_path else None
        ),
        "requires_jmdict_for_seed": capability.requires_jmdict_for_seed,
        "pos_overlay_path": str(resolved_pos_overlay.path) if resolved_pos_overlay else None,
        "pos_overlay_id": resolved_pos_overlay.pack_id if resolved_pos_overlay else None,
        "config": config,
    }


def _blocked_payload(
    *,
    pair: str,
    reason: str,
    frequency_db: Optional[Path],
    jmdict_path: Optional[Path],
) -> dict[str, object]:
    return {
        "ok": False,
        "status": "blocked",
        "reason": reason,
        "pair": pair,
        "frequency_db": str(frequency_db) if frequency_db else None,
        "jmdict_path": str(jmdict_path) if jmdict_path else None,
        "prepared": False,
    }


def _public_seed_cache_payload(payload: dict[str, object]) -> dict[str, object]:
    public = dict(payload)
    public.pop("config", None)
    return public


def _frequency_pack_id_matches_pair(pack_id: str, capability) -> bool:
    return pack_id in {
        _pack_id_key(filename)
        for filename in (
            capability.default_frequency_db,
            *tuple(capability.fallback_frequency_dbs or ()),
        )
        if filename
    }


def _default_pos_overlay_pack_ids_for_pair(pair: str) -> tuple[str, ...]:
    _source, separator, target = str(pair or "").strip().lower().partition("-")
    if not separator:
        return ()
    if target == "es":
        return ("pos-es-ud-ancora-v1",)
    return ()


def _pack_id_key(value: object) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    return Path(normalized).stem.strip().lower()
