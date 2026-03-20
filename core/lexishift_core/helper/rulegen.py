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
from lexishift_core.replacement.core import VocabRule
from lexishift_core.helper.lp_capabilities import default_freedict_reverse_path
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.rulegen.adapters import RulegenAdapterRequest, run_rules_with_adapter
from lexishift_core.rulegen.generation import RuleScoringConfig
from lexishift_core.rulegen.ranking import ReverseCheckScoringConfig
from lexishift_core.srs import SrsItem, SrsSettings, SrsStore, save_srs_store
from lexishift_core.srs.admission_policy import resolve_default_pos_weights
from lexishift_core.srs.source import SOURCE_INITIAL_SET
from lexishift_core.srs.store_ops import build_item_id, upsert_item
from lexishift_core.scoring.weighting import GlossDecay

__all__ = [
    "RulegenConfig",
    "RulegenOutput",
    "SetInitializationConfig",
    "SetInitializationReport",
    "build_seed_candidates",
    "build_snapshot",
    "initialize_store_from_frequency_list",
    "initialize_store_from_frequency_list_with_report",
    "load_target_word_packages_from_store",
    "load_targets_from_store",
    "run_ja_en_rulegen",
    "run_rulegen_for_pair",
    "write_rulegen_outputs",
]


@dataclass(frozen=True)
class SetInitializationConfig:
    frequency_db: Path
    jmdict_path: Optional[Path] = None
    top_n: int = 2000
    initial_active_count: int = 40
    language_pair: str = "en-ja"
    stopwords_path: Optional[Path] = None
    require_jmdict: bool = True


@dataclass(frozen=True)
class SetInitializationReport:
    selected_count: int
    selected_unique_count: int
    admitted_count: int
    inserted_count: int
    updated_count: int
    selected_preview: Sequence[str]
    initial_active_preview: Sequence[str]
    admission_weight_profile: Mapping[str, float]
    initial_active_weight_preview: Sequence[Mapping[str, object]]


@dataclass(frozen=True)
class RulegenConfig:
    language_pair: str = "en-ja"
    confidence_threshold: float = 0.0
    max_definitions_per_target: Optional[int] = 3
    max_rules_per_target: Optional[int] = None
    semantic_demotion_scale: float = 1.0
    scoring: RuleScoringConfig = field(default_factory=RuleScoringConfig)
    reverse_check: ReverseCheckScoringConfig = field(default_factory=ReverseCheckScoringConfig)
    max_snapshot_targets: int = 50
    max_snapshot_sources: int = 6
    include_variants: bool = True
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = GlossDecay()


def _load_seed_module():
    return __import__(
        "lexishift_core.srs.seed",
        fromlist=["SeedSelectionConfig", "build_seed_candidates"],
    )


def build_seed_candidates(*args, **kwargs):
    seed_module = _load_seed_module()
    return seed_module.build_seed_candidates(*args, **kwargs)


def load_targets_from_store(store: SrsStore, *, pair: str) -> list[str]:
    return [item.lemma for item in store.items if item.language_pair == pair and item.lemma]


def load_target_word_packages_from_store(
    store: SrsStore,
    *,
    pair: str,
    targets: Optional[Sequence[str]] = None,
) -> dict[str, Mapping[str, object]]:
    target_set = {str(target).strip() for target in targets or [] if str(target).strip()}
    packages: dict[str, Mapping[str, object]] = {}
    for item in store.items:
        if item.language_pair != pair or not item.lemma:
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
    )
    selected_words = build_seed_candidates(
        frequency_db=config.frequency_db,
        config=selection_config,
    )
    seen_ids: set[str] = set()
    unique_selected_words = []
    for selected in selected_words:
        item_id = build_item_id(selected.language_pair, selected.lemma)
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        unique_selected_words.append(selected)

    initial_active_count = max(0, int(config.initial_active_count))
    admitted_words = unique_selected_words[:initial_active_count]
    existing_by_id = {item.item_id: item for item in store.items}
    inserted_count = 0
    updated_count = 0
    updated = store
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
                word_package=selected_word_package,
            )
            existing_by_id[item_id] = item
        updated = upsert_item(updated, item)
    selected_preview = tuple(selected.lemma for selected in unique_selected_words[:10])
    initial_active_preview = tuple(
        selected.lemma for selected in admitted_words[:initial_active_count]
    )
    report = SetInitializationReport(
        selected_count=len(selected_words),
        selected_unique_count=len(unique_selected_words),
        admitted_count=len(admitted_words),
        inserted_count=inserted_count,
        updated_count=updated_count,
        selected_preview=selected_preview,
        initial_active_preview=initial_active_preview,
        admission_weight_profile=resolved_pos_weights.to_dict(),
        initial_active_weight_preview=tuple(
            _build_weight_preview_entry(selected) for selected in admitted_words[:20]
        ),
    )
    return updated, report


def run_ja_en_rulegen(
    *,
    targets: Iterable[str],
    word_packages_by_target: Optional[Mapping[str, Mapping[str, object]]] = None,
    jmdict_path: Path,
    config: RulegenConfig,
) -> Sequence[VocabRule]:
    return run_rules_with_adapter(
        RulegenAdapterRequest(
            pair="en-ja",
            targets=tuple(str(target).strip() for target in targets if str(target).strip()),
            language_pair=config.language_pair,
            confidence_threshold=config.confidence_threshold,
            max_definitions_per_target=config.max_definitions_per_target,
            max_rules_per_target=config.max_rules_per_target,
            semantic_demotion_scale=config.semantic_demotion_scale,
            include_variants=config.include_variants,
            allow_multiword_glosses=config.allow_multiword_glosses,
            scoring=config.scoring,
            gloss_decay=config.gloss_decay,
            jmdict_path=jmdict_path,
            word_packages_by_target=word_packages_by_target,
        )
    )


def _safe_optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, (str, bytes, bytearray)):
        try:
            return float(value)
        except ValueError:
            return None
    return None


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


def _build_weight_preview_entry(selected: object) -> Mapping[str, object]:
    base_weight = _safe_optional_float(getattr(selected, "base_weight", None))
    pos_weight = _safe_optional_float(getattr(selected, "pos_weight", None))
    admission_weight = _safe_optional_float(getattr(selected, "admission_weight", None))
    return {
        "lemma": str(getattr(selected, "lemma", "")).strip(),
        "pos": getattr(selected, "pos", None),
        "pos_bucket": str(getattr(selected, "pos_bucket", "")),
        "base_weight": round(base_weight, 6) if base_weight is not None else None,
        "pos_weight": round(pos_weight, 6) if pos_weight is not None else None,
        "admission_weight": round(admission_weight, 6) if admission_weight is not None else None,
    }


def run_rulegen_for_pair(
    *,
    paths: HelperPaths,
    pair: str,
    profile_id: str = "default",
    store: SrsStore,
    settings: Optional[SrsSettings],
    jmdict_path: Optional[Path] = None,
    freedict_de_en_path: Optional[Path] = None,
    set_init_config: Optional[SetInitializationConfig] = None,
    rulegen_config: Optional[RulegenConfig] = None,
    targets_override: Optional[Sequence[str]] = None,
    initialize_if_empty: bool = True,
    persist_store: bool = True,
) -> tuple[SrsStore, RulegenOutput]:
    rulegen_config = rulegen_config or RulegenConfig(language_pair=pair)
    updated_store = store
    if targets_override is not None:
        targets = [str(target).strip() for target in targets_override if str(target).strip()]
    else:
        targets = load_targets_from_store(updated_store, pair=pair)
    if targets_override is None and not targets and initialize_if_empty and set_init_config:
        updated_store = initialize_store_from_frequency_list(
            store,
            config=set_init_config,
        )
        targets = load_targets_from_store(updated_store, pair=pair)
    target_word_packages = load_target_word_packages_from_store(
        updated_store,
        pair=pair,
        targets=targets,
    )
    resolved_reverse_freedict_path = default_freedict_reverse_path(
        pair,
        language_packs_dir=paths.language_packs_dir,
    )
    if resolved_reverse_freedict_path is not None and not resolved_reverse_freedict_path.exists():
        resolved_reverse_freedict_path = None
    rules = run_rules_with_adapter(
        RulegenAdapterRequest(
            pair=pair,
            targets=targets,
            language_pair=rulegen_config.language_pair,
            confidence_threshold=rulegen_config.confidence_threshold,
            max_definitions_per_target=rulegen_config.max_definitions_per_target,
            max_rules_per_target=rulegen_config.max_rules_per_target,
            semantic_demotion_scale=rulegen_config.semantic_demotion_scale,
            include_variants=rulegen_config.include_variants,
            allow_multiword_glosses=rulegen_config.allow_multiword_glosses,
            scoring=rulegen_config.scoring,
            reverse_check=rulegen_config.reverse_check,
            gloss_decay=rulegen_config.gloss_decay,
            jmdict_path=jmdict_path,
            freedict_de_en_path=freedict_de_en_path,
            freedict_reverse_path=resolved_reverse_freedict_path,
            word_packages_by_target=target_word_packages or None,
        )
    )
    snapshot = build_snapshot(
        rules=rules,
        pair=pair,
        max_targets=rulegen_config.max_snapshot_targets,
        max_sources=rulegen_config.max_snapshot_sources,
    )
    if persist_store and updated_store is not store:
        save_srs_store(updated_store, paths.srs_store_path_for(profile_id))
    return updated_store, RulegenOutput(
        rules=rules,
        snapshot=snapshot,
        target_count=len(targets),
    )
