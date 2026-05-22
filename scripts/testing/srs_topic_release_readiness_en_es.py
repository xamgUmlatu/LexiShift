#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from srs_topic_release_overlay_summary import summarize_topic_overlays


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_TAXONOMY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_es.json"
)
DEFAULT_DEPTH_AUDIT = TEST_OUTPUTS_ROOT / "srs_topic_family_depth_audit_en_es_latest.json"
DEFAULT_OVERLAYS = (
    TEST_OUTPUTS_ROOT / "srs_animals_plants_topic_overlay_en_es_spalex_10k_latest.json",
    TEST_OUTPUTS_ROOT / "srs_food_cooking_topic_overlay_en_es_spalex_10k_latest.json",
    TEST_OUTPUTS_ROOT / "srs_wikidata_natural_taxonomy_topic_overlay_en_es_spalex_10k_latest.json",
    TEST_OUTPUTS_ROOT / "srs_source_topic_overlay_en_es_spalex_10k_latest.json",
    TEST_OUTPUTS_ROOT / "srs_obvious_topic_miss_overlay_en_es_spalex_10k_latest.json",
)
DEFAULT_SOURCE_PRECISION_REVIEW = (
    TEST_OUTPUTS_ROOT / "srs_source_topic_precision_review_en_es_spalex_10k_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_release_readiness_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_release_readiness_en_es_latest.md"
DEFAULT_FRONTIER_LABEL = "spalex_10k_research"

RELEASE_READY_MIN_COUNT = 100
RELEASE_READY_MIN_BANDS = 3
LIMITED_RELEASE_MIN_COUNT = 50
LIMITED_RELEASE_MIN_BANDS = 2
BETA_MIN_COUNT = 30
REGISTER_RELEASE_MIN_COUNT = 100
REGISTER_BETA_MIN_COUNT = 30


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify en-es SRS topic/register coverage readiness for first release "
            "from the topic-family depth audit plus reviewed overlay artifacts."
        )
    )
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--depth-audit-json", type=Path, default=DEFAULT_DEPTH_AUDIT)
    parser.add_argument("--frontier-label", default=DEFAULT_FRONTIER_LABEL)
    parser.add_argument(
        "--overlay-json",
        action="append",
        type=Path,
        default=[],
        help=(
            "Reviewed topic overlay JSON. May be repeated. Defaults to current "
            "animals/plants and food/cooking SPALEX 10k overlays."
        ),
    )
    parser.add_argument(
        "--source-precision-review-json",
        type=Path,
        default=DEFAULT_SOURCE_PRECISION_REVIEW,
        help=(
            "Optional sampled precision review for source-backed release candidates. "
            "Missing file leaves the readiness matrix unchanged."
        ),
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    overlay_paths = args.overlay_json if args.overlay_json else list(DEFAULT_OVERLAYS)
    report = build_report(
        taxonomy_payload=_load_json(args.taxonomy_json),
        depth_audit_payload=_load_json(args.depth_audit_json),
        overlay_payloads=[
            payload
            for payload in (_load_json_if_exists(path) for path in overlay_paths)
            if payload is not None
        ],
        source_precision_payload=_load_json_if_exists(args.source_precision_review_json),
        taxonomy_path=args.taxonomy_json,
        depth_audit_path=args.depth_audit_json,
        overlay_paths=overlay_paths,
        source_precision_path=args.source_precision_review_json,
        frontier_label=str(args.frontier_label),
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
    taxonomy_payload: Mapping[str, object],
    depth_audit_payload: Mapping[str, object],
    overlay_payloads: Sequence[Mapping[str, object]] = (),
    source_precision_payload: Mapping[str, object] | None = None,
    taxonomy_path: Path | None = None,
    depth_audit_path: Path | None = None,
    overlay_paths: Sequence[Path] = (),
    source_precision_path: Path | None = None,
    frontier_label: str = DEFAULT_FRONTIER_LABEL,
    generated_at: str | None = None,
) -> dict[str, object]:
    families = _taxonomy_families(taxonomy_payload)
    frontier = _resolve_frontier(depth_audit_payload, frontier_label=frontier_label)
    depth_by_family = {
        str(row.get("family") or ""): row for row in _mapping_rows(frontier.get("families"))
    }
    overlays = summarize_topic_overlays(overlay_payloads)
    topic_rows = [
        _readiness_row(family, depth_by_family.get(str(family.get("id") or ""), {}), overlays)
        for family in families
    ]
    source_precision = _source_precision_summary(source_precision_payload)
    topic_rows = [_with_source_precision(row, source_precision) for row in topic_rows]
    findings = _findings(
        topic_rows,
        frontier=frontier,
        overlays=overlays,
        source_precision=source_precision,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_release_readiness_classified"
            if status == "ok"
            else "srs_topic_release_readiness_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": "en-es",
        "inputs": {
            "taxonomy_json": _repo_path(taxonomy_path),
            "depth_audit_json": _repo_path(depth_audit_path),
            "frontier_label": str(frontier.get("label") or frontier_label),
            "overlay_json": [_repo_path(path) for path in overlay_paths],
            "source_precision_review_json": (
                _repo_path(source_precision_path) if source_precision.get("exists") else ""
            ),
        },
        "release_gate": _release_gate(),
        "frontier": {
            "label": str(frontier.get("label") or ""),
            "exists": bool(frontier.get("exists")),
            "seed_count": int(frontier.get("seed_count") or 0),
            "unique_lemma_count": int(frontier.get("unique_lemma_count") or 0),
        },
        "overlay_summary": overlays,
        "source_precision_review": source_precision,
        "topics": topic_rows,
        "summary": _summary(topic_rows, findings),
        "findings": findings,
        "limitations": [
            "This is a release-readiness classifier, not a new source audit.",
            "Runtime-eligible full-membership overlay rows are counted separately from source-derived trusted rows.",
            "Effective rows use the larger of source-trusted and runtime-eligible overlay counts to avoid optimistic double counting.",
            "Difficulty bands currently come from the source-depth audit; overlay rows do not yet carry a calibrated difficulty-band distribution.",
            "Source precision review is sampled compact evidence, not a full-universe precision estimate.",
            "Register rows are policy-review candidates, not ordinary interest topics.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    frontier = _as_mapping(report.get("frontier"))
    lines = [
        "# en-es SRS Topic Release Readiness",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Frontier: `{frontier.get('label', '')}` (`{frontier.get('seed_count', 0)}` seeds)",
        f"- Default-visible candidates: `{summary.get('default_visible_count', 0)}`",
        f"- Limited-visible candidates: `{summary.get('limited_visible_count', 0)}`",
        f"- Beta-visible candidates: `{summary.get('beta_visible_count', 0)}`",
        f"- Hidden/source-blocked candidates: `{summary.get('hidden_count', 0)}`",
        "",
        "## Release Gate",
        "",
    ]
    gate = _as_mapping(report.get("release_gate"))
    for key in (
        "release_ready",
        "limited_release",
        "beta_limited",
        "register_policy_review",
        "blocked",
    ):
        lines.append(f"- `{key}`: {gate.get(key, '')}")
    lines.extend(["", "## Source Precision Review", ""])
    precision = _as_mapping(report.get("source_precision_review"))
    if precision.get("exists"):
        lines.extend(
            [
                f"- Review state: `{precision.get('labels_state', '')}`",
                f"- Reviewed rows: `{precision.get('reviewed_count', 0)}`",
                f"- Accepted rows: `{precision.get('accepted_count', 0)}` "
                f"({_format_percent(precision.get('accepted_rate'))})",
                f"- Rejected rows: `{precision.get('rejected_count', 0)}` "
                f"({_format_percent(precision.get('rejected_rate'))})",
                f"- Pending rows: `{precision.get('pending_count', 0)}`",
                "- Families needing guard review: "
                f"`{', '.join(_string_list(precision.get('noisy_families'))) or 'none'}`",
            ]
        )
    else:
        lines.append("- _No sampled source precision review was available._")
    lines.extend(
        [
            "",
            "## Topic Matrix",
            "",
            "| Family | Axis | Status | Visibility | Effective Rows | Source Rows | Runtime Overlay Rows | Bands | Next Work |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in _mapping_rows(report.get("topics")):
        next_work = "; ".join(_string_list(row.get("next_work"))[:3])
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row.get('family', '')}`",
                    f"`{row.get('axis', '')}`",
                    f"`{row.get('release_status', '')}`",
                    f"`{row.get('recommended_visibility', '')}`",
                    str(row.get("effective_candidate_count", 0)),
                    str(row.get("source_trusted_candidate_count", 0)),
                    str(row.get("reviewed_overlay_candidate_count", 0)),
                    str(row.get("source_nonempty_band_count", 0)),
                    next_work,
                )
            )
            + " |"
        )
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Limitations", ""])
    for item in _string_list(report.get("limitations")):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _release_gate() -> dict[str, object]:
    return {
        "release_ready": (
            f">= {RELEASE_READY_MIN_COUNT} effective rows and "
            f">= {RELEASE_READY_MIN_BANDS} source difficulty bands"
        ),
        "limited_release": (
            f">= {LIMITED_RELEASE_MIN_COUNT} effective rows and "
            f">= {LIMITED_RELEASE_MIN_BANDS} source difficulty bands, or strong count "
            "with shallow depth explicitly labeled"
        ),
        "beta_limited": (
            f">= {BETA_MIN_COUNT} effective rows with at least one source difficulty band; "
            "ship only with limited/beta UX copy"
        ),
        "register_policy_review": (
            f">= {REGISTER_RELEASE_MIN_COUNT} review-only rows can be release candidates "
            "after register/style UX policy review"
        ),
        "blocked": (
            "0 effective rows, legal-source gated rows, or topics without a reviewed/source-backed "
            "candidate path stay hidden"
        ),
        "effective_row_policy": (
            "max(source trusted candidate count, reviewed overlay candidate count)"
        ),
    }


def _readiness_row(
    family: Mapping[str, object],
    depth: Mapping[str, object],
    overlays: Mapping[str, object],
) -> dict[str, object]:
    family_id = str(family.get("id") or "").strip()
    axis = str(family.get("axis") or "topic").strip() or "topic"
    source_count = int(depth.get("trusted_candidate_count") or 0)
    overlay_by_topic = _as_mapping(overlays.get("by_topic"))
    overlay = _as_mapping(overlay_by_topic.get(family_id))
    overlay_count = int(overlay.get("row_count") or 0)
    review_only_count = int(depth.get("review_only_candidate_count") or 0)
    effective_count = max(source_count, overlay_count)
    if axis == "register":
        effective_count = max(effective_count, review_only_count)
    band_count = int(depth.get("trusted_nonempty_band_count") or 0)
    status, visibility, next_work = _classify(
        axis=axis,
        readiness_state=str(family.get("readiness_state") or ""),
        effective_count=effective_count,
        source_count=source_count,
        overlay_count=overlay_count,
        review_only_count=review_only_count,
        band_count=band_count,
    )
    return {
        "family": family_id,
        "display_name": str(family.get("display_name") or family_id),
        "axis": axis,
        "product_priority": str(family.get("product_priority") or ""),
        "readiness_state": str(family.get("readiness_state") or ""),
        "data_strategy": str(family.get("data_strategy") or ""),
        "release_status": status,
        "recommended_visibility": visibility,
        "effective_candidate_count": effective_count,
        "effective_candidate_source": (
            "review_only_register"
            if axis == "register" and review_only_count >= effective_count
            else "reviewed_overlay"
            if overlay_count >= source_count and overlay_count > 0
            else "source_depth"
            if source_count > 0
            else "none"
        ),
        "source_trusted_candidate_count": source_count,
        "source_nonempty_band_count": band_count,
        "source_max_difficulty": depth.get("trusted_max_difficulty"),
        "source_coverage_posture": str(depth.get("coverage_posture") or ""),
        "reviewed_overlay_candidate_count": overlay_count,
        "reviewed_overlay_confidence_counts": dict(
            _as_mapping(overlay.get("counts_by_confidence"))
        ),
        "review_only_candidate_count": review_only_count,
        "next_work": next_work,
    }


def _source_precision_summary(
    source_precision_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    if not source_precision_payload:
        return {"exists": False, "by_family": {}}
    summary = _as_mapping(source_precision_payload.get("summary"))
    by_family = {
        str(row.get("label") or ""): row
        for row in _mapping_rows(source_precision_payload.get("precision_by_family"))
    }
    noisy_families = [
        family
        for family, row in sorted(by_family.items())
        if float(row.get("rejected_rate") or 0) >= 0.4
    ]
    label_result = _as_mapping(source_precision_payload.get("label_result"))
    return {
        "exists": True,
        "decision": str(source_precision_payload.get("decision") or ""),
        "labels_state": str(label_result.get("labels_state") or ""),
        "reviewed_count": int(summary.get("count") or 0),
        "accepted_count": int(summary.get("accepted_count") or 0),
        "accepted_rate": float(summary.get("accepted_rate") or 0),
        "rejected_count": int(summary.get("rejected_count") or 0),
        "rejected_rate": float(summary.get("rejected_rate") or 0),
        "pending_count": int(summary.get("pending_count") or 0),
        "noisy_families": noisy_families,
        "by_family": by_family,
    }


def _with_source_precision(
    row: Mapping[str, object],
    source_precision: Mapping[str, object],
) -> dict[str, object]:
    next_row = dict(row)
    family = str(next_row.get("family") or "")
    by_family = _as_mapping(source_precision.get("by_family"))
    family_precision = _as_mapping(by_family.get(family))
    if not family_precision:
        next_row["source_precision_review"] = {}
        return next_row

    precision = {
        "reviewed_count": int(family_precision.get("count") or 0),
        "accepted_count": int(family_precision.get("accepted_count") or 0),
        "accepted_rate": float(family_precision.get("accepted_rate") or 0),
        "rejected_count": int(family_precision.get("rejected_count") or 0),
        "rejected_rate": float(family_precision.get("rejected_rate") or 0),
        "strong_count": int(family_precision.get("strong_count") or 0),
        "light_count": int(family_precision.get("light_count") or 0),
    }
    next_row["source_precision_review"] = precision
    release_status = str(next_row.get("release_status") or "")
    next_work = [
        item
        for item in _string_list(next_row.get("next_work"))
        if item != "run sampled precision review"
    ]
    if release_status == "release_candidate":
        if precision["rejected_rate"] >= 0.4:
            next_work.insert(0, "tighten source-label guards before default promotion")
        else:
            next_work.insert(0, "review light-topic scalar handling before default promotion")
    next_row["next_work"] = next_work
    return next_row


def _classify(
    *,
    axis: str,
    readiness_state: str,
    effective_count: int,
    source_count: int,
    overlay_count: int,
    review_only_count: int,
    band_count: int,
) -> tuple[str, str, list[str]]:
    if axis == "register":
        if review_only_count >= REGISTER_RELEASE_MIN_COUNT:
            return (
                "register_release_candidate_policy_review",
                "visible_after_policy_review",
                [
                    "run sampled precision review for register/style labels",
                    "decide whether this appears in the same UX section as topics",
                    "lab-smoke register preference behavior before promotion",
                ],
            )
        if review_only_count >= REGISTER_BETA_MIN_COUNT:
            return (
                "register_beta_candidate_policy_review",
                "beta_after_policy_review",
                [
                    "expand or review register labels to reach the release-candidate floor",
                    "define register/style UX copy and storage semantics",
                    "lab-smoke register preference behavior before promotion",
                ],
            )
        return (
            "register_enrichment_required",
            "hidden_until_enriched",
            [
                "collect more reviewed register/style evidence",
                "define register/style UX policy before exposure",
            ],
        )

    if readiness_state == "legal_source_gated":
        return (
            "blocked_legal_source_required",
            "hidden_until_licensed_source",
            [
                "identify a legally usable source or internal taxonomy",
                "build a review packet from that source",
                "generate a reviewed overlay and rerun release readiness",
            ],
        )
    if effective_count <= 0:
        return (
            "blocked_source_required",
            "hidden_until_source_backed",
            [
                "identify a source or curated seed list",
                "build a sampled review packet",
                "generate a reviewed overlay and rerun the lab",
            ],
        )
    if effective_count >= RELEASE_READY_MIN_COUNT and band_count >= RELEASE_READY_MIN_BANDS:
        return (
            "release_candidate",
            "default_visible",
            [
                "run sampled precision review",
                "freeze release evidence in the readiness artifact",
                "lab-smoke preference strength across proficiency values",
            ],
        )
    if effective_count >= RELEASE_READY_MIN_COUNT and band_count >= LIMITED_RELEASE_MIN_BANDS:
        return (
            "release_candidate_limited_depth",
            "visible_with_limited_depth_note",
            [
                "run sampled precision review",
                "add mid/hard-band enrichment if release UX needs smoother progression",
                "lab-smoke preference strength across proficiency values",
            ],
        )
    if effective_count >= LIMITED_RELEASE_MIN_COUNT and band_count >= LIMITED_RELEASE_MIN_BANDS:
        return (
            "limited_release_candidate",
            "visible_with_limited_depth_note",
            [
                "run sampled precision review",
                "add more reviewed rows if the lab still feels clumpy",
                "lab-smoke preference strength across proficiency values",
            ],
        )
    if effective_count >= LIMITED_RELEASE_MIN_COUNT and overlay_count >= LIMITED_RELEASE_MIN_COUNT:
        return (
            "limited_release_candidate_overlay_only",
            "visible_with_limited_depth_note",
            [
                "derive difficulty-band coverage for reviewed overlay rows",
                "run sampled precision review on the broader overlay",
                "lab-smoke preference strength across proficiency values",
            ],
        )
    if effective_count >= BETA_MIN_COUNT and band_count >= 1:
        return (
            "beta_limited_candidate",
            "beta_visible_or_hidden",
            [
                "add enough reviewed rows to reach the limited-release floor",
                "improve difficulty spread beyond one or two bands",
                "label the topic as limited/beta if exposed",
            ],
        )
    return (
        "enrichment_required",
        "hidden_until_enriched",
        [
            "add reviewed source or curated overlay rows",
            "target at least two difficulty bands",
            "rerun the release-readiness classifier",
        ],
    )


def _taxonomy_families(taxonomy: Mapping[str, object]) -> list[Mapping[str, object]]:
    return [
        row for row in _mapping_rows(taxonomy.get("families")) if str(row.get("id") or "").strip()
    ]


def _resolve_frontier(
    depth_audit: Mapping[str, object],
    *,
    frontier_label: str,
) -> Mapping[str, object]:
    frontiers = _mapping_rows(depth_audit.get("frontiers"))
    for row in frontiers:
        if str(row.get("label") or "") == frontier_label:
            return row
    for row in reversed(frontiers):
        if row.get("exists"):
            return row
    return {}


def _findings(
    topic_rows: Sequence[Mapping[str, object]],
    *,
    frontier: Mapping[str, object],
    overlays: Mapping[str, object],
    source_precision: Mapping[str, object],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if frontier.get("exists"):
        findings.append(
            _finding(
                "PASS",
                "frontier_available",
                "Release-readiness frontier is available.",
            )
        )
    else:
        findings.append(
            _finding(
                "FAIL",
                "frontier_missing",
                "Release-readiness frontier is missing.",
            )
        )
    if _as_mapping(overlays.get("by_topic")):
        findings.append(
            _finding(
                "PASS",
                "reviewed_overlays_available",
                "Reviewed topic overlay artifacts are available.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "reviewed_overlays_absent",
                "No reviewed overlay artifacts were available.",
            )
        )

    counts = Counter(str(row.get("release_status") or "") for row in topic_rows)
    if counts.get("blocked_source_required", 0) or counts.get("blocked_legal_source_required", 0):
        findings.append(
            _finding(
                "WARN",
                "some_topics_blocked",
                "Some topic families should stay hidden until source or legal blockers clear.",
            )
        )
    if counts.get("release_candidate", 0) > 0:
        findings.append(
            _finding(
                "PASS",
                "release_candidates_present",
                "At least one topic family meets the default release-candidate floor.",
            )
        )
    if source_precision.get("exists"):
        findings.append(
            _finding(
                "PASS",
                "source_precision_review_available",
                "Sampled source precision review is available.",
            )
        )
        if _string_list(source_precision.get("noisy_families")):
            findings.append(
                _finding(
                    "WARN",
                    "source_precision_guards_needed",
                    "Some default-visible source topics need guard review before promotion.",
                )
            )
        if int(source_precision.get("pending_count") or 0) > 0:
            findings.append(
                _finding(
                    "WARN",
                    "source_precision_review_pending",
                    "Some source-backed release candidates still need sampled precision labels.",
                )
            )
    return findings


def _summary(
    topic_rows: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    status_counts = Counter(str(row.get("release_status") or "") for row in topic_rows)
    visibility_counts = Counter(str(row.get("recommended_visibility") or "") for row in topic_rows)
    return {
        "topic_count": len(topic_rows),
        "release_status_counts": dict(status_counts),
        "visibility_counts": dict(visibility_counts),
        "default_visible_count": visibility_counts.get("default_visible", 0),
        "limited_visible_count": visibility_counts.get("visible_with_limited_depth_note", 0)
        + visibility_counts.get("visible_after_policy_review", 0),
        "beta_visible_count": visibility_counts.get("beta_visible_or_hidden", 0)
        + visibility_counts.get("beta_after_policy_review", 0),
        "hidden_count": visibility_counts.get("hidden_until_enriched", 0)
        + visibility_counts.get("hidden_until_source_backed", 0)
        + visibility_counts.get("hidden_until_licensed_source", 0),
        "finding_counts": dict(Counter(str(row.get("level") or "") for row in findings)),
        "issues": [row.get("code") for row in findings if row.get("level") == "FAIL"],
        "warnings": [row.get("code") for row in findings if row.get("level") == "WARN"],
    }


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(_resolve_path(path).read_text(encoding="utf-8"))
    return _as_mapping(payload)


def _load_json_if_exists(path: Path) -> Mapping[str, object] | None:
    resolved = _resolve_path(path)
    if not resolved.exists():
        return None
    return _load_json(resolved)


def _resolve_path(path: Path) -> Path:
    expanded = Path(path).expanduser()
    if expanded.is_absolute():
        return expanded
    return PROJECT_ROOT / expanded


def _repo_path(path: Path | None) -> str | None:
    if path is None:
        return None
    resolved = _resolve_path(path)
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _format_percent(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


if __name__ == "__main__":
    raise SystemExit(main())
