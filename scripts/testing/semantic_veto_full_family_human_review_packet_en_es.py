#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_full_family_human_review_packet_core import (  # noqa: E402
    DEFAULT_PILOT_FAMILY_COUNT,
    build_full_family_human_review_packet as build_full_family_human_review_packet,
)
from semantic_veto_full_family_human_review_packet_rendering import (  # noqa: E402
    render_human_review_packet_markdown as render_human_review_packet_markdown,
)
from semantic_veto_heuristic_group_pilot_en_es import DEFAULT_WORDNET_DIR  # noqa: E402
from semantic_veto_product_quality_en_es import _load_json, _resolve_repo_path  # noqa: E402
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_DATASET_JSON = (
    TEST_INPUTS_ROOT / "semantic_routing_cases" / "en_es_full_family_representative_manual_v1.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_human_review_packet_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_human_review_packet_en_es_latest.md"
)
DEFAULT_WEAKNESS_TAXONOMY_JSON = (
    TEST_INPUTS_ROOT / "semantic_veto_test_weakness_taxonomy_en_es.json"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a human-facing review packet for the frozen en-es full-family "
            "representative semantic-veto draft dataset. This does not trust or "
            "promote any draft row."
        )
    )
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--wordnet-dir", type=Path, default=DEFAULT_WORDNET_DIR)
    parser.add_argument(
        "--weakness-taxonomy-json", type=Path, default=DEFAULT_WEAKNESS_TAXONOMY_JSON
    )
    parser.add_argument("--pilot-family-count", type=int, default=DEFAULT_PILOT_FAMILY_COUNT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    dataset_path = _resolve_repo_path(args.dataset_json)
    wordnet_dir = _resolve_repo_path(args.wordnet_dir)
    json_out = _resolve_repo_path(args.json_out)
    markdown_out = _resolve_repo_path(args.markdown_out)
    report = build_full_family_human_review_packet(
        dataset_payload=_load_json(dataset_path),
        wordnet_index=WordNetIndex.load(wordnet_dir),
        weakness_taxonomy=_load_json(_resolve_repo_path(args.weakness_taxonomy_json)),
        dataset_path=dataset_path,
        wordnet_dir=wordnet_dir,
        weakness_taxonomy_path=_resolve_repo_path(args.weakness_taxonomy_json),
        pilot_family_count=max(1, int(args.pilot_family_count)),
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_human_review_packet_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
