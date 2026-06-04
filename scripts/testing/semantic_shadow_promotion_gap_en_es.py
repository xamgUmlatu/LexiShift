#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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

from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    _resolve_promoted_targets_for_policy,
    build_benchmark_trigger_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_support import (  # noqa: E402
    build_shadow_candidate_support_details,
)
from semantic_shadow_experiment_support import (  # noqa: E402
    build_en_es_seed_mode_payloads,
    build_inventory_for_seed_targets,
    build_trigger_row_metadata_from_cases,
    load_en_es_shadow_experiment_resources,
    load_reverse_records_by_source_for_seed_modes,
)

DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_promotion_gap_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_promotion_gap_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose en-es semantic-shadow promotion misses under a concrete "
            "seed mode and support-score setting."
        )
    )
    parser.add_argument(
        "--seed-mode",
        default="rulegen_top3_plus_forward_gloss_plus_neighbor_borrow",
        help="Seed mode to inspect.",
    )
    parser.add_argument(
        "--forward-seed-max-words",
        type=int,
        default=1,
        help="Forward gloss fragment max word count.",
    )
    parser.add_argument(
        "--include-neighbor-borrow-seed-modes",
        action="store_true",
        default=True,
        help="Load neighbor-borrow seed modes.",
    )
    parser.add_argument(
        "--policy",
        default="support_score_v1",
        help="Promotion policy to evaluate.",
    )
    parser.add_argument(
        "--support-score-min",
        type=float,
        default=5.0,
        help="Support-score promotion threshold.",
    )
    parser.add_argument(
        "--support-score-max-promoted",
        type=int,
        default=2,
        help="Maximum promoted shadows per trigger row.",
    )
    parser.add_argument(
        "--support-score-weights-json",
        default="",
        help=(
            "Optional JSON object string with shadow support weight overrides, "
            "for example '{\"multi_source_candidate_support\": 1.5}'."
        ),
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Output JSON path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Output Markdown path.",
    )
    return parser.parse_args()


def _as_sequence(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _reason_signature(reasons: Sequence[object]) -> str:
    normalized = [str(reason or "").strip() for reason in reasons if str(reason or "").strip()]
    return "+".join(normalized) if normalized else "none"


def _build_lookup(inventory: Mapping[str, object]) -> dict[tuple[str, str], Mapping[str, object]]:
    lookup: dict[tuple[str, str], Mapping[str, object]] = {}
    for target_row in _as_sequence(inventory.get("targets")):
        target = str(target_row.get("target") or "").strip()
        if not target:
            continue
        for entry in _as_sequence(target_row.get("trigger_entries")):
            trigger = str(entry.get("trigger") or "").strip()
            if trigger:
                lookup[(target, trigger)] = entry
    return lookup


def _round_score(value: object) -> str:
    if not isinstance(value, (float, int)):
        return "n/a"
    return f"{float(value):.1f}"


def build_report(
    *,
    seed_mode: str,
    forward_seed_max_words: int,
    include_neighbor_borrow_seed_modes: bool,
    policy: str,
    support_score_min: float,
    support_score_max_promoted: int,
    support_score_weights: Mapping[str, object] | None = None,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    resources = load_en_es_shadow_experiment_resources()
    seed_mode_payloads = build_en_es_seed_mode_payloads(
        resources,
        forward_seed_max_words=max(1, int(forward_seed_max_words)),
        include_neighbor_borrow_seed_modes=bool(include_neighbor_borrow_seed_modes),
    )
    payload = seed_mode_payloads.get(seed_mode)
    if payload is None:
        raise ValueError(f"Unknown en-es seed mode: {seed_mode!r}")
    reverse_records_by_source = load_reverse_records_by_source_for_seed_modes(
        resources,
        tuple(seed_mode_payloads.values()),
    )
    inventory = build_inventory_for_seed_targets(
        resources,
        seed_targets=payload.seed_targets,
        reverse_records_by_source=reverse_records_by_source,
        promotion_policy=policy,
    )
    inventory_lookup = _build_lookup(inventory)
    gold_rows = build_benchmark_trigger_overlap_gold(resources.benchmark_targets)
    row_metadata = build_trigger_row_metadata_from_cases(resources.cases)

    promotion_miss_rows: list[dict[str, object]] = []
    candidate_missing_rows: list[dict[str, object]] = []
    score_histogram: Counter[str] = Counter()
    reason_signature_counts: Counter[str] = Counter()
    semantic_family_counts: Counter[str] = Counter()
    total_gold_trigger_rows = 0
    hit_rows = 0

    for (target, trigger), gold_shadow_targets in sorted(gold_rows.items()):
        gold_set = {value for value in gold_shadow_targets if value}
        if not gold_set:
            continue
        total_gold_trigger_rows += 1
        entry = inventory_lookup.get((target, trigger), {})
        active_candidates = _as_sequence(entry.get("active_candidates"))
        active_profile_fallback = (
            entry.get("active_profile_fallback")
            if isinstance(entry.get("active_profile_fallback"), Mapping)
            else None
        )
        shadow_candidates = _as_sequence(entry.get("shadow_candidates"))
        mined_targets = {
            str(candidate.get("target") or "").strip()
            for candidate in shadow_candidates
            if str(candidate.get("target") or "").strip()
        }
        promoted_targets = _resolve_promoted_targets_for_policy(
            policy=policy,
            gold_shadow_targets=gold_set,
            shadow_candidates=shadow_candidates,
            active_candidates=active_candidates,
            active_profile_fallback=active_profile_fallback,
            support_score_min=float(support_score_min),
            support_score_max_promoted=max(1, int(support_score_max_promoted)),
            support_frequency_representative_bonus=0.0,
            support_frequency_representative_top_k=0,
            support_frequency_similarity_weight=0.0,
            support_frequency_similarity_tau=0.15,
            support_representative_pruning_mode="off",
            support_score_weights=support_score_weights,
        )
        if set(promoted_targets) & gold_set:
            hit_rows += 1
            continue
        metadata = row_metadata.get((target, trigger), {})
        semantic_families = metadata.get("slice_dimensions", {}).get("semantic_family", [])
        family_label = (
            semantic_families[0]
            if isinstance(semantic_families, Sequence)
            and not isinstance(semantic_families, (str, bytes))
            and semantic_families
            else "unknown"
        )
        scored_gold_candidates: list[dict[str, object]] = []
        for candidate in shadow_candidates:
            candidate_target = str(candidate.get("target") or "").strip()
            if candidate_target not in gold_set:
                continue
            support = build_shadow_candidate_support_details(
                candidate=candidate,
                active_candidates=active_candidates,
                active_profile_pos=str((active_profile_fallback or {}).get("canonical_pos") or ""),
                active_profile_support=bool(
                    str((active_profile_fallback or {}).get("canonical_pos") or "").strip()
                ),
                score_weights=support_score_weights,
            )
            support_score = float(support.get("support_score") or 0.0)
            score_histogram[_round_score(support_score)] += 1
            signature = _reason_signature(support.get("promotion_reasons", ()))
            reason_signature_counts[signature] += 1
            scored_gold_candidates.append(
                {
                    "target": candidate_target,
                    "canonical_pos": str(candidate.get("canonical_pos") or "").strip(),
                    "support_score": support_score,
                    "support_gap_to_threshold": float(support_score_min) - support_score,
                    "same_pos_as_active": bool(support.get("same_pos_as_active")),
                    "promotion_reasons": list(support.get("promotion_reasons", ())),
                    "support_score_breakdown": dict(
                        support.get("support_score_breakdown")
                        if isinstance(support.get("support_score_breakdown"), Mapping)
                        else {}
                    ),
                }
            )
        if scored_gold_candidates:
            semantic_family_counts[family_label] += 1
            best_gold_candidate = max(
                scored_gold_candidates,
                key=lambda item: (
                    float(item.get("support_score") or 0.0),
                    item.get("target", ""),
                ),
            )
            promotion_miss_rows.append(
                {
                    "target": target,
                    "trigger": trigger,
                    "gold_shadow_targets": sorted(gold_set),
                    "promoted_targets": list(promoted_targets),
                    "semantic_family": family_label,
                    "active_candidate_count": len(active_candidates),
                    "best_gold_candidate": best_gold_candidate,
                    "gold_candidates": scored_gold_candidates,
                }
            )
            continue
        candidate_missing_rows.append(
            {
                "target": target,
                "trigger": trigger,
                "gold_shadow_targets": sorted(gold_set),
                "semantic_family": family_label,
                "active_candidate_count": len(active_candidates),
                "mined_shadow_targets": sorted(mined_targets),
            }
        )

    promotion_miss_rows.sort(
        key=lambda row: (
            float(row.get("best_gold_candidate", {}).get("support_gap_to_threshold") or 0.0),
            row.get("target", ""),
            row.get("trigger", ""),
        )
    )
    candidate_missing_rows.sort(
        key=lambda row: (
            row.get("semantic_family", ""),
            row.get("target", ""),
            row.get("trigger", ""),
        )
    )
    return {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "ok",
        "seed_mode": seed_mode,
        "policy": policy,
        "forward_seed_max_words": int(forward_seed_max_words),
        "support_score_min": float(support_score_min),
        "support_score_max_promoted": int(support_score_max_promoted),
        "support_score_weights": dict(support_score_weights or {}),
        "summary": {
            "gold_trigger_rows": total_gold_trigger_rows,
            "hit_rows": hit_rows,
            "promotion_miss_rows": len(promotion_miss_rows),
            "candidate_missing_rows": len(candidate_missing_rows),
        },
        "promotion_miss_score_histogram": dict(
            sorted(score_histogram.items(), key=lambda item: float(item[0]))
        ),
        "promotion_miss_reason_signatures": dict(
            sorted(reason_signature_counts.items(), key=lambda item: (-item[1], item[0]))
        ),
        "promotion_miss_semantic_families": dict(
            sorted(semantic_family_counts.items(), key=lambda item: (-item[1], item[0]))
        ),
        "promotion_miss_rows": promotion_miss_rows,
        "candidate_missing_rows": candidate_missing_rows,
    }


def _render_rate(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "n/a"
    return f"{(float(numerator) / float(denominator)) * 100:.1f}%"


def _render_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    gold_rows = int(summary.get("gold_trigger_rows") or 0)
    hit_rows = int(summary.get("hit_rows") or 0)
    promotion_miss_rows = int(summary.get("promotion_miss_rows") or 0)
    candidate_missing_rows = int(summary.get("candidate_missing_rows") or 0)
    lines = [
        "# en-es Semantic Shadow Promotion Gap",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Seed mode: `{report.get('seed_mode', '')}`",
        f"- Policy: `{report.get('policy', '')}`",
        f"- Support score min / max promoted: `{report.get('support_score_min', '')}` / `{report.get('support_score_max_promoted', '')}`",
        f"- Gold trigger rows: `{gold_rows}`",
        f"- Rows with promoted gold blocker: `{hit_rows}` (`{_render_rate(hit_rows, gold_rows)}`)",
        f"- Promotion-miss rows: `{promotion_miss_rows}`",
        f"- Candidate-missing rows: `{candidate_missing_rows}`",
    ]
    support_score_weights = report.get("support_score_weights")
    if isinstance(support_score_weights, Mapping) and support_score_weights:
        lines.append(
            "- Support score weights: "
            f"`{json.dumps(support_score_weights, sort_keys=True, ensure_ascii=False)}`"
        )
    histogram = report.get("promotion_miss_score_histogram")
    if isinstance(histogram, Mapping):
        lines.extend(["", "## Promotion-Miss Score Histogram"])
        for score, count in histogram.items():
            lines.append(f"- score `{score}`: `{count}`")
    signatures = report.get("promotion_miss_reason_signatures")
    if isinstance(signatures, Mapping):
        lines.extend(["", "## Promotion-Miss Reason Signatures"])
        for signature, count in list(signatures.items())[:10]:
            lines.append(f"- `{signature}`: `{count}`")
    families = report.get("promotion_miss_semantic_families")
    if isinstance(families, Mapping):
        lines.extend(["", "## Promotion-Miss Semantic Families"])
        for family, count in list(families.items())[:10]:
            lines.append(f"- `{family}`: `{count}`")
    promotion_rows = report.get("promotion_miss_rows")
    if isinstance(promotion_rows, Sequence) and not isinstance(promotion_rows, (str, bytes)):
        lines.extend(["", "## Promotion-Miss Examples"])
        if not promotion_rows:
            lines.append("- None")
        else:
            for row in promotion_rows[:10]:
                if not isinstance(row, Mapping):
                    continue
                best = (
                    row.get("best_gold_candidate")
                    if isinstance(row.get("best_gold_candidate"), Mapping)
                    else {}
                )
                lines.append(
                    f"- `{row.get('target', '')}` / `{row.get('trigger', '')}` -> "
                    f"`{best.get('target', '')}` score=`{best.get('support_score', '')}` "
                    f"gap=`{best.get('support_gap_to_threshold', '')}` "
                    f"family=`{row.get('semantic_family', '')}` "
                    f"reasons={best.get('promotion_reasons', [])}"
                )
    candidate_rows = report.get("candidate_missing_rows")
    if isinstance(candidate_rows, Sequence) and not isinstance(candidate_rows, (str, bytes)):
        lines.extend(["", "## Candidate-Missing Examples"])
        if not candidate_rows:
            lines.append("- None")
        else:
            for row in candidate_rows[:10]:
                if not isinstance(row, Mapping):
                    continue
                lines.append(
                    f"- `{row.get('target', '')}` / `{row.get('trigger', '')}` "
                    f"gold={row.get('gold_shadow_targets', [])} "
                    f"family=`{row.get('semantic_family', '')}`"
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    support_score_weights: Mapping[str, object] | None = None
    if str(args.support_score_weights_json or "").strip():
        parsed_weights = json.loads(str(args.support_score_weights_json))
        if not isinstance(parsed_weights, Mapping):
            raise ValueError("--support-score-weights-json must decode to a JSON object.")
        support_score_weights = parsed_weights
    report = build_report(
        seed_mode=str(args.seed_mode or "").strip(),
        forward_seed_max_words=max(1, int(args.forward_seed_max_words)),
        include_neighbor_borrow_seed_modes=bool(args.include_neighbor_borrow_seed_modes),
        policy=str(args.policy or "support_score_v1").strip(),
        support_score_min=float(args.support_score_min),
        support_score_max_promoted=max(1, int(args.support_score_max_promoted)),
        support_score_weights=support_score_weights,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
