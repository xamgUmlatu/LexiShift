#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.resources.dict_loaders import load_jmdict_glosses_ordered  # noqa: E402
from lexishift_core.frequency.providers import (  # noqa: E402
    SqliteFrequencyProviderConfig,
    build_sqlite_frequency_provider,
)
from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig  # noqa: E402
from lexishift_core.rulegen.pairs.ja_en import (  # noqa: E402
    JaEnRulegenConfig,
    generate_ja_en_results,
)
from lexishift_core.srs.seed import (  # noqa: E402
    SeedSelectionConfig,
    build_seed_candidates,
)
from lexishift_core.scoring.weighting import GlossDecay  # noqa: E402


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


def build_seed_report(bccwj: Path, jmdict: Path, top_n: int, sample: int) -> dict:
    raw_config = SeedSelectionConfig(
        top_n=top_n,
        require_jmdict=False,
        jmdict_path=None,
    )
    filtered_config = SeedSelectionConfig(
        top_n=top_n,
        require_jmdict=True,
        jmdict_path=jmdict,
    )
    raw_seeds = build_seed_candidates(frequency_db=bccwj, config=raw_config)
    filtered_seeds = build_seed_candidates(frequency_db=bccwj, config=filtered_config)
    pmw_values = [seed.pmw for seed in filtered_seeds if seed.pmw is not None]
    return {
        "top_n": top_n,
        "raw_count": len(raw_seeds),
        "filtered_count": len(filtered_seeds),
        "retention": (len(filtered_seeds) / len(raw_seeds)) if raw_seeds else 0.0,
        "pmw_mean": mean(pmw_values) if pmw_values else None,
        "pmw_min": min(pmw_values) if pmw_values else None,
        "pmw_max": max(pmw_values) if pmw_values else None,
        "sample": [
            {
                "lemma": seed.lemma,
                "core_rank": seed.core_rank,
                "pmw": seed.pmw,
                "weight": seed.base_weight,
            }
            for seed in filtered_seeds[:sample]
        ],
    }


def build_rulegen_sweep(
    *,
    bccwj: Path,
    jmdict: Path,
    coca: Path | None,
    coca_column: str,
    top_ns: list[int],
    thresholds: list[float],
    decays: list[tuple[float, ...]],
) -> list[dict]:
    gloss_mapping = load_jmdict_glosses_ordered(jmdict)
    frequency_provider = None
    if coca and coca.exists():
        sqlite_cfg = SqliteFrequencyConfig(path=coca)
        provider_cfg = SqliteFrequencyProviderConfig(sqlite=sqlite_cfg, value_column=coca_column)
        frequency_provider = build_sqlite_frequency_provider(provider_cfg)
    report = []
    for top_n in top_ns:
        seed_config = SeedSelectionConfig(
            top_n=top_n,
            require_jmdict=True,
            jmdict_path=jmdict,
        )
        seeds = build_seed_candidates(frequency_db=bccwj, config=seed_config)
        targets = [seed.lemma for seed in seeds]
        for threshold in thresholds:
            for decay in decays:
                config = JaEnRulegenConfig(
                    jmdict_path=jmdict,
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
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JA→EN SRS tests and write output files.")
    parser.add_argument("--bccwj", required=True, type=Path, help="Path to BCCWJ SUW SQLite")
    parser.add_argument("--jmdict", required=True, type=Path, help="Path to JMDict XML")
    parser.add_argument("--coca", type=Path, help="Path to COCA SQLite (optional)")
    parser.add_argument("--coca-column", default="frequency", help="COCA value column")
    parser.add_argument("--top-n", default="2000", help="Comma list of top-N values")
    parser.add_argument("--thresholds", default="0.0", help="Comma list of confidence thresholds")
    parser.add_argument("--decays", default="1.0,0.7,0.5", help="Semicolon list of gloss decay schedules")
    parser.add_argument("--sample", type=int, default=10, help="Sample size for seed report")
    parser.add_argument("--out-dir", type=Path, default=Path("docs/test_outputs/ja_en"), help="Output base dir")
    args = parser.parse_args()

    top_ns = parse_int_list(args.top_n)
    thresholds = parse_float_list(args.thresholds)
    decays = parse_decay_schedules(args.decays)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    seed_report = build_seed_report(args.bccwj, args.jmdict, top_ns[0], args.sample)
    (out_dir / "seed_report.json").write_text(
        json.dumps(seed_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "seed_report.txt").write_text(
        _format_seed_report(seed_report),
        encoding="utf-8",
    )

    sweep_report = build_rulegen_sweep(
        bccwj=args.bccwj,
        jmdict=args.jmdict,
        coca=args.coca,
        coca_column=args.coca_column,
        top_ns=top_ns,
        thresholds=thresholds,
        decays=decays,
    )
    (out_dir / "rulegen_sweep.json").write_text(
        json.dumps(sweep_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Seed report: {out_dir / 'seed_report.json'}")
    print(f"Sweep report: {out_dir / 'rulegen_sweep.json'}")


def _format_seed_report(report: dict) -> str:
    lines = [
        f"Top-N: {report['top_n']}",
        f"Raw count: {report['raw_count']}",
        f"Filtered count: {report['filtered_count']}",
        f"Retention: {report['retention']:.2%}",
    ]
    if report.get("pmw_mean") is not None:
        lines.append(
            f"PMW mean/min/max: {report['pmw_mean']:.2f} / {report['pmw_min']:.2f} / {report['pmw_max']:.2f}"
        )
    lines.append("")
    lines.append("Sample:")
    for item in report.get("sample", []):
        lines.append(
            f"- {item['lemma']} | core_rank={item['core_rank']} | pmw={item['pmw']} | weight={item['weight']:.4f}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
