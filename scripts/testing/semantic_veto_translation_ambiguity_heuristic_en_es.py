#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from semantic_veto_full_family_representative_sample_en_es import DEFAULT_WORDNET_DIR  # noqa: E402
from semantic_veto_product_quality_en_es import _load_json, _resolve_repo_path  # noqa: E402
from semantic_veto_translation_ambiguity_heuristic_core import (  # noqa: E402
    TOP_K,
    build_translation_ambiguity_heuristic_report as build_translation_ambiguity_heuristic_report,
)
from semantic_veto_translation_ambiguity_heuristic_rendering import (  # noqa: E402
    render_translation_ambiguity_heuristic_markdown as render_translation_ambiguity_heuristic_markdown,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_DATASET_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_repaired_full_v1.json"
)
DEFAULT_SCORE_SURFACE_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_repaired_full_score_surface_en_es_latest.json"
)
DEFAULT_SRS_BRIDGE_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_translation_ambiguity_heuristic_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_translation_ambiguity_heuristic_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare stronger inventory-available heuristics for ranking en-es "
            "semantic-veto source-target families by likely evidence need. "
            "Runtime policy remains unchanged."
        )
    )
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--score-surface-json", type=Path, default=DEFAULT_SCORE_SURFACE_JSON)
    parser.add_argument("--srs-bridge-json", type=Path, default=DEFAULT_SRS_BRIDGE_JSON)
    parser.add_argument("--wordnet-dir", type=Path, default=DEFAULT_WORDNET_DIR)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    wordnet_dir = _resolve_repo_path(args.wordnet_dir)
    report = build_translation_ambiguity_heuristic_report(
        dataset_payload=_load_json(args.dataset_json),
        score_surface_payload=_load_json(args.score_surface_json),
        srs_bridge_payload=_load_json(args.srs_bridge_json),
        wordnet_index=WordNetIndex.load(wordnet_dir),
        dataset_path=args.dataset_json,
        score_surface_path=args.score_surface_json,
        srs_bridge_path=args.srs_bridge_json,
        wordnet_dir=wordnet_dir,
        top_k=int(args.top_k),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_translation_ambiguity_heuristic_markdown(report), encoding="utf-8"
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
