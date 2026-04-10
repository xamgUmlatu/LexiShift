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

from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.resources.dict_loaders import (  # noqa: E402
    load_translation_gloss_records_by_translation_ordered,
    load_translation_gloss_records_ordered,
)
from lexishift_core.rulegen.semantic_shadow_embedding_bridge import (  # noqa: E402
    DEFAULT_EMBEDDING_BRIDGE_MODEL,
    augment_inventory_with_embedding_bridge,
    build_embedding_bridge_neighbor_index,
    build_target_embedding_bridge_profiles,
)
from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
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
    / "semantic_shadow_embedding_bridge_sweep_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "semantic_shadow_embedding_bridge_sweep_en_es_latest.md"
)
DEFAULT_MODE_IDS = ("rulegen_top3_plus_forward_gloss", "benchmark_reviewed")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate an embedding-backed shadow bridge for en-es by augmenting the "
            "current shadow inventory only when lexical mining failed to surface any "
            "benchmark-target shadow."
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
        default="4,5",
        help="Comma-separated threshold values for support_score_v1.",
    )
    parser.add_argument(
        "--max-promoted-values",
        default="1,2,3",
        help="Comma-separated values for max promoted shadows.",
    )
    parser.add_argument(
        "--bridge-min-similarity-values",
        default="0.60,0.65,0.70",
        help="Comma-separated embedding bridge similarity thresholds.",
    )
    parser.add_argument(
        "--bridge-top-k-values",
        default="1,2",
        help="Comma-separated top-k values for embedding bridge neighbors.",
    )
    parser.add_argument(
        "--bridge-model",
        default=DEFAULT_EMBEDDING_BRIDGE_MODEL,
        help="Sentence-transformers model name for target-card bridge embeddings.",
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
    parsed = [max(1, int(item.strip())) for item in str(value or "").split(",") if item.strip()]
    if not parsed:
        raise ValueError("At least one integer value is required.")
    return parsed


def _parse_float_csv(value: str) -> list[float]:
    parsed = [float(item.strip()) for item in str(value or "").split(",") if item.strip()]
    if not parsed:
        raise ValueError("At least one float value is required.")
    return parsed


def build_embedding_bridge_sweep_report(
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
    bridge_min_similarity_values: Sequence[float],
    bridge_top_k_values: Sequence[int],
    bridge_model: str,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    dataset_payload = load_benchmark_dataset_payload(benchmark_dataset)
    benchmark_targets = build_benchmark_shadow_targets(dataset_payload["cases"])
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

    target_names = sorted(
        {str(target.target).strip() for target in benchmark_targets if str(target.target).strip()}
    )
    forward_records_by_target = load_translation_gloss_records_ordered(
        forward_pack.path,
        target_lang="en",
        headwords=target_names,
    )
    target_reverse_records_by_target = load_translation_gloss_records_by_translation_ordered(
        reverse_pack.path,
        translations=target_names,
    )
    target_profiles = build_target_embedding_bridge_profiles(
        benchmark_targets=benchmark_targets,
        forward_records_by_target=forward_records_by_target,
        target_reverse_records_by_target=target_reverse_records_by_target,
    )
    full_neighbor_index = build_embedding_bridge_neighbor_index(
        target_profiles=target_profiles,
        model_name=bridge_model,
        min_similarity=min(bridge_min_similarity_values),
        top_k=max(bridge_top_k_values),
    )

    rows: list[dict[str, object]] = []
    for mode_id in mode_ids:
        mode_payload = seed_modes.get(mode_id)
        if not isinstance(mode_payload, Mapping):
            continue
        base_inventory = mode_payload.get("inventory")
        if not isinstance(base_inventory, Mapping):
            continue
        for (
            bridge_mode,
            bridge_min_similarity,
            bridge_top_k,
            neighbor_index,
        ) in _iter_mode_bridge_configs(
            full_neighbor_index=full_neighbor_index,
            bridge_min_similarity_values=bridge_min_similarity_values,
            bridge_top_k_values=bridge_top_k_values,
        ):
            for support_score_min in support_score_values:
                for max_promoted in max_promoted_values:
                    if bridge_mode == "baseline":
                        inventory = base_inventory
                    else:
                        inventory = augment_inventory_with_embedding_bridge(
                            inventory=base_inventory,
                            target_profiles=target_profiles,
                            neighbor_index=neighbor_index,
                            support_score_min_for_backoff=float(support_score_min),
                        )
                    injected_count = _count_embedding_bridge_candidates(inventory)
                    evaluation = evaluate_shadow_inventory_against_benchmark_overlap_gold(
                        inventory=inventory,
                        benchmark_targets=benchmark_targets,
                        policies=("support_score_v1",),
                        support_score_min=float(support_score_min),
                        support_score_max_promoted=int(max_promoted),
                    )
                    support_policy = (
                        evaluation.get("policies", {}).get("support_score_v1", {})
                        if isinstance(evaluation.get("policies"), Mapping)
                        else {}
                    )
                    summary = support_policy.get("summary", {})
                    candidate_pool = evaluation.get("candidate_pool_summary", {})
                    if not isinstance(summary, Mapping) or not isinstance(candidate_pool, Mapping):
                        continue
                    rows.append(
                        {
                            "mode_id": mode_id,
                            "bridge_mode": bridge_mode,
                            "bridge_min_similarity": bridge_min_similarity,
                            "bridge_top_k": bridge_top_k,
                            "bridge_injected_candidate_count": injected_count,
                            "support_score_min": float(support_score_min),
                            "max_promoted_shadows": int(max_promoted),
                            "candidate_pool_trigger_recall": candidate_pool.get(
                                "candidate_pool_trigger_recall"
                            ),
                            "candidate_precision": summary.get("candidate_precision"),
                            "candidate_recall": summary.get("candidate_recall"),
                            "gold_trigger_hit_rate": summary.get("gold_trigger_hit_rate"),
                            "overblocking_rate": summary.get("overblocking_rate"),
                            "underblocked_count": summary.get("gold_trigger_rows_underblocked"),
                            "overblocked_count": summary.get("no_gold_trigger_rows_overblocked"),
                            "sample_underblocked_rows": support_policy.get(
                                "sample_underblocked_rows", []
                            ),
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
                float(row.get("bridge_min_similarity") or 1.0),
            ),
        )[0]
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "bridge_model": bridge_model,
        "rows": rows,
        "best_rows_by_mode": best_rows_by_mode,
    }


def _iter_mode_bridge_configs(
    *,
    full_neighbor_index: Mapping[str, Sequence[Mapping[str, object]]],
    bridge_min_similarity_values: Sequence[float],
    bridge_top_k_values: Sequence[int],
) -> Sequence[tuple[str, float | None, int | None, Mapping[str, Sequence[Mapping[str, object]]]]]:
    rows: list[
        tuple[str, float | None, int | None, Mapping[str, Sequence[Mapping[str, object]]]]
    ] = [("baseline", None, None, {})]
    for min_similarity in bridge_min_similarity_values:
        for top_k in bridge_top_k_values:
            filtered_neighbor_index = {
                target: [
                    dict(neighbor)
                    for neighbor in neighbors
                    if float(neighbor.get("similarity") or 0.0) >= float(min_similarity)
                ][: max(1, int(top_k))]
                for target, neighbors in full_neighbor_index.items()
            }
            rows.append(
                (
                    "embedding_bridge",
                    float(min_similarity),
                    int(top_k),
                    filtered_neighbor_index,
                )
            )
    return rows


def _count_embedding_bridge_candidates(inventory: Mapping[str, object]) -> int:
    total = 0
    targets = inventory.get("targets")
    if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)):
        return total
    for target_row in targets:
        if not isinstance(target_row, Mapping):
            continue
        trigger_entries = target_row.get("trigger_entries")
        if not isinstance(trigger_entries, Sequence) or isinstance(trigger_entries, (str, bytes)):
            continue
        for trigger_entry in trigger_entries:
            if not isinstance(trigger_entry, Mapping):
                continue
            shadow_candidates = trigger_entry.get("shadow_candidates")
            if not isinstance(shadow_candidates, Sequence) or isinstance(
                shadow_candidates, (str, bytes)
            ):
                continue
            for candidate in shadow_candidates:
                if not isinstance(candidate, Mapping):
                    continue
                if "semantic_embedding_bridge" in tuple(candidate.get("candidate_sources") or ()):
                    total += 1
    return total


def _render_rate(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Shadow Embedding Bridge Sweep",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Bridge model: `{report.get('bridge_model', '')}`",
        "- Meaning: keep lexical mining and support-score promotion fixed, then inject a narrow embedding-backed backoff candidate only when lexical mining surfaced no benchmark-target shadow.",
        "",
        "## Best Rows",
        "| Mode | Bridge | Min Sim | Top K | Injected | Support Min | Max Promoted | Precision | Recall | Hit Rate | Overblocking |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    best_rows = report.get("best_rows_by_mode")
    if isinstance(best_rows, Mapping):
        for mode_id, row in sorted(best_rows.items()):
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{mode_id}`",
                        f"`{row.get('bridge_mode', '')}`",
                        (
                            "n/a"
                            if row.get("bridge_min_similarity") is None
                            else f"`{float(row.get('bridge_min_similarity') or 0.0):.2f}`"
                        ),
                        (
                            "n/a"
                            if row.get("bridge_top_k") is None
                            else f"`{int(row.get('bridge_top_k') or 0)}`"
                        ),
                        f"`{int(row.get('bridge_injected_candidate_count') or 0)}`",
                        f"`{float(row.get('support_score_min') or 0.0):.1f}`",
                        f"`{int(row.get('max_promoted_shadows') or 0)}`",
                        _render_rate(row.get("candidate_precision")),
                        _render_rate(row.get("candidate_recall")),
                        _render_rate(row.get("gold_trigger_hit_rate")),
                        _render_rate(row.get("overblocking_rate")),
                    ]
                )
                + " |"
            )
    rows = report.get("rows")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        lines.extend(
            [
                "",
                "## Rows",
                "| Mode | Bridge | Min Sim | Top K | Support Min | Max Promoted | Precision | Recall | Hit Rate | Overblocking | Underblocked |",
                "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in sorted(
            [candidate for candidate in rows if isinstance(candidate, Mapping)],
            key=lambda row: (
                str(row.get("mode_id") or ""),
                str(row.get("bridge_mode") or ""),
                float(row.get("bridge_min_similarity") or -1.0),
                int(row.get("bridge_top_k") or 0),
                float(row.get("support_score_min") or 0.0),
                int(row.get("max_promoted_shadows") or 0),
            ),
        ):
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{row.get('mode_id', '')}`",
                        f"`{row.get('bridge_mode', '')}`",
                        (
                            "n/a"
                            if row.get("bridge_min_similarity") is None
                            else f"`{float(row.get('bridge_min_similarity') or 0.0):.2f}`"
                        ),
                        (
                            "n/a"
                            if row.get("bridge_top_k") is None
                            else f"`{int(row.get('bridge_top_k') or 0)}`"
                        ),
                        f"`{float(row.get('support_score_min') or 0.0):.1f}`",
                        f"`{int(row.get('max_promoted_shadows') or 0)}`",
                        _render_rate(row.get("candidate_precision")),
                        _render_rate(row.get("candidate_recall")),
                        _render_rate(row.get("gold_trigger_hit_rate")),
                        _render_rate(row.get("overblocking_rate")),
                        f"`{int(row.get('underblocked_count') or 0)}`",
                    ]
                )
                + " |"
            )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = _parse_args()
    report = build_embedding_bridge_sweep_report(
        benchmark_dataset=args.benchmark_dataset,
        benchmark_json=args.benchmark_json,
        data_root=args.data_root,
        translation_dict=args.translation_dict,
        reverse_translation_dict=args.reverse_translation_dict,
        forward_seed_max_words=int(args.forward_seed_max_words),
        mode_ids=_parse_mode_ids(args.mode_ids),
        support_score_values=_parse_int_csv(args.support_score_values),
        max_promoted_values=_parse_int_csv(args.max_promoted_values),
        bridge_min_similarity_values=_parse_float_csv(args.bridge_min_similarity_values),
        bridge_top_k_values=_parse_int_csv(args.bridge_top_k_values),
        bridge_model=str(args.bridge_model or "").strip() or DEFAULT_EMBEDDING_BRIDGE_MODEL,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
