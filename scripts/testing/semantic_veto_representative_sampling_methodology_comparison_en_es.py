#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from semantic_veto_difficulty_stratification_en_es import (
    DEFAULT_SOURCE_FREQUENCY_DB,
    FrequencyLookup,
)
from semantic_veto_heuristic_group_pilot_en_es import (
    DEFAULT_DIFFICULTY_REPORT,
    DEFAULT_WORDNET_DIR,
)
from semantic_veto_product_quality_en_es import _load_json, _resolve_repo_path
from semantic_veto_representative_heuristic_band_sampler_en_es import (
    DEFAULT_JSON_OUT as DEFAULT_REPRESENTATIVE_SAMPLE_JSON,
)
from semantic_veto_representative_sampling_methodology_comparison_core import (
    DEFAULT_CONSTRUCTION_STABILITY_SAMPLE_SIZES,
    DEFAULT_CONSTRUCTION_STABILITY_SEEDS,
    DEFAULT_PILOT_JSON,
    DEFAULT_SAMPLE_SIZES,
    DEFAULT_SEEDS,
    build_sampling_methodology_comparison_report as build_sampling_methodology_comparison_report,
    _parse_int_list,
    _parse_str_list,
)
from lexishift_core.helper.paths import resolve_data_root
from semantic_veto_representative_target_family_construction_en_es import (
    DEFAULT_JSON_OUT as DEFAULT_REPRESENTATIVE_CONSTRUCTION_JSON,
)
from semantic_veto_representative_sampling_methodology_comparison_rendering import (
    render_sampling_methodology_comparison_markdown as render_sampling_methodology_comparison_markdown,
)
from semantic_wordnet_source_adapter_support import WordNetIndex


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_representative_sampling_methodology_comparison_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_representative_sampling_methodology_comparison_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare the old hard-case heuristic-group pilot with the representative "
            "heuristic-band sampler, including source-sampling seed and scale stability."
        )
    )
    parser.add_argument("--pilot-json", type=Path, default=DEFAULT_PILOT_JSON)
    parser.add_argument("--sample-json", type=Path, default=DEFAULT_REPRESENTATIVE_SAMPLE_JSON)
    parser.add_argument(
        "--construction-json", type=Path, default=DEFAULT_REPRESENTATIVE_CONSTRUCTION_JSON
    )
    parser.add_argument("--source-frequency-db", type=Path, default=DEFAULT_SOURCE_FREQUENCY_DB)
    parser.add_argument("--wordnet-dir", type=Path, default=DEFAULT_WORDNET_DIR)
    parser.add_argument("--difficulty-json", type=Path, default=DEFAULT_DIFFICULTY_REPORT)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--wiktionary-en-es-sqlite", type=Path, default=None)
    parser.add_argument("--wiktionary-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--freedict-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--sample-sizes", default=DEFAULT_SAMPLE_SIZES)
    parser.add_argument("--seeds", default=DEFAULT_SEEDS)
    parser.add_argument(
        "--construction-stability-sample-sizes",
        default=DEFAULT_CONSTRUCTION_STABILITY_SAMPLE_SIZES,
    )
    parser.add_argument(
        "--construction-stability-seeds",
        default=DEFAULT_CONSTRUCTION_STABILITY_SEEDS,
    )
    parser.add_argument("--skip-construction-stability", action="store_true")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def write_report(report: Mapping[str, object], *, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_sampling_methodology_comparison_markdown(report),
        encoding="utf-8",
    )


def main() -> int:
    args = _parse_args()
    pilot_path = _resolve_repo_path(args.pilot_json)
    sample_path = _resolve_repo_path(args.sample_json)
    construction_path = _resolve_repo_path(args.construction_json)
    source_frequency_path = _resolve_repo_path(args.source_frequency_db)
    wordnet_dir = _resolve_repo_path(args.wordnet_dir)
    difficulty_path = _resolve_repo_path(args.difficulty_json)
    data_root = _resolve_repo_path(args.data_root)
    wiktionary_en_es = args.wiktionary_en_es_sqlite or (
        data_root / "language_packs" / "wiktionary-en-es.sqlite"
    )
    wiktionary_es_en = args.wiktionary_es_en_sqlite or (
        data_root / "language_packs" / "wiktionary-es-en.sqlite"
    )
    freedict_es_en = args.freedict_es_en_sqlite or (
        data_root / "language_packs" / "freedict-es-en" / "main.sqlite"
    )
    report = build_sampling_methodology_comparison_report(
        pilot_payload=_load_json(pilot_path),
        representative_sample_payload=_load_json(sample_path),
        construction_payload=_load_json(construction_path),
        source_frequency=FrequencyLookup.from_sqlite(
            path=source_frequency_path,
            language="en",
        ),
        wordnet_index=WordNetIndex.load(wordnet_dir),
        difficulty_payload=_load_json(difficulty_path) if difficulty_path.exists() else {},
        pilot_json_path=pilot_path,
        sample_json_path=sample_path,
        construction_json_path=construction_path,
        source_frequency_path=source_frequency_path,
        wordnet_dir=wordnet_dir,
        wiktionary_en_es_sqlite=(
            wiktionary_en_es
            if wiktionary_en_es.exists() and not args.skip_construction_stability
            else None
        ),
        wiktionary_es_en_sqlite=(
            wiktionary_es_en
            if wiktionary_es_en.exists() and not args.skip_construction_stability
            else None
        ),
        freedict_es_en_sqlite=(
            freedict_es_en
            if freedict_es_en.exists() and not args.skip_construction_stability
            else None
        ),
        sample_sizes=_parse_int_list(args.sample_sizes),
        seeds=_parse_str_list(args.seeds),
        construction_stability_sample_sizes=(
            []
            if args.skip_construction_stability
            else _parse_int_list(args.construction_stability_sample_sizes)
        ),
        construction_stability_seeds=(
            []
            if args.skip_construction_stability
            else _parse_str_list(args.construction_stability_seeds)
        ),
    )
    write_report(
        report,
        json_out=_resolve_repo_path(args.json_out),
        markdown_out=_resolve_repo_path(args.markdown_out),
    )
    print(f"Wrote JSON artifact to {_resolve_repo_path(args.json_out)}")
    print(f"Wrote Markdown artifact to {_resolve_repo_path(args.markdown_out)}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
