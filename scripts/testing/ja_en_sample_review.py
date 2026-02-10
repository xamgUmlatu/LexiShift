#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

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


def parse_float_list(text: str) -> list[float]:
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sample JA→EN rules for human review.")
    parser.add_argument("--bccwj", required=True, type=Path, help="Path to BCCWJ SUW SQLite")
    parser.add_argument("--jmdict", required=True, type=Path, help="Path to JMDict XML")
    parser.add_argument("--coca", type=Path, help="Path to COCA SQLite (optional)")
    parser.add_argument("--coca-column", default="frequency", help="COCA value column")
    parser.add_argument("--top-n", type=int, default=2000, help="Top N by core_rank")
    parser.add_argument("--threshold", type=float, default=0.0, help="Confidence threshold")
    parser.add_argument("--decay", default="1.0,0.7,0.5", help="Gloss decay schedule")
    parser.add_argument("--mode", choices=("top", "random"), default="top")
    parser.add_argument("--sample", type=int, default=50, help="Number of rules to sample")
    parser.add_argument("--targets", default="", help="Comma-separated target lemmas to include (optional)")
    parser.add_argument("--out-dir", type=Path, default=Path("docs/test_outputs/ja_en"), help="Output base dir")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed for random mode")
    args = parser.parse_args()

    gloss_mapping = load_jmdict_glosses_ordered(args.jmdict)
    frequency_provider = None
    if args.coca and args.coca.exists():
        sqlite_cfg = SqliteFrequencyConfig(path=args.coca)
        provider_cfg = SqliteFrequencyProviderConfig(sqlite=sqlite_cfg, value_column=args.coca_column)
        frequency_provider = build_sqlite_frequency_provider(provider_cfg)

    target_list = [item.strip() for item in args.targets.split(",") if item.strip()]
    if target_list:
        targets = target_list
    else:
        seed_config = SeedSelectionConfig(
            top_n=args.top_n,
            require_jmdict=True,
            jmdict_path=args.jmdict,
        )
        seeds = build_seed_candidates(frequency_db=args.bccwj, config=seed_config)
        targets = [seed.lemma for seed in seeds]

    decay = tuple(parse_float_list(args.decay))
    config = JaEnRulegenConfig(
        jmdict_path=args.jmdict,
        gloss_mapping=gloss_mapping,
        gloss_decay=GlossDecay(schedule=decay),
        confidence_threshold=args.threshold,
        frequency_provider=frequency_provider,
    )
    results = generate_ja_en_results(targets, config=config)
    results.sort(key=lambda item: item.confidence, reverse=True)

    if args.mode == "random":
        rng = random.Random(args.seed)
        sampled = rng.sample(results, min(args.sample, len(results)))
    else:
        sampled = results[: args.sample]

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir / f"samples_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_payload = [
        {
            "source_phrase": item.rule.source_phrase,
            "replacement": item.rule.replacement,
            "confidence": item.confidence,
            "gloss_index": item.candidate.metadata.get("gloss_index"),
            "gloss_total": item.candidate.metadata.get("gloss_total"),
            "language_pair": item.rule.metadata.language_pair if item.rule.metadata else None,
        }
        for item in sampled
    ]
    (out_dir / "samples.json").write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = ["source_phrase\treplacement\tconfidence\tgloss_index\tgloss_total"]
    for item in json_payload:
        lines.append(
            f"{item['source_phrase']}\t{item['replacement']}\t{item['confidence']:.4f}\t{item['gloss_index']}\t{item['gloss_total']}"
        )
    (out_dir / "samples.tsv").write_text("\n".join(lines), encoding="utf-8")

    print(f"Sample output: {out_dir}")


if __name__ == "__main__":
    main()
