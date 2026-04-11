#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_routing_sentence_veto_support import (
    DEFAULT_SENTENCE_VETO_DATASET,
    DEFAULT_SENTENCE_VETO_JSON_OUT,
    DEFAULT_SENTENCE_VETO_MARKDOWN_OUT,
    build_sentence_veto_report,
    render_sentence_veto_markdown,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the curated sentence-level semantic-routing veto harness over a fixed "
            "active-vs-shadow dataset."
        )
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_DATASET,
        help="Sentence-level semantic-routing dataset JSON.",
    )
    parser.add_argument(
        "--scorer",
        type=str,
        default="tfidf_cosine",
        help="Similarity backend id.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="",
        help="Optional model override for embedding-backed scorers.",
    )
    parser.add_argument(
        "--context-view",
        type=str,
        default="masked_sentence",
        help="Context view id.",
    )
    parser.add_argument(
        "--evidence-view",
        type=str,
        default="all_evidence_text",
        help="Evidence view id.",
    )
    parser.add_argument(
        "--min-active-score",
        type=float,
        default=0.05,
        help="Minimum active score required before replace is allowed.",
    )
    parser.add_argument(
        "--min-margin",
        type=float,
        default=0.0,
        help="Minimum active-minus-shadow margin required for replace.",
    )
    parser.add_argument(
        "--window-tokens",
        type=int,
        default=4,
        help="Context-window token radius for window views.",
    )
    parser.add_argument(
        "--mask-token",
        type=str,
        default="___",
        help="Mask token used by masked context views.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_sentence_veto_report(
        dataset_path=args.dataset,
        scorer_id=str(args.scorer or "").strip(),
        model_name=str(args.model_name or "").strip() or None,
        context_view=str(args.context_view or "").strip(),
        evidence_view=str(args.evidence_view or "").strip(),
        min_active_score=float(args.min_active_score),
        min_margin=float(args.min_margin),
        window_tokens=max(0, int(args.window_tokens)),
        mask_token=str(args.mask_token or "").strip() or "___",
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_sentence_veto_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
