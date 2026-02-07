from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import json
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.core import VocabRule
from lexishift_core.helper_paths import HelperPaths
from lexishift_core.rule_generation_ja_en import JaEnRulegenConfig, generate_ja_en_results
from lexishift_core.srs import SrsItem, SrsSettings, SrsStore, save_srs_store
from lexishift_core.srs_admission_policy import resolve_default_pos_weights
from lexishift_core.srs_source import SOURCE_INITIAL_SET
from lexishift_core.srs_seed import SeedSelectionConfig, build_seed_candidates
from lexishift_core.srs_store_ops import build_item_id, upsert_item
from lexishift_core.storage import VocabDataset, save_vocab_dataset
from lexishift_core.weighting import GlossDecay


@dataclass(frozen=True)
class SetInitializationConfig:
    frequency_db: Path
    jmdict_path: Path
    top_n: int = 2000
    initial_active_count: int = 40
    language_pair: str = "en-ja"
    stopwords_path: Optional[Path] = None


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
    max_snapshot_targets: int = 50
    max_snapshot_sources: int = 6
    include_variants: bool = True
    allow_multiword_glosses: bool = False
    gloss_decay: GlossDecay = GlossDecay()


@dataclass(frozen=True)
class RulegenOutput:
    rules: Sequence[VocabRule]
    snapshot: Mapping[str, object]
    target_count: int


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def load_targets_from_store(store: SrsStore, *, pair: str) -> list[str]:
    return [item.lemma for item in store.items if item.language_pair == pair and item.lemma]


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
    selection_config = SeedSelectionConfig(
        language_pair=config.language_pair,
        top_n=config.top_n,
        jmdict_path=config.jmdict_path,
        stopwords_path=config.stopwords_path,
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
        existing_item = existing_by_id.get(item_id)
        if existing_item is not None:
            updated_count += 1
            confidence = _safe_optional_float(getattr(selected, "admission_weight", None))
            item = existing_item
            if existing_item.confidence is None and confidence is not None:
                item = replace(existing_item, confidence=confidence)
        else:
            inserted_count += 1
            confidence = _safe_optional_float(getattr(selected, "admission_weight", None))
            item = SrsItem(
                item_id=item_id,
                lemma=selected.lemma,
                language_pair=selected.language_pair,
                source_type=SOURCE_INITIAL_SET,
                confidence=confidence,
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


def build_snapshot(
    *,
    rules: Sequence[VocabRule],
    pair: str,
    generated_at: str,
    max_targets: int,
    max_sources: int,
) -> Mapping[str, object]:
    mapping: dict[str, list[str]] = {}
    for rule in rules:
        lemma = str(rule.replacement or "").strip()
        source = str(rule.source_phrase or "").strip()
        if not lemma or not source:
            continue
        mapping.setdefault(lemma, [])
        if source not in mapping[lemma]:
            mapping[lemma].append(source)
    targets = []
    for lemma in sorted(mapping.keys())[:max_targets]:
        sources = mapping[lemma][:max_sources]
        targets.append({"lemma": lemma, "sources": sources})
    source_total = sum(len(sources) for sources in mapping.values())
    snapshot = {
        "version": 1,
        "generated_at": generated_at,
        "pair": pair,
        "targets": targets,
        "stats": {
            "target_count": len(mapping),
            "rule_count": len(rules),
            "source_count": source_total,
        },
    }
    return snapshot


def run_ja_en_rulegen(
    *,
    targets: Iterable[str],
    jmdict_path: Path,
    config: RulegenConfig,
) -> Sequence[VocabRule]:
    rulegen_config = JaEnRulegenConfig(
        jmdict_path=jmdict_path,
        language_pair=config.language_pair,
        confidence_threshold=config.confidence_threshold,
        include_variants=config.include_variants,
        allow_multiword_glosses=config.allow_multiword_glosses,
        gloss_decay=config.gloss_decay,
    )
    results = generate_ja_en_results(targets, config=rulegen_config)
    return [result.rule for result in results]


def _safe_optional_float(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def write_rulegen_outputs(
    *,
    paths: HelperPaths,
    pair: str,
    rules: Sequence[VocabRule],
    snapshot: Mapping[str, object],
) -> None:
    dataset = VocabDataset(rules=tuple(rules))
    save_vocab_dataset(dataset, paths.ruleset_path(pair))
    Path(paths.snapshot_path(pair)).write_text(
        json.dumps(snapshot, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def run_rulegen_for_pair(
    *,
    paths: HelperPaths,
    pair: str,
    store: SrsStore,
    settings: Optional[SrsSettings],
    jmdict_path: Path,
    set_init_config: Optional[SetInitializationConfig] = None,
    rulegen_config: Optional[RulegenConfig] = None,
    targets_override: Optional[Sequence[str]] = None,
    initialize_if_empty: bool = True,
    persist_store: bool = True,
) -> tuple[SrsStore, RulegenOutput]:
    rulegen_config = rulegen_config or RulegenConfig(language_pair=pair)
    if targets_override is not None:
        targets = [str(target).strip() for target in targets_override if str(target).strip()]
    else:
        targets = load_targets_from_store(store, pair=pair)
    updated_store = store
    if targets_override is None and not targets and initialize_if_empty and set_init_config:
        updated_store = initialize_store_from_frequency_list(
            store,
            config=set_init_config,
        )
        targets = load_targets_from_store(updated_store, pair=pair)
    rules: Sequence[VocabRule] = []
    if pair == "en-ja":
        rules = run_ja_en_rulegen(
            targets=targets,
            jmdict_path=jmdict_path,
            config=rulegen_config,
        )
    else:
        rules = []
    generated_at = _now_iso()
    snapshot = build_snapshot(
        rules=rules,
        pair=pair,
        generated_at=generated_at,
        max_targets=rulegen_config.max_snapshot_targets,
        max_sources=rulegen_config.max_snapshot_sources,
    )
    if persist_store and updated_store is not store:
        save_srs_store(updated_store, paths.srs_store_path)
    return updated_store, RulegenOutput(
        rules=rules,
        snapshot=snapshot,
        target_count=len(targets),
    )
