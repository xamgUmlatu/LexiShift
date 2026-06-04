#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RunMatrixRow:
    label: str
    lane: str
    source: str
    benchmark_json: Path
    triage_json: Path
    selector: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _select_best_run(pair_payload: Mapping[str, Any]) -> dict[str, Any]:
    best = pair_payload.get("best_run")
    if not isinstance(best, dict):
        raise ValueError("pair payload missing best_run")
    return best


def _select_best_matching_run(
    pair_payload: Mapping[str, Any],
    *,
    predicate: Callable[[Mapping[str, Any]], bool],
) -> dict[str, Any]:
    runs = pair_payload.get("runs")
    if not isinstance(runs, Sequence):
        raise ValueError("pair payload missing runs")
    matches = [run for run in runs if isinstance(run, dict) and predicate(run)]
    if not matches:
        raise ValueError("no matching run found for selector")

    def _sort_key(run: Mapping[str, Any]) -> tuple[float, float, float, float, float]:
        summary = run.get("summary")
        if not isinstance(summary, Mapping):
            return (float("-inf"), float("-inf"), float("-inf"), float("-inf"), float("-inf"))
        return (
            float(summary.get("objective_score") or 0.0),
            float(summary.get("top1_accuracy") or 0.0),
            float(summary.get("top3_recall") or 0.0),
            -float(summary.get("forbidden_top1_rate") or 0.0),
            -float(summary.get("forbidden_any_rate") or 0.0),
        )

    return max(matches, key=_sort_key)


def _extract_run(
    *,
    benchmark_json: Path,
    pair: str,
    selector: str,
) -> dict[str, Any]:
    payload = _load_json(benchmark_json)
    pair_payload = payload.get("pairs")
    if not isinstance(pair_payload, Mapping):
        raise ValueError(f"invalid benchmark payload: {benchmark_json}")
    details = pair_payload.get(pair)
    if not isinstance(details, Mapping):
        raise ValueError(f"pair '{pair}' missing from benchmark: {benchmark_json}")
    if selector == "best":
        return _select_best_run(details)
    if selector == "best_rev_on_no_cap":
        return _select_best_matching_run(
            details,
            predicate=lambda run: (
                _run_flag(run, "reverse_check_enabled") is True
                and _run_optional_int(run, "max_rules_per_target") is None
            ),
        )
    if selector == "best_rev_off":
        return _select_best_matching_run(
            details,
            predicate=lambda run: _run_flag(run, "reverse_check_enabled") is False,
        )
    raise ValueError(f"unsupported selector: {selector}")


def _run_config(run: Mapping[str, Any]) -> Mapping[str, Any]:
    config = run.get("config")
    if not isinstance(config, Mapping):
        raise ValueError("run missing config")
    return config


def _run_summary(run: Mapping[str, Any]) -> Mapping[str, Any]:
    summary = run.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("run missing summary")
    return summary


def _run_flag(run: Mapping[str, Any], key: str) -> Optional[bool]:
    config = _run_config(run)
    value = config.get(key)
    if isinstance(value, bool):
        return value
    return None


def _run_optional_int(run: Mapping[str, Any], key: str) -> Optional[int]:
    config = _run_config(run)
    value = config.get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _triage_info(path: Path) -> tuple[int, str]:
    payload = _load_json(path)
    items = payload.get("items")
    if not isinstance(items, Sequence):
        return 0, "-"
    failures: list[str] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        case_id = str(item.get("case_id") or "").strip()
        target = str(item.get("target") or "").strip()
        top1 = str(item.get("top1_source") or "").strip()
        if case_id:
            failures.append(f"{target or case_id}:{top1 or '?'}")
    return len(failures), ", ".join(failures) if failures else "-"


def _format_percent(value: object) -> str:
    try:
        return f"{100.0 * float(value):.2f}%"
    except (TypeError, ValueError):
        return "-"


def _format_optional_int(value: object) -> str:
    if value is None:
        return "none"
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return "-"


def render_markdown(
    *,
    rows: Sequence[RunMatrixRow],
    pair: str,
) -> str:
    lines = [
        f"# Reverse-Check Run Matrix ({pair})",
        "",
        "Purpose:",
        "- Keep the important reverse-check parameter sets and their benchmark outcomes in one durable table.",
        "- Separate the canonical baseline lane from reverse-specific experiment lanes.",
        "",
        "| Label | Lane | Selector | Rev | Match | Near | NearMax | FarPenalty | MissPenalty | XAmb | XSpec | MaxRules | Top1 | Top3 | ForbidTop1 | ForbidAny | AvgRules | Triage | Remaining Failures |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        run = _extract_run(
            benchmark_json=row.benchmark_json,
            pair=pair,
            selector=row.selector,
        )
        config = _run_config(run)
        summary = _run_summary(run)
        triage_count, failures = _triage_info(row.triage_json)
        lines.append(
            "| "
            f"{row.label} | "
            f"{row.lane} | "
            f"{row.source} / {row.selector} | "
            f"{'on' if bool(config.get('reverse_check_enabled')) else 'off'} | "
            f"{float(config.get('reverse_check_match_bonus') or 0.0):.2f} | "
            f"{float(config.get('reverse_check_near_bonus') or 0.0):.2f} | "
            f"{int(config.get('reverse_check_near_rank_max') or 0)} | "
            f"{float(config.get('reverse_check_far_hit_penalty') or 0.0):.2f} | "
            f"{float(config.get('reverse_check_miss_penalty') or 0.0):.2f} | "
            f"{_format_exact_hit_ambiguity(config)} | "
            f"{float(config.get('reverse_check_exact_hit_specificity_bonus') or 0.0):.2f} | "
            f"{_format_optional_int(config.get('max_rules_per_target'))} | "
            f"{_format_percent(summary.get('top1_accuracy'))} | "
            f"{_format_percent(summary.get('top3_recall'))} | "
            f"{_format_percent(summary.get('forbidden_top1_rate'))} | "
            f"{_format_percent(summary.get('forbidden_any_rate'))} | "
            f"{float(summary.get('avg_rules_per_target') or 0.0):.2f} | "
            f"{triage_count} | "
            f"{failures} |"
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- `canonical latest` is the required default benchmark lane and may now land on either `rev=off` or `rev=on`, depending on the current best run.",
            "- `reverse latest` is the named reverse-check lane exposed via `npm --prefix scripts run quality:rulegen:reverse:en-es`.",
            "- `reverse latest (no cap)` keeps the reverse lane parameters but selects the best `max_rules_per_target=none` run for comparison.",
        ]
    )
    return "\n".join(lines) + "\n"


def _format_exact_hit_ambiguity(config: Mapping[str, Any]) -> str:
    threshold = int(config.get("reverse_check_exact_hit_ambiguity_threshold") or 0)
    penalty = float(config.get("reverse_check_exact_hit_ambiguity_penalty") or 0.0)
    if threshold <= 0 or penalty <= 0.0:
        return "off"
    return f"{threshold}:{penalty:.2f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the durable reverse-check run matrix.")
    parser.add_argument("--pair", default="en-es")
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "rulegen_reverse_en_es_run_matrix_latest.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pair = str(args.pair).strip().lower()
    rows = [
        RunMatrixRow(
            label="Canonical Latest",
            lane="baseline",
            source="canonical latest",
            benchmark_json=PROJECT_ROOT
            / "docs"
            / "test_outputs"
            / "rulegen_benchmark_en_es_latest.json",
            triage_json=PROJECT_ROOT
            / "docs"
            / "test_outputs"
            / "rulegen_benchmark_triage_latest.json",
            selector="best",
        ),
        RunMatrixRow(
            label="Far-Hit Experiment",
            lane="dated experiment",
            source="2026-03-13 experiment",
            benchmark_json=PROJECT_ROOT
            / "docs"
            / "test_outputs"
            / "experiments"
            / "rulegen_en_es_reverse_check_20260313"
            / "rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json",
            triage_json=PROJECT_ROOT
            / "docs"
            / "test_outputs"
            / "experiments"
            / "rulegen_en_es_reverse_check_20260313"
            / "rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.json",
            selector="best",
        ),
        RunMatrixRow(
            label="Reverse Latest",
            lane="named reverse lane",
            source="reverse latest",
            benchmark_json=PROJECT_ROOT
            / "docs"
            / "test_outputs"
            / "rulegen_benchmark_en_es_reverse_latest.json",
            triage_json=PROJECT_ROOT
            / "docs"
            / "test_outputs"
            / "rulegen_benchmark_triage_en_es_reverse_latest.json",
            selector="best",
        ),
        RunMatrixRow(
            label="Reverse Latest (No Cap)",
            lane="named reverse lane",
            source="reverse latest",
            benchmark_json=PROJECT_ROOT
            / "docs"
            / "test_outputs"
            / "rulegen_benchmark_en_es_reverse_latest.json",
            triage_json=PROJECT_ROOT
            / "docs"
            / "test_outputs"
            / "rulegen_benchmark_triage_en_es_reverse_latest.json",
            selector="best_rev_on_no_cap",
        ),
    ]
    markdown = render_markdown(rows=rows, pair=pair)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(markdown, encoding="utf-8")
    print(f"markdown_out: {args.markdown_out}")


if __name__ == "__main__":
    main()
