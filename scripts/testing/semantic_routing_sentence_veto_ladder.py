#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_routing_sentence_veto_support import (
    DEFAULT_SENTENCE_VETO_DATASET,
    DEFAULT_SENTENCE_VETO_LADDER_JSON_OUT,
    DEFAULT_SENTENCE_VETO_LADDER_MARKDOWN_OUT,
    build_sentence_veto_ladder_report,
    render_sentence_veto_ladder_markdown,
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep soft-affordance decision ladders over the frozen sentence-veto runtime row "
            "without changing the underlying hard-replace scorer configuration."
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
        default="sentence_transformer_cosine",
        help="Similarity backend id for the frozen hard-replace row.",
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
        default=0.0,
        help="Frozen hard-replace active-score threshold.",
    )
    parser.add_argument(
        "--min-margin",
        type=float,
        default=0.0,
        help="Frozen hard-replace margin threshold.",
    )
    parser.add_argument(
        "--phrase-control-mode",
        type=str,
        default="noun_family_frame_guard",
        help="Phrase/frame control mode id.",
    )
    parser.add_argument(
        "--active-rescue-mode",
        type=str,
        default="sense_label_near_tie_active_rescue",
        help="Active-side rescue mode id.",
    )
    parser.add_argument(
        "--soft-active-grid",
        type=str,
        default="0.50,0.52,0.55,0.58,0.60",
        help="Comma-separated soft-affordance active-score thresholds.",
    )
    parser.add_argument(
        "--soft-margin-grid",
        type=str,
        default="-0.20,-0.15,-0.10,-0.05,-0.03,-0.02,-0.01,0.00",
        help="Comma-separated soft-affordance margin thresholds.",
    )
    parser.add_argument(
        "--soft-false-positive-budgets",
        type=str,
        default="0,1,2",
        help="Comma-separated soft false-positive count budgets for frontier reporting.",
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
        default=DEFAULT_SENTENCE_VETO_LADDER_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_LADDER_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_sentence_veto_ladder_report(
        dataset_path=args.dataset,
        scorer_id=str(args.scorer or "").strip(),
        model_name=str(args.model_name or "").strip() or None,
        context_view=str(args.context_view or "").strip(),
        evidence_view=str(args.evidence_view or "").strip(),
        min_active_score=float(args.min_active_score),
        min_margin=float(args.min_margin),
        phrase_control_mode=str(args.phrase_control_mode or "").strip(),
        active_rescue_mode=str(args.active_rescue_mode or "").strip(),
        soft_min_active_scores=_parse_float_grid(args.soft_active_grid),
        soft_min_margins=_parse_float_grid(args.soft_margin_grid),
        soft_false_positive_budgets=_parse_int_grid(args.soft_false_positive_budgets),
        window_tokens=max(0, int(args.window_tokens)),
        mask_token=str(args.mask_token or "").strip() or "___",
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_sentence_veto_ladder_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
