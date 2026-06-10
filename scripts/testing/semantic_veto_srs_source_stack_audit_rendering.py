from __future__ import annotations

from typing import Mapping, Sequence


def render_source_stack_markdown(report: Mapping[str, object]) -> str:
    summary = report["summary"]
    stack = report["combined_stack"]
    lines = [
        "# Semantic Veto SRS Source Stack Audit (`en-es`)",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Status: `{summary['status']}`",
        f"- Recommended stack: `{summary['recommended_stack']}`",
        f"- SPALEX clean distinct rows: `{summary['spalex_clean_distinct_count']}`",
        f"- Current CDE distinct rows: `{summary['current_cde_distinct_count']}`",
        f"- Combined distinct candidates: `{summary['combined_distinct_candidate_count']}`",
        f"- Current CDE rows missing from SPALEX: `{stack['cde_missing_from_spalex_count']}`",
        "",
        "## Target Readiness",
        "",
        "| Target | Reaches | CDE rows | SPALEX-added rows | Kaikki headwords | POS mapped | Explicit topics | Medicine signal | Reverse target |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in stack["target_readiness"]:
        lines.append(
            "| {target_size} | {reaches_target} | {baseline_rows} | {spalex_added_rows} | "
            "{kaikki_headword_count} ({kaikki_headword_share:.1%}) | "
            "{pos_mapped_from_cde_or_kaikki_count} ({pos_mapped_from_cde_or_kaikki_share:.1%}) | "
            "{explicit_topic_count} ({explicit_topic_share:.1%}) | "
            "{medicine_signal_count} ({medicine_signal_share:.1%}) | "
            "{reverse_spanish_target_count} ({reverse_spanish_target_share:.1%}) |".format(**row)
        )
    lines.extend(["", "## Findings", ""])
    for finding in report["findings"]:
        lines.append(f"- `{finding['level']}` `{finding['code']}`: {finding['message']}")
    lines.extend(
        [
            "",
            "## Source Roles",
            "",
            "- `SPALEX`: use as the publishable candidate frontier source with frequency, Zipf, and prevalence signals.",
            "- `freq-es-cde`: keep only as the current manual-supply/internal benchmark; do not make it a dependency of publishable SPALEX packs.",
            "- `Kaikki/Wiktionary`: use as the POS/gloss/dictionary/topic enrichment layer, not as the primary ranking source.",
            "",
            "## Recommended Next Steps",
            "",
        ]
    )
    for step in report["recommended_next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def build_summary(
    spalex: Mapping[str, object],
    current: Mapping[str, object],
    kaikki_forward: Mapping[str, object],
    kaikki_reverse: Mapping[str, object],
    stack: Mapping[str, object],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    error_count = sum(
        1
        for source in (spalex, current, kaikki_forward, kaikki_reverse)
        if source.get("status") == "error"
    )
    if error_count:
        status = "error"
    elif any(finding["level"] == "REVIEW" for finding in findings):
        status = "review"
    else:
        status = "ok"
    return {
        "status": status,
        "recommended_stack": (
            "spalex_only_publishable_frontier_plus_optional_kaikki_enrichment_"
            "with_freq_es_cde_internal_benchmark"
        ),
        "error_source_count": error_count,
        "spalex_clean_distinct_count": spalex.get("clean_distinct_spelling_count", 0),
        "current_cde_distinct_count": current.get("distinct_lemma_count", 0),
        "kaikki_forward_distinct_headword_count": kaikki_forward.get("distinct_headword_count", 0),
        "kaikki_reverse_spanish_target_count": kaikki_reverse.get(
            "distinct_spanish_translation_target_count", 0
        ),
        "combined_distinct_candidate_count": stack.get("combined_distinct_candidate_count", 0),
    }


def build_findings(
    spalex: Mapping[str, object],
    current: Mapping[str, object],
    kaikki_forward: Mapping[str, object],
    kaikki_reverse: Mapping[str, object],
    stack: Mapping[str, object],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for name, source in (
        ("spalex", spalex),
        ("current_frequency", current),
        ("kaikki_forward", kaikki_forward),
        ("kaikki_reverse", kaikki_reverse),
    ):
        if source.get("status") == "error":
            findings.append(
                {
                    "level": "ERROR",
                    "code": f"{name.upper()}_UNAVAILABLE",
                    "message": (
                        f"{name} input is unavailable: {', '.join(source.get('issues') or [])}"
                    ),
                }
            )
    if findings:
        return findings
    spalex_clean = int(spalex.get("clean_distinct_spelling_count") or 0)
    if spalex_clean >= 10000:
        findings.append(
            {
                "level": "PASS",
                "code": "SPALEX_REACHES_10K",
                "message": (
                    f"SPALEX has {spalex_clean} clean distinct spellings, enough "
                    "for a 10k expansion frontier."
                ),
            }
        )
    if int(stack.get("cde_missing_from_spalex_count") or 0) > 0:
        findings.append(
            {
                "level": "REVIEW",
                "code": "SPALEX_NOT_STANDALONE_REPLACEMENT",
                "message": (
                    f"{stack['cde_missing_from_spalex_count']} current CDE lemmas "
                    "are absent from SPALEX. Keep the CDE-seed union as an internal "
                    "continuity benchmark, not as a publishable pack dependency."
                ),
            }
        )
    target_10k = _target_row(stack, 10000)
    if target_10k:
        _append_10k_findings(findings, target_10k)
    findings.append(
        {
            "level": "REVIEW",
            "code": "KAIKKI_LICENSE_AND_DUMP_PINNING_REQUIRED",
            "message": (
                "Kaikki enrichment remains promotion-review data until attribution, "
                "share-alike/GFDL posture, and dated dump identity are encoded in manifests."
            ),
        }
    )
    return findings


def recommended_next_steps(findings: Sequence[Mapping[str, str]]) -> list[str]:
    if any(finding["level"] == "ERROR" for finding in findings):
        return [
            "Resolve missing local audit inputs before making a source-stack decision.",
            "Do not promote an expanded SRS source while the audit cannot read all source layers.",
        ]
    return [
        "Treat SPALEX as the leading publishable candidate-frontier source.",
        "Prototype `freq-es-spalex-v1` as SPALEX-only, with optional Kaikki POS/topic enrichment tracked as a review-gated component.",
        "Keep `freq-es-spalex-expanded-v1` as a CDE-seed union only for internal comparison against the current manual-supply baseline.",
        "Backfill POS/gloss/topic metadata from the installed Kaikki forward pack and keep missing Kaikki rows explicit.",
        "Add a narrow topic overlay for medicine/health before claiming interest-tailored admission quality.",
        "Encode SPALEX CC BY attribution and Kaikki review-required attribution/share-alike/dump-pin requirements in source manifests before promotion.",
        "Run a neutral vs medicine-weighted SRS admission probe after the provisional source pack exists.",
    ]


def _append_10k_findings(findings: list[dict[str, str]], target_10k: Mapping[str, object]) -> None:
    if target_10k["kaikki_headword_share"] >= 0.9:
        findings.append(
            {
                "level": "PASS",
                "code": "KAIKKI_COVERS_COMBINED_10K",
                "message": (
                    "Installed Kaikki covers "
                    f"{target_10k['kaikki_headword_count']} / 10000 combined "
                    "candidates as headwords."
                ),
            }
        )
    if target_10k["pos_mapped_from_cde_or_kaikki_share"] >= 0.9:
        findings.append(
            {
                "level": "PASS",
                "code": "POS_BACKFILL_COVERS_COMBINED_10K",
                "message": (
                    "CDE plus Kaikki POS maps "
                    f"{target_10k['pos_mapped_from_cde_or_kaikki_count']} / 10000 "
                    "combined candidates."
                ),
            }
        )
    if target_10k["explicit_topic_share"] < 0.5:
        findings.append(
            {
                "level": "REVIEW",
                "code": "TOPIC_METADATA_REQUIRES_OVERLAY",
                "message": (
                    "Explicit Kaikki topic coverage is useful but partial "
                    f"({target_10k['explicit_topic_count']} / 10000), so domain "
                    "overlays and/or embedding-assisted tagging are still needed."
                ),
            }
        )
    if target_10k["medicine_signal_count"] > 0:
        findings.append(
            {
                "level": "PASS",
                "code": "MEDICINE_SEED_SIGNAL_EXISTS",
                "message": (
                    "Kaikki provides an initial medicine/health signal for "
                    f"{target_10k['medicine_signal_count']} / 10000 combined candidates."
                ),
            }
        )


def _target_row(stack: Mapping[str, object], target_size: int) -> Mapping[str, object] | None:
    for row in stack.get("target_readiness") or []:
        if int(row["target_size"]) == target_size:
            return row
    return None
