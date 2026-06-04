#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import is_dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from lexishift_core.srs.profile_bootstrap import rerank_seed_words_for_profile  # noqa: E402


DEFAULT_REVIEW_PACKET_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_animals_plants_signal_review_packet_en_es_spalex_10k_latest.json"
)
DEFAULT_OVERLAY_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_animals_plants_topic_overlay_en_es_spalex_10k_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_animals_plants_topic_overlay_poc_en_es_spalex_10k_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_animals_plants_topic_overlay_poc_en_es_spalex_10k_latest.md"
)
DEFAULT_SOURCE_LABEL = "freq-es-spalex-expanded-v1"
DEFAULT_PAIR = "en-es"
DEFAULT_TOP_N = 10000
DEFAULT_PROFILE_TOP_N = 24
ACCEPTED_DECISION_MEMBERSHIPS = {
    "accept_strong_topic": 1.0,
    "accept_light_topic": 0.65,
}
PROFILE_INJECTION_MIN_MEMBERSHIP = 1.0
PROFILE_INTERESTS = ("animals", "plants_nature")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build and exercise an en-es animals/plants topic-overlay PoC from the "
            "review-label packet. This is diagnostic-only and does not mutate helper state."
        )
    )
    parser.add_argument("--review-packet-json", type=Path, default=DEFAULT_REVIEW_PACKET_JSON)
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--source-label", default=DEFAULT_SOURCE_LABEL)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--profile-top-n", type=int, default=DEFAULT_PROFILE_TOP_N)
    parser.add_argument("--overlay-json-out", type=Path, default=DEFAULT_OVERLAY_JSON_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    review_packet_path = _resolve_path(args.review_packet_json)
    review_packet = _load_json(review_packet_path)
    frequency_db = (
        _resolve_path(args.frequency_db)
        if args.frequency_db
        else _frequency_db_from_review_packet(review_packet)
    )
    report = build_report(
        review_packet_payload=review_packet,
        review_packet_path=review_packet_path,
        frequency_db=frequency_db,
        pair=str(args.pair),
        source_label=str(args.source_label),
        top_n=max(1, int(args.top_n)),
        profile_top_n=max(1, int(args.profile_top_n)),
    )
    overlay_json_out = _resolve_path(args.overlay_json_out)
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    overlay_json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    overlay_json_out.write_text(
        json.dumps(report["topic_overlay"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote overlay artifact to {overlay_json_out}")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    review_packet_payload: Mapping[str, object],
    review_packet_path: Path | None = None,
    frequency_db: Path | None = None,
    pair: str = DEFAULT_PAIR,
    source_label: str = DEFAULT_SOURCE_LABEL,
    top_n: int = DEFAULT_TOP_N,
    profile_top_n: int = DEFAULT_PROFILE_TOP_N,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    overlay = build_topic_overlay(
        review_packet_payload=review_packet_payload,
        review_packet_path=review_packet_path,
        pair=pair,
        generated_at=generated_at,
    )
    resolved_frequency_db = (
        Path(frequency_db).expanduser().resolve(strict=False) if frequency_db else None
    )
    if not resolved_frequency_db or not resolved_frequency_db.exists():
        findings = [
            _finding(
                "FAIL",
                "frequency_db_missing",
                "Frequency DB is missing; overlay was built but admission PoC could not run.",
            )
        ]
        return _report(
            status="review",
            generated_at=generated_at,
            review_packet_path=review_packet_path,
            frequency_db=resolved_frequency_db,
            pair=pair,
            source_label=source_label,
            top_n=top_n,
            profile_top_n=profile_top_n,
            overlay=overlay,
            scenarios=[],
            findings=findings,
        )

    seeds = build_seed_candidates(
        frequency_db=resolved_frequency_db,
        config=SeedSelectionConfig(
            language_pair=pair,
            top_n=top_n,
            require_jmdict=False,
            source_label=source_label,
            sort_by_admission_weight=True,
        ),
    )
    overlay_rows_by_lemma = _overlay_rows_by_lemma(_mapping_rows(overlay.get("rows")))
    overlay_seeds = [
        _seed_with_overlay(seed, overlay_rows_by_lemma.get(_seed_lemma(seed), ())) for seed in seeds
    ]
    neutral_rank_by_lemma = _rank_by_lemma(seeds)
    scenarios = [
        _profile_scenario(
            interest=interest,
            base_seeds=seeds,
            overlay_seeds=overlay_seeds,
            neutral_rank_by_lemma=neutral_rank_by_lemma,
            overlay_rows_by_lemma=overlay_rows_by_lemma,
            profile_top_n=profile_top_n,
        )
        for interest in PROFILE_INTERESTS
    ]
    findings = _findings(overlay=overlay, seeds=seeds, scenarios=scenarios)
    status = "ok" if not any(item["level"] == "FAIL" for item in findings) else "review"
    return _report(
        status=status,
        generated_at=generated_at,
        review_packet_path=review_packet_path,
        frequency_db=resolved_frequency_db,
        pair=pair,
        source_label=source_label,
        top_n=top_n,
        profile_top_n=profile_top_n,
        overlay=overlay,
        scenarios=scenarios,
        findings=findings,
    )


def build_topic_overlay(
    *,
    review_packet_payload: Mapping[str, object],
    review_packet_path: Path | None = None,
    pair: str = DEFAULT_PAIR,
    generated_at: str | None = None,
) -> dict[str, object]:
    rows_by_key: dict[tuple[str, str], dict[str, object]] = {}
    rejected_counts: Counter[str] = Counter()
    unlabeled_count = 0
    for row in _mapping_rows(review_packet_payload.get("review_queue")):
        manual_review = _as_mapping(row.get("manual_review"))
        decision = str(manual_review.get("decision") or "").strip()
        if not decision:
            unlabeled_count += 1
            continue
        membership = ACCEPTED_DECISION_MEMBERSHIPS.get(decision)
        if membership is None:
            rejected_counts[decision] += 1
            continue
        lemma = str(row.get("lemma") or "").strip()
        topic = str(row.get("family") or "").strip()
        if not lemma or not topic:
            continue
        overlay_row = {
            "lemma": lemma,
            "language_pair": pair,
            "topic": topic,
            "membership": round(float(membership), 6),
            "confidence_label": "strong" if membership >= 1.0 else "light",
            "review_decision": decision,
            "review_id": str(row.get("review_id") or ""),
            "review_state": str(manual_review.get("state") or ""),
            "reviewer": str(manual_review.get("reviewer") or ""),
            "source_channel": str(row.get("source_channel") or ""),
            "source_label": str(row.get("source_label") or ""),
            "evidence_tier": str(row.get("best_tier") or ""),
            "evidence_band": str(row.get("confidence_band") or ""),
            "evidence_score": _round_float(row.get("confidence")),
            "provenance": {
                "review_packet": _repo_path(review_packet_path),
                "label_source": str(manual_review.get("label_source") or ""),
                "promotion_state": "poc_candidate_not_product_overlay",
                "notes": str(manual_review.get("notes") or ""),
            },
        }
        key = (lemma, topic)
        previous = rows_by_key.get(key)
        if previous is None or float(overlay_row["membership"]) > float(
            previous.get("membership") or 0.0
        ):
            rows_by_key[key] = overlay_row

    rows = sorted(rows_by_key.values(), key=lambda item: (str(item["topic"]), str(item["lemma"])))
    counts_by_topic = Counter(str(row.get("topic") or "") for row in rows)
    counts_by_confidence = Counter(str(row.get("confidence_label") or "") for row in rows)
    findings = []
    if rows:
        findings.append(
            _finding(
                "PASS", "overlay_rows_present", "Accepted review labels produced overlay rows."
            )
        )
    else:
        findings.append(
            _finding(
                "FAIL", "overlay_rows_empty", "No accepted review labels produced overlay rows."
            )
        )
    if unlabeled_count:
        findings.append(
            _finding("FAIL", "review_rows_unlabeled", "Some review rows have no decision label.")
        )
    else:
        findings.append(
            _finding("PASS", "review_rows_labeled", "All review rows have decision labels.")
        )
    return {
        "schema_version": 1,
        "overlay_id": "srs_animals_plants_topic_overlay_en_es_spalex_10k_poc_v1",
        "status": "ok" if not any(item["level"] == "FAIL" for item in findings) else "review",
        "decision": "topic_overlay_candidate_ready"
        if not any(item["level"] == "FAIL" for item in findings)
        else "topic_overlay_candidate_needs_review",
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "review_packet_json": _repo_path(review_packet_path),
            "review_packet_decision": str(review_packet_payload.get("decision") or ""),
        },
        "overlay_policy": {
            "runtime_policy_change": "none",
            "promotion_state": "poc_candidate_not_product_overlay",
            "membership_from_decision": ACCEPTED_DECISION_MEMBERSHIPS,
            "rejected_decisions_excluded": dict(sorted(rejected_counts.items())),
        },
        "summary": {
            "row_count": len(rows),
            "counts_by_topic": dict(sorted(counts_by_topic.items())),
            "counts_by_confidence": dict(sorted(counts_by_confidence.items())),
            "unlabeled_review_row_count": unlabeled_count,
        },
        "rows": rows,
        "findings": findings,
    }


def _report(
    *,
    status: str,
    generated_at: str,
    review_packet_path: Path | None,
    frequency_db: Path | None,
    pair: str,
    source_label: str,
    top_n: int,
    profile_top_n: int,
    overlay: Mapping[str, object],
    scenarios: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": status,
        "decision": "srs_animals_plants_topic_overlay_poc_ready"
        if status == "ok"
        else "srs_animals_plants_topic_overlay_poc_needs_review",
        "generated_at": generated_at,
        "inputs": {
            "review_packet_json": _repo_path(review_packet_path),
            "frequency_db": str(frequency_db or ""),
            "pair": pair,
            "source_label": source_label,
            "top_n": int(top_n),
            "profile_top_n": int(profile_top_n),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "helper_state_mutation": "none",
            "source_download": "none",
            "overlay_application": (
                "Accepted review labels are injected into seed metadata as profile_topics, "
                "then existing profile-bootstrap reranking is run for diagnostic profiles. "
                "Only rows at or above PROFILE_INJECTION_MIN_MEMBERSHIP are injected; "
                "lower-membership rows remain in the overlay artifact for later review."
            ),
            "profile_injection_min_membership": PROFILE_INJECTION_MIN_MEMBERSHIP,
        },
        "topic_overlay": overlay,
        "profile_scenarios": list(scenarios),
        "findings": list(findings),
        "summary": _summary(overlay=overlay, scenarios=scenarios, findings=findings),
        "limitations": [
            "This PoC does not install or enable a product overlay.",
            "Light accepted labels are included with lower membership in the artifact, but are not injected into profile_topics in this PoC because current profile-bootstrap scoring consumes topic presence rather than scalar membership.",
            "The result proves an integration path for reviewed labels; it does not prove complete animal or plant topic coverage.",
        ],
    }


def _profile_scenario(
    *,
    interest: str,
    base_seeds: Sequence[object],
    overlay_seeds: Sequence[object],
    neutral_rank_by_lemma: Mapping[str, int],
    overlay_rows_by_lemma: Mapping[str, Sequence[Mapping[str, object]]],
    profile_top_n: int,
) -> dict[str, object]:
    baseline = _rerank_view(
        interest=interest,
        seeds=base_seeds,
        neutral_rank_by_lemma=neutral_rank_by_lemma,
        overlay_rows_by_lemma=overlay_rows_by_lemma,
        profile_top_n=profile_top_n,
    )
    with_overlay = _rerank_view(
        interest=interest,
        seeds=overlay_seeds,
        neutral_rank_by_lemma=neutral_rank_by_lemma,
        overlay_rows_by_lemma=overlay_rows_by_lemma,
        profile_top_n=profile_top_n,
    )
    return {
        "interest": interest,
        "baseline": baseline,
        "with_overlay": with_overlay,
        "delta": {
            "overlay_topic_rows_in_top_n": int(with_overlay["overlay_topic_rows_in_top_n"])
            - int(baseline["overlay_topic_rows_in_top_n"]),
            "exact_interest_rows_in_top_n": int(with_overlay["exact_interest_rows_in_top_n"])
            - int(baseline["exact_interest_rows_in_top_n"]),
        },
    }


def _rerank_view(
    *,
    interest: str,
    seeds: Sequence[object],
    neutral_rank_by_lemma: Mapping[str, int],
    overlay_rows_by_lemma: Mapping[str, Sequence[Mapping[str, object]]],
    profile_top_n: int,
) -> dict[str, object]:
    _reranked, diagnostics = rerank_seed_words_for_profile(
        seeds,
        profile_context={"interests": [interest]},
        preview_limit=profile_top_n,
    )
    support_by_topic = {
        str(row.get("topic") or ""): row
        for row in _mapping_rows(_as_mapping(diagnostics.get("active_topic_support")).get("topics"))
    }
    top_rows = []
    overlay_topic_hits = 0
    exact_interest_hits = 0
    for preview in _mapping_rows(diagnostics.get("ranking_preview")):
        lemma = str(preview.get("lemma") or "")
        overlay_topics = sorted(
            {
                str(row.get("topic") or "")
                for row in overlay_rows_by_lemma.get(lemma, ())
                if str(row.get("topic") or "")
            }
        )
        traits = _as_mapping(preview.get("candidate_traits"))
        topic_hints = _string_list(traits.get("topic_hints"))
        has_interest_hint = interest in topic_hints
        if interest in overlay_topics and has_interest_hint:
            overlay_topic_hits += 1
        if has_interest_hint:
            exact_interest_hits += 1
        top_rows.append(
            {
                "rank": preview.get("reranked_rank"),
                "neutral_rank": neutral_rank_by_lemma.get(lemma),
                "lemma": lemma,
                "rank_delta": preview.get("rank_delta"),
                "admission_weight": preview.get("admission_weight"),
                "profile_score": preview.get("profile_score"),
                "topic_hints": topic_hints[:12],
                "overlay_topics": overlay_topics,
                "topic_affinity": _round_float(
                    _as_mapping(preview.get("signals")).get("topic_affinity")
                ),
                "topic_affinity_source": _as_mapping(preview.get("signals")).get(
                    "topic_affinity_source"
                ),
            }
        )
    return {
        "support": dict(_as_mapping(support_by_topic.get(interest))),
        "overlay_topic_rows_in_top_n": overlay_topic_hits,
        "exact_interest_rows_in_top_n": exact_interest_hits,
        "top_rows": top_rows,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    overlay_summary = _as_mapping(_as_mapping(report.get("topic_overlay")).get("summary"))
    lines = [
        "# en-es Animals/Plants Topic Overlay PoC",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Frequency DB: `{_as_mapping(report.get('inputs')).get('frequency_db', '')}`",
        f"- Overlay rows: `{overlay_summary.get('row_count', 0)}`",
        f"- Overlay topics: `{overlay_summary.get('counts_by_topic', {})}`",
        "",
        "## Findings",
        "",
    ]
    for finding in report.get("findings", []):
        item = _as_mapping(finding)
        lines.append(
            f"- `{item.get('level', '')}` `{item.get('code', '')}`: {item.get('message', '')}"
        )
    lines.extend(["", "## Profile Scenarios", ""])
    for scenario in _mapping_rows(report.get("profile_scenarios")):
        lines.extend(_scenario_markdown(scenario))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _scenario_markdown(scenario: Mapping[str, object]) -> list[str]:
    interest = str(scenario.get("interest") or "")
    baseline = _as_mapping(scenario.get("baseline"))
    with_overlay = _as_mapping(scenario.get("with_overlay"))
    delta = _as_mapping(scenario.get("delta"))
    lines = [
        f"### `{interest}`",
        "",
        f"- baseline overlay hits in top preview: `{baseline.get('overlay_topic_rows_in_top_n', 0)}`",
        f"- with-overlay hits in top preview: `{with_overlay.get('overlay_topic_rows_in_top_n', 0)}`",
        f"- overlay hit delta: `{delta.get('overlay_topic_rows_in_top_n', 0)}`",
        "",
        "| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |",
        "| ---: | --- | ---: | --- | --- | ---: | --- |",
    ]
    for row in _mapping_rows(with_overlay.get("top_rows")):
        lines.append(
            f"| {row.get('rank', '')} | `{row.get('lemma', '')}` | "
            f"{row.get('neutral_rank', '')} | `{', '.join(_string_list(row.get('topic_hints'))[:8])}` | "
            f"`{', '.join(_string_list(row.get('overlay_topics'))[:8])}` | "
            f"{row.get('topic_affinity', '')} | `{row.get('topic_affinity_source', '')}` |"
        )
    lines.append("")
    return lines


def _findings(
    *,
    overlay: Mapping[str, object],
    seeds: Sequence[object],
    scenarios: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    findings = []
    overlay_status = str(overlay.get("status") or "")
    if overlay_status == "ok":
        findings.append(
            _finding("PASS", "topic_overlay_ready", "Topic overlay candidate was built.")
        )
    else:
        findings.append(
            _finding("FAIL", "topic_overlay_not_ready", "Topic overlay candidate needs review.")
        )
    if seeds:
        findings.append(_finding("PASS", "seed_frontier_loaded", "SRS seed frontier loaded."))
    else:
        findings.append(_finding("FAIL", "seed_frontier_empty", "SRS seed frontier is empty."))
    for scenario in scenarios:
        interest = str(scenario.get("interest") or "")
        delta = _as_mapping(scenario.get("delta"))
        if int(delta.get("overlay_topic_rows_in_top_n") or 0) > 0:
            findings.append(
                _finding(
                    "PASS",
                    f"overlay_lifts_profile:{interest}",
                    "Overlay increases topic-labeled rows in the profile preview.",
                )
            )
        else:
            findings.append(
                _finding(
                    "WARN",
                    f"overlay_profile_delta_thin:{interest}",
                    "Overlay did not increase topic-labeled rows in the top preview.",
                )
            )
    return findings


def _summary(
    *,
    overlay: Mapping[str, object],
    scenarios: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "overlay_row_count": _as_mapping(overlay.get("summary")).get("row_count", 0),
        "overlay_counts_by_topic": _as_mapping(overlay.get("summary")).get("counts_by_topic", {}),
        "scenario_deltas": {
            str(row.get("interest") or ""): _as_mapping(row.get("delta")) for row in scenarios
        },
        "finding_counts": dict(Counter(str(row.get("level") or "") for row in findings)),
        "warnings": [row.get("code") for row in findings if row.get("level") == "WARN"],
        "issues": [row.get("code") for row in findings if row.get("level") == "FAIL"],
    }


def _seed_with_overlay(
    seed: object,
    overlay_rows: Sequence[Mapping[str, object]],
) -> object:
    if not overlay_rows:
        return seed
    metadata = dict(_as_mapping(getattr(seed, "metadata", {})))
    profile_topics = set(_string_list(metadata.get("profile_topics")))
    overlay_payload = []
    for row in overlay_rows:
        topic = str(row.get("topic") or "").strip()
        membership = _round_float(row.get("membership")) or 0.0
        if topic and membership >= PROFILE_INJECTION_MIN_MEMBERSHIP:
            profile_topics.add(topic)
        overlay_payload.append(
            {
                "topic": topic,
                "membership": row.get("membership"),
                "review_id": row.get("review_id"),
                "confidence_label": row.get("confidence_label"),
            }
        )
    metadata["profile_topics"] = sorted(profile_topics)
    metadata["topic_overlay_rows"] = overlay_payload
    if is_dataclass(seed):
        return replace(seed, metadata=metadata)
    seed.__dict__["metadata"] = metadata
    return seed


def _overlay_rows_by_lemma(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        lemma = str(row.get("lemma") or "").strip()
        if not lemma:
            continue
        grouped.setdefault(lemma, []).append(row)
    return {key: tuple(values) for key, values in grouped.items()}


def _frequency_db_from_review_packet(review_packet_payload: Mapping[str, object]) -> Path | None:
    audit_json = str(_as_mapping(review_packet_payload.get("inputs")).get("audit_json") or "")
    if not audit_json:
        return None
    audit_path = _resolve_path(Path(audit_json))
    if not audit_path.exists():
        return None
    audit_payload = _load_json(audit_path)
    frequency_db = str(_as_mapping(audit_payload.get("inputs")).get("frequency_db") or "")
    return Path(frequency_db).expanduser().resolve(strict=False) if frequency_db else None


def _rank_by_lemma(seeds: Sequence[object]) -> dict[str, int]:
    return {_seed_lemma(seed): index + 1 for index, seed in enumerate(seeds) if _seed_lemma(seed)}


def _seed_lemma(seed: object) -> str:
    return str(getattr(seed, "lemma", "") or "").strip()


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        return [stripped]
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _round_float(value: object) -> float | None:
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _resolve_path(path: Path) -> Path:
    path = Path(path).expanduser()
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve(strict=False)


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
