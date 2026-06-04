#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_veto_evidence_gap_generation_admission_core import (
    ACTIVE_SLOT as ACTIVE_SLOT,
    NO_WINNER_SLOT as NO_WINNER_SLOT,
    SHADOW_SLOT as SHADOW_SLOT,
    build_evidence_gap_generation_admission_report as build_evidence_gap_generation_admission_report,
    _load_json,
)
from semantic_veto_evidence_gap_generation_admission_rendering import (
    render_evidence_gap_generation_admission_markdown as render_evidence_gap_generation_admission_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_REQUESTS_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_generation_requests_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_generation_admission_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_generation_admission_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Admit generated responses for the en-es semantic-veto evidence-gap "
            "pilot. This validates response shape and generated sentences without "
            "changing runtime policy or scoring thresholds."
        )
    )
    parser.add_argument("--generation-requests-json", type=Path, default=DEFAULT_REQUESTS_JSON)
    parser.add_argument("--generated-responses-json", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    generated_responses_payload = (
        _load_json(args.generated_responses_json) if args.generated_responses_json else None
    )
    report = build_evidence_gap_generation_admission_report(
        generation_requests_payload=_load_json(args.generation_requests_json),
        generation_requests_path=args.generation_requests_json,
        generated_responses_payload=generated_responses_payload,
        generated_responses_path=args.generated_responses_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_evidence_gap_generation_admission_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
