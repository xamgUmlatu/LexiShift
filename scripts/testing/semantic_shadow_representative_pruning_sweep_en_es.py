#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
CORE_ROOT = PROJECT_ROOT / "core"
for candidate in (str(SCRIPT_ROOT), str(CORE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    REPRESENTATIVE_PRUNING_MODES,
    build_benchmark_shadow_targets,
)
from semantic_shadow_seed_compare_en_es import (  # noqa: E402
    DEFAULT_BENCHMARK_JSON,
    DEFAULT_DATASET_PATH,
    build_seed_compare_report,
    load_benchmark_dataset_payload,
)

DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_shadow_representative_pruning_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_shadow_representative_pruning_sweep_en_es_latest.md"
)
DEFAULT_MODE_IDS = (
    "benchmark_reviewed",
    "rulegen_top3_plus_forward_gloss",
    "rulegen_all_plus_forward_gloss",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep representative-pruning modes on top of the en-es shadow support-score "
            "policy against the reviewed overlap proxy."
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
        "--forward-seed-max-words",
        type=int,
        default=1,
        help="Maximum word count for forward-gloss-derived trigger seeds.",
    )
    parser.add_argument(
        "--mode-ids",
        default=",".join(DEFAULT_MODE_IDS),
        help="Comma-separated seed modes to evaluate.",
    )
    parser.add_argument(
        "--support-score-values",
        default="3,4,5",
        help="Comma-separated support-score thresholds.",
    )
    parser.add_argument(
        "--max-promoted-values",
        default="1,2,3",
        help="Comma-separated values for max promoted shadows.",
    )
    parser.add_argument(
        "--pruning-modes",
        default=",".join(REPRESENTATIVE_PRUNING_MODES),
        help="Comma-separated representative-pruning modes.",
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


def _parse_mode_ids(value: str) -> list[str]:
    parsed = [item.strip() for item in str(value or "").split(",") if item.strip()]
    if not parsed:
        raise ValueError("At least one mode id is required.")
    return parsed


def _parse_int_csv(value: str) -> list[int]:
    parsed: list[int] = []
    for raw_item in str(value or "").split(","):
        text = raw_item.strip()
        if not text:
            continue
        parsed.append(max(1, int(text)))
    if not parsed:
        raise ValueError("At least one integer value is required.")
    return parsed


def _parse_pruning_modes(value: str) -> list[str]:
    parsed = [item.strip() for item in str(value or "").split(",") if item.strip()]
    if not parsed:
        raise ValueError("At least one pruning mode is required.")
    for mode in parsed:
        if mode not in REPRESENTATIVE_PRUNING_MODES:
            raise ValueError(
                f"Unsupported pruning mode: {mode!r}; expected one of {REPRESENTATIVE_PRUNING_MODES!r}"
            )
    return parsed


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _load_benchmark_targets(dataset_payload: Mapping[str, object]):
    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, Sequence) or isinstance(raw_cases, (str, bytes)):
        raise ValueError("Benchmark dataset is missing a `cases` list.")
    return build_benchmark_shadow_targets(
        [dict(case) for case in raw_cases if isinstance(case, Mapping)]
    )


def build_representative_pruning_sweep_report(
    *,
    benchmark_dataset: Path,
    benchmark_json: Path,
    data_root: Path,
    translation_dict: Path | None,
    reverse_translation_dict: Path | None,
    forward_seed_max_words: int,
    mode_ids: Sequence[str],
    support_score_values: Sequence[int],
    max_promoted_values: Sequence[int],
    pruning_modes: Sequence[str],
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dataset_payload = load_benchmark_dataset_payload(benchmark_dataset)
    benchmark_targets = _load_benchmark_targets(dataset_payload)
    benchmark_report = json.loads(benchmark_json.read_text(encoding="utf-8"))
    helper_paths = build_helper_paths(Path(data_root))
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=translation_dict,
        reverse_translation_dict_path=reverse_translation_dict,
    )
    compare_report = build_seed_compare_report(
        dataset_payload=dataset_payload,
        benchmark_report=benchmark_report,
        data_root=Path(data_root),
        forward_pack=forward_pack,
        reverse_pack=reverse_pack,
        forward_seed_max_words=forward_seed_max_words,
    )
    seed_modes = compare_report.get("seed_modes")
    if not isinstance(seed_modes, Mapping):
        return {
            "schema_version": 1,
            "pair": "en-es",
            "generated_at": generated_at,
            "status": "seed_modes_unavailable",
            "rows": [],
            "best_rows_by_mode": {},
        }

    rows: list[dict[str, object]] = []
    for mode_id in mode_ids:
        mode_payload = seed_modes.get(mode_id)
        if not isinstance(mode_payload, Mapping):
            continue
        inventory = mode_payload.get("inventory")
        if not isinstance(inventory, Mapping):
            continue
        for pruning_mode in pruning_modes:
            for support_score_min in support_score_values:
                for max_promoted in max_promoted_values:
                    evaluation = evaluate_shadow_inventory_against_benchmark_overlap_gold(
                        inventory=inventory,
                        benchmark_targets=benchmark_targets,
                        policies=("support_score_v1",),
                        support_score_min=float(support_score_min),
                        support_score_max_promoted=int(max_promoted),
                        support_representative_pruning_mode=pruning_mode,
                    )
                    policies = evaluation.get("policies")
                    if not isinstance(policies, Mapping):
                        continue
                    support_policy = policies.get("support_score_v1")
                    if not isinstance(support_policy, Mapping):
                        continue
                    summary = support_policy.get("summary")
                    candidate_pool = evaluation.get("candidate_pool_summary")
                    if not isinstance(summary, Mapping) or not isinstance(candidate_pool, Mapping):
                        continue
                    rows.append(
                        {
                            "mode_id": mode_id,
                            "pruning_mode": pruning_mode,
                            "support_score_min": float(support_score_min),
                            "max_promoted_shadows": int(max_promoted),
                            "candidate_pool_trigger_recall": candidate_pool.get(
                                "candidate_pool_trigger_recall"
                            ),
                            "candidate_precision": summary.get("candidate_precision"),
                            "candidate_recall": summary.get("candidate_recall"),
                            "candidate_f1": summary.get("candidate_f1"),
                            "gold_trigger_hit_rate": summary.get("gold_trigger_hit_rate"),
                            "overblocking_rate": summary.get("overblocking_rate"),
                        }
                    )

    best_rows_by_mode: dict[str, dict[str, object]] = {}
    for mode_id in mode_ids:
        mode_rows = [row for row in rows if str(row.get("mode_id") or "") == mode_id]
        if not mode_rows:
            continue
        best_rows_by_mode[mode_id] = sorted(
            mode_rows,
            key=lambda row: (
                -float(row.get("candidate_recall") or 0.0),
                -float(row.get("candidate_precision") or 0.0),
                float(row.get("overblocking_rate") or 1.0),
                float(row.get("support_score_min") or 0.0),
                float(row.get("max_promoted_shadows") or 0.0),
            ),
        )[0]

    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": str(compare_report.get("status") or "unknown"),
        "forward_seed_max_words": int(forward_seed_max_words),
        "mode_ids": list(mode_ids),
        "support_score_values": [int(value) for value in support_score_values],
        "max_promoted_values": [int(value) for value in max_promoted_values],
        "pruning_modes": list(pruning_modes),
        "rows": rows,
        "best_rows_by_mode": best_rows_by_mode,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Representative-Pruning Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Forward seed max words: `{report.get('forward_seed_max_words', '')}`",
        (
            "- Sweep meaning: keep seed generation fixed per mode, keep support scoring fixed, "
            "and vary only the representative-pruning mode plus the support-score operating point."
        ),
    ]
    rows = report.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "",
            "## Rows",
            "| Mode | Pruning | Min Score | Max Promoted | Precision | Recall | F1 | Gold Hit | Overblocking |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("mode_id", "")),
                    str(row.get("pruning_mode", "")),
                    str(row.get("support_score_min", "")),
                    str(row.get("max_promoted_shadows", "")),
                    _render_rate(row.get("candidate_precision")),
                    _render_rate(row.get("candidate_recall")),
                    _render_rate(row.get("candidate_f1")),
                    _render_rate(row.get("gold_trigger_hit_rate")),
                    _render_rate(row.get("overblocking_rate")),
                ]
            )
            + " |"
        )

    best_rows = report.get("best_rows_by_mode")
    if isinstance(best_rows, Mapping) and best_rows:
        lines.extend(["", "## Best Rows By Mode"])
        for mode_id, row in best_rows.items():
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                f"`{mode_id}` best row: pruning `{row.get('pruning_mode')}`, "
                f"`min_score={row.get('support_score_min')}`, "
                f"`max_promoted={row.get('max_promoted_shadows')}` -> "
                f"precision `{_render_rate(row.get('candidate_precision'))}`, "
                f"recall `{_render_rate(row.get('candidate_recall'))}`, "
                f"overblocking `{_render_rate(row.get('overblocking_rate'))}`"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    report = build_representative_pruning_sweep_report(
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        data_root=args.data_root,
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        forward_seed_max_words=max(1, int(args.forward_seed_max_words)),
        mode_ids=_parse_mode_ids(args.mode_ids),
        support_score_values=_parse_int_csv(args.support_score_values),
        max_promoted_values=_parse_int_csv(args.max_promoted_values),
        pruning_modes=_parse_pruning_modes(args.pruning_modes),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
