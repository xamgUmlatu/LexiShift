from __future__ import annotations

from collections import Counter
from typing import Mapping


def build_chosen_pos_distribution(
    lemma_reports: list[Mapping[str, object]] | tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    canonical_counter: Counter[str] = Counter()
    bucket_counter: Counter[str] = Counter()
    raw_counter: Counter[str] = Counter()
    for row in lemma_reports:
        chosen = _as_mapping(row.get("chosen_pos"))
        if not chosen:
            continue
        canonical_counter.update([str(chosen.get("canonical") or "other")])
        bucket_counter.update([str(chosen.get("bucket") or "other")])
        raw_counter.update([str(chosen.get("raw_pos") or "")])
    return {
        "canonical": [
            {"canonical": canonical, "count": count}
            for canonical, count in canonical_counter.most_common()
        ],
        "buckets": [
            {"bucket": bucket, "count": count} for bucket, count in bucket_counter.most_common()
        ],
        "raw_pos": [
            {"raw_pos": raw_pos, "count": count} for raw_pos, count in raw_counter.most_common(20)
        ],
    }


def build_samples(
    lemma_reports: list[Mapping[str, object]] | tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    unresolved = [
        str(row.get("lemma") or "")
        for row in lemma_reports
        if not bool(row.get("has_any_pos")) and str(row.get("lemma") or "")
    ][:30]
    ambiguous = [
        {
            "lemma": str(row.get("lemma") or ""),
            "raw_pos_values": list(row.get("raw_pos_values") or []),
            "chosen_pos": _as_mapping(row.get("chosen_pos")),
        }
        for row in lemma_reports
        if bool(row.get("ambiguous_raw_pos"))
    ][:20]
    return {
        "unresolved_lemmas": unresolved,
        "ambiguous_pos_lemmas": ambiguous,
    }


def candidate_pos_backfill_limitations() -> list[str]:
    return [
        "exact_lowercase_join_only_no_accent_or_inflection_expansion",
        "wiktionary_es_en_headword_pos_only_translation_side_pos_excluded",
        "pos_backfill_does_not_supply_topic_or_domain_metadata",
        "audit_does_not_validate_frequency_quality_or_license_suitability",
        "audit_does_not_install_or_replace_the_current_frequency_pack",
    ]


def candidate_pos_backfill_recommended_next_steps(summary: Mapping[str, object]) -> list[str]:
    mapped_count = int(summary.get("mapped_pos_lemma_count") or 0)
    weighted_count = int(summary.get("weighted_lexical_bucket_lemma_count") or 0)
    steps = [
        "Keep this as a candidate-readiness gate: a candidate can be inspected locally without becoming a default pack.",
        "Use the mapped and weighted-bucket counts to decide whether the candidate is viable for a 5k or 10k SRS denominator refresh.",
    ]
    if mapped_count >= 5000 and mapped_count < 10000:
        steps.append(
            "Treat the candidate as plausible for a 5k POS-aware shortlist, but do not claim 10k POS-complete readiness yet."
        )
    if weighted_count < 5000:
        steps.append(
            "Improve lexical bucket coverage before relying on POS weighting as the main learner-quality control."
        )
    if int(summary.get("unresolved_lemma_count") or 0) > 0:
        steps.append(
            "Inspect unresolved high-rank lemmas before promotion; many may be function words, inflections, numerals, or casing/accent variants."
        )
    steps.append(
        "After provenance and licensing are acceptable, build a candidate pack in the exact frequency-pack schema and rerun the source-readiness audit plus SRS Zipf bridge."
    )
    return steps


def render_candidate_pos_backfill_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    candidate = _as_mapping(report.get("candidate"))
    lines = [
        "# en-es Candidate POS Backfill Audit",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Candidate DB: `{candidate.get('path')}`",
        f"- Candidate unique lemmas: `{summary.get('candidate_unique_lemma_count')}`",
        f"- Lemmas with any external POS: `{summary.get('any_pos_lemma_count')}` ({_format_ratio(summary.get('any_pos_lemma_share'))})",
        f"- Lemmas with mapped POS: `{summary.get('mapped_pos_lemma_count')}` ({_format_ratio(summary.get('mapped_pos_lemma_share'))})",
        f"- Lemmas with confident weighted lexical bucket: `{summary.get('weighted_lexical_bucket_lemma_count')}` ({_format_ratio(summary.get('weighted_lexical_bucket_lemma_share'))})",
        f"- Ambiguous raw POS lemmas: `{summary.get('ambiguous_raw_pos_lemma_count')}`",
        "",
        "This is a no-mutation readiness audit. It does not install a candidate pack, change "
        "SRS admission, change rulegen, or start LLM generation.",
        "",
        "## Source Coverage",
        "",
        "| Source | Status | Exists | Usable POS Rows | Source Lemmas | Candidate Hits | Candidate Hit Share | Issues |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for source in _mapping_rows(report.get("sources")):
        lines.append(
            "| "
            f"`{source.get('source_id')}` | "
            f"`{source.get('status')}` | "
            f"`{bool(source.get('exists'))}` | "
            f"{int(source.get('usable_pos_row_count') or 0)} | "
            f"{int(source.get('distinct_source_lemma_count') or 0)} | "
            f"{int(source.get('candidate_hit_count') or 0)} | "
            f"{_format_ratio(source.get('candidate_hit_share'))} | "
            f"{_format_issues(source.get('issues'))} |"
        )
    lines.extend(
        [
            "",
            "## Target Readiness",
            "",
            "| Target | Any POS Reaches | Mapped POS Reaches | Confident Weighted Lexical Bucket Reaches | Mapped Shortfall |",
            "| ---: | --- | --- | --- | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("target_readiness")):
        lines.append(
            "| "
            f"{int(row.get('target_size') or 0)} | "
            f"`{bool(row.get('any_pos_reaches_target'))}` | "
            f"`{bool(row.get('mapped_pos_reaches_target'))}` | "
            f"`{bool(row.get('weighted_lexical_bucket_reaches_target'))}` | "
            f"{int(row.get('mapped_pos_shortfall') or 0)} |"
        )
    lines.extend(
        [
            "",
            "## Rank-Band Coverage",
            "",
            "| Top N | Any POS | Mapped POS | Confident Weighted Bucket | Ambiguous Raw POS |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("rank_band_coverage")):
        lines.append(
            "| "
            f"{int(row.get('rank_band_top_n') or 0)} | "
            f"{int(row.get('any_pos_lemma_count') or 0)} ({_format_ratio(row.get('any_pos_lemma_share'))}) | "
            f"{int(row.get('mapped_pos_lemma_count') or 0)} ({_format_ratio(row.get('mapped_pos_lemma_share'))}) | "
            f"{int(row.get('weighted_lexical_bucket_lemma_count') or 0)} ({_format_ratio(row.get('weighted_lexical_bucket_lemma_share'))}) | "
            f"{int(row.get('ambiguous_raw_pos_lemma_count') or 0)} ({_format_ratio(row.get('ambiguous_raw_pos_lemma_share'))}) |"
        )
    lines.extend(
        [
            "",
            "## Filter Scenarios",
            "",
            "| Scenario | Kept | Top 100 | Top 500 | Top 1,000 | First Kept Lemmas |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in _mapping_rows(report.get("filter_scenarios")):
        first_kept = row.get("first_kept_lemmas")
        if isinstance(first_kept, list) and first_kept:
            first_kept_text = ", ".join(f"`{item}`" for item in first_kept[:8])
        else:
            first_kept_text = "`none`"
        lines.append(
            "| "
            f"`{row.get('scenario_id')}` | "
            f"{int(row.get('kept_count') or 0)} ({_format_ratio(row.get('kept_share'))}) | "
            f"{int(row.get('top_100_kept_count') or 0)} | "
            f"{int(row.get('top_500_kept_count') or 0)} | "
            f"{int(row.get('top_1000_kept_count') or 0)} | "
            f"{first_kept_text} |"
        )
    lines.extend(["", "## Chosen POS Distribution", ""])
    distribution = _as_mapping(report.get("chosen_pos_distribution"))
    lines.extend(
        [
            "| Bucket | Count |",
            "| --- | ---: |",
        ]
    )
    for bucket_row in _mapping_rows(distribution.get("buckets")):
        lines.append(f"| `{bucket_row.get('bucket')}` | {int(bucket_row.get('count') or 0)} |")
    lines.extend(["", "## Issues", ""])
    issues = summary.get("issues")
    if isinstance(issues, list) and issues:
        for issue in issues:
            lines.append(f"- `{issue}`")
    else:
        lines.append("- `none`")
    lines.extend(["", "## Samples", ""])
    samples = _as_mapping(report.get("samples"))
    lines.append("Unresolved lemmas:")
    unresolved = samples.get("unresolved_lemmas") if isinstance(samples, Mapping) else []
    if isinstance(unresolved, list) and unresolved:
        lines.append(", ".join(f"`{item}`" for item in unresolved))
    else:
        lines.append("`none`")
    lines.append("")
    lines.append("Ambiguous POS lemmas:")
    ambiguous = samples.get("ambiguous_pos_lemmas") if isinstance(samples, Mapping) else []
    if isinstance(ambiguous, list) and ambiguous:
        lines.append(", ".join(f"`{_as_mapping(item).get('lemma')}`" for item in ambiguous))
    else:
        lines.append("`none`")
    lines.extend(["", "## Recommended Next Steps", ""])
    for index, item in enumerate(report.get("recommended_next_steps") or [], start=1):
        lines.append(f"{index}. {item}")
    lines.append("")
    return "\n".join(lines)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _format_ratio(value: object) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "0.0%"


def _format_issues(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "`none`"
    return ", ".join(f"`{_escape_pipe(str(item))}`" for item in value)


def _escape_pipe(value: str) -> str:
    return str(value).replace("|", "\\|")


__all__ = [
    "build_chosen_pos_distribution",
    "build_samples",
    "candidate_pos_backfill_limitations",
    "candidate_pos_backfill_recommended_next_steps",
    "render_candidate_pos_backfill_markdown",
]
