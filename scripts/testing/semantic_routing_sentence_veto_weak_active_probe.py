#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from semantic_routing_sentence_veto_support import (
    DEFAULT_SENTENCE_VETO_DATASET,
    DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_JSON_OUT,
    DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_MARKDOWN_OUT,
    build_sentence_veto_weak_active_probe_report,
    render_sentence_veto_weak_active_probe_markdown,
)


def _parse_float_grid(value: str) -> list[float]:
    normalized = str(value or "").strip()
    if not normalized:
        return []
    return [float(item.strip()) for item in normalized.split(",") if item.strip()]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare bounded runtime alternatives for weak-active-support sentence-veto misses "
            "without changing the shipped runtime policy."
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
        help="Similarity backend id for the probe.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="",
        help="Optional model override for embedding-backed scorers.",
    )
    parser.add_argument(
        "--overlay-primary-margin-floors",
        type=str,
        default="-0.02,-0.03,-0.04,-0.05",
        help="Comma-separated primary-margin floors for the simulated rescue overlay.",
    )
    parser.add_argument(
        "--overlay-backup-margin-floor",
        type=float,
        default=0.02,
        help="Backup margin floor required for the simulated rescue overlay.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_SENTENCE_VETO_WEAK_ACTIVE_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_sentence_veto_weak_active_probe_report(
        dataset_path=args.dataset,
        scorer_id=str(args.scorer or "").strip(),
        model_name=str(args.model_name or "").strip() or None,
        overlay_primary_margin_floors=_parse_float_grid(args.overlay_primary_margin_floors),
        overlay_backup_margin_floor=float(args.overlay_backup_margin_floor),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_sentence_veto_weak_active_probe_markdown(report),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
