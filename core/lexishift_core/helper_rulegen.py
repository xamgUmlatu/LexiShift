from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from lexishift_core.core import VocabRule
from lexishift_core.helper_paths import HelperPaths
from lexishift_core.rule_generation_ja_en import JaEnRulegenConfig, generate_ja_en_results
from lexishift_core.srs import SrsItem, SrsSettings, SrsStore, save_srs_store
from lexishift_core.srs_seed import SeedSelectionConfig, build_seed_candidates
from lexishift_core.srs_store_ops import build_item_id, upsert_item
from lexishift_core.storage import VocabDataset, save_vocab_dataset
from lexishift_core.weighting import GlossDecay


@dataclass(frozen=True)
class SeedConfig:
    frequency_db: Path
    jmdict_path: Path
    top_n: int = 2000
    language_pair: str = "en-ja"


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


def seed_store_from_bccwj(
    store: SrsStore,
    *,
    config: SeedConfig,
) -> SrsStore:
    seed_config = SeedSelectionConfig(
        language_pair=config.language_pair,
        top_n=config.top_n,
        jmdict_path=config.jmdict_path,
    )
    seeds = build_seed_candidates(frequency_db=config.frequency_db, config=seed_config)
    updated = store
    for seed in seeds:
        item = SrsItem(
            item_id=build_item_id(seed.language_pair, seed.lemma),
            lemma=seed.lemma,
            language_pair=seed.language_pair,
            source_type="seed",
        )
        updated = upsert_item(updated, item)
    return updated


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
    seed_config: Optional[SeedConfig] = None,
    rulegen_config: Optional[RulegenConfig] = None,
    seed_if_empty: bool = True,
) -> tuple[SrsStore, RulegenOutput]:
    rulegen_config = rulegen_config or RulegenConfig(language_pair=pair)
    targets = load_targets_from_store(store, pair=pair)
    updated_store = store
    if not targets and seed_if_empty and seed_config:
        updated_store = seed_store_from_bccwj(store, config=seed_config)
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
    if updated_store is not store:
        save_srs_store(updated_store, paths.srs_store_path)
    return updated_store, RulegenOutput(
        rules=rules,
        snapshot=snapshot,
        target_count=len(targets),
    )
