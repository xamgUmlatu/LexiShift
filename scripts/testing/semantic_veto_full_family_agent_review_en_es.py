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
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(Path(__file__).resolve().parent),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _escape_md,
    _load_json,
    _mapping_rows,
    _repo_path,
    _resolve_repo_path,
)


DEFAULT_PACKET_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_full_family_human_review_packet_en_es_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_full_family_agent_review_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_full_family_agent_review_en_es_latest.md"
DEFAULT_REVIEWS_JSON = TEST_INPUTS_ROOT / "semantic_veto_full_family_agent_reviews_en_es.json"
REVIEW_AUTHORITY = "codex_agent_review_user_approval_required"

VALID_ACTIVE_STATUSES = frozenset(
    {
        "aligned",
        "corrected_active_sense_required",
        "source_target_mapping_rejected",
        "source_form_artifact_rejected",
        "questionable_mapping_rejected",
    }
)
VALID_DISPOSITIONS = frozenset(
    {
        "aligned_mapping_rewrite_contexts",
        "aligned_mapping_shadow_rows_not_competitors",
        "salvage_with_corrected_active_sense",
        "source_target_mapping_rejected",
        "source_form_artifact_rejected",
        "questionable_mapping_rejected",
    }
)
VALID_ACTIONS = frozenset({"repair_pool", "exclude_from_trusted_eval"})


def _load_full_family_agent_reviews(
    path: Path = DEFAULT_REVIEWS_JSON,
) -> tuple[dict[str, object], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("family_reviews")
    if not isinstance(rows, list):
        raise ValueError(f"family_reviews missing from {path}")
    return tuple(dict(row) for row in rows if isinstance(row, dict))


FULL_FAMILY_AGENT_REVIEWS = _load_full_family_agent_reviews()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record a full agent semantic review over all 58 frozen en-es full-family "
            "representative sample families. This does not mark rows as user-approved."
        )
    )
    parser.add_argument("--packet-json", type=Path, default=DEFAULT_PACKET_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    packet_path = _resolve_repo_path(args.packet_json)
    json_out = _resolve_repo_path(args.json_out)
    markdown_out = _resolve_repo_path(args.markdown_out)
    report = build_full_family_agent_review_report(
        packet_payload=_load_json(packet_path),
        packet_path=packet_path,
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_full_family_agent_review_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_full_family_agent_review_report(
    *,
    packet_payload: Mapping[str, object],
    packet_path: Path | None = None,
    review_manifest: Sequence[Mapping[str, object]] = FULL_FAMILY_AGENT_REVIEWS,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    packet_families = _mapping_rows(packet_payload.get("family_review_rows"))
    review_rows, manifest_issues = _join_reviews(packet_families, review_manifest)
    issues = list(manifest_issues)
    if len(packet_families) != int(
        _as_mapping(packet_payload.get("summary")).get("dataset_family_count") or 0
    ):
        issues.append("packet_does_not_cover_full_dataset")
    if not review_rows:
        issues.append("no_review_rows")
    return {
        "schema_version": 1,
        "artifact_id": "semantic_veto_full_family_agent_review_en_es_v1",
        "pair": str(packet_payload.get("pair") or "en-es"),
        "status": "ok" if not issues else "review",
        "decision": "full_family_agent_review_complete_user_approval_required"
        if not issues
        else "full_family_agent_review_incomplete",
        "generated_at": generated_at,
        "review_authority": REVIEW_AUTHORITY,
        "inputs": {
            "packet_path": _repo_path(packet_path),
            "packet_decision": str(packet_payload.get("decision") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "score_promotion": "none",
            "review_unit": "source_target_family",
            "review_scope": "all frozen 58 representative-sample families",
            "row_authority": REVIEW_AUTHORITY,
            "trusted_row_rule": (
                "Rows remain untrusted until user approval and repaired case materialization. "
                "This artifact decides what is salvageable, rejected, or shadow-weak."
            ),
        },
        "summary": _summary(review_rows, issues),
        "issues": issues,
        "family_reviews": review_rows,
        "next_steps": [
            "Build a repaired full-family candidate only from repair_pool families.",
            "Drop rejected source-target mappings from trusted evaluation denominators.",
            "For shadow-weak families, keep positives but avoid counting same-target POS shadows as true competitors.",
            "Rerun scoring and band-formula sweeps only after repaired rows are materialized.",
        ],
    }


def render_full_family_agent_review_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Full-Family Agent Review",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Review authority: `{report.get('review_authority', '')}`",
        f"- Families reviewed: `{summary.get('family_count', 0)}`",
        f"- Repair-pool families: `{summary.get('repair_pool_family_count', 0)}`",
        f"- Excluded families: `{summary.get('excluded_family_count', 0)}`",
        "",
        "This is a full agent semantic review, not user-approved gold data. It tells us "
        "which of the 58 sampled source-target families are worth repairing before "
        "the next scorer or band-formula sweep.",
        "",
        "## Summary",
        "",
        _summary_table(summary),
        "",
        "## Dispositions",
        "",
        _family_table(report.get("family_reviews")),
        "",
        "## Issues",
        "",
        _issue_list(report.get("issues")),
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines).rstrip() + "\n"


def _join_reviews(
    packet_families: Sequence[Mapping[str, object]],
    review_manifest: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[str]]:
    issues: list[str] = []
    packet_by_key = {_key(row): row for row in packet_families}
    review_by_key: dict[tuple[str, str], Mapping[str, object]] = {}
    for row in review_manifest:
        key = _key(row)
        if key in review_by_key:
            issues.append(f"duplicate_review:{key[0]}->{key[1]}")
        review_by_key[key] = row
        if str(row.get("active_sense_status") or "") not in VALID_ACTIVE_STATUSES:
            issues.append(f"invalid_active_sense_status:{key[0]}->{key[1]}")
        if str(row.get("family_disposition") or "") not in VALID_DISPOSITIONS:
            issues.append(f"invalid_family_disposition:{key[0]}->{key[1]}")
        if str(row.get("scoring_action") or "") not in VALID_ACTIONS:
            issues.append(f"invalid_scoring_action:{key[0]}->{key[1]}")
    missing_reviews = sorted(set(packet_by_key) - set(review_by_key))
    unexpected_reviews = sorted(set(review_by_key) - set(packet_by_key))
    issues.extend(f"missing_review:{source}->{target}" for source, target in missing_reviews)
    issues.extend(f"unexpected_review:{source}->{target}" for source, target in unexpected_reviews)
    rows: list[dict[str, object]] = []
    for index, packet_row in enumerate(packet_families, start=1):
        key = _key(packet_row)
        review = review_by_key.get(key, {})
        cases = _mapping_rows(packet_row.get("case_review_rows"))
        shadows = _mapping_rows(packet_row.get("shadow_evidence"))
        disposition = str(review.get("family_disposition") or "")
        rows.append(
            {
                "review_index": index,
                "family_id": str(packet_row.get("family_id") or ""),
                "trigger": key[0],
                "target_lemma": key[1],
                "source_zipf_band_en": str(packet_row.get("source_zipf_band_en") or ""),
                "target_zipf_band_es": str(packet_row.get("target_zipf_band_es") or ""),
                "polysemy_band": str(packet_row.get("polysemy_band") or ""),
                "pos_shape": str(packet_row.get("pos_shape") or ""),
                "draft_case_count": len(cases),
                "draft_shadow_count": len(shadows),
                "active_sense_status": str(review.get("active_sense_status") or "missing"),
                "family_disposition": disposition or "missing",
                "scoring_action": str(review.get("scoring_action") or "missing"),
                "corrected_active_gloss": str(review.get("corrected_active_gloss") or ""),
                "case_policy": _case_policy(disposition=disposition, shadow_count=len(shadows)),
                "notes": str(review.get("notes") or ""),
            }
        )
    return rows, sorted(dict.fromkeys(issues))


def _case_policy(*, disposition: str, shadow_count: int) -> dict[str, str]:
    if disposition in {
        "source_target_mapping_rejected",
        "source_form_artifact_rejected",
        "questionable_mapping_rejected",
    }:
        return {
            "positive_active": "exclude_current_rows",
            "shadow_negative": "exclude_current_rows",
            "phrase_no_winner": "exclude_or_reauthor_only_after_replacement_family_exists",
        }
    if disposition == "salvage_with_corrected_active_sense":
        return {
            "positive_active": "rewrite_against_corrected_active_sense",
            "shadow_negative": "author_real_competitor_targets",
            "phrase_no_winner": "rewrite_realistic_no_winner",
        }
    if disposition == "aligned_mapping_shadow_rows_not_competitors":
        return {
            "positive_active": "rewrite_independent_contexts",
            "shadow_negative": "drop_or_relabel_same_target_shadows",
            "phrase_no_winner": "rewrite_realistic_no_winner",
        }
    return {
        "positive_active": "rewrite_independent_contexts",
        "shadow_negative": "author_real_competitor_targets" if shadow_count else "not_applicable",
        "phrase_no_winner": "rewrite_realistic_no_winner",
    }


def _summary(rows: Sequence[Mapping[str, object]], issues: Sequence[str]) -> dict[str, object]:
    action_counts = Counter(str(row.get("scoring_action") or "") for row in rows)
    disposition_counts = Counter(str(row.get("family_disposition") or "") for row in rows)
    active_counts = Counter(str(row.get("active_sense_status") or "") for row in rows)
    source_band_counts = Counter(str(row.get("source_zipf_band_en") or "") for row in rows)
    repair_rows = [row for row in rows if str(row.get("scoring_action") or "") == "repair_pool"]
    return {
        "issues": list(issues),
        "family_count": len(rows),
        "repair_pool_family_count": len(repair_rows),
        "excluded_family_count": action_counts.get("exclude_from_trusted_eval", 0),
        "draft_case_count": sum(int(row.get("draft_case_count") or 0) for row in rows),
        "draft_shadow_count": sum(int(row.get("draft_shadow_count") or 0) for row in rows),
        "scoring_action_counts": dict(sorted(action_counts.items())),
        "family_disposition_counts": dict(sorted(disposition_counts.items())),
        "active_sense_status_counts": dict(sorted(active_counts.items())),
        "source_band_counts": dict(sorted(source_band_counts.items())),
        "repair_pool_source_band_counts": dict(
            sorted(
                Counter(str(row.get("source_zipf_band_en") or "") for row in repair_rows).items()
            )
        ),
    }


def _summary_table(summary: Mapping[str, object]) -> str:
    lines = ["| Key | Value |", "| --- | --- |"]
    for key, value in summary.items():
        lines.append(
            f"| `{_escape_md(str(key))}` | `{_escape_md(json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value))}` |"
        )
    return "\n".join(lines)


def _family_table(value: object) -> str:
    rows = _mapping_rows(value)
    if not rows:
        return "_No family reviews._"
    lines = [
        "| # | Family | Source Band | Disposition | Action | Corrected Active | Notes |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row.get("review_index") or ""),
                    f"`{_escape_md(str(row.get('trigger') or ''))} -> {_escape_md(str(row.get('target_lemma') or ''))}`",
                    f"`{_escape_md(str(row.get('source_zipf_band_en') or ''))}`",
                    f"`{_escape_md(str(row.get('family_disposition') or ''))}`",
                    f"`{_escape_md(str(row.get('scoring_action') or ''))}`",
                    _escape_md(str(row.get("corrected_active_gloss") or "")),
                    _escape_md(str(row.get("notes") or "")),
                )
            )
            + " |"
        )
    return "\n".join(lines)


def _issue_list(value: object) -> str:
    rows = [str(item) for item in value or ()]
    if not rows:
        return "- `none`"
    return "\n".join(f"- `{_escape_md(row)}`" for row in rows)


def _key(row: Mapping[str, object]) -> tuple[str, str]:
    return (
        str(row.get("trigger") or "").strip(),
        str(row.get("target") or row.get("target_lemma") or "").strip(),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
