#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.helper.translation_packs import TranslationPackRef  # noqa: E402
from lexishift_core.resources.dict_loaders import (  # noqa: E402
    load_translation_gloss_records_by_translation_ordered,
    load_translation_gloss_records_ordered,
)
from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    REFERENCE_SHADOW_POLICY_MODES,
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_embedding_bridge import (  # noqa: E402
    DEFAULT_EMBEDDING_BRIDGE_MODEL,
    DEFAULT_EMBEDDING_BRIDGE_TOP_K,
    build_embedding_bridge_neighbor_index,
    build_target_embedding_bridge_profiles,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    DEFAULT_FORWARD_SEED_MAX_WORDS,
    SHADOW_PROMOTION_POLICIES,
    BenchmarkShadowTarget,
    augment_shadow_targets_with_forward_gloss_triggers,
    build_benchmark_shadow_targets,
    build_en_es_shadow_inventory,
    build_rulegen_shadow_targets,
)
from lexishift_core.rulegen.semantic_shadow_seed_borrowing import (  # noqa: E402
    DEFAULT_NEIGHBOR_BORROW_MIN_SIMILARITY,
    DEFAULT_NEIGHBOR_BORROW_MIN_REVERSE_TARGET_COUNT,
    DEFAULT_NEIGHBOR_BORROW_MAX_TRIGGERS,
    augment_shadow_targets_with_neighbor_borrowed_triggers,
)
from rulegen_benchmark_dataset import load_benchmark_dataset_payload  # noqa: E402


DEFAULT_DATASET_PATH = (
    PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases" / "en_es.json"
)
DEFAULT_BENCHMARK_JSON = (
    PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_seed_compare_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_seed_compare_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare en-es shadow-mining quality when the miner is seeded from reviewed "
            "benchmark triggers versus rulegen best-run sources."
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
        help="Maximum word count for forward-gloss-derived automatic trigger seeds.",
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


def _build_pack_record(pack: TranslationPackRef | None) -> dict[str, object] | None:
    if pack is None:
        return None
    return {
        "path": str(pack.path),
        "exists": pack.path.exists(),
        "provider": pack.provider,
        "pack_id": pack.pack_id,
        "direction": pack.direction,
    }


def _collect_cases(dataset_payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, Sequence) or isinstance(raw_cases, (str, bytes)):
        raise ValueError("Benchmark dataset is missing a `cases` list.")
    return [dict(case) for case in raw_cases if isinstance(case, Mapping)]


def _load_best_run_case_results(
    benchmark_report: Mapping[str, object],
) -> list[Mapping[str, object]]:
    pairs = benchmark_report.get("pairs")
    if not isinstance(pairs, Mapping):
        raise ValueError("Benchmark report is missing `pairs`.")
    en_es = pairs.get("en-es")
    if not isinstance(en_es, Mapping):
        raise ValueError("Benchmark report is missing `pairs.en-es`.")
    best_run = en_es.get("best_run")
    if not isinstance(best_run, Mapping):
        raise ValueError("Benchmark report is missing `pairs.en-es.best_run`.")
    case_results = best_run.get("case_results")
    if not isinstance(case_results, Sequence) or isinstance(case_results, (str, bytes)):
        raise ValueError("Benchmark report best_run is missing `case_results`.")
    return [dict(case) for case in case_results if isinstance(case, Mapping)]


def _collect_reviewed_triggers(targets: Sequence[BenchmarkShadowTarget]) -> list[str]:
    seen: dict[str, None] = {}
    for target in targets:
        for trigger in target.reviewed_triggers:
            seen.setdefault(trigger, None)
    return list(seen.keys())


def _build_mode_payload(
    *,
    mode_id: str,
    seed_targets: Sequence[BenchmarkShadowTarget],
    gold_targets: Sequence[BenchmarkShadowTarget],
    forward_records_by_target: Mapping[str, Sequence[object]],
    reverse_records_by_source: Mapping[str, Sequence[object]],
    target_reverse_records_by_target: Mapping[str, Sequence[object]],
    forward_provider: str,
    reverse_provider: str,
) -> dict[str, object]:
    inventory = build_en_es_shadow_inventory(
        benchmark_targets=seed_targets,
        forward_records_by_target=forward_records_by_target,
        reverse_records_by_source=reverse_records_by_source,
        target_reverse_records_by_target=target_reverse_records_by_target,
        forward_provider=forward_provider,
        reverse_provider=reverse_provider,
    )
    proxy_evaluation = evaluate_shadow_inventory_against_benchmark_overlap_gold(
        inventory=inventory,
        benchmark_targets=gold_targets,
        policies=SHADOW_PROMOTION_POLICIES + REFERENCE_SHADOW_POLICY_MODES,
    )
    return {
        "mode_id": mode_id,
        "seed_target_count": len(seed_targets),
        "seed_trigger_count": sum(len(target.reviewed_triggers) for target in seed_targets),
        "seed_targets": [target.target for target in seed_targets],
        "inventory": inventory,
        "proxy_evaluation": proxy_evaluation,
    }


def build_seed_compare_report(
    *,
    dataset_payload: Mapping[str, object],
    benchmark_report: Mapping[str, object],
    data_root: Path,
    forward_pack: TranslationPackRef | None,
    reverse_pack: TranslationPackRef | None,
    forward_seed_max_words: int = DEFAULT_FORWARD_SEED_MAX_WORDS,
    include_neighbor_borrow_seed_modes: bool = False,
    neighbor_borrow_model: str = DEFAULT_EMBEDDING_BRIDGE_MODEL,
    neighbor_borrow_min_similarity: float = DEFAULT_NEIGHBOR_BORROW_MIN_SIMILARITY,
    neighbor_borrow_top_k: int = DEFAULT_EMBEDDING_BRIDGE_TOP_K,
    neighbor_borrow_min_reverse_target_count: int = DEFAULT_NEIGHBOR_BORROW_MIN_REVERSE_TARGET_COUNT,
    neighbor_borrow_max_triggers_per_target: int = DEFAULT_NEIGHBOR_BORROW_MAX_TRIGGERS,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    gold_targets = build_benchmark_shadow_targets(_collect_cases(dataset_payload))
    best_run_case_results = _load_best_run_case_results(benchmark_report)
    target_filter = [target.target for target in gold_targets]
    rulegen_top3_targets = build_rulegen_shadow_targets(
        best_run_case_results,
        targets=target_filter,
        source_field="top3_sources",
    )
    rulegen_all_targets = build_rulegen_shadow_targets(
        best_run_case_results,
        targets=target_filter,
        source_field="all_sources",
    )

    missing_resources: list[str] = []
    if forward_pack is None or not forward_pack.path.exists():
        missing_resources.append("forward_translation_pack")
    if reverse_pack is None or not reverse_pack.path.exists():
        missing_resources.append("reverse_translation_pack")
    report: dict[str, object] = {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "missing_resources" if missing_resources else "ok",
        "gold_reference": {
            "path": str(Path(str(dataset_payload.get("source_files", [DEFAULT_DATASET_PATH])[0]))),
            "target_count": len(gold_targets),
            "reviewed_trigger_count": sum(len(target.reviewed_triggers) for target in gold_targets),
        },
        "benchmark_report": {
            "path": "",
            "best_run_case_count": len(best_run_case_results),
        },
        "resource_status": {
            "data_root": str(data_root),
            "forward_pack": _build_pack_record(forward_pack),
            "reverse_pack": _build_pack_record(reverse_pack),
            "missing_resources": missing_resources,
        },
        "seed_modes": {},
    }
    if missing_resources:
        return report

    all_targets = sorted(
        {target.target for target in gold_targets if str(target.target or "").strip()}
    )
    forward_records_by_target = load_translation_gloss_records_ordered(
        forward_pack.path,
        target_lang="en",
        headwords=all_targets,
    )
    target_reverse_records_by_target = load_translation_gloss_records_by_translation_ordered(
        reverse_pack.path,
        translations=all_targets,
    )
    top3_plus_forward_gloss = augment_shadow_targets_with_forward_gloss_triggers(
        rulegen_top3_targets,
        forward_records_by_target=forward_records_by_target,
        max_words=forward_seed_max_words,
    )
    all_plus_forward_gloss = augment_shadow_targets_with_forward_gloss_triggers(
        rulegen_all_targets,
        forward_records_by_target=forward_records_by_target,
        max_words=forward_seed_max_words,
    )
    seed_modes = {
        "benchmark_reviewed": gold_targets,
        "rulegen_top3_sources": rulegen_top3_targets,
        "rulegen_all_sources": rulegen_all_targets,
        "rulegen_top3_plus_forward_gloss": top3_plus_forward_gloss,
        "rulegen_all_plus_forward_gloss": all_plus_forward_gloss,
    }
    reverse_records_by_source = load_translation_gloss_records_ordered(
        reverse_pack.path,
        target_lang="es",
        headwords=sorted(
            {
                trigger
                for seed_targets in seed_modes.values()
                for target in seed_targets
                for trigger in target.reviewed_triggers
                if str(trigger or "").strip()
            }
        ),
    )
    if include_neighbor_borrow_seed_modes:
        target_profiles = build_target_embedding_bridge_profiles(
            benchmark_targets=gold_targets,
            forward_records_by_target=forward_records_by_target,
            target_reverse_records_by_target=target_reverse_records_by_target,
        )
        neighbor_index = build_embedding_bridge_neighbor_index(
            target_profiles=target_profiles,
            model_name=neighbor_borrow_model,
            min_similarity=float(neighbor_borrow_min_similarity),
            top_k=int(neighbor_borrow_top_k),
        )
        seed_modes["rulegen_top3_plus_forward_gloss_plus_neighbor_borrow"] = (
            augment_shadow_targets_with_neighbor_borrowed_triggers(
                top3_plus_forward_gloss,
                neighbor_index=neighbor_index,
                reverse_records_by_source=reverse_records_by_source,
                min_reverse_target_count=int(neighbor_borrow_min_reverse_target_count),
                max_borrowed_triggers_per_target=int(neighbor_borrow_max_triggers_per_target),
                max_words=int(forward_seed_max_words),
            )
        )
        seed_modes["rulegen_all_plus_forward_gloss_plus_neighbor_borrow"] = (
            augment_shadow_targets_with_neighbor_borrowed_triggers(
                all_plus_forward_gloss,
                neighbor_index=neighbor_index,
                reverse_records_by_source=reverse_records_by_source,
                min_reverse_target_count=int(neighbor_borrow_min_reverse_target_count),
                max_borrowed_triggers_per_target=int(neighbor_borrow_max_triggers_per_target),
                max_words=int(forward_seed_max_words),
            )
        )
    for mode_id, seed_targets in seed_modes.items():
        report["seed_modes"][mode_id] = _build_mode_payload(
            mode_id=mode_id,
            seed_targets=seed_targets,
            gold_targets=gold_targets,
            forward_records_by_target=forward_records_by_target,
            reverse_records_by_source=reverse_records_by_source,
            target_reverse_records_by_target=target_reverse_records_by_target,
            forward_provider=forward_pack.provider,
            reverse_provider=reverse_pack.provider,
        )
    return report


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Seed Comparison",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        "- Comparison meaning: keep the miner, promotion policy, and lower-bound gold proxy fixed; swap only the seed trigger source.",
        "- Goal: estimate how much current shadow quality depends on reviewed benchmark triggers versus rulegen-emitted sources.",
    ]
    gold_reference = report.get("gold_reference")
    if isinstance(gold_reference, Mapping):
        lines.extend(
            [
                f"- Gold targets: `{gold_reference.get('target_count', 0)}`",
                f"- Gold reviewed triggers: `{gold_reference.get('reviewed_trigger_count', 0)}`",
            ]
        )
    resource_status = report.get("resource_status")
    if isinstance(resource_status, Mapping):
        missing = resource_status.get("missing_resources")
        if isinstance(missing, Sequence) and not isinstance(missing, (str, bytes)) and missing:
            lines.extend(["", "## Missing Resources", *(f"- `{item}`" for item in missing)])
            return "\n".join(lines) + "\n"

    seed_modes = report.get("seed_modes")
    if not isinstance(seed_modes, Mapping):
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "",
            "## Strict Policy Snapshot (`cross_checked_v1`)",
            "| Seed Mode | Seed Triggers | Inventory Coverage | Gold Trigger Coverage | Candidate Recall | Candidate Precision | Overblocking |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for mode_id in (
        "benchmark_reviewed",
        "rulegen_top3_sources",
        "rulegen_all_sources",
        "rulegen_top3_plus_forward_gloss",
        "rulegen_all_plus_forward_gloss",
    ):
        payload = seed_modes.get(mode_id)
        if not isinstance(payload, Mapping):
            continue
        proxy = payload.get("proxy_evaluation")
        if not isinstance(proxy, Mapping):
            continue
        candidate_pool = proxy.get("candidate_pool_summary")
        policies = proxy.get("policies")
        strict_summary = {}
        if isinstance(policies, Mapping):
            strict = policies.get("cross_checked_v1")
            if isinstance(strict, Mapping):
                strict_summary = (
                    strict.get("summary") if isinstance(strict.get("summary"), Mapping) else {}
                )
        seed_trigger_count = int(payload.get("seed_trigger_count") or 0)
        lines.append(
            "| "
            + " | ".join(
                [
                    mode_id,
                    str(seed_trigger_count),
                    _render_rate(
                        candidate_pool.get("inventory_entry_coverage_rate")
                        if isinstance(candidate_pool, Mapping)
                        else None
                    ),
                    _render_rate(
                        candidate_pool.get("gold_trigger_inventory_coverage_rate")
                        if isinstance(candidate_pool, Mapping)
                        else None
                    ),
                    _render_rate(strict_summary.get("candidate_recall")),
                    _render_rate(strict_summary.get("candidate_precision")),
                    _render_rate(strict_summary.get("overblocking_rate")),
                ]
            )
            + " |"
        )

    for mode_id in (
        "benchmark_reviewed",
        "rulegen_top3_sources",
        "rulegen_all_sources",
        "rulegen_top3_plus_forward_gloss",
        "rulegen_all_plus_forward_gloss",
    ):
        payload = seed_modes.get(mode_id)
        if not isinstance(payload, Mapping):
            continue
        proxy = payload.get("proxy_evaluation")
        if not isinstance(proxy, Mapping):
            continue
        candidate_pool = proxy.get("candidate_pool_summary")
        policies = proxy.get("policies")
        strict_summary = {}
        if isinstance(policies, Mapping):
            strict = policies.get("cross_checked_v1")
            if isinstance(strict, Mapping):
                strict_summary = (
                    strict.get("summary") if isinstance(strict.get("summary"), Mapping) else {}
                )
        lines.extend(
            [
                "",
                f"## {mode_id}",
                f"- Seed targets: `{payload.get('seed_target_count', 0)}`",
                f"- Seed triggers: `{payload.get('seed_trigger_count', 0)}`",
            ]
        )
        if isinstance(candidate_pool, Mapping):
            lines.extend(
                [
                    f"- Inventory coverage: `{candidate_pool.get('trigger_rows_with_inventory_entry', 0)} / {candidate_pool.get('trigger_rows_total', 0)}` (`{_render_rate(candidate_pool.get('inventory_entry_coverage_rate'))}`)",
                    f"- Gold trigger coverage: `{candidate_pool.get('gold_trigger_rows_with_inventory_entry', 0)} / {candidate_pool.get('gold_trigger_rows', 0)}` (`{_render_rate(candidate_pool.get('gold_trigger_inventory_coverage_rate'))}`)",
                    f"- Gold rows with active support: `{candidate_pool.get('gold_trigger_rows_with_active_candidates', 0)} / {candidate_pool.get('gold_trigger_rows', 0)}` (`{_render_rate(candidate_pool.get('gold_trigger_active_support_rate'))}`)",
                    f"- Candidate-pool overlap recall: `{_render_rate(candidate_pool.get('candidate_pool_trigger_recall'))}`",
                ]
            )
        if strict_summary:
            lines.extend(
                [
                    f"- `cross_checked_v1` candidate precision: `{_render_rate(strict_summary.get('candidate_precision'))}`",
                    f"- `cross_checked_v1` candidate recall: `{_render_rate(strict_summary.get('candidate_recall'))}`",
                    f"- `cross_checked_v1` gold hit rate: `{_render_rate(strict_summary.get('gold_trigger_hit_rate'))}`",
                    f"- `cross_checked_v1` overblocking rate: `{_render_rate(strict_summary.get('overblocking_rate'))}`",
                ]
            )
        if isinstance(policies, Mapping):
            strict = policies.get("cross_checked_v1")
            if isinstance(strict, Mapping):
                underblocked = strict.get("sample_underblocked_rows")
                if (
                    isinstance(underblocked, Sequence)
                    and not isinstance(underblocked, (str, bytes))
                    and underblocked
                ):
                    lines.append("- Sample underblocked rows:")
                    for row in underblocked[:6]:
                        if not isinstance(row, Mapping):
                            continue
                        lines.append(
                            "  - "
                            f"`{row.get('target', '')}` / `{row.get('trigger', '')}` "
                            f"gold={row.get('gold_shadow_targets', [])} "
                            f"promoted={row.get('promoted_targets', [])}"
                        )

    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    dataset_payload = load_benchmark_dataset_payload(args.benchmark_dataset)
    benchmark_report = json.loads(args.benchmark_json.read_text(encoding="utf-8"))
    helper_paths = build_helper_paths(Path(args.data_root))
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=args.translation_dict,
        reverse_translation_dict_path=args.reverse_translation_dict,
    )
    report = build_seed_compare_report(
        dataset_payload=dataset_payload,
        benchmark_report=benchmark_report,
        data_root=Path(args.data_root),
        forward_pack=forward_pack,
        reverse_pack=reverse_pack,
        forward_seed_max_words=args.forward_seed_max_words,
    )
    benchmark_payload = report.get("benchmark_report")
    if isinstance(benchmark_payload, dict):
        benchmark_payload["path"] = str(args.benchmark_json)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
