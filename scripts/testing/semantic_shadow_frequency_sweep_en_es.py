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

from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.resources.dict_loaders import load_translation_gloss_records_ordered  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_frequency import open_shadow_frequency_lookup  # noqa: E402
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    build_benchmark_shadow_targets,
    build_en_es_shadow_inventory,
    filter_shadow_targets_by_trigger_support,
)
from semantic_shadow_trigger_support_sweep_en_es import (  # noqa: E402
    DEFAULT_BENCHMARK_JSON,
    DEFAULT_DATASET_PATH,
    _build_source_mode_payloads,
    _collect_cases,
    _load_best_run_case_results,
    _parse_mode_ids,
    _render_rate,
    _safe_f1,
)
from rulegen_benchmark_dataset import load_benchmark_dataset_payload  # noqa: E402


DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_frequency_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_frequency_sweep_en_es_latest.md"
)
DEFAULT_MODE_IDS = ("benchmark_reviewed", "rulegen_top3_plus_forward_gloss")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep Spanish target-frequency features on top of the current en-es shadow "
            "support score, focusing on similarity between active and shadow frequency bands."
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
        "--trigger-support-score-min",
        type=float,
        default=0.0,
        help="Fixed trigger-support threshold before mining; `0` disables trigger filtering.",
    )
    parser.add_argument(
        "--shadow-support-score-min",
        type=float,
        default=5.0,
        help="Fixed base shadow support-score threshold.",
    )
    parser.add_argument(
        "--shadow-max-promoted",
        type=int,
        default=2,
        help="Fixed maximum number of promoted shadows.",
    )
    parser.add_argument(
        "--frequency-bonus-values",
        default="0",
        help="Comma-separated representative bonus values to sweep.",
    )
    parser.add_argument(
        "--frequency-top-k-values",
        default="0",
        help="Comma-separated top-k representative counts to sweep.",
    )
    parser.add_argument(
        "--frequency-similarity-weight-values",
        default="0,0.1,0.25,0.5,1.0",
        help="Comma-separated active-vs-shadow frequency similarity weights to sweep.",
    )
    parser.add_argument(
        "--frequency-similarity-tau-values",
        default="0.05,0.1,0.15,0.25,0.4",
        help="Comma-separated tolerance values for active-vs-shadow frequency similarity.",
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
        parsed.append(max(0, int(text)))
    if not parsed:
        raise ValueError("At least one integer value is required.")
    return parsed


def _parse_float_csv(value: str) -> list[float]:
    parsed: list[float] = []
    for raw_item in str(value or "").split(","):
        text = raw_item.strip()
        if not text:
            continue
        parsed.append(max(0.0, float(text)))
    if not parsed:
        raise ValueError("At least one float value is required.")
    return parsed


def _evaluate_seed_targets(
    *,
    seed_targets,
    gold_targets,
    forward_records_by_target,
    reverse_records_by_source,
    forward_provider: str,
    reverse_provider: str,
    shadow_support_score_min: float,
    shadow_max_promoted: int,
    frequency_bonus: float,
    frequency_top_k: int,
    frequency_similarity_weight: float,
    frequency_similarity_tau: float,
    frequency_lookup,
) -> dict[str, object]:
    inventory = build_en_es_shadow_inventory(
        benchmark_targets=seed_targets,
        forward_records_by_target=forward_records_by_target,
        reverse_records_by_source=reverse_records_by_source,
        forward_provider=forward_provider,
        reverse_provider=reverse_provider,
        frequency_lookup=frequency_lookup,
    )
    evaluation = evaluate_shadow_inventory_against_benchmark_overlap_gold(
        inventory=inventory,
        benchmark_targets=gold_targets,
        policies=("support_score_v1",),
        support_score_min=shadow_support_score_min,
        support_score_max_promoted=shadow_max_promoted,
        support_frequency_representative_bonus=frequency_bonus,
        support_frequency_representative_top_k=frequency_top_k,
        support_frequency_similarity_weight=frequency_similarity_weight,
        support_frequency_similarity_tau=frequency_similarity_tau,
    )
    summary = {}
    policies = evaluation.get("policies")
    if isinstance(policies, Mapping):
        support_score = policies.get("support_score_v1")
        if isinstance(support_score, Mapping):
            candidate_summary = support_score.get("summary")
            if isinstance(candidate_summary, Mapping):
                summary = dict(candidate_summary)
    candidate_pool = evaluation.get("candidate_pool_summary")
    return {
        "inventory": inventory,
        "evaluation": evaluation,
        "summary": summary,
        "candidate_pool_summary": candidate_pool if isinstance(candidate_pool, Mapping) else {},
    }


def build_frequency_sweep_report(
    *,
    benchmark_dataset: Path,
    benchmark_json: Path,
    data_root: Path,
    translation_dict: Path | None,
    reverse_translation_dict: Path | None,
    forward_seed_max_words: int,
    mode_ids: Sequence[str],
    trigger_support_score_min: float,
    shadow_support_score_min: float,
    shadow_max_promoted: int,
    frequency_bonus_values: Sequence[float],
    frequency_top_k_values: Sequence[int],
    frequency_similarity_weight_values: Sequence[float],
    frequency_similarity_tau_values: Sequence[float],
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dataset_payload = load_benchmark_dataset_payload(benchmark_dataset)
    benchmark_report = json.loads(benchmark_json.read_text(encoding="utf-8"))
    gold_targets = build_benchmark_shadow_targets(_collect_cases(dataset_payload))
    benchmark_target_map = {target.target: target for target in gold_targets}
    best_run_case_results = _load_best_run_case_results(benchmark_report)
    helper_paths = build_helper_paths(Path(data_root))
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=translation_dict,
        reverse_translation_dict_path=reverse_translation_dict,
    )
    all_targets = sorted(
        {target.target for target in gold_targets if str(target.target or "").strip()}
    )
    forward_records_by_target = load_translation_gloss_records_ordered(
        forward_pack.path,
        target_lang="en",
        headwords=all_targets,
    )
    source_mode_payloads = _build_source_mode_payloads(
        gold_targets=gold_targets,
        best_run_case_results=best_run_case_results,
        forward_records_by_target=forward_records_by_target,
        reverse_records_by_source={},
        forward_provider=forward_pack.provider,
        reverse_provider=reverse_pack.provider,
        forward_seed_max_words=forward_seed_max_words,
    )
    source_mode_payloads["benchmark_reviewed"] = {
        "seed_targets": gold_targets,
        "source_targets_by_label": {"benchmark_reviewed": gold_targets},
    }
    all_triggers = sorted(
        {
            trigger
            for mode_payload in source_mode_payloads.values()
            for target in mode_payload["seed_targets"]
            for trigger in target.reviewed_triggers
            if str(trigger or "").strip()
        }
    )
    reverse_records_by_source = load_translation_gloss_records_ordered(
        reverse_pack.path,
        target_lang="es",
        headwords=all_triggers,
    )
    rows: list[dict[str, object]] = []
    best_rows_by_mode: dict[str, dict[str, object]] = {}
    frequency_lookup = open_shadow_frequency_lookup(pair="en-es", helper_paths=helper_paths)
    try:
        for mode_id in mode_ids:
            mode_payload = source_mode_payloads.get(mode_id)
            if not isinstance(mode_payload, Mapping):
                continue
            seed_targets = mode_payload["seed_targets"]
            source_targets_by_label = mode_payload["source_targets_by_label"]
            if mode_id == "benchmark_reviewed" or float(trigger_support_score_min) <= 0.0:
                filtered_targets = list(seed_targets)
            else:
                filtered_targets, _support_rows = filter_shadow_targets_by_trigger_support(
                    seed_targets=seed_targets,
                    source_targets_by_label=source_targets_by_label,
                    forward_records_by_target=forward_records_by_target,
                    reverse_records_by_source=reverse_records_by_source,
                    forward_provider=forward_pack.provider,
                    reverse_provider=reverse_pack.provider,
                    benchmark_target_map=benchmark_target_map,
                    min_score=float(trigger_support_score_min),
                )
            baseline = _evaluate_seed_targets(
                seed_targets=filtered_targets,
                gold_targets=gold_targets,
                forward_records_by_target=forward_records_by_target,
                reverse_records_by_source=reverse_records_by_source,
                forward_provider=forward_pack.provider,
                reverse_provider=reverse_pack.provider,
                shadow_support_score_min=shadow_support_score_min,
                shadow_max_promoted=shadow_max_promoted,
                frequency_bonus=0.0,
                frequency_top_k=0,
                frequency_similarity_weight=0.0,
                frequency_similarity_tau=0.15,
                frequency_lookup=frequency_lookup,
            )
            baseline_summary = baseline["summary"]
            baseline_candidate_pool = baseline["candidate_pool_summary"]
            for frequency_bonus in frequency_bonus_values:
                for frequency_top_k in frequency_top_k_values:
                    for frequency_similarity_weight in frequency_similarity_weight_values:
                        for frequency_similarity_tau in frequency_similarity_tau_values:
                            evaluated = _evaluate_seed_targets(
                                seed_targets=filtered_targets,
                                gold_targets=gold_targets,
                                forward_records_by_target=forward_records_by_target,
                                reverse_records_by_source=reverse_records_by_source,
                                forward_provider=forward_pack.provider,
                                reverse_provider=reverse_pack.provider,
                                shadow_support_score_min=shadow_support_score_min,
                                shadow_max_promoted=shadow_max_promoted,
                                frequency_bonus=float(frequency_bonus),
                                frequency_top_k=int(frequency_top_k),
                                frequency_similarity_weight=float(frequency_similarity_weight),
                                frequency_similarity_tau=float(frequency_similarity_tau),
                                frequency_lookup=frequency_lookup,
                            )
                            summary = evaluated["summary"]
                            candidate_pool = evaluated["candidate_pool_summary"]
                            rows.append(
                                {
                                    "mode_id": mode_id,
                                    "trigger_support_score_min": float(trigger_support_score_min),
                                    "shadow_support_score_min": float(shadow_support_score_min),
                                    "shadow_max_promoted": int(shadow_max_promoted),
                                    "frequency_bonus": float(frequency_bonus),
                                    "frequency_top_k": int(frequency_top_k),
                                    "frequency_similarity_weight": float(
                                        frequency_similarity_weight
                                    ),
                                    "frequency_similarity_tau": float(frequency_similarity_tau),
                                    "candidate_precision": summary.get("candidate_precision"),
                                    "candidate_recall": summary.get("candidate_recall"),
                                    "candidate_f1": _safe_f1(
                                        summary.get("candidate_precision"),
                                        summary.get("candidate_recall"),
                                    ),
                                    "gold_trigger_hit_rate": summary.get("gold_trigger_hit_rate"),
                                    "overblocking_rate": summary.get("overblocking_rate"),
                                    "candidate_pool_trigger_recall": candidate_pool.get(
                                        "candidate_pool_trigger_recall"
                                    ),
                                    "gold_trigger_inventory_coverage_rate": candidate_pool.get(
                                        "gold_trigger_inventory_coverage_rate"
                                    ),
                                    "baseline_precision": baseline_summary.get(
                                        "candidate_precision"
                                    ),
                                    "baseline_recall": baseline_summary.get("candidate_recall"),
                                    "baseline_f1": _safe_f1(
                                        baseline_summary.get("candidate_precision"),
                                        baseline_summary.get("candidate_recall"),
                                    ),
                                    "baseline_overblocking": baseline_summary.get(
                                        "overblocking_rate"
                                    ),
                                    "baseline_candidate_pool_trigger_recall": (
                                        baseline_candidate_pool.get("candidate_pool_trigger_recall")
                                    ),
                                    "frequency_lookup_available": frequency_lookup is not None,
                                    "frequency_pack_id": (
                                        frequency_lookup.pack_id
                                        if frequency_lookup is not None
                                        else ""
                                    ),
                                }
                            )
            mode_rows = [row for row in rows if str(row.get("mode_id") or "") == mode_id]
            if mode_rows:
                best_rows_by_mode[mode_id] = sorted(
                    mode_rows,
                    key=lambda row: (
                        -float(row.get("candidate_f1") or 0.0),
                        -float(row.get("candidate_precision") or 0.0),
                        -float(row.get("candidate_recall") or 0.0),
                        float(row.get("overblocking_rate") or 1.0),
                        float(row.get("frequency_similarity_weight") or 0.0),
                        float(row.get("frequency_similarity_tau") or 0.0),
                        float(row.get("frequency_bonus") or 0.0),
                        float(row.get("frequency_top_k") or 0.0),
                    ),
                )[0]
    finally:
        if frequency_lookup is not None:
            frequency_lookup.close()
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "forward_seed_max_words": int(forward_seed_max_words),
        "trigger_support_score_min": float(trigger_support_score_min),
        "shadow_support_score_min": float(shadow_support_score_min),
        "shadow_max_promoted": int(shadow_max_promoted),
        "mode_ids": list(mode_ids),
        "frequency_bonus_values": [float(value) for value in frequency_bonus_values],
        "frequency_top_k_values": [int(value) for value in frequency_top_k_values],
        "frequency_similarity_weight_values": [
            float(value) for value in frequency_similarity_weight_values
        ],
        "frequency_similarity_tau_values": [
            float(value) for value in frequency_similarity_tau_values
        ],
        "rows": rows,
        "best_rows_by_mode": best_rows_by_mode,
    }


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Frequency Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Forward seed max words: `{report.get('forward_seed_max_words', '')}`",
        f"- Fixed trigger support min: `{report.get('trigger_support_score_min', '')}`",
        (
            "- Fixed shadow support score: "
            f"`min={report.get('shadow_support_score_min', '')}`, "
            f"`max_promoted={report.get('shadow_max_promoted', '')}`"
        ),
        (
            "- Sweep meaning: keep the current lexical source-only pipeline fixed, then add "
            "frequency-based bonuses, especially active-vs-shadow frequency similarity."
        ),
    ]
    rows = report.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "",
            "## Rows",
            "| Mode | Rep Bonus | Top-K | Sim Weight | Sim Tau | Precision | Recall | F1 | Gold Hit | Overblocking | Baseline Precision | Baseline Recall | Baseline F1 | Baseline Overblocking |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
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
                    str(row.get("frequency_bonus", "")),
                    str(row.get("frequency_top_k", "")),
                    str(row.get("frequency_similarity_weight", "")),
                    str(row.get("frequency_similarity_tau", "")),
                    _render_rate(row.get("candidate_precision")),
                    _render_rate(row.get("candidate_recall")),
                    _render_rate(row.get("candidate_f1")),
                    _render_rate(row.get("gold_trigger_hit_rate")),
                    _render_rate(row.get("overblocking_rate")),
                    _render_rate(row.get("baseline_precision")),
                    _render_rate(row.get("baseline_recall")),
                    _render_rate(row.get("baseline_f1")),
                    _render_rate(row.get("baseline_overblocking")),
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
                f"`{mode_id}` with `rep_bonus={row.get('frequency_bonus')}`, "
                f"`top_k={row.get('frequency_top_k')}`, "
                f"`sim_weight={row.get('frequency_similarity_weight')}`, "
                f"`sim_tau={row.get('frequency_similarity_tau')}`: "
                f"precision `{_render_rate(row.get('candidate_precision'))}`, "
                f"recall `{_render_rate(row.get('candidate_recall'))}`, "
                f"F1 `{_render_rate(row.get('candidate_f1'))}`, "
                f"overblocking `{_render_rate(row.get('overblocking_rate'))}`"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    report = build_frequency_sweep_report(
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        data_root=args.data_root,
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        forward_seed_max_words=max(1, int(args.forward_seed_max_words)),
        mode_ids=_parse_mode_ids(args.mode_ids),
        trigger_support_score_min=float(args.trigger_support_score_min),
        shadow_support_score_min=float(args.shadow_support_score_min),
        shadow_max_promoted=max(1, int(args.shadow_max_promoted)),
        frequency_bonus_values=_parse_float_csv(args.frequency_bonus_values),
        frequency_top_k_values=_parse_int_csv(args.frequency_top_k_values),
        frequency_similarity_weight_values=_parse_float_csv(
            args.frequency_similarity_weight_values
        ),
        frequency_similarity_tau_values=_parse_float_csv(args.frequency_similarity_tau_values),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
