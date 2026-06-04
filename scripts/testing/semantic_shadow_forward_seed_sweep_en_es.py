#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from semantic_shadow_seed_compare_en_es import (  # noqa: E402
    DEFAULT_BENCHMARK_JSON,
    DEFAULT_DATASET_PATH,
    build_seed_compare_report,
    load_benchmark_dataset_payload,
)


DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_forward_seed_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_forward_seed_sweep_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep the maximum word count for forward-gloss-derived automatic trigger seeds "
            "in the en-es shadow-seeding compare."
        )
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
        help="Optional explicit forward translation pack path for en-es.",
    )
    parser.add_argument(
        "--reverse-translation-dict",
        type=Path,
        default=None,
        help="Optional explicit reverse translation pack path for en-es.",
    )
    parser.add_argument(
        "--forward-seed-max-words-values",
        default="1,2,3,4,5",
        help="Comma-separated integer sweep values for forward-seed maximum word count.",
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


def _parse_int_csv(value: str) -> list[int]:
    parsed: list[int] = []
    for raw_item in str(value or "").split(","):
        text = raw_item.strip()
        if not text:
            continue
        parsed.append(max(1, int(text)))
    if not parsed:
        raise ValueError("At least one forward-seed max-words value is required.")
    return parsed


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def build_forward_seed_sweep_report(
    *,
    benchmark_dataset: Path,
    benchmark_json: Path,
    data_root: Path,
    translation_dict: Path | None,
    reverse_translation_dict: Path | None,
    forward_seed_max_words_values: Sequence[int],
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dataset_payload = load_benchmark_dataset_payload(benchmark_dataset)
    benchmark_report = json.loads(benchmark_json.read_text(encoding="utf-8"))
    helper_paths = build_helper_paths(Path(data_root))
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=translation_dict,
        reverse_translation_dict_path=reverse_translation_dict,
    )

    sweep_rows: list[dict[str, object]] = []
    for max_words in forward_seed_max_words_values:
        compare_report = build_seed_compare_report(
            dataset_payload=dataset_payload,
            benchmark_report=benchmark_report,
            data_root=Path(data_root),
            forward_pack=forward_pack,
            reverse_pack=reverse_pack,
            forward_seed_max_words=max_words,
        )
        for mode_id in ("rulegen_top3_plus_forward_gloss", "rulegen_all_plus_forward_gloss"):
            seed_modes = compare_report.get("seed_modes")
            if not isinstance(seed_modes, dict):
                continue
            mode_payload = seed_modes.get(mode_id)
            if not isinstance(mode_payload, dict):
                continue
            proxy = mode_payload.get("proxy_evaluation")
            if not isinstance(proxy, dict):
                continue
            candidate_pool = proxy.get("candidate_pool_summary")
            policies = proxy.get("policies")
            strict_summary = {}
            if isinstance(policies, dict):
                strict = policies.get("cross_checked_v1")
                if isinstance(strict, dict):
                    summary = strict.get("summary")
                    if isinstance(summary, dict):
                        strict_summary = summary
            sweep_rows.append(
                {
                    "forward_seed_max_words": int(max_words),
                    "mode_id": mode_id,
                    "seed_trigger_count": int(mode_payload.get("seed_trigger_count") or 0),
                    "gold_trigger_inventory_coverage_rate": (
                        candidate_pool.get("gold_trigger_inventory_coverage_rate")
                        if isinstance(candidate_pool, dict)
                        else None
                    ),
                    "candidate_pool_trigger_recall": (
                        candidate_pool.get("candidate_pool_trigger_recall")
                        if isinstance(candidate_pool, dict)
                        else None
                    ),
                    "candidate_precision": strict_summary.get("candidate_precision"),
                    "candidate_recall": strict_summary.get("candidate_recall"),
                    "gold_trigger_hit_rate": strict_summary.get("gold_trigger_hit_rate"),
                    "overblocking_rate": strict_summary.get("overblocking_rate"),
                }
            )

    ranked_rows = sorted(
        sweep_rows,
        key=lambda row: (
            -float(row.get("candidate_recall") or 0.0),
            -float(row.get("candidate_precision") or 0.0),
            float(row.get("overblocking_rate") or 1.0),
            float(row.get("seed_trigger_count") or 0.0),
            str(row.get("mode_id") or ""),
        ),
    )
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "benchmark_dataset": str(benchmark_dataset),
        "benchmark_json": str(benchmark_json),
        "forward_seed_max_words_values": list(forward_seed_max_words_values),
        "rows": sweep_rows,
        "best_current_rows": ranked_rows[:4],
    }


def _render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# en-es Forward Seed Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        (
            "- Sweep meaning: keep the shadow miner and strict `cross_checked_v1` promotion "
            "policy fixed, then vary only the maximum word count allowed for "
            "forward-gloss-derived automatic trigger seeds."
        ),
    ]
    rows = report.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "",
            "## Rows",
            "| Max Words | Mode | Seed Triggers | Gold Trigger Coverage | Candidate-Pool Recall | Strict Precision | Strict Recall | Overblocking |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("forward_seed_max_words", "")),
                    str(row.get("mode_id", "")),
                    str(row.get("seed_trigger_count", "")),
                    _render_rate(row.get("gold_trigger_inventory_coverage_rate")),
                    _render_rate(row.get("candidate_pool_trigger_recall")),
                    _render_rate(row.get("candidate_precision")),
                    _render_rate(row.get("candidate_recall")),
                    _render_rate(row.get("overblocking_rate")),
                ]
            )
            + " |"
        )

    best_rows = report.get("best_current_rows")
    if isinstance(best_rows, Sequence) and not isinstance(best_rows, (str, bytes)) and best_rows:
        lines.extend(["", "## Best Current Rows"])
        for row in best_rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- "
                f"`max_words={row.get('forward_seed_max_words')}` / `{row.get('mode_id')}`: "
                f"precision `{_render_rate(row.get('candidate_precision'))}`, "
                f"recall `{_render_rate(row.get('candidate_recall'))}`, "
                f"overblocking `{_render_rate(row.get('overblocking_rate'))}`"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    report = build_forward_seed_sweep_report(
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        data_root=Path(args.data_root),
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        forward_seed_max_words_values=_parse_int_csv(args.forward_seed_max_words_values),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
