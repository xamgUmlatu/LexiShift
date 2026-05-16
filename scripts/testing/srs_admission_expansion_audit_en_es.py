#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from lexishift_core.srs.profile_bootstrap import rerank_seed_words_for_profile  # noqa: E402


DEFAULT_PAIR = "en-es"
DEFAULT_TOP_N = 10000
DEFAULT_PREVIEW_LIMIT = 20
DEFAULT_PROFILE_TOP_N = 20
DEFAULT_SOURCE_LABEL = "freq-es-spalex-expanded-v1"
DEFAULT_PROFILE_INTERESTS = ("medicine", "finance", "sports", "music")
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_admission_expansion_audit_en_es_spalex_10k_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_admission_expansion_audit_en_es_spalex_10k_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit an expanded en-es frequency pack through the existing SRS seed and "
            "profile-admission path. This is diagnostic-only and does not mutate helper "
            "state, publish SRS sets, or generate semantic-veto data."
        )
    )
    parser.add_argument("--frequency-db", type=Path, required=True)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--preview-limit", type=int, default=DEFAULT_PREVIEW_LIMIT)
    parser.add_argument("--profile-top-n", type=int, default=DEFAULT_PROFILE_TOP_N)
    parser.add_argument("--source-label", default=DEFAULT_SOURCE_LABEL)
    parser.add_argument(
        "--profile-interest",
        action="append",
        default=[],
        help="Profile interest to audit. May be repeated.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    interests = tuple(args.profile_interest or DEFAULT_PROFILE_INTERESTS)
    report = build_report(
        frequency_db=args.frequency_db,
        pair=str(args.pair),
        top_n=max(1, int(args.top_n)),
        preview_limit=max(1, int(args.preview_limit)),
        profile_top_n=max(1, int(args.profile_top_n)),
        source_label=str(args.source_label),
        profile_interests=interests,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    frequency_db: Path,
    pair: str = DEFAULT_PAIR,
    top_n: int = DEFAULT_TOP_N,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
    profile_top_n: int = DEFAULT_PROFILE_TOP_N,
    source_label: str = DEFAULT_SOURCE_LABEL,
    profile_interests: Sequence[str] = DEFAULT_PROFILE_INTERESTS,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    resolved_db = Path(frequency_db).expanduser().resolve(strict=False)
    base_report = _sqlite_pack_summary(resolved_db)
    if not base_report["exists"]:
        return {
            "schema_version": 1,
            "pair": pair,
            "status": "review",
            "decision": "srs_admission_expansion_audit_needs_review",
            "generated_at": generated_at,
            "inputs": _inputs(
                frequency_db=resolved_db,
                pair=pair,
                top_n=top_n,
                preview_limit=preview_limit,
                profile_top_n=profile_top_n,
                source_label=source_label,
                profile_interests=profile_interests,
            ),
            "pack": base_report,
            "summary": {
                "issues": ["frequency_db_missing"],
            },
            "findings": [
                _finding(
                    "FAIL",
                    "frequency_db_missing",
                    "Candidate frequency SQLite does not exist.",
                )
            ],
        }

    rank_order_seeds = _build_seeds(
        frequency_db=resolved_db,
        pair=pair,
        top_n=top_n,
        source_label=source_label,
        sort_by_admission_weight=False,
    )
    admitted_seeds = _build_seeds(
        frequency_db=resolved_db,
        pair=pair,
        top_n=top_n,
        source_label=source_label,
        sort_by_admission_weight=True,
    )
    neutral_rank_by_lemma = _rank_by_lemma(admitted_seeds)
    raw_top_bucket_counts = _bucket_counts(rank_order_seeds[:100])
    admitted_top_bucket_counts = _bucket_counts(admitted_seeds[:100])
    seed_summary = _seed_summary(
        rank_order_seeds=rank_order_seeds,
        admitted_seeds=admitted_seeds,
        top_n=top_n,
        preview_limit=preview_limit,
        raw_top_bucket_counts=raw_top_bucket_counts,
        admitted_top_bucket_counts=admitted_top_bucket_counts,
    )
    profile_scenarios = [
        _profile_scenario(
            interest=interest,
            seeds=admitted_seeds,
            neutral_rank_by_lemma=neutral_rank_by_lemma,
            profile_top_n=profile_top_n,
        )
        for interest in profile_interests
    ]
    findings = _build_findings(
        pack=base_report,
        seed_summary=seed_summary,
        profile_scenarios=profile_scenarios,
        top_n=top_n,
    )
    status = "ok" if not any(item["level"] == "FAIL" for item in findings) else "review"
    return {
        "schema_version": 1,
        "pair": pair,
        "status": status,
        "decision": (
            "srs_admission_expansion_audit_passed"
            if status == "ok"
            else "srs_admission_expansion_audit_needs_review"
        ),
        "generated_at": generated_at,
        "inputs": _inputs(
            frequency_db=resolved_db,
            pair=pair,
            top_n=top_n,
            preview_limit=preview_limit,
            profile_top_n=profile_top_n,
            source_label=source_label,
            profile_interests=profile_interests,
        ),
        "methodology": {
            "runtime_policy_change": "none",
            "helper_state_mutation": "none",
            "semantic_veto_generation": "none",
            "admission_path": (
                "Build rank-order seeds from the candidate SQLite, then let the existing "
                "SRS seed code sort by admission_weight = normalized commonness * POS weight."
            ),
            "profile_path": (
                "Run existing profile-bootstrap reranking on the admitted seed frontier for "
                "diagnostic interests only; this does not publish or admit runtime items."
            ),
            "frontier_boundary": (
                "top_n is selected by candidate rank/commonness before POS/profile reranking."
            ),
        },
        "pack": base_report,
        "seed_admission": seed_summary,
        "profile_scenarios": profile_scenarios,
        "findings": findings,
        "summary": _summary(seed_summary, profile_scenarios, findings),
        "limitations": [
            "This audit does not mutate SRS state, run helper publication, or change default packs.",
            "Profile scenarios prove that tagged rows can receive admission pressure; they do not prove that topic labels are complete or perfectly precise.",
            "Topic metadata is sparse relative to the full 10k frontier, so untagged rows remain general-frequency candidates.",
            "Semantic-veto evidence coverage remains a downstream concern after SRS admission readiness.",
        ],
    }


def _build_seeds(
    *,
    frequency_db: Path,
    pair: str,
    top_n: int,
    source_label: str,
    sort_by_admission_weight: bool,
) -> list[object]:
    return build_seed_candidates(
        frequency_db=frequency_db,
        config=SeedSelectionConfig(
            language_pair=pair,
            top_n=top_n,
            require_jmdict=False,
            source_label=source_label,
            sort_by_admission_weight=sort_by_admission_weight,
        ),
    )


def _seed_summary(
    *,
    rank_order_seeds: Sequence[object],
    admitted_seeds: Sequence[object],
    top_n: int,
    preview_limit: int,
    raw_top_bucket_counts: Mapping[str, int],
    admitted_top_bucket_counts: Mapping[str, int],
) -> dict[str, object]:
    selected_count = len(admitted_seeds)
    unique_lemmas = len({str(getattr(seed, "lemma", "") or "") for seed in admitted_seeds})
    pos_mapped_count = sum(1 for seed in admitted_seeds if bool(getattr(seed, "pos_mapped", False)))
    topic_rows = [seed for seed in admitted_seeds if _seed_topics(seed)]
    rank_columns = Counter(str(_metadata(seed).get("rank_column") or "") for seed in admitted_seeds)
    pmw_columns = Counter(str(_metadata(seed).get("pmw_column") or "") for seed in admitted_seeds)
    pos_source_profiles = Counter(
        str(_metadata(seed).get("pos_source_profile") or "") for seed in admitted_seeds
    )
    topic_counter: Counter[str] = Counter()
    for seed in topic_rows:
        topic_counter.update(_seed_topics(seed))
    return {
        "top_n_requested": top_n,
        "selected_count": selected_count,
        "unique_lemma_count": unique_lemmas,
        "rank_column_counts": dict(sorted(rank_columns.items())),
        "pmw_column_counts": dict(sorted(pmw_columns.items())),
        "pos_mapped_count": pos_mapped_count,
        "pos_mapped_share": _ratio(pos_mapped_count, selected_count),
        "pos_bucket_counts": dict(sorted(_bucket_counts(admitted_seeds).items())),
        "pos_source_profile_counts": dict(sorted(pos_source_profiles.items())),
        "topic_row_count": len(topic_rows),
        "topic_row_share": _ratio(len(topic_rows), selected_count),
        "top_topics": [
            {"topic": topic, "count": count} for topic, count in topic_counter.most_common(20)
        ],
        "raw_top_100_pos_bucket_counts": dict(sorted(raw_top_bucket_counts.items())),
        "admitted_top_100_pos_bucket_counts": dict(sorted(admitted_top_bucket_counts.items())),
        "nonlexical_top_100_before": _nonlexical_count(raw_top_bucket_counts),
        "nonlexical_top_100_after": _nonlexical_count(admitted_top_bucket_counts),
        "rank_order_preview": [_seed_preview(seed) for seed in rank_order_seeds[:preview_limit]],
        "admission_order_preview": [_seed_preview(seed) for seed in admitted_seeds[:preview_limit]],
    }


def _profile_scenario(
    *,
    interest: str,
    seeds: Sequence[object],
    neutral_rank_by_lemma: Mapping[str, int],
    profile_top_n: int,
) -> dict[str, object]:
    reranked, diagnostics = rerank_seed_words_for_profile(
        seeds,
        profile_context={"interests": [interest]},
        preview_limit=profile_top_n,
    )
    support_by_topic = {
        str(row.get("topic") or ""): row
        for row in _mapping_rows(_as_mapping(diagnostics.get("active_topic_support")).get("topics"))
    }
    support = _as_mapping(support_by_topic.get(interest))
    top_rows = []
    for rank, seed in enumerate(reranked[:profile_top_n], start=1):
        lemma = str(getattr(seed, "lemma", "") or "")
        top_rows.append(
            {
                "profile_rank": rank,
                "neutral_rank": neutral_rank_by_lemma.get(lemma),
                "lemma": lemma,
                "pos_bucket": str(getattr(seed, "pos_bucket", "") or ""),
                "admission_weight": _round_float(getattr(seed, "admission_weight", None)),
                "topics": _seed_topics(seed)[:12],
            }
        )
    interest_hits = [row for row in top_rows if interest in row["topics"]]
    return {
        "interest": interest,
        "status": "eligible" if bool(support.get("eligible_for_scarcity_calibration")) else "thin",
        "support": dict(support),
        "top_rows": top_rows,
        "top_rows_with_exact_interest": len(interest_hits),
        "mean_neutral_rank_of_profile_top_rows": _mean(
            row.get("neutral_rank") for row in top_rows if row.get("neutral_rank")
        ),
    }


def _sqlite_pack_summary(db_path: Path) -> dict[str, object]:
    if not db_path.exists():
        return {
            "db_path": str(db_path),
            "exists": False,
            "row_count": 0,
            "distinct_lemma_count": 0,
            "columns": [],
            "source_family_counts": {},
        }
    conn = sqlite3.connect(db_path)
    try:
        columns = [str(row[1]) for row in conn.execute("PRAGMA table_info(frequency)")]
        row = conn.execute("SELECT COUNT(*), COUNT(DISTINCT lemma) FROM frequency").fetchone()
        source_family_counts: dict[str, int] = {}
        if "source_family" in columns:
            source_family_counts = {
                str(source or "unknown"): int(count or 0)
                for source, count in conn.execute(
                    "SELECT source_family, COUNT(*) FROM frequency GROUP BY source_family"
                )
            }
        return {
            "db_path": str(db_path),
            "exists": True,
            "row_count": int(row[0] or 0) if row else 0,
            "distinct_lemma_count": int(row[1] or 0) if row else 0,
            "columns": columns,
            "source_family_counts": dict(sorted(source_family_counts.items())),
        }
    finally:
        conn.close()


def _build_findings(
    *,
    pack: Mapping[str, object],
    seed_summary: Mapping[str, object],
    profile_scenarios: Sequence[Mapping[str, object]],
    top_n: int,
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if int(pack.get("distinct_lemma_count") or 0) >= top_n:
        findings.append(
            _finding("PASS", "candidate_reaches_top_n", "Candidate pack reaches target size.")
        )
    else:
        findings.append(
            _finding("FAIL", "candidate_below_top_n", "Candidate pack is below target size.")
        )
    if int(seed_summary.get("selected_count") or 0) == top_n:
        findings.append(
            _finding("PASS", "seed_selection_reaches_top_n", "SRS seed path selected top_n rows.")
        )
    else:
        findings.append(
            _finding(
                "FAIL",
                "seed_selection_shortfall",
                "SRS seed path did not produce the requested top_n rows.",
            )
        )
    if float(seed_summary.get("pos_mapped_share") or 0.0) >= 0.90:
        findings.append(
            _finding("PASS", "pos_mapped_for_frontier", "POS mapping covers the 10k frontier.")
        )
    else:
        findings.append(
            _finding("WARN", "pos_mapping_partial", "POS mapping is partial in the frontier.")
        )
    if int(seed_summary.get("topic_row_count") or 0) > 0:
        findings.append(
            _finding("PASS", "topic_rows_available", "Topic rows are available for profile lift.")
        )
    else:
        findings.append(
            _finding("WARN", "topic_rows_absent", "No topic rows are available for profile lift.")
        )
    if float(seed_summary.get("topic_row_share") or 0.0) < 0.25:
        findings.append(
            _finding(
                "WARN",
                "topic_coverage_sparse",
                "Topic coverage is sparse; do not claim complete interest tailoring.",
            )
        )
    if int(seed_summary.get("nonlexical_top_100_after") or 0) < int(
        seed_summary.get("nonlexical_top_100_before") or 0
    ):
        findings.append(
            _finding(
                "PASS",
                "pos_weighting_changes_frontier",
                "POS weighting demotes non-lexical/function-heavy rows in the top preview.",
            )
        )
    for scenario in profile_scenarios:
        if scenario.get("status") == "eligible":
            findings.append(
                _finding(
                    "PASS",
                    f"profile_interest_supported:{scenario.get('interest')}",
                    "Profile interest has enough tagged support for diagnostic reranking.",
                )
            )
        else:
            findings.append(
                _finding(
                    "WARN",
                    f"profile_interest_thin:{scenario.get('interest')}",
                    "Profile interest has thin or missing tagged support.",
                )
            )
    return findings


def render_markdown(report: Mapping[str, object]) -> str:
    seed = _as_mapping(report.get("seed_admission"))
    lines = [
        "# en-es SRS Admission Expansion Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Frequency DB: `{_as_mapping(report.get('pack')).get('db_path', '')}`",
        f"- SRS seed rows: `{seed.get('selected_count', 0)}`",
        f"- Unique lemmas: `{seed.get('unique_lemma_count', 0)}`",
        f"- POS mapped: `{seed.get('pos_mapped_count', 0)}` ({_pct(seed.get('pos_mapped_share'))})",
        f"- Topic rows: `{seed.get('topic_row_count', 0)}` ({_pct(seed.get('topic_row_share'))})",
        f"- Non-lexical/function-heavy rows in top 100: `{seed.get('nonlexical_top_100_before', 0)}` rank-order -> `{seed.get('nonlexical_top_100_after', 0)}` admission-order",
        "",
        "## Scope",
        "",
        "This is an SRS admission integration audit. It does not mutate helper state, publish runtime SRS sets, change the veto algorithm, or generate semantic-veto helper data.",
        "",
        "## Findings",
        "",
    ]
    for finding in report.get("findings", []):
        item = _as_mapping(finding)
        lines.append(
            f"- `{item.get('level', '')}` `{item.get('code', '')}`: {item.get('message', '')}"
        )
    lines.extend(
        [
            "",
            "## Seed Admission",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| top_n requested | {seed.get('top_n_requested', 0)} |",
            f"| selected rows | {seed.get('selected_count', 0)} |",
            f"| unique lemmas | {seed.get('unique_lemma_count', 0)} |",
            f"| POS mapped share | {_pct(seed.get('pos_mapped_share'))} |",
            f"| topic row share | {_pct(seed.get('topic_row_share'))} |",
            "",
            "### POS Buckets",
            "",
            _counter_table(seed.get("pos_bucket_counts"), "Bucket"),
            "",
            "### Top Topics",
            "",
            _topic_table(seed.get("top_topics")),
            "",
            "### Rank-Order Preview",
            "",
            _preview_table(seed.get("rank_order_preview")),
            "",
            "### Admission-Order Preview",
            "",
            _preview_table(seed.get("admission_order_preview")),
            "",
            "## Profile Scenarios",
            "",
        ]
    )
    for scenario in report.get("profile_scenarios", []):
        sc = _as_mapping(scenario)
        support = _as_mapping(sc.get("support"))
        lines.extend(
            [
                f"### `{sc.get('interest', '')}`",
                "",
                f"- status: `{sc.get('status', '')}`",
                f"- support candidates: `{support.get('candidate_count', 0)}`",
                f"- support mass: `{support.get('support_mass', 0)}`",
                f"- exact-interest rows in top preview: `{sc.get('top_rows_with_exact_interest', 0)}`",
                "",
                _profile_table(sc.get("top_rows")),
                "",
            ]
        )
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _summary(
    seed_summary: Mapping[str, object],
    profile_scenarios: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "selected_count": seed_summary.get("selected_count"),
        "unique_lemma_count": seed_summary.get("unique_lemma_count"),
        "pos_mapped_share": seed_summary.get("pos_mapped_share"),
        "topic_row_share": seed_summary.get("topic_row_share"),
        "nonlexical_top_100_before": seed_summary.get("nonlexical_top_100_before"),
        "nonlexical_top_100_after": seed_summary.get("nonlexical_top_100_after"),
        "profile_interest_status_counts": dict(
            Counter(str(row.get("status") or "") for row in profile_scenarios)
        ),
        "finding_counts": dict(Counter(str(row.get("level") or "") for row in findings)),
        "issues": [row.get("code") for row in findings if row.get("level") == "FAIL"],
        "warnings": [row.get("code") for row in findings if row.get("level") == "WARN"],
    }


def _inputs(
    *,
    frequency_db: Path,
    pair: str,
    top_n: int,
    preview_limit: int,
    profile_top_n: int,
    source_label: str,
    profile_interests: Sequence[str],
) -> dict[str, object]:
    return {
        "frequency_db": str(frequency_db),
        "pair": pair,
        "top_n": int(top_n),
        "preview_limit": int(preview_limit),
        "profile_top_n": int(profile_top_n),
        "source_label": source_label,
        "profile_interests": list(profile_interests),
    }


def _seed_preview(seed: object) -> dict[str, object]:
    return {
        "lemma": str(getattr(seed, "lemma", "") or ""),
        "rank": _round_float(getattr(seed, "core_rank", None)),
        "pmw": _round_float(getattr(seed, "pmw", None)),
        "base_weight": _round_float(getattr(seed, "base_weight", None)),
        "admission_weight": _round_float(getattr(seed, "admission_weight", None)),
        "pos": str(getattr(seed, "pos", "") or ""),
        "pos_bucket": str(getattr(seed, "pos_bucket", "") or ""),
        "pos_mapped": bool(getattr(seed, "pos_mapped", False)),
        "topics": _seed_topics(seed)[:12],
    }


def _seed_topics(seed: object) -> list[str]:
    metadata = _metadata(seed)
    values: list[str] = []
    for key in ("sense_topics", "topics", "topic", "profile_topics"):
        raw = metadata.get(key)
        if isinstance(raw, list):
            values.extend(str(item) for item in raw if str(item).strip())
        elif isinstance(raw, str) and raw.strip():
            values.extend(item.strip() for item in raw.split(",") if item.strip())
    return sorted(dict.fromkeys(values))


def _metadata(seed: object) -> Mapping[str, object]:
    value = getattr(seed, "metadata", {})
    return value if isinstance(value, Mapping) else {}


def _bucket_counts(seeds: Sequence[object]) -> Counter[str]:
    return Counter(str(getattr(seed, "pos_bucket", "") or "unknown") for seed in seeds)


def _nonlexical_count(counts: Mapping[str, int]) -> int:
    return sum(int(counts.get(bucket, 0) or 0) for bucket in ("adverb", "other"))


def _rank_by_lemma(seeds: Sequence[object]) -> dict[str, int]:
    return {
        str(getattr(seed, "lemma", "") or ""): index + 1
        for index, seed in enumerate(seeds)
        if str(getattr(seed, "lemma", "") or "")
    }


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _mean(values: Iterable[object]) -> float | None:
    floats = [float(value) for value in values if value is not None and str(value).strip()]
    if not floats:
        return None
    return round(sum(floats) / len(floats), 6)


def _round_float(value: object, *, places: int = 6) -> float | None:
    try:
        if value is None:
            return None
        return round(float(value), places)
    except (TypeError, ValueError):
        return None


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _counter_table(value: object, label: str) -> str:
    mapping = _as_mapping(value)
    lines = [f"| {label} | Count |", "| --- | ---: |"]
    for key, count in sorted(mapping.items(), key=lambda item: str(item[0])):
        lines.append(f"| `{key}` | {count} |")
    return "\n".join(lines)


def _topic_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "No topics found."
    lines = ["| Topic | Count |", "| --- | ---: |"]
    for row in rows:
        lines.append(f"| `{row.get('topic', '')}` | {row.get('count', 0)} |")
    return "\n".join(lines)


def _preview_table(value: object) -> str:
    rows = _mapping_rows(value)
    lines = [
        "| Lemma | Rank | POS | Admission | Topics |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        topics = ", ".join(str(item) for item in row.get("topics", [])[:4])
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('lemma', '')}`",
                    str(row.get("rank", "")),
                    f"`{row.get('pos_bucket', '')}`",
                    str(row.get("admission_weight", "")),
                    topics or "none",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _profile_table(value: object) -> str:
    rows = _mapping_rows(value)
    lines = [
        "| Profile Rank | Neutral Rank | Lemma | POS | Admission | Topics |",
        "| ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        topics = ", ".join(str(item) for item in row.get("topics", [])[:4])
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("profile_rank", "")),
                    str(row.get("neutral_rank", "")),
                    f"`{row.get('lemma', '')}`",
                    f"`{row.get('pos_bucket', '')}`",
                    str(row.get("admission_weight", "")),
                    topics or "none",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
