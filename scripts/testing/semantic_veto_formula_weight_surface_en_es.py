#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_veto_formula_weight_surface_core import (
    build_formula_weight_surface_report as build_formula_weight_surface_report,
)
from semantic_veto_formula_weight_surface_rendering import (
    render_formula_weight_surface_markdown as render_formula_weight_surface_markdown,
)
from semantic_veto_product_quality_en_es import _as_mapping, _load_json, _resolve_repo_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_MANIFEST = TEST_INPUTS_ROOT / "semantic_veto_formula_shape_bakeoff_en_es.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_formula_weight_surface_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_formula_weight_surface_en_es_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze the local and sampled weight surface for semantic-veto "
            "heuristic formula sweeps. This is diagnostic-only."
        )
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = _load_json(args.manifest)
    inputs = _as_mapping(manifest.get("inputs"))
    surface_path = _resolve_repo_path(inputs.get("difficulty_surface_json"))
    policy_path = _resolve_repo_path(inputs.get("product_quality_policy_json"))
    report = build_formula_weight_surface_report(
        manifest=manifest,
        difficulty_surface_payload=_load_json(surface_path),
        policy_payload=_load_json(policy_path),
        manifest_path=args.manifest,
        difficulty_surface_path=surface_path,
        policy_path=policy_path,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(render_formula_weight_surface_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
