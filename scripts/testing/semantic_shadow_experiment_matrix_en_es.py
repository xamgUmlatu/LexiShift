#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_shadow_experiment_matrix_runner import (  # noqa: E402
    build_experiment_matrix_report,
    render_experiment_matrix_markdown,
)
from semantic_shadow_experiment_support import (  # noqa: E402
    DEFAULT_BENCHMARK_JSON,
    DEFAULT_DATASET_PATH,
    DEFAULT_GENERALIZATION_SPLITS_MANIFEST_PATH,
)

DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "docs" / "test_inputs" / "semantic_shadow_experiment_matrix_en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_experiment_matrix_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_experiment_matrix_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a manifest-driven en-es semantic-shadow experiment matrix across "
            "seed-admission, promotion, and veto-evaluation settings."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Experiment manifest JSON.",
    )
    parser.add_argument(
        "--benchmark-dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Reviewed rulegen benchmark dataset JSON.",
    )
    parser.add_argument(
        "--benchmark-json",
        type=Path,
        default=DEFAULT_BENCHMARK_JSON,
        help="Rulegen benchmark report JSON containing best_run case_results.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(resolve_data_root()),
        help="LexiShift data root (default: helper resolve_data_root()).",
    )
    parser.add_argument(
        "--translation-dict",
        type=Path,
        default=None,
        help="Optional forward translation-pack override for en-es experiments.",
    )
    parser.add_argument(
        "--reverse-translation-dict",
        type=Path,
        default=None,
        help="Optional reverse translation-pack override for en-es experiments.",
    )
    parser.add_argument(
        "--generalization-splits-manifest",
        type=Path,
        default=DEFAULT_GENERALIZATION_SPLITS_MANIFEST_PATH,
        help="Explicit tune vs held-out split manifest for reviewed overlap evaluation rows.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_experiment_matrix_report(
        manifest_path=args.manifest,
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        data_root=args.data_root,
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        generalization_splits_manifest=args.generalization_splits_manifest,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_experiment_matrix_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
