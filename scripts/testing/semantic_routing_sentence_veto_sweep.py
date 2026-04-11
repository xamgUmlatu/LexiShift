#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from semantic_routing_sentence_veto_support import (
    DEFAULT_SENTENCE_VETO_DATASET,
    DEFAULT_SENTENCE_VETO_SWEEP_JSON_OUT,
    DEFAULT_SENTENCE_VETO_SWEEP_MARKDOWN_OUT,
    SENTENCE_VETO_CONTEXT_VIEWS,
    SENTENCE_VETO_EVIDENCE_VIEWS,
    SENTENCE_VETO_SCORERS,
    build_sentence_veto_sweep_report,
    render_sentence_veto_sweep_markdown,
)


def _parse_float_grid(value: str) -> list[float]:
    normalized = str(value or "").strip()
    if not normalized:
        return []
    return [float(item.strip()) for item in normalized.split(",") if item.strip()]


def _parse_int_grid(value: str) -> list[int]:
    normalized = str(value or "").strip()
    if not normalized:
        return []
    return [int(item.strip()) for item in normalized.split(",") if item.strip()]


def _parse_string_grid(value: str, *, default_values: Sequence[str]) -> list[str]:
    normalized = str(value or "").strip()
    if not normalized:
        return list(default_values)
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep sentence-level semantic-routing veto scorer families, context views, "
            "evidence views, and threshold settings over a fixed active-vs-shadow dataset."
        )
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_DATASET,
        help="Sentence-level semantic-routing dataset JSON.",
    )
    parser.add_argument(
        "--scorers",
        type=str,
        default="token_jaccard,tfidf_cosine",
        help="Comma-separated scorer ids.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="",
        help="Optional model override for embedding-backed scorers.",
    )
    parser.add_argument(
        "--context-views",
        type=str,
        default=",".join(SENTENCE_VETO_CONTEXT_VIEWS),
        help="Comma-separated context view ids.",
    )
    parser.add_argument(
        "--evidence-views",
        type=str,
        default="sense_label,gloss_text,all_evidence_text",
        help="Comma-separated evidence view ids.",
    )
    parser.add_argument(
        "--min-active-grid",
        type=str,
        default="0.00,0.05,0.10,0.15,0.25,0.35,0.45,0.55",
        help="Comma-separated active-score thresholds.",
    )
    parser.add_argument(
        "--min-margin-grid",
        type=str,
        default="0.00,0.05,0.10,0.15",
        help="Comma-separated margin thresholds.",
    )
    parser.add_argument(
        "--harmful-replace-budgets",
        type=str,
        default="0,1,2",
        help="Comma-separated harmful-replace count budgets for frontier reporting.",
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
        default=DEFAULT_SENTENCE_VETO_SWEEP_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_SWEEP_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_sentence_veto_sweep_report(
        dataset_path=args.dataset,
        scorers=_parse_string_grid(args.scorers, default_values=SENTENCE_VETO_SCORERS),
        model_name=str(args.model_name or "").strip() or None,
        context_views=_parse_string_grid(
            args.context_views,
            default_values=SENTENCE_VETO_CONTEXT_VIEWS,
        ),
        evidence_views=_parse_string_grid(
            args.evidence_views,
            default_values=SENTENCE_VETO_EVIDENCE_VIEWS,
        ),
        min_active_scores=_parse_float_grid(args.min_active_grid),
        min_margins=_parse_float_grid(args.min_margin_grid),
        harmful_replace_budgets=_parse_int_grid(args.harmful_replace_budgets),
        window_tokens=max(0, int(args.window_tokens)),
        mask_token=str(args.mask_token or "").strip() or "___",
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_sentence_veto_sweep_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
