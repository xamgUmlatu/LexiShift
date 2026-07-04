from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
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
SOURCE_INDEX_CACHE_SCHEMA_VERSION = 2


def build_srs_browsing_source_index(
    paths: HelperPaths,
    *,
    pair: str,
    profile_id: str = "default",
    top_n: int | None = None,
    max_targets: int | None = None,
    max_rules: int | None = None,
    allow_generate: bool = True,
    force_refresh: bool = False,
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
    pos_overlay = resolve_pair_pos_overlay(paths, pair=normalized_pair)
    cache_path = paths.srs_browsing_source_index_path_for(
        profile_id=normalized_profile_id,
        pair=normalized_pair,
    )
    cache_key = _source_index_cache_key(
        pair=normalized_pair,
        profile_id=normalized_profile_id,
        top_n=effective_top_n,
        max_targets=effective_max_targets,
        max_rules=effective_max_rules,
        frequency_db=resolved_set_source_db,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        pos_overlay_path=pos_overlay.path if pos_overlay else None,
    )
    if not force_refresh:
        cached = _load_cached_source_index(cache_path, cache_key=cache_key)
        if cached is not None:
            return cached

    missing_inputs = _missing_required_inputs(
        capability=capability,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        set_source_db=resolved_set_source_db,
    )
    resources = _resources_payload(
        paths,
        pair=normalized_pair,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        set_source_db=resolved_set_source_db,
        pos_overlay_path=pos_overlay.path if pos_overlay else None,
        frequency_pack=None,
    )
    if missing_inputs:
        stale = (
            None
            if force_refresh
            else _load_cached_source_index(
                cache_path,
                cache_key=None,
                cache_source="helper-cache-stale",
                current_cache_key=cache_key,
                missing_inputs=missing_inputs,
            )
        )
        if stale is not None:
            return stale
        return _not_ready_payload(
            pair=normalized_pair,
            profile_id=normalized_profile_id,
            reason="missing_required_resources",
            missing_inputs=missing_inputs,
            resources=resources,
            cache_path=cache_path,
            cache_key=cache_key,
            cache_source="miss",
        )
    if not allow_generate:
        return _not_ready_payload(
            pair=normalized_pair,
            profile_id=normalized_profile_id,
            reason="source_index_cache_miss",
            missing_inputs=(),
            resources=resources,
            cache_path=cache_path,
            cache_key=cache_key,
            cache_source="miss",
        )

    try:
        ensure_pair_requirements_fn(
            pair=normalized_pair,
            jmdict_path=resolved_jmdict_path,
            translation_dict_path=resolved_translation_dict_path,
            require_frequency_db=True,
            set_source_db=resolved_set_source_db,
            check_seed_resources=True,
            check_rulegen_resources=True,
        )
    except FileNotFoundError as exc:
        missing = _missing_required_inputs(
            capability=capability,
            jmdict_path=resolved_jmdict_path,
            translation_dict_path=resolved_translation_dict_path,
            set_source_db=resolved_set_source_db,
        ) or ({"type": "resource_path", "path": str(exc)},)
        return _not_ready_payload(
            pair=normalized_pair,
            profile_id=normalized_profile_id,
            reason="missing_required_resources",
            missing_inputs=missing,
            resources=resources,
            cache_path=cache_path,
            cache_key=cache_key,
            cache_source="miss",
        )

    frequency_pack = resolve_pair_frequency_pack(
        paths,
        pair=normalized_pair,
        set_source_db=resolved_set_source_db,
    )
    resources = _resources_payload(
        paths,
        pair=normalized_pair,
        jmdict_path=resolved_jmdict_path,
        translation_dict_path=resolved_translation_dict_path,
        set_source_db=resolved_set_source_db,
        pos_overlay_path=pos_overlay.path if pos_overlay else None,
        frequency_pack=frequency_pack,
    )
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
    payload = {
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
        "resources": resources,
        "source_index_cache": {
            "source": "generated",
            "cache_path": str(cache_path),
            "cache_key": cache_key,
        },
    }
    _write_cached_source_index(cache_path, cache_key=cache_key, payload=payload)
    return payload


def _missing_required_inputs(
    *,
    capability: object,
    jmdict_path: Path | None,
    translation_dict_path: Path | None,
    set_source_db: Path | None,
) -> tuple[dict[str, object], ...]:
    missing: list[dict[str, object]] = []
    requires_jmdict = bool(
        getattr(capability, "requires_jmdict_for_seed", False)
        or getattr(capability, "requires_jmdict_for_rulegen", False)
    )
    if requires_jmdict:
        _append_missing_path(missing, resource_type="jmdict_path", path=jmdict_path)
    if bool(getattr(capability, "requires_translation_dictionary_for_rulegen", False)):
        _append_missing_path(
            missing,
            resource_type="translation_dict_path",
            path=translation_dict_path,
        )
        if missing and missing[-1]["type"] == "translation_dict_path":
            missing.append(
                {
                    "type": "translation_pack_path",
                    "path": missing[-1].get("path"),
                }
            )
    _append_missing_path(missing, resource_type="set_source_db", path=set_source_db)
    return tuple(missing)


def _append_missing_path(
    missing: list[dict[str, object]],
    *,
    resource_type: str,
    path: Path | None,
) -> None:
    if path is None:
        missing.append({"type": resource_type, "path": None})
    elif not Path(path).exists():
        missing.append({"type": resource_type, "path": str(path)})


def _resources_payload(
    paths: HelperPaths,
    *,
    pair: str,
    jmdict_path: Path | None,
    translation_dict_path: Path | None,
    set_source_db: Path | None,
    pos_overlay_path: Path | None,
    frequency_pack: object | None,
) -> dict[str, object]:
    return {
        "frequency_db": str(set_source_db) if set_source_db else None,
        "frequency_db_exists": bool(set_source_db and Path(set_source_db).exists()),
        "frequency_pack_id": getattr(frequency_pack, "pack_id", None),
        "jmdict_path": str(jmdict_path) if jmdict_path else None,
        "jmdict_exists": bool(jmdict_path and Path(jmdict_path).exists()),
        "translation_dict_path": str(translation_dict_path) if translation_dict_path else None,
        "translation_dict_exists": bool(
            translation_dict_path and Path(translation_dict_path).exists()
        ),
        "pos_overlay_path": str(pos_overlay_path) if pos_overlay_path else None,
        "pos_overlay_exists": bool(pos_overlay_path and Path(pos_overlay_path).exists()),
        "kanjidic2_path": _existing_optional_path(
            default_kanjidic2_path(pair, language_packs_dir=paths.language_packs_dir)
        ),
        "kanjivg_path": _existing_optional_path(
            default_kanjivg_path(pair, language_packs_dir=paths.language_packs_dir)
        ),
        "jmnedict_path": _existing_optional_path(
            default_jmnedict_path(pair, language_packs_dir=paths.language_packs_dir)
        ),
        "jlpt_vocabulary_path": _existing_optional_path(
            default_jlpt_vocabulary_path(pair, language_packs_dir=paths.language_packs_dir)
        ),
        "lesson_vocabulary_path": _existing_optional_path(
            default_japanese_lesson_vocabulary_path(
                pair,
                language_packs_dir=paths.language_packs_dir,
            )
        ),
    }


def _not_ready_payload(
    *,
    pair: str,
    profile_id: str,
    reason: str,
    missing_inputs: Sequence[Mapping[str, object]],
    resources: Mapping[str, object],
    cache_path: Path,
    cache_key: str,
    cache_source: str,
) -> dict[str, object]:
    return {
        "status": "not_ready",
        "reason": reason,
        "pair": pair,
        "profile_id": profile_id,
        "rules": [],
        "rule_count": 0,
        "target_count": 0,
        "source": "candidate_frontier_rulegen",
        "resources": dict(resources),
        "missing_inputs": [dict(item) for item in missing_inputs],
        "source_index_cache": {
            "source": cache_source,
            "cache_path": str(cache_path),
            "cache_key": cache_key,
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
                    "lexishift_origin": "srs",
                    "language_pair": pair,
                    "source_index": "candidate_frontier",
                    "word_package": _compact_word_package(
                        metadata,
                        fallback_surface=replacement,
                    ),
                },
            }
        )
        if len(compact) >= limit:
            break
    return compact


def _compact_word_package(
    metadata: Mapping[str, object],
    *,
    fallback_surface: str,
) -> dict[str, object]:
    word_package = metadata.get("word_package")
    package = word_package if isinstance(word_package, Mapping) else {}
    metadata_script_forms = metadata.get("script_forms")
    package_script_forms = package.get("script_forms")
    script_forms = (
        package_script_forms
        if isinstance(package_script_forms, Mapping)
        else metadata_script_forms
        if isinstance(metadata_script_forms, Mapping)
        else {}
    )
    surface = (
        str(package.get("surface") or "").strip()
        or str(script_forms.get("kanji") or script_forms.get("surface") or "").strip()
        or str(fallback_surface or "").strip()
    )
    reading = (
        str(package.get("reading") or "").strip() or str(script_forms.get("kana") or "").strip()
    )
    compact: dict[str, object] = {
        "surface": surface,
        "reading": reading,
    }
    compact_script_forms = {
        key: value
        for key, value in {
            "kanji": surface,
            "kana": reading,
            "romaji": str(script_forms.get("romaji") or "").strip(),
        }.items()
        if value
    }
    if compact_script_forms:
        compact["script_forms"] = compact_script_forms
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


def _source_index_cache_key(
    *,
    pair: str,
    profile_id: str,
    top_n: int,
    max_targets: int,
    max_rules: int,
    frequency_db: Path | None,
    jmdict_path: Path | None,
    translation_dict_path: Path | None,
    pos_overlay_path: Path | None,
) -> str:
    payload = {
        "schema_version": SOURCE_INDEX_CACHE_SCHEMA_VERSION,
        "pair": pair,
        "profile_id": profile_id,
        "top_n": top_n,
        "max_targets": max_targets,
        "max_rules": max_rules,
        "resources": {
            "frequency_db": _path_fingerprint(frequency_db),
            "jmdict_path": _path_fingerprint(jmdict_path),
            "translation_dict_path": _path_fingerprint(translation_dict_path),
            "pos_overlay_path": _path_fingerprint(pos_overlay_path),
        },
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _path_fingerprint(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    candidate = Path(path)
    try:
        stat = candidate.stat()
    except OSError:
        return {"path": str(candidate), "exists": False}
    return {
        "path": str(candidate),
        "exists": True,
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def _load_cached_source_index(
    cache_path: Path,
    *,
    cache_key: str | None,
    cache_source: str = "helper-cache",
    current_cache_key: str | None = None,
    missing_inputs: Sequence[Mapping[str, object]] = (),
) -> dict[str, object] | None:
    try:
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, Mapping):
        return None
    if raw.get("schema_version") != SOURCE_INDEX_CACHE_SCHEMA_VERSION:
        return None
    stored_cache_key = str(raw.get("cache_key") or "")
    if cache_key is not None and stored_cache_key != cache_key:
        return None
    payload = raw.get("payload")
    if not isinstance(payload, Mapping):
        return None
    rules = payload.get("rules")
    if not isinstance(rules, list):
        return None
    cached = dict(payload)
    metadata = dict(cached.get("source_index_cache") or {})
    metadata.update(
        {
            "source": cache_source,
            "cache_path": str(cache_path),
            "cache_key": stored_cache_key,
            "saved_at": str(raw.get("saved_at") or ""),
        }
    )
    if current_cache_key and current_cache_key != stored_cache_key:
        metadata["current_cache_key"] = current_cache_key
    if missing_inputs:
        missing = [dict(item) for item in missing_inputs]
        metadata["stale_reason"] = "missing_required_resources"
        metadata["missing_inputs"] = missing
        cached["missing_inputs"] = missing
        cached["resource_status"] = "missing_required_resources"
    cached["source_index_cache"] = metadata
    return cached


def _write_cached_source_index(
    cache_path: Path,
    *,
    cache_key: str,
    payload: Mapping[str, object],
) -> None:
    wrapper = {
        "schema_version": SOURCE_INDEX_CACHE_SCHEMA_VERSION,
        "cache_key": cache_key,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "payload": dict(payload),
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(wrapper, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _existing_optional_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path) if Path(path).exists() else None
