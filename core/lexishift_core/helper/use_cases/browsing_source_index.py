from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path

from lexishift_core.helper.lp_capabilities import (
    default_japanese_lesson_vocabulary_path,
    default_jlpt_vocabulary_path,
    default_jmnedict_path,
    default_kanjidic2_path,
    default_kanjivg_path,
    resolve_pair_capability,
)
from lexishift_core.helper.pair_resources import resolve_pair_frequency_pack
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen import RulegenConfig, SetInitializationConfig
from lexishift_core.rulegen.tuning import resolve_rulegen_tuning
from lexishift_core.srs import SrsSettings, SrsStore
from lexishift_core.srs.pos_overlay import resolve_pair_pos_overlay


DEFAULT_SOURCE_INDEX_TOP_N = 2000
DEFAULT_MAX_SOURCE_INDEX_TARGETS = 400
DEFAULT_MAX_SOURCE_INDEX_RULES = 1200


def build_srs_browsing_source_index(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str = "default",
    top_n: int | None = None,
    max_targets: int | None = None,
    max_rules: int | None = None,
    jmdict_path: Path | None = None,
    translation_dict_path: Path | None = None,
    set_source_db: Path | None = None,
    resolve_pair_set_top_n_fn: Callable[..., int | None],
    resolve_pair_resources_fn: Callable[..., tuple[Path | None, Path | None, Path | None]],
    ensure_pair_requirements_fn: Callable[..., None],
    resolve_profile_id_fn: Callable[..., str],
    resolve_stopwords_path_fn: Callable[..., Path | None],
    initialize_store_from_frequency_list_with_report_fn: Callable[..., tuple[SrsStore, object]],
    run_rulegen_for_pair_fn: Callable[..., tuple[SrsStore, object]],
) -> dict[str, object]:
    capability = resolve_pair_capability(pair)
    normalized_pair = capability.pair
    normalized_profile_id = resolve_profile_id_fn(paths, profile_id=profile_id)
    effective_top_n = _effective_positive_int(
        top_n,
        fallback=resolve_pair_set_top_n_fn(
            pair=normalized_pair,
            requested_top_n=None,
            purpose="refresh",
        )
        or DEFAULT_SOURCE_INDEX_TOP_N,
    )
    effective_max_targets = _effective_positive_int(
        max_targets,
        fallback=min(effective_top_n, DEFAULT_MAX_SOURCE_INDEX_TARGETS),
    )
    effective_max_rules = _effective_positive_int(
        max_rules,
        fallback=DEFAULT_MAX_SOURCE_INDEX_RULES,
    )
    resolved_jmdict_path, resolved_translation_dict_path, resolved_set_source_db = (
        resolve_pair_resources_fn(
            paths,
            pair=normalized_pair,
            jmdict_path=jmdict_path,
            translation_dict_path=translation_dict_path,
            set_source_db=set_source_db,
        )
    )
    ensure_pair_requirements_fn(
        pair=normalized_pair,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        require_frequency_db=True,
        set_source_db=resolved_set_source_db,
        check_seed_resources=True,
        check_rulegen_resources=True,
    )
    if resolved_set_source_db is None:
        raise ValueError(f"Missing frequency source DB for pair '{normalized_pair}'.")

    frequency_pack = resolve_pair_frequency_pack(
        paths,
        pair=normalized_pair,
        set_source_db=resolved_set_source_db,
    )
    pos_overlay = resolve_pair_pos_overlay(paths, pair=normalized_pair)
    set_init_config = SetInitializationConfig(
        frequency_db=resolved_set_source_db,
        jmdict_path=resolved_jmdict_path,
        source_label=frequency_pack.provider if frequency_pack else None,
        top_n=effective_top_n,
        initial_active_count=effective_max_targets,
        language_pair=normalized_pair,
        stopwords_path=resolve_stopwords_path_fn(paths, pair=normalized_pair),
        require_jmdict=capability.requires_jmdict_for_seed,
        pos_overlay_path=pos_overlay.path if pos_overlay else None,
        seed_cache_dir=paths.srs_seed_frontier_cache_dir(),
    )
    temp_store, init_report = initialize_store_from_frequency_list_with_report_fn(
        SrsStore(),
        config=set_init_config,
    )
    targets = tuple(
        str(item.lemma).strip()
        for item in temp_store.items
        if str(getattr(item, "lemma", "") or "").strip()
    )
    target_ids = tuple(
        str(item.item_id).strip()
        for item in temp_store.items
        if str(getattr(item, "item_id", "") or "").strip()
    )
    tuning = resolve_rulegen_tuning(pair=normalized_pair)
    _updated_store, output = run_rulegen_for_pair_fn(
        paths=paths,
        pair=normalized_pair,
        profile_id=normalized_profile_id,
        store=temp_store,
        settings=SrsSettings(),
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        rulegen_config=RulegenConfig(
            language_pair=normalized_pair,
            max_definitions_per_target=tuning.max_definitions_per_target,
            max_rules_per_target=tuning.max_rules_per_target,
            semantic_demotion_scale=tuning.semantic_demotion_scale,
            enable_source_frequency_prior=tuning.source_frequency_prior_enabled,
            include_variants=tuning.include_variants,
            allow_multiword_glosses=tuning.allow_multiword_glosses,
            enable_exact_gloss_demotions=tuning.enable_exact_gloss_demotions,
            max_snapshot_targets=0,
            max_snapshot_sources=0,
        ),
        targets_override=targets,
        active_item_ids=target_ids,
        initialize_if_empty=False,
        persist_store=False,
    )
    rules = _compact_source_rules(
        getattr(output, "rules", ()),
        pair=normalized_pair,
        limit=effective_max_rules,
    )
    return {
        "status": "ok",
        "pair": normalized_pair,
        "profile_id": normalized_profile_id,
        "rules": rules,
        "rule_count": len(rules),
        "target_count": len(targets),
        "source": "candidate_frontier_rulegen",
        "frontier": {
            "top_n": effective_top_n,
            "max_targets": effective_max_targets,
            "selected_unique_count": int(getattr(init_report, "selected_unique_count", 0) or 0),
            "admitted_count": int(getattr(init_report, "admitted_count", 0) or 0),
            "selected_preview": list(getattr(init_report, "selected_preview", ()) or ()),
        },
        "resources": {
            "frequency_db": str(resolved_set_source_db),
            "frequency_pack_id": frequency_pack.pack_id if frequency_pack else None,
            "jmdict_path": str(resolved_jmdict_path) if resolved_jmdict_path else None,
            "translation_dict_path": (
                str(resolved_translation_dict_path) if resolved_translation_dict_path else None
            ),
            "pos_overlay_path": str(pos_overlay.path) if pos_overlay else None,
            "kanjidic2_path": _existing_optional_path(
                default_kanjidic2_path(normalized_pair, language_packs_dir=paths.language_packs_dir)
            ),
            "kanjivg_path": _existing_optional_path(
                default_kanjivg_path(normalized_pair, language_packs_dir=paths.language_packs_dir)
            ),
            "jmnedict_path": _existing_optional_path(
                default_jmnedict_path(normalized_pair, language_packs_dir=paths.language_packs_dir)
            ),
            "jlpt_vocabulary_path": _existing_optional_path(
                default_jlpt_vocabulary_path(
                    normalized_pair,
                    language_packs_dir=paths.language_packs_dir,
                )
            ),
            "lesson_vocabulary_path": _existing_optional_path(
                default_japanese_lesson_vocabulary_path(
                    normalized_pair,
                    language_packs_dir=paths.language_packs_dir,
                )
            ),
        },
    }


def _compact_source_rules(
    rules: Sequence[Mapping[str, object] | object],
    *,
    pair: str,
    limit: int,
) -> list[dict[str, object]]:
    compact: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for rule in rules:
        source_phrase = _rule_attr(rule, "source_phrase")
        replacement = _rule_attr(rule, "replacement")
        metadata = _rule_metadata(rule)
        if not source_phrase or not replacement:
            continue
        key = (source_phrase, replacement, _word_package_key(metadata))
        if key in seen:
            continue
        seen.add(key)
        compact.append(
            {
                "source_phrase": source_phrase,
                "replacement": replacement,
                "enabled": True,
                "metadata": {
                    **metadata,
                    "lexishift_origin": "srs",
                    "language_pair": pair,
                    "source_index": "candidate_frontier",
                },
            }
        )
        if len(compact) >= limit:
            break
    return compact


def _rule_attr(rule: Mapping[str, object] | object, name: str) -> str:
    if isinstance(rule, Mapping):
        value = rule.get(name)
    else:
        value = getattr(rule, name, None)
    return str(value or "").strip()


def _rule_metadata(rule: Mapping[str, object] | object) -> dict[str, object]:
    if isinstance(rule, Mapping):
        value = rule.get("metadata")
    else:
        value = getattr(rule, "metadata", None)
    if is_dataclass(value):
        return {key: item for key, item in asdict(value).items() if item is not None}
    return dict(value) if isinstance(value, Mapping) else {}


def _word_package_key(metadata: Mapping[str, object]) -> str:
    word_package = metadata.get("word_package")
    if not isinstance(word_package, Mapping):
        return ""
    surface = str(word_package.get("surface") or "").strip()
    reading = str(word_package.get("reading") or "").strip()
    return f"{surface}|{reading}" if reading else surface


def _effective_positive_int(value: object, *, fallback: int) -> int:
    try:
        parsed = int(value) if value is not None else int(fallback)
    except (TypeError, ValueError):
        parsed = int(fallback)
    return max(1, parsed)


def _existing_optional_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path) if Path(path).exists() else None
