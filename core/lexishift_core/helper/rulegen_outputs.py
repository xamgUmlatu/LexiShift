from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Mapping, Sequence

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.persistence.storage import VocabDataset, save_vocab_dataset
from lexishift_core.replacement.core import VocabRule


@dataclass(frozen=True)
class RulegenOutput:
    rules: Sequence[VocabRule]
    snapshot: Mapping[str, object]
    target_count: int
    semantic_inventory: Mapping[str, object] | None = None


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def build_snapshot(
    *,
    rules: Sequence[VocabRule],
    pair: str,
    max_targets: int,
    max_sources: int,
    generated_at: str | None = None,
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
    return {
        "version": 1,
        "generated_at": generated_at or _now_iso(),
        "pair": pair,
        "targets": targets,
        "stats": {
            "target_count": len(mapping),
            "rule_count": len(rules),
            "source_count": source_total,
        },
    }


def write_rulegen_outputs(
    *,
    paths: HelperPaths,
    pair: str,
    profile_id: str = "default",
    rules: Sequence[VocabRule],
    snapshot: Mapping[str, object],
    semantic_inventory: Mapping[str, object] | None = None,
) -> None:
    dataset = VocabDataset(rules=tuple(rules))
    save_vocab_dataset(dataset, paths.ruleset_path(pair, profile_id=profile_id))
    Path(paths.snapshot_path(pair, profile_id=profile_id)).write_text(
        json.dumps(snapshot, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    semantic_inventory_path = paths.semantic_inventory_path(pair, profile_id=profile_id)
    if semantic_inventory is not None:
        Path(semantic_inventory_path).write_text(
            json.dumps(semantic_inventory, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    elif semantic_inventory_path.exists():
        semantic_inventory_path.unlink()
