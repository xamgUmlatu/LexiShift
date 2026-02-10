#!/usr/bin/env python3
from __future__ import annotations

import sys

import argparse
import json
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.frequency.providers import (  # noqa: E402
    SqliteFrequencyProviderConfig,
    build_sqlite_frequency_provider,
)
from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig
from lexishift_core.rulegen.pairs.ja_en import JaEnRulegenConfig, generate_ja_en_rules
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates
from lexishift_core.persistence.storage import VocabDataset, save_vocab_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Build JA→EN SRS ruleset from BCCWJ + JMDict.")
    parser.add_argument("--bccwj", required=True, type=Path, help="Path to BCCWJ SUW SQLite")
    parser.add_argument("--jmdict", required=True, type=Path, help="Path to JMDict XML")
    parser.add_argument("--coca", type=Path, help="Path to COCA SQLite (optional)")
    parser.add_argument("--top-n", type=int, default=2000, help="Top N by core_rank")
    parser.add_argument("--output", required=True, type=Path, help="Output ruleset JSON path")
    parser.add_argument("--confidence-threshold", type=float, default=0.0)
    parser.add_argument("--gloss-decay", default="1.0,0.7,0.5", help="Gloss decay schedule")
    args = parser.parse_args()

    seed_config = SeedSelectionConfig(
        top_n=args.top_n,
        jmdict_path=args.jmdict,
    )
    seeds = build_seed_candidates(frequency_db=args.bccwj, config=seed_config)
    targets = [seed.lemma for seed in seeds]

    frequency_provider = None
    if args.coca and args.coca.exists():
        value_column = _guess_value_column(args.coca)
        sqlite_config = SqliteFrequencyConfig(path=args.coca)
        provider_config = SqliteFrequencyProviderConfig(
            sqlite=sqlite_config,
            value_column=value_column,
        )
        frequency_provider = build_sqlite_frequency_provider(provider_config)

    decay = tuple(float(item.strip()) for item in args.gloss_decay.split(",") if item.strip())
    rule_config = JaEnRulegenConfig(
        jmdict_path=args.jmdict,
        confidence_threshold=args.confidence_threshold,
        gloss_decay=rule_config_gloss_decay(decay),
        frequency_provider=frequency_provider,
    )
    rules = generate_ja_en_rules(targets, config=rule_config)
    dataset = VocabDataset(rules=tuple(rules))
    save_vocab_dataset(dataset, args.output)


def _guess_value_column(path: Path) -> str:
    candidates = ("pmw", "frequency", "freq", "freq_per_million", "count")
    try:
        with sqlite3.connect(str(path)) as conn:
            rows = conn.execute("PRAGMA table_info(frequency);").fetchall()
    except sqlite3.Error:
        return "frequency"
    columns = [row[1] for row in rows if len(row) > 1]
    lower = {name.lower(): name for name in columns}
    for candidate in candidates:
        if candidate in lower:
            return lower[candidate]
    return columns[0] if columns else "frequency"


def rule_config_gloss_decay(schedule: tuple[float, ...]):
    from lexishift_core.scoring.weighting import GlossDecay

    return GlossDecay(schedule=schedule) if schedule else GlossDecay()


if __name__ == "__main__":
    main()
