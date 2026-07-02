from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.helper.rulegen_outputs import (
    RulegenOutput,
    build_snapshot,
    write_rulegen_outputs,
)
from lexishift_core.lexicon.word_package import (
    normalize_word_package,
    resolve_language_tag_from_pair,
)
from lexishift_core.helper.lp_capabilities import (
    default_frequency_db_path,
    default_reverse_translation_dictionary_path,
    resolve_pair_capability,
)
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.rulegen.adapters import (
    run_results_with_adapter,
    run_rules_with_adapter,
)
from lexishift_core.rulegen.generation import RuleScoringConfig
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig
from lexishift_core.srs import SrsItem, SrsSettings, SrsStore, save_srs_store
from lexishift_core.srs.admission_policy import resolve_default_pos_weights
from lexishift_core.srs.profile_bootstrap import (
    score_seed_words_for_profile,
)
from lexishift_core.srs.selector import (
    SELECTION_POLICY_TOP_N,
    SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT,
    select_candidates,
    select_scored_candidates,
)
from lexishift_core.srs.set_strategy import (
    STRATEGY_FREQUENCY_BOOTSTRAP,
    STRATEGY_PROFILE_BOOTSTRAP,
)
from lexishift_core.srs.source import SOURCE_INITIAL_SET
from lexishift_core.srs.store_ops import build_item_id, upsert_item
from lexishift_core.srs.time import format_ts, now_utc
from lexishift_core.scoring.weighting import GlossDecay
from lexishift_core.helper.rulegen_bootstrap_selection import (
    SeedWordLike as _SeedWordLike,
    as_seed_word_like as _as_seed_word_like,
    build_frequency_bootstrap_selector_config as _build_frequency_bootstrap_selector_config,
    build_profile_bootstrap_selector_config as _build_profile_bootstrap_selector_config,
    build_weight_preview_entry as _build_weight_preview_entry,
    coerce_seed_words as _coerce_seed_words,
    dedupe_profile_bootstrap_entries as _dedupe_profile_bootstrap_entries,
    dedupe_seed_words as _dedupe_seed_words,
    safe_optional_float as _safe_optional_float,
    seed_to_bootstrap_selector_candidates as _seed_to_bootstrap_selector_candidates,
)
from lexishift_core.helper.rulegen_srs_serving import (
    annotate_rules_with_srs_serving_metadata,
    item_is_active_for_pair as _item_is_active_for_pair,
    normalize_item_id_filter as _normalize_item_id_filter,
    normalize_item_id_sequence as _normalize_item_id_sequence,
)
from lexishift_core.helper.rulegen_adapter_request import (
    build_rulegen_adapter_request as _build_rulegen_adapter_request,
)

PROFILE_BOOTSTRAP_DIAGNOSTIC_PREVIEW_LIMIT = 200

__all__ = [
    "RulegenConfig",
    "RulegenOutput",
    "SetInitializationConfig",
    "SetInitializationReport",
    "build_seed_candidates",
    "build_snapshot",
    "annotate_rules_with_srs_serving_metadata",
    "initialize_store_from_frequency_list",
    "initialize_store_from_frequency_list_with_report",
    "load_target_word_packages_from_store",
    "load_targets_from_store",
    "run_en_ja_rulegen",
    "run_rulegen_for_pair",
    "write_rulegen_outputs",
]


@dataclass(frozen=True)
class SetInitializationConfig:
    frequency_db: Path
    jmdict_path: Optional[Path] = None
    source_label: Optional[str] = None
    top_n: Optional[int] = None
    initial_active_count: int = 40
    language_pair: str = "en-ja"
    stopwords_path: Optional[Path] = None
    require_jmdict: bool = True
    strategy: str = STRATEGY_FREQUENCY_BOOTSTRAP
    profile_context: Optional[Mapping[str, object]] = None
    selection_seed: Optional[int] = None
    selection_policy_override: Optional[str] = None
    pos_overlay_path: Optional[Path] = None
    seed_cache_dir: Optional[Path] = None
    profile_topic_overlay: Optional[Mapping[str, object]] = None
    profile_topic_overlay_diagnostics: Mapping[str, object] = field(default_factory=dict)
    blocked_lemmas: tuple[str, ...] = ()


@dataclass(frozen=True)
class SetInitializationReport:
    selected_count: int
    selected_unique_count: int
    admitted_count: int
    inserted_count: int
    updated_count: int
    selected_preview: Sequence[str]
    selected_unique_lemmas: Sequence[str]
    initial_active_preview: Sequence[str]
    admission_weight_profile: Mapping[str, float]
    initial_active_weight_preview: Sequence[Mapping[str, object]]
    selection_strategy: str = STRATEGY_FREQUENCY_BOOTSTRAP
    selection_policy: str = SELECTION_POLICY_TOP_N
    selection_seed: Optional[int] = None
    selector_version: Optional[str] = None
    profile_bootstrap_diagnostics: Mapping[str, object] = field(default_factory=dict)
    selected_unique_identity_keys: Sequence[str] = ()
    initial_active_identity_keys: Sequence[str] = ()
    blocked_lemmas: tuple[str, ...] = ()


@dataclass(frozen=True)
class RulegenConfig:
    language_pair: str = "en-ja"
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = 3
    max_rules_per_target: Optional[int] = None
    semantic_demotion_scale: float = 1.0
    enable_source_frequency_prior: bool = False
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)
    max_snapshot_targets: int = 50
    max_snapshot_sources: int = 6
    include_variants: bool = True
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = GlossDecay()
    enable_exact_gloss_demotions: bool = False


def _load_seed_module():
    return __import__(
        "lexishift_core.srs.seed",
        fromlist=["SeedSelectionConfig", "build_seed_candidates"],
    )


def _load_topic_overlay_module():
    return __import__(
        "lexishift_core.srs.topic_overlay",
        fromlist=["apply_profile_topic_overlay_to_seeds"],
    )


def _load_semantic_publication_module():
    return __import__(
        "lexishift_core.rulegen.semantic_publication",
        fromlist=["build_semantic_inventory_from_results"],
    )


def build_seed_candidates(*args, **kwargs):
    seed_module = _load_seed_module()
    return seed_module.build_seed_candidates(*args, **kwargs)


def load_targets_from_store(
    store: SrsStore,
    *,
    pair: str,
    active_item_ids: Optional[Sequence[str]] = None,
) -> list[str]:
    active_item_id_list = _normalize_item_id_sequence(active_item_ids)
    if active_item_id_list is None:
        return [item.lemma for item in store.items if _item_is_active_for_pair(item, pair)]

    items_by_id = {
        item.item_id: item for item in store.items if _item_is_active_for_pair(item, pair)
    }
    targets: list[str] = []
    seen_lemmas: set[str] = set()
    for item_id in active_item_id_list:
        item = items_by_id.get(item_id)
        if item is None or item.lemma in seen_lemmas:
            continue
        seen_lemmas.add(item.lemma)
        targets.append(item.lemma)
    return targets


def load_target_word_packages_from_store(
    store: SrsStore,
    *,
    pair: str,
    targets: Optional[Sequence[str]] = None,
    active_item_ids: Optional[Sequence[str]] = None,
) -> dict[str, Mapping[str, object]]:
    target_set = {str(target).strip() for target in targets or [] if str(target).strip()}
    active_item_id_set = _normalize_item_id_filter(active_item_ids)
    packages: dict[str, Mapping[str, object]] = {}
    for item in store.items:
        if not _item_is_active_for_pair(item, pair):
            continue
        if active_item_id_set is not None and item.item_id not in active_item_id_set:
            continue
        if target_set and item.lemma not in target_set:
            continue
        normalized = normalize_word_package(
            item.word_package,
            fallback_surface=item.lemma,
            fallback_language_tag=resolve_language_tag_from_pair(item.language_pair),
            fallback_provider=item.source_type or "srs",
        )
        if normalized is None:
            continue
        packages[item.lemma] = normalized
    return packages


def initialize_store_from_frequency_list(
    store: SrsStore,
    *,
    config: SetInitializationConfig,
) -> SrsStore:
    updated_store, _report = initialize_store_from_frequency_list_with_report(store, config=config)
    return updated_store


def initialize_store_from_frequency_list_with_report(
    store: SrsStore,
    *,
    config: SetInitializationConfig,
) -> tuple[SrsStore, SetInitializationReport]:
    resolved_pos_weights = resolve_default_pos_weights(language_pair=config.language_pair)
    seed_module = _load_seed_module()
    selection_config = seed_module.SeedSelectionConfig(
        language_pair=config.language_pair,
        top_n=config.top_n,
        jmdict_path=config.jmdict_path,
        stopwords_path=config.stopwords_path,
        require_jmdict=config.require_jmdict,
        admission_pos_weights=resolved_pos_weights,
        source_label=config.source_label,
        pos_overlay_path=config.pos_overlay_path,
        cache_dir=config.seed_cache_dir,
    )
    selected_words = _coerce_seed_words(
        build_seed_candidates(
            frequency_db=config.frequency_db,
            config=selection_config,
        )
    )
    topic_overlay_module = _load_topic_overlay_module()
    selected_words, profile_topic_overlay_diagnostics = (
        topic_overlay_module.apply_profile_topic_overlay_to_seeds(
            selected_words,
            overlay_payload=config.profile_topic_overlay,
            profile_context=config.profile_context,
            pair=config.language_pair,
            diagnostics=config.profile_topic_overlay_diagnostics,
        )
    )
    selected_words = _coerce_seed_words(selected_words)
    initial_active_count = max(0, int(config.initial_active_count))
    blocked_lemmas = _normalize_blocked_lemmas(config.blocked_lemmas)
    selection_seed = _normalize_optional_int(config.selection_seed)
    selection_policy = _resolve_selection_policy_override(config.selection_policy_override)
    selection_strategy = STRATEGY_FREQUENCY_BOOTSTRAP
    selector_version = None
    profile_bootstrap_diagnostics: Mapping[str, object] = {}
    unique_selected_words: list[_SeedWordLike]
    admitted_words: list[_SeedWordLike]

    if config.strategy == STRATEGY_PROFILE_BOOTSTRAP:
        scored_entries, profile_bootstrap_diagnostics = score_seed_words_for_profile(
            selected_words,
            profile_context=config.profile_context,
            preview_limit=min(len(selected_words), PROFILE_BOOTSTRAP_DIAGNOSTIC_PREVIEW_LIMIT),
        )
        selection_strategy = STRATEGY_PROFILE_BOOTSTRAP
        selector_version = str(profile_bootstrap_diagnostics.get("selector_version") or "").strip()
        selection_policy = _resolve_selection_policy_override(
            (
                config.selection_policy_override
                if config.selection_policy_override is not None
                else profile_bootstrap_diagnostics.get("selection_policy")
            )
        )
        profile_bootstrap_diagnostics = {
            **dict(profile_bootstrap_diagnostics),
            "selection_policy": selection_policy,
        }
        if profile_topic_overlay_diagnostics:
            profile_bootstrap_diagnostics["profile_topic_overlay"] = dict(
                profile_topic_overlay_diagnostics
            )
        unique_scored_entries = [
            entry
            for entry in _dedupe_profile_bootstrap_entries(scored_entries)
            if not _seed_lemma_is_blocked(entry.seed, blocked_lemmas)
        ]
        selected_candidates = select_scored_candidates(
            [entry.scored_candidate for entry in unique_scored_entries],
            config=_build_profile_bootstrap_selector_config(
                selection_policy=selection_policy,
                selection_count=initial_active_count,
            ),
            selection_count=initial_active_count,
            seed=selection_seed,
        )
        unique_entry_seeds = [
            (entry, seed)
            for entry in unique_scored_entries
            for seed in (_as_seed_word_like(entry.seed),)
            if seed is not None
        ]
        unique_selected_words = [seed for _entry, seed in unique_entry_seeds]
        unique_entry_by_lemma = {
            str(seed.lemma).strip(): seed
            for _entry, seed in unique_entry_seeds
            if str(seed.lemma).strip()
        }
        admitted_words = [
            unique_entry_by_lemma[entry.candidate.lemma]
            for entry in selected_candidates
            if entry.candidate.lemma in unique_entry_by_lemma
        ]
    else:
        unique_selected_words = [
            seed for seed in _dedupe_seed_words(selected_words) if seed.lemma not in blocked_lemmas
        ]
        selected_candidates = select_candidates(
            _seed_to_bootstrap_selector_candidates(unique_selected_words),
            config=_build_frequency_bootstrap_selector_config(
                selection_policy=selection_policy,
                selection_count=initial_active_count,
            ),
            selection_count=initial_active_count,
            seed=selection_seed,
        )
        seed_by_lemma = {
            str(seed.lemma).strip(): seed
            for seed in unique_selected_words
            if str(seed.lemma).strip()
        }
        admitted_words = [
            seed_by_lemma[entry.candidate.lemma]
            for entry in selected_candidates
            if entry.candidate.lemma in seed_by_lemma
        ]

    existing_by_id = {item.item_id: item for item in store.items}
    inserted_count = 0
    updated_count = 0
    updated = store
    admitted_at = format_ts(now_utc())
    for selected in admitted_words:
        item_id = build_item_id(selected.language_pair, selected.lemma)
        selected_word_package = _resolve_selected_word_package(selected)
        existing_item = existing_by_id.get(item_id)
        if existing_item is not None:
            updated_count += 1
            confidence = _safe_optional_float(getattr(selected, "admission_weight", None))
            item = existing_item
            if item.confidence is None and confidence is not None:
                item = replace(item, confidence=confidence)
            if item.word_package is None and selected_word_package is not None:
                item = replace(item, word_package=selected_word_package)
        else:
            inserted_count += 1
            confidence = _safe_optional_float(getattr(selected, "admission_weight", None))
            item = SrsItem(
                item_id=item_id,
                lemma=selected.lemma,
                language_pair=selected.language_pair,
                source_type=SOURCE_INITIAL_SET,
                confidence=confidence,
                admitted_at=admitted_at,
                word_package=selected_word_package,
            )
            existing_by_id[item_id] = item
        updated = upsert_item(updated, item)
    selected_preview = tuple(selected.lemma for selected in unique_selected_words[:10])
    initial_active_preview = tuple(
        selected.lemma for selected in admitted_words[:initial_active_count]
    )
    selected_unique_identity_keys = tuple(
        identity_key
        for selected in unique_selected_words
        for identity_key in (_candidate_identity_key_from_seed(selected),)
        if identity_key
    )
    initial_active_identity_keys = tuple(
        identity_key
        for selected in admitted_words[:initial_active_count]
        for identity_key in (_candidate_identity_key_from_seed(selected),)
        if identity_key
    )
    report = SetInitializationReport(
        selected_count=len(selected_words),
        selected_unique_count=len(unique_selected_words),
        admitted_count=len(admitted_words),
        inserted_count=inserted_count,
        updated_count=updated_count,
        selected_preview=selected_preview,
        selected_unique_lemmas=tuple(
            str(selected.lemma).strip()
            for selected in unique_selected_words
            if str(selected.lemma).strip()
        ),
        initial_active_preview=initial_active_preview,
        admission_weight_profile=resolved_pos_weights.to_dict(),
        initial_active_weight_preview=tuple(
            _build_weight_preview_entry(selected) for selected in admitted_words[:20]
        ),
        selection_strategy=selection_strategy,
        selection_policy=selection_policy,
        selection_seed=selection_seed,
        selector_version=selector_version or None,
        profile_bootstrap_diagnostics=dict(profile_bootstrap_diagnostics),
        selected_unique_identity_keys=selected_unique_identity_keys,
        initial_active_identity_keys=initial_active_identity_keys,
        blocked_lemmas=tuple(sorted(blocked_lemmas)),
    )
    return updated, report


def run_en_ja_rulegen(
    *,
    targets: Iterable[str],
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
    jmdict_path: Path,
    config: RulegenConfig,
) -> Sequence[object]:
    normalized_targets = tuple(str(target).strip() for target in targets if str(target).strip())
    return run_rules_with_adapter(
        _build_rulegen_adapter_request(
            pair="en-ja",
            targets=normalized_targets,
            rulegen_config=config,
            jmdict_path=jmdict_path,
            translation_dict_path=None,
            resolved_reverse_translation_dict_path=None,
            word_packages_by_target=word_packages_by_target,
        )
    )


def _resolve_selected_word_package(selected: object) -> Optional[Mapping[str, object]]:
    language_pair = str(getattr(selected, "language_pair", "") or "").strip()
    lemma = str(getattr(selected, "lemma", "") or "").strip()
    source = SOURCE_INITIAL_SET
    return normalize_word_package(
        getattr(selected, "word_package", None),
        fallback_surface=lemma,
        fallback_language_tag=resolve_language_tag_from_pair(language_pair),
        fallback_provider=source,
    )


def _normalize_blocked_lemmas(values: Iterable[str]) -> frozenset[str]:
    return frozenset(str(value or "").strip() for value in values if str(value or "").strip())


def _seed_lemma_is_blocked(seed: object, blocked_lemmas: frozenset[str]) -> bool:
    return str(getattr(seed, "lemma", "") or "").strip() in blocked_lemmas


def _candidate_identity_key_from_seed(seed: object) -> str:
    identity_module = __import__(
        "lexishift_core.srs.candidate_identity",
        fromlist=["candidate_identity_key_from_seed"],
    )
    return identity_module.candidate_identity_key_from_seed(seed)


def _resolve_selection_policy_override(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT, "reserved_topic_lane"}:
        return normalized
    return SELECTION_POLICY_TOP_N


def _normalize_optional_int(value: object) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def run_rulegen_for_pair(
    *,
    paths: HelperPaths,
    pair: str,
    profile_id: str = "default",
    store: SrsStore,
    settings: Optional[SrsSettings],
    jmdict_path: Optional[Path] = None,
    translation_dict_path: Optional[Path] = None,
    set_init_config: Optional[SetInitializationConfig] = None,
    rulegen_config: Optional[RulegenConfig] = None,
    targets_override: Optional[Sequence[str]] = None,
    active_item_ids: Optional[Sequence[str]] = None,
    semantic_context_targets: Optional[Sequence[str]] = None,
    initialize_if_empty: bool = True,
    persist_store: bool = True,
) -> tuple[SrsStore, RulegenOutput]:
    rulegen_config = rulegen_config or RulegenConfig(language_pair=pair)
    updated_store = store
    if targets_override is not None:
        targets = [str(target).strip() for target in targets_override if str(target).strip()]
    else:
        targets = load_targets_from_store(
            updated_store,
            pair=pair,
            active_item_ids=active_item_ids,
        )
    if targets_override is None and not targets and initialize_if_empty and set_init_config:
        updated_store = initialize_store_from_frequency_list(
            store,
            config=set_init_config,
        )
        targets = load_targets_from_store(
            updated_store,
            pair=pair,
            active_item_ids=active_item_ids,
        )
    target_word_packages = load_target_word_packages_from_store(
        updated_store,
        pair=pair,
        targets=targets,
        active_item_ids=active_item_ids,
    )
    resolved_reverse_translation_dict_path = default_reverse_translation_dictionary_path(
        pair,
        language_packs_dir=paths.language_packs_dir,
    )
    if (
        resolved_reverse_translation_dict_path is not None
        and not resolved_reverse_translation_dict_path.exists()
    ):
        resolved_reverse_translation_dict_path = None
    source_frequency_db_path = _resolve_source_frequency_db_path(
        paths,
        pair=pair,
        enabled=rulegen_config.enable_source_frequency_prior,
    )
    results = run_results_with_adapter(
        _build_rulegen_adapter_request(
            pair=pair,
            targets=targets,
            rulegen_config=rulegen_config,
            jmdict_path=jmdict_path,
            translation_dict_path=translation_dict_path,
            resolved_reverse_translation_dict_path=resolved_reverse_translation_dict_path,
            source_frequency_db_path=source_frequency_db_path,
            word_packages_by_target=target_word_packages or None,
        )
    )
    rules = list(
        annotate_rules_with_srs_serving_metadata(
            [result.rule for result in results],
            store=updated_store,
            pair=pair,
            active_item_ids=active_item_ids,
        )
    )
    snapshot = build_snapshot(
        rules=rules,
        pair=pair,
        max_targets=rulegen_config.max_snapshot_targets,
        max_sources=rulegen_config.max_snapshot_sources,
    )
    semantic_publication_module = _load_semantic_publication_module()
    semantic_inventory = semantic_publication_module.build_semantic_inventory_from_results(
        results=results,
        pair=pair,
        profile_id=profile_id,
        generated_at=str(snapshot.get("generated_at") or ""),
    )
    normalized_semantic_context_targets = tuple(
        dict.fromkeys(
            str(target).strip()
            for target in (semantic_context_targets or ())
            if str(target).strip()
        )
    )
    normalized_targets = tuple(str(target).strip() for target in targets if str(target).strip())
    if (
        normalized_semantic_context_targets
        and normalized_semantic_context_targets != normalized_targets
    ):
        context_results = run_results_with_adapter(
            _build_rulegen_adapter_request(
                pair=pair,
                targets=normalized_semantic_context_targets,
                rulegen_config=rulegen_config,
                jmdict_path=jmdict_path,
                translation_dict_path=translation_dict_path,
                resolved_reverse_translation_dict_path=resolved_reverse_translation_dict_path,
                source_frequency_db_path=source_frequency_db_path,
            )
        )
        context_inventory = semantic_publication_module.build_semantic_inventory_from_results(
            results=context_results,
            pair=pair,
            profile_id=profile_id,
            generated_at=str(snapshot.get("generated_at") or ""),
        )
        rules, semantic_inventory = (
            semantic_publication_module.merge_semantic_publication_with_context_inventory(
                rules=rules,
                primary_inventory=semantic_inventory,
                context_inventory=context_inventory,
            )
        )
    reference_inventory = _load_installed_semantic_reference_inventory(paths=paths, pair=pair)
    if reference_inventory is not None:
        rules, semantic_inventory = (
            semantic_publication_module.merge_semantic_publication_with_reference_inventory(
                rules=rules,
                primary_inventory=semantic_inventory,
                reference_inventory=reference_inventory,
            )
        )
    if persist_store and updated_store is not store:
        save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
    return updated_store, RulegenOutput(
        rules=rules,
        snapshot=snapshot,
        target_count=len(targets),
        semantic_inventory=semantic_inventory,
    )


def _resolve_source_frequency_db_path(
    paths: HelperPaths,
    *,
    pair: str,
    enabled: bool,
) -> Optional[Path]:
    if not enabled:
        return None
    normalized_pair = str(pair or "").strip().lower()
    if "-" not in normalized_pair:
        return None
    source_lang = normalized_pair.split("-", 1)[0].strip()
    if not source_lang:
        return None
    candidate = default_frequency_db_path(
        f"{source_lang}-{source_lang}",
        frequency_packs_dir=paths.frequency_packs_dir,
    )
    if candidate is None or not candidate.exists() or not candidate.is_file():
        return None
    return candidate


def _load_installed_semantic_reference_inventory(
    *,
    paths: HelperPaths,
    pair: str,
) -> Mapping[str, object] | None:
    import json

    pack_id = resolve_pair_capability(pair).default_semantic_pack_id
    if not pack_id:
        return None
    semantic_pack_module = __import__(
        "lexishift_core.helper.use_cases.semantic_pack_install",
        fromlist=["resolve_installed_semantic_pack_inventory_path"],
    )
    inventory_path = semantic_pack_module.resolve_installed_semantic_pack_inventory_path(
        paths=paths,
        pair=pair,
        pack_id=pack_id,
    )
    if inventory_path is None:
        return None
    try:
        payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, Mapping) else None
