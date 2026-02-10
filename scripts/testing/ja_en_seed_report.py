#!/usr/bin/env python3
from __future__ import annotations

import sys

import argparse
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Report JA seed stats from BCCWJ + JMDict.")
    parser.add_argument("--bccwj", required=True, type=Path, help="Path to BCCWJ SUW SQLite")
    parser.add_argument("--jmdict", required=True, type=Path, help="Path to JMDict XML")
    parser.add_argument("--top-n", type=int, default=2000, help="Top N by core_rank")
    parser.add_argument("--sample", type=int, default=10, help="Sample size to print")
    args = parser.parse_args()

    raw_config = SeedSelectionConfig(
        top_n=args.top_n,
        require_jmdict=False,
        jmdict_path=None,
    )
    filtered_config = SeedSelectionConfig(
        top_n=args.top_n,
        require_jmdict=True,
        jmdict_path=args.jmdict,
    )

    raw_seeds = build_seed_candidates(frequency_db=args.bccwj, config=raw_config)
    filtered_seeds = build_seed_candidates(frequency_db=args.bccwj, config=filtered_config)

    print(f"Top-N by core_rank: {args.top_n}")
    print(f"Raw seed count: {len(raw_seeds)}")
    print(f"JMDict-filtered seed count: {len(filtered_seeds)}")
    if raw_seeds:
        print(f"Retention: {len(filtered_seeds) / len(raw_seeds):.2%}")

    pmw_values = [seed.pmw for seed in filtered_seeds if seed.pmw is not None]
    if pmw_values:
        print(f"PMW mean: {mean(pmw_values):.2f} | min: {min(pmw_values):.2f} | max: {max(pmw_values):.2f}")

    print("\nSample seeds:")
    for seed in filtered_seeds[: args.sample]:
        print(f"- {seed.lemma} | core_rank={seed.core_rank} | pmw={seed.pmw} | weight={seed.base_weight:.4f}")


if __name__ == "__main__":
    main()
