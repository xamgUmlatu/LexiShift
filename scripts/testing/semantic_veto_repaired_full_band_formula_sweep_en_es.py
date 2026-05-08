#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_veto_product_quality_en_es import _load_json
from semantic_veto_repaired_full_band_formula_sweep_core import (
    TOP_K,
    build_repaired_full_band_formula_sweep_report as build_repaired_full_band_formula_sweep_report,
)
from semantic_veto_repaired_full_band_formula_sweep_rendering import (
    render_repaired_full_band_formula_sweep_markdown as render_repaired_full_band_formula_sweep_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DATASET_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_SCORE_SURFACE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repaired_full_score_surface_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_repaired_full_band_formula_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_repaired_full_band_formula_sweep_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep programmatic band/formula heuristics against the user-approved "
            "en-es repaired-full semantic-veto lane. Runtime policy remains unchanged."
        )
    )
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--score-surface-json", type=Path, default=DEFAULT_SCORE_SURFACE_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_repaired_full_band_formula_sweep_report(
        dataset_payload=_load_json(args.dataset_json),
        score_surface_payload=_load_json(args.score_surface_json),
        dataset_path=args.dataset_json,
        score_surface_path=args.score_surface_json,
        top_k=args.top_k,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_repaired_full_band_formula_sweep_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
