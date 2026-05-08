#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
SEMANTIC_CASES_ROOT = TEST_INPUTS_ROOT / "semantic_routing_cases"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from semantic_veto_evidence_gap_generation_score_contribution_core import (  # noqa: E402
    DEFAULT_CONTEXT_VIEW,
    DEFAULT_EVIDENCE_VIEW,
    DEFAULT_SCORER_ID,
    build_evidence_gap_score_contribution_report as build_evidence_gap_score_contribution_report,
    _load_json,
)
from semantic_veto_evidence_gap_generation_score_contribution_rendering import (  # noqa: E402
    render_evidence_gap_score_contribution_markdown as render_evidence_gap_score_contribution_markdown,
)


DEFAULT_DATASET_JSON = SEMANTIC_CASES_ROOT / "en_es_full_family_repaired_full_v1.json"
DEFAULT_ADMISSION_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_admission_balanced_smoke_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_score_contribution_balanced_smoke_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_score_contribution_balanced_smoke_en_es_latest.md"
)
DEFAULT_AUGMENTED_DIR = (
    TEST_OUTPUTS_ROOT / "experiments" / "semantic_veto_evidence_gap_augmented_datasets"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure whether admitted evidence-gap generated items improve frozen "
            "manual sentence-veto cases. This is an offline/no-spend scorer probe."
        )
    )
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--admission-json", type=Path, default=DEFAULT_ADMISSION_JSON)
    parser.add_argument("--augmented-dir", type=Path, default=DEFAULT_AUGMENTED_DIR)
    parser.add_argument("--scorer-id", default=DEFAULT_SCORER_ID)
    parser.add_argument("--context-view", default=DEFAULT_CONTEXT_VIEW)
    parser.add_argument("--evidence-view", default=DEFAULT_EVIDENCE_VIEW)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_evidence_gap_score_contribution_report(
        dataset_payload=_load_json(args.dataset_json),
        admission_payload=_load_json(args.admission_json),
        dataset_path=args.dataset_json,
        admission_path=args.admission_json,
        augmented_dir=args.augmented_dir,
        scorer_id=args.scorer_id,
        context_view=args.context_view,
        evidence_view=args.evidence_view,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_evidence_gap_score_contribution_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
