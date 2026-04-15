#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


DEFAULT_OBJECTIVE_WEIGHTS = {
    "top1_accuracy": 100.0,
    "top3_recall": 60.0,
    "forbidden_top1_rate": 120.0,
    "forbidden_any_rate": 80.0,
    "avg_rules_per_target": 6.0,
    "variant_top1_rate": 10.0,
}


@dataclass(frozen=True)
class LoadedProfile:
    label: str
    benchmark_path: Path
    triage_path: Path | None
    pair: str
    best_run: Mapping[str, object]
    triage_items: Sequence[Mapping[str, object]]


def _parse_labeled_path(value: str) -> tuple[str, Path]:
    label, sep, raw_path = value.partition("=")
    if not sep or not label.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError(f"Expected LABEL=PATH entry, got: {value!r}")
    return label.strip(), Path(raw_path.strip())


def _load_json(path: Path) -> Mapping[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_profiles(
    *,
    profile_entries: Sequence[tuple[str, Path]],
    triage_by_label: Mapping[str, Path],
    pair: str | None,
) -> list[LoadedProfile]:
    loaded: list[LoadedProfile] = []
    resolved_pair = pair or ""
    for label, benchmark_path in profile_entries:
        benchmark_payload = _load_json(benchmark_path)
        pairs_payload = benchmark_payload.get("pairs", {})
        if not isinstance(pairs_payload, Mapping):
            raise ValueError(f"Invalid benchmark payload at {benchmark_path}")
        profile_pair = resolved_pair
        if not profile_pair:
            pair_names = [str(name) for name in pairs_payload.keys()]
            if len(pair_names) != 1:
                raise ValueError(
                    f"Benchmark payload at {benchmark_path} contains multiple pairs; use --pair"
                )
            profile_pair = pair_names[0]
            resolved_pair = profile_pair
        pair_payload = pairs_payload.get(profile_pair)
        if not isinstance(pair_payload, Mapping):
            raise ValueError(f"Pair {profile_pair!r} missing from {benchmark_path}")
        best_run = pair_payload.get("best_run")
        if not isinstance(best_run, Mapping):
            raise ValueError(f"best_run missing from {benchmark_path}")

        triage_path = triage_by_label.get(label)
        triage_items: Sequence[Mapping[str, object]] = ()
        if triage_path is not None:
            triage_payload = _load_json(triage_path)
            raw_items = triage_payload.get("items", ())
            if isinstance(raw_items, Sequence):
                triage_items = tuple(item for item in raw_items if isinstance(item, Mapping))

        loaded.append(
            LoadedProfile(
                label=label,
                benchmark_path=benchmark_path,
                triage_path=triage_path,
                pair=profile_pair,
                best_run=best_run,
                triage_items=triage_items,
            )
        )
    return loaded


def _case_objective_contribution(case_payload: Mapping[str, object]) -> float:
    return (
        (DEFAULT_OBJECTIVE_WEIGHTS["top1_accuracy"] if case_payload.get("top1_correct") else 0.0)
        + (
            DEFAULT_OBJECTIVE_WEIGHTS["top3_recall"]
            if case_payload.get("top3_contains_expected")
            else 0.0
        )
        - (
            DEFAULT_OBJECTIVE_WEIGHTS["forbidden_top1_rate"]
            if case_payload.get("top1_forbidden")
            else 0.0
        )
        - (
            DEFAULT_OBJECTIVE_WEIGHTS["forbidden_any_rate"]
            if case_payload.get("forbidden_any_present")
            else 0.0
        )
        - (
            float(case_payload.get("rule_count") or 0)
            * DEFAULT_OBJECTIVE_WEIGHTS["avg_rules_per_target"]
        )
        - (
            DEFAULT_OBJECTIVE_WEIGHTS["variant_top1_rate"]
            if case_payload.get("top1_is_variant")
            else 0.0
        )
    )


def _bucket_count(value: object, *, cutoffs: Sequence[int]) -> str:
    numeric = int(value or 0)
    lower = 0
    for cutoff in cutoffs:
        if numeric <= cutoff:
            return f"{lower}-{cutoff}"
        lower = cutoff + 1
    return f"{cutoffs[-1] + 1}+"


def _trait_regions(trait_summary: Mapping[str, object]) -> list[tuple[str, str]]:
    router_input = trait_summary.get("router_input", {})
    if not isinstance(router_input, Mapping):
        return []
    regions = [
        (
            "candidate_row_count_band",
            _bucket_count(router_input.get("candidate_row_count", 0), cutoffs=(4, 9, 14)),
        ),
        (
            "candidate_definition_bucket_band",
            _bucket_count(
                router_input.get("candidate_definition_bucket_count", 0),
                cutoffs=(2, 4, 7),
            ),
        ),
        (
            "candidate_reverse_hit_band",
            _bucket_count(
                router_input.get("candidate_reverse_hit_count", 0),
                cutoffs=(0, 2, 5),
            ),
        ),
        (
            "candidate_phrase_pressure",
            "phrase-heavy"
            if int(router_input.get("candidate_phrase_count", 0) or 0) > 0
            else "phrase-light",
        ),
        (
            "candidate_variant_pressure",
            "variant-present"
            if int(router_input.get("candidate_variant_count", 0) or 0) > 0
            else "variant-absent",
        ),
    ]
    family_names = router_input.get("candidate_family_names", ())
    if isinstance(family_names, Sequence):
        for family_name in family_names:
            family_text = str(family_name or "").strip()
            if family_text:
                regions.append(("candidate_family", family_text))
    return regions


def _profile_case_map(
    profiles: Sequence[LoadedProfile],
) -> dict[str, dict[str, Mapping[str, object]]]:
    case_map: dict[str, dict[str, Mapping[str, object]]] = {}
    for profile in profiles:
        case_results = profile.best_run.get("case_results", ())
        if not isinstance(case_results, Sequence):
            continue
        for case_payload in case_results:
            if not isinstance(case_payload, Mapping):
                continue
            case_id = str(case_payload.get("case_id") or "").strip()
            if case_id:
                case_map.setdefault(case_id, {})[profile.label] = case_payload
    return case_map


def build_profile_bank_analysis(
    *,
    profiles: Sequence[LoadedProfile],
) -> dict[str, object]:
    if not profiles:
        raise ValueError("No profiles supplied")
    pair = profiles[0].pair
    labels = [profile.label for profile in profiles]
    case_map = _profile_case_map(profiles)

    top1_diff_case_ids: list[str] = []
    top3_diff_case_ids: list[str] = []
    rule_count_diff_case_ids: list[str] = []
    trait_region_cases: dict[tuple[str, str], list[str]] = defaultdict(list)
    trait_region_scores: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for case_id, profile_cases in sorted(case_map.items()):
        if any(label not in profile_cases for label in labels):
            continue
        top1_values = [str(profile_cases[label].get("top1_source") or "") for label in labels]
        top3_values = [bool(profile_cases[label].get("top3_contains_expected")) for label in labels]
        rule_counts = [int(profile_cases[label].get("rule_count") or 0) for label in labels]
        if len(set(top1_values)) > 1:
            top1_diff_case_ids.append(case_id)
        if len(set(top3_values)) > 1:
            top3_diff_case_ids.append(case_id)
        if len(set(rule_counts)) > 1:
            rule_count_diff_case_ids.append(case_id)

        canonical_traits = profile_cases[labels[0]].get("trait_summary", {})
        if isinstance(canonical_traits, Mapping):
            for region_key in _trait_regions(canonical_traits):
                if case_id not in trait_region_cases[region_key]:
                    trait_region_cases[region_key].append(case_id)
                for label in labels:
                    trait_region_scores[region_key][label].append(
                        _case_objective_contribution(profile_cases[label])
                    )

    regions_payload: list[dict[str, object]] = []
    for (trait_name, trait_value), case_ids in sorted(trait_region_cases.items()):
        average_score_by_profile = {
            label: (
                sum(scores) / len(scores)
                if (scores := trait_region_scores[(trait_name, trait_value)].get(label, []))
                else 0.0
            )
            for label in labels
        }
        best_score = max(average_score_by_profile.values()) if average_score_by_profile else 0.0
        best_profiles = sorted(
            label
            for label, score in average_score_by_profile.items()
            if abs(score - best_score) < 1e-9
        )
        regions_payload.append(
            {
                "trait": trait_name,
                "value": trait_value,
                "case_count": len(case_ids),
                "case_ids": case_ids,
                "avg_case_objective_by_profile": average_score_by_profile,
                "best_profiles": best_profiles,
            }
        )

    profile_payload = {}
    for profile in profiles:
        summary = profile.best_run.get("summary", {})
        triage_case_ids = [str(item.get("case_id") or "") for item in profile.triage_items]
        profile_payload[profile.label] = {
            "benchmark_json": str(profile.benchmark_path),
            "triage_json": str(profile.triage_path) if profile.triage_path else None,
            "config_label": str(profile.best_run.get("config_label") or ""),
            "summary": summary,
            "triage_case_ids": triage_case_ids,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pair": pair,
        "profile_labels": labels,
        "profiles": profile_payload,
        "comparison": {
            "top1_diff_case_ids": top1_diff_case_ids,
            "top3_diff_case_ids": top3_diff_case_ids,
            "rule_count_diff_case_ids": rule_count_diff_case_ids,
        },
        "trait_regions": regions_payload,
    }


def render_markdown_report(analysis: Mapping[str, object]) -> str:
    labels = tuple(str(label) for label in analysis.get("profile_labels", ()))
    profiles = analysis.get("profiles", {})
    comparison = analysis.get("comparison", {})
    trait_regions = analysis.get("trait_regions", ())

    lines = [
        f"# Rulegen Profile Bank Analysis ({analysis.get('pair')})",
        "",
        f"- Generated at: `{analysis.get('generated_at')}`",
        f"- Profiles: {', '.join(f'`{label}`' for label in labels)}",
        "",
        "## Aggregate Metrics",
        "",
        "| Profile | Objective | Top1 | Top3 | ForbidAny | AvgRules | Triage | Config |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for label in labels:
        profile_payload = profiles.get(label, {})
        summary = profile_payload.get("summary", {})
        triage_count = len(profile_payload.get("triage_case_ids", ()))
        lines.append(
            "| "
            + f"{label} | "
            + f"{float(summary.get('objective_score') or 0.0):.3f} | "
            + f"{100.0 * float(summary.get('top1_accuracy') or 0.0):.2f}% | "
            + f"{100.0 * float(summary.get('top3_recall') or 0.0):.2f}% | "
            + f"{100.0 * float(summary.get('forbidden_any_rate') or 0.0):.2f}% | "
            + f"{float(summary.get('avg_rules_per_target') or 0.0):.2f} | "
            + f"{triage_count} | "
            + f"`{profile_payload.get('config_label') or ''}` |"
        )

    top1_diff_case_ids = comparison.get("top1_diff_case_ids", ())
    top3_diff_case_ids = comparison.get("top3_diff_case_ids", ())
    rule_count_diff_case_ids = comparison.get("rule_count_diff_case_ids", ())
    lines.extend(
        [
            "",
            "## Main Reading",
            "",
            f"- Top-1 winner differences across the frozen profile bank: **{len(top1_diff_case_ids)} cases**.",
            f"- Top-3 coverage differences across the frozen profile bank: **{len(top3_diff_case_ids)} cases**.",
            f"- Rule-count differences across the frozen profile bank: **{len(rule_count_diff_case_ids)} cases**.",
            "",
            "## Trait Regions",
            "",
        ]
    )

    sorted_regions = sorted(
        (region for region in trait_regions if isinstance(region, Mapping)),
        key=lambda region: (
            -int(region.get("case_count") or 0),
            str(region.get("trait") or ""),
            str(region.get("value") or ""),
        ),
    )
    for region in sorted_regions:
        if int(region.get("case_count") or 0) < 2:
            continue
        averages = region.get("avg_case_objective_by_profile", {})
        if not isinstance(averages, Mapping):
            continue
        average_text = ", ".join(
            f"`{label}`={float(averages.get(label) or 0.0):.2f}" for label in labels
        )
        best_profiles = ", ".join(f"`{label}`" for label in region.get("best_profiles", ()))
        case_ids = ", ".join(f"`{case_id}`" for case_id in region.get("case_ids", ()))
        lines.append(f"- `{region.get('trait')}` = `{region.get('value')}`")
        lines.append(f"  case_count={int(region.get('case_count') or 0)} best={best_profiles}")
        lines.append(f"  avg_case_objective: {average_text}")
        lines.append(f"  cases: {case_ids}")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare a frozen rulegen profile bank across benchmark artifacts."
    )
    parser.add_argument(
        "--profile-json",
        dest="profile_jsons",
        action="append",
        required=True,
        help="Profile benchmark artifact in LABEL=PATH form. Repeat for each profile.",
    )
    parser.add_argument(
        "--triage-json",
        dest="triage_jsons",
        action="append",
        default=[],
        help="Optional triage artifact in LABEL=PATH form. Repeat for matching profiles.",
    )
    parser.add_argument(
        "--pair",
        default=None,
        help="Benchmark pair to compare. Required if benchmark artifacts contain multiple pairs.",
    )
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    args = parser.parse_args()

    profile_entries = [_parse_labeled_path(value) for value in args.profile_jsons]
    triage_by_label = dict(_parse_labeled_path(value) for value in args.triage_jsons)

    loaded_profiles = _load_profiles(
        profile_entries=profile_entries,
        triage_by_label=triage_by_label,
        pair=args.pair,
    )
    analysis = build_profile_bank_analysis(profiles=loaded_profiles)

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_out is not None:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(
            render_markdown_report(analysis),
            encoding="utf-8",
        )

    print(f"pair: {analysis['pair']}")
    print(f"profiles: {len(analysis['profile_labels'])}")
    print("top1_diff_cases: " f"{len(analysis['comparison']['top1_diff_case_ids'])}")
    print("top3_diff_cases: " f"{len(analysis['comparison']['top3_diff_case_ids'])}")
    print("rule_count_diff_cases: " f"{len(analysis['comparison']['rule_count_diff_case_ids'])}")
    if args.json_out is not None:
        print(f"json_out: {args.json_out}")
    if args.markdown_out is not None:
        print(f"markdown_out: {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
