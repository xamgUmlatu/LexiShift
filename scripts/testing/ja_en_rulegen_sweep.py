#!/usr/bin/env python3
from __future__ import annotations

import sys

import argparse
import json
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.dict_loaders import load_jmdict_glosses_ordered  # noqa: E402
from lexishift_core.frequency_providers import (
    SqliteFrequencyProviderConfig,
    build_sqlite_frequency_provider,
)
from lexishift_core.frequency_sqlite_store import SqliteFrequencyConfig
from lexishift_core.rule_generation_ja_en import JaEnRulegenConfig, generate_ja_en_results
from lexishift_core.srs_seed import SeedSelectionConfig, build_seed_candidates
from lexishift_core.weighting import GlossDecay


def parse_int_list(text: str) -> list[int]:
    return [int(item.strip()) for item in text.split(",") if item.strip()]


def parse_float_list(text: str) -> list[float]:
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def parse_decay_schedules(text: str) -> list[tuple[float, ...]]:
    if not text:
        return [(1.0, 0.7, 0.5)]
    schedules = []
    for block in text.split(";"):
        block = block.strip()
        if not block:
            continue
        schedules.append(tuple(parse_float_list(block)))
    return schedules or [(1.0, 0.7, 0.5)]


def summarize_results(results) -> dict:
    total = len(results)
    unique_targets = len({item.rule.replacement for item in results})
    per_target = {}
    confidences = []
    for item in results:
        per_target[item.rule.replacement] = per_target.get(item.rule.replacement, 0) + 1
        confidences.append(item.confidence)
    avg_rules = (total / unique_targets) if unique_targets else 0.0
    stats = {
        "total_rules": total,
        "unique_targets": unique_targets,
        "avg_rules_per_target": round(avg_rules, 3),
    }
    if confidences:
        stats.update(
            {
                "confidence_min": round(min(confidences), 4),
                "confidence_mean": round(mean(confidences), 4),
                "confidence_max": round(max(confidences), 4),
            }
        )
    top_targets = sorted(per_target.items(), key=lambda item: item[1], reverse=True)[:5]
    stats["top_targets"] = [{"lemma": lemma, "rules": count} for lemma, count in top_targets]
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep JA→EN rulegen parameters.")
    parser.add_argument("--bccwj", required=True, type=Path, help="Path to BCCWJ SUW SQLite")
    parser.add_argument("--jmdict", required=True, type=Path, help="Path to JMDict XML")
    parser.add_argument("--coca", type=Path, help="Path to COCA SQLite (optional)")
    parser.add_argument("--coca-column", default="frequency", help="COCA value column (e.g., frequency, pmw)")
    parser.add_argument("--top-n", default="2000", help="Comma list of top-N values")
    parser.add_argument("--thresholds", default="0.0", help="Comma list of confidence thresholds")
    parser.add_argument("--decays", default="1.0,0.7,0.5", help="Semicolon list of gloss decay schedules")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    top_ns = parse_int_list(args.top_n)
    thresholds = parse_float_list(args.thresholds)
    decays = parse_decay_schedules(args.decays)

    gloss_mapping = load_jmdict_glosses_ordered(args.jmdict)
    frequency_provider = None
    if args.coca and args.coca.exists():
        sqlite_cfg = SqliteFrequencyConfig(path=args.coca)
        provider_cfg = SqliteFrequencyProviderConfig(sqlite=sqlite_cfg, value_column=args.coca_column)
        frequency_provider = build_sqlite_frequency_provider(provider_cfg)

    report = []
    for top_n in top_ns:
        seed_config = SeedSelectionConfig(
            top_n=top_n,
            require_jmdict=True,
            jmdict_path=args.jmdict,
        )
        seeds = build_seed_candidates(frequency_db=args.bccwj, config=seed_config)
        targets = [seed.lemma for seed in seeds]
        for threshold in thresholds:
            for decay in decays:
                config = JaEnRulegenConfig(
                    jmdict_path=args.jmdict,
                    gloss_mapping=gloss_mapping,
                    gloss_decay=GlossDecay(schedule=decay),
                    confidence_threshold=threshold,
                    frequency_provider=frequency_provider,
                )
                results = generate_ja_en_results(targets, config=config)
                entry = {
                    "top_n": top_n,
                    "confidence_threshold": threshold,
                    "gloss_decay": decay,
                    "seed_count": len(targets),
                    "summary": summarize_results(results),
                }
                report.append(entry)
                print(json.dumps(entry, ensure_ascii=False))

    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
