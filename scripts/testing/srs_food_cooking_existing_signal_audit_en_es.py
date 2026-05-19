#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping, Sequence

from srs_animals_plants_existing_signal_audit_en_es import (
    _candidate_lemmas,
    _first_translation_item,
    _is_primary_noun_sense,
    _safe_int,
    _sense_index,
    _sense_text,
    load_kaikki_rows,
    make_evidence,
    normalize_source_label,
    row_labels,
    summarize_family,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_POLICY = PROJECT_ROOT / "docs" / "test_inputs" / "srs_food_cooking_signal_policy_en_es.json"
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-es-cde.sqlite"
DEFAULT_KAIKKI_FORWARD_DB = DEFAULT_DATA_ROOT / "language_packs" / "wiktionary-es-en.sqlite"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_food_cooking_existing_signal_audit_en_es_current_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_food_cooking_existing_signal_audit_en_es_current_latest.md"
)
FAMILY = "food_cooking"


@dataclass(frozen=True)
class FoodPolicy:
    path: Path
    policy_id: str
    broad_excluded_labels: frozenset[str]
    ambiguous_context_labels: frozenset[str]
    topic_confidence: Mapping[str, float]
    category_confidence: Mapping[str, float]
    primary_translations: frozenset[str]
    primary_translation_reject_context_labels: Mapping[str, frozenset[str]]
    reviewed_signal_rejects: frozenset[tuple[str, str]]
    food_translation_pattern: re.Pattern[str]
    food_gloss_pattern: re.Pattern[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit how much food/cooking topic evidence can be extracted from existing "
            "local en-es sources. Read-only; no downloads and no pack mutation."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument("--top-n", type=int, default=10000)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        policy_path=args.policy_json,
        frequency_db=args.frequency_db,
        kaikki_forward_db=args.kaikki_forward_db,
        top_n=max(1, int(args.top_n)),
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
    policy_path: Path = DEFAULT_POLICY,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    kaikki_forward_db: Path = DEFAULT_KAIKKI_FORWARD_DB,
    top_n: int = 10000,
    generated_at: str | None = None,
) -> dict[str, object]:
    policy = load_food_policy(policy_path)
    frequency_path = Path(frequency_db).expanduser().resolve(strict=False)
    kaikki_path = Path(kaikki_forward_db).expanduser().resolve(strict=False)
    if not frequency_path.exists() or not kaikki_path.exists():
        findings = []
        if not frequency_path.exists():
            findings.append(_finding("FAIL", "frequency_db_missing", "Frequency DB is missing."))
        if not kaikki_path.exists():
            findings.append(_finding("FAIL", "kaikki_db_missing", "Kaikki DB is missing."))
        return _report(
            status="review",
            generated_at=generated_at,
            policy=policy,
            frequency_db=frequency_path,
            kaikki_forward_db=kaikki_path,
            top_n=top_n,
            row_count=0,
            family_summary=_empty_family_summary(),
            findings=findings,
            broad_exclusions=[],
        )

    lemmas = list(dict.fromkeys(_candidate_lemmas(frequency_path, top_n=top_n)))
    source_rows = load_kaikki_rows(kaikki_path)
    evidence_by_lemma = {}
    broad_exclusions: list[dict[str, object]] = []
    for lemma in lemmas:
        rows = source_rows.get(lemma, [])
        evidence = evidence_from_rows(lemma, rows, policy)
        if evidence:
            evidence_by_lemma[(FAMILY, lemma)] = evidence
        elif len(broad_exclusions) < 24:
            broad_hits = sorted(
                {
                    label
                    for row in rows
                    for label in row_labels(row)
                    if label in policy.broad_excluded_labels
                }
            )
            if broad_hits:
                broad_exclusions.append({"lemma": lemma, "excluded_labels": broad_hits})

    family_summary = summarize_family(FAMILY, lemmas, evidence_by_lemma)
    findings = [
        _finding("PASS", "existing_sources_loaded", "Frequency and Kaikki DBs are available."),
        _finding(
            "PASS",
            "food_cooking_overlap_allowed",
            "Food/cooking evidence may overlap animals or plants; overlap is a topic-membership feature, not a conflict.",
        ),
    ]
    if int(family_summary["candidate_count"]) > 0:
        findings.append(
            _finding(
                "PASS",
                "food_cooking_evidence_found",
                "Existing sources contain food/cooking evidence beyond direct sense topics.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "food_cooking_evidence_absent",
                "Existing sources found no food/cooking evidence.",
            )
        )
    return _report(
        status="ok" if not any(row["level"] == "FAIL" for row in findings) else "review",
        generated_at=generated_at,
        policy=policy,
        frequency_db=frequency_path,
        kaikki_forward_db=kaikki_path,
        top_n=top_n,
        row_count=len(lemmas),
        family_summary=family_summary,
        findings=findings,
        broad_exclusions=broad_exclusions,
    )


def evidence_from_rows(
    lemma: str, rows: Sequence[Mapping[str, object]], policy: FoodPolicy
) -> list[object]:
    evidence = []
    for row in rows:
        row_context = row_labels(row)
        ambiguity_penalty = _combined_penalty(row, row_context, policy)
        for topic_value in _string_list(row.get("topics")):
            topic = normalize_source_label(topic_value)
            if topic in policy.topic_confidence:
                evidence.append(
                    make_evidence(
                        family=FAMILY,
                        lemma=lemma,
                        tier="A",
                        evidence_type="explicit_sense_topic",
                        source_channel="sense_topics",
                        source_label=topic,
                        base_confidence=policy.topic_confidence[topic],
                        specificity=1.0,
                        ambiguity_penalty=ambiguity_penalty,
                        review_required=False,
                    )
                )
        for channel in ("sense_categories", "entry_categories", "sense_tags", "entry_tags"):
            for label in _string_list(row.get(channel)):
                normalized_label = normalize_source_label(label)
                if normalized_label not in policy.category_confidence:
                    continue
                if _reviewed_signal_rejected(lemma, normalized_label, policy):
                    continue
                evidence.append(
                    make_evidence(
                        family=FAMILY,
                        lemma=lemma,
                        tier="C",
                        evidence_type="allowlisted_category_or_tag",
                        source_channel=channel,
                        source_label=normalized_label,
                        base_confidence=policy.category_confidence[normalized_label],
                        specificity=0.95,
                        ambiguity_penalty=ambiguity_penalty,
                        review_required=True,
                    )
                )
        text_fields = _sense_text(row)
        primary = _primary_translation_match(text_fields["translation"], policy)
        if primary and _is_primary_noun_sense(row):
            source_label = f"primary_translation:{primary}"
            if _reviewed_signal_rejected(
                lemma, source_label, policy
            ) or _primary_translation_context_rejected(primary, row_context, policy):
                continue
            evidence.append(
                make_evidence(
                    family=FAMILY,
                    lemma=lemma,
                    tier="B",
                    evidence_type="primary_exact_translation",
                    source_channel="translation",
                    source_label=source_label,
                    base_confidence=0.9,
                    specificity=0.95,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=False,
                    snippet=text_fields["translation"][:160],
                )
            )
        elif policy.food_translation_pattern.search(
            text_fields["translation"]
        ) and not _reviewed_signal_rejected(lemma, "food_translation_pattern", policy):
            evidence.append(
                make_evidence(
                    family=FAMILY,
                    lemma=lemma,
                    tier="D",
                    evidence_type="narrow_translation_pattern",
                    source_channel="translation",
                    source_label="food_translation_pattern",
                    base_confidence=0.72,
                    specificity=0.9,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=True,
                    snippet=text_fields["translation"][:160],
                )
            )
        elif policy.food_gloss_pattern.search(
            text_fields["combined"]
        ) and not _reviewed_signal_rejected(lemma, "food_gloss_pattern", policy):
            evidence.append(
                make_evidence(
                    family=FAMILY,
                    lemma=lemma,
                    tier="D",
                    evidence_type="narrow_gloss_pattern",
                    source_channel="gloss_or_translation",
                    source_label="food_gloss_pattern",
                    base_confidence=0.62,
                    specificity=0.85,
                    ambiguity_penalty=ambiguity_penalty,
                    review_required=True,
                    snippet=text_fields["combined"][:160],
                )
            )
    return evidence


def load_food_policy(path: Path = DEFAULT_POLICY) -> FoodPolicy:
    resolved = Path(path).expanduser().resolve(strict=False)
    payload = _load_json(resolved)
    patterns = _as_mapping(payload.get("patterns"))
    return FoodPolicy(
        path=resolved,
        policy_id=str(payload.get("policy_id") or resolved.stem),
        broad_excluded_labels=frozenset(_normalized_list(payload.get("broad_excluded_labels"))),
        ambiguous_context_labels=frozenset(
            _normalized_list(payload.get("ambiguous_context_labels"))
        ),
        topic_confidence=_confidence_map(payload.get("topic_confidence")),
        category_confidence=_confidence_map(payload.get("category_confidence")),
        primary_translations=frozenset(
            str(item or "").strip().casefold()
            for item in _string_list(payload.get("primary_translations"))
            if str(item or "").strip()
        ),
        primary_translation_reject_context_labels=_translation_context_map(
            payload.get("primary_translation_reject_context_labels")
        ),
        reviewed_signal_rejects=frozenset(
            _reviewed_signal_rejects(payload.get("reviewed_signal_rejects"))
        ),
        food_translation_pattern=re.compile(str(patterns.get("food_translation") or r"(?!x)x")),
        food_gloss_pattern=re.compile(str(patterns.get("food_gloss") or r"(?!x)x")),
    )


def render_markdown(report: Mapping[str, object]) -> str:
    family = _as_mapping(report.get("family"))
    lines = [
        "# en-es Food/Cooking Existing Signal Audit",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate lemmas measured: `{report.get('row_count', 0)}`",
        f"- Food/cooking candidates: `{family.get('candidate_count', 0)}`",
        f"- Review-required candidates: `{family.get('review_required_count', 0)}`",
        "",
        "## Findings",
        "",
    ]
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Candidate share: `{family.get('candidate_share', 0)}`",
            f"- Tier counts: `{family.get('tier_counts', {})}`",
            f"- Confidence bands: `{family.get('confidence_band_counts', {})}`",
            "",
            "## Top Source Labels",
            "",
        ]
    )
    for row in _mapping_rows(family.get("top_source_labels")):
        lines.append(f"- `{row.get('label', '')}`: {row.get('count', 0)}")
    lines.extend(["", "## Top Candidates", ""])
    for row in _mapping_rows(family.get("top_candidates")):
        lines.append(
            f"- `{row.get('lemma', '')}`: `{row.get('confidence_band', '')}` "
            f"{row.get('confidence', 0)} via `{row.get('best_tier', '')}`"
        )
    lines.extend(["", "## Broad Exclusions Sample", ""])
    exclusions = _mapping_rows(report.get("broad_exclusions"))
    if not exclusions:
        lines.append("- _None captured._")
    for row in exclusions:
        lines.append(f"- `{row.get('lemma', '')}`: {', '.join(row.get('excluded_labels', []))}")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _report(
    *,
    status: str,
    generated_at: str | None,
    policy: FoodPolicy,
    frequency_db: Path,
    kaikki_forward_db: Path,
    top_n: int,
    row_count: int,
    family_summary: Mapping[str, object],
    findings: Sequence[Mapping[str, object]],
    broad_exclusions: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "food_cooking_existing_signal_audit_completed"
            if status == "ok"
            else "food_cooking_existing_signal_audit_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "signal_policy_json": str(policy.path),
            "signal_policy_id": policy.policy_id,
            "frequency_db": str(frequency_db),
            "kaikki_forward_db": str(kaikki_forward_db),
            "top_n": int(top_n),
        },
        "confidence_model": {
            "combiner": "max_evidence_score_v1",
            "score_formula": "base_confidence * specificity * ambiguity_penalty",
            "bands": {
                "high": ">= 0.85, eligible for strong review after policy adoption",
                "medium": ">= 0.65 and < 0.85, eligible for light lift or review",
                "review": ">= 0.45 and < 0.65, review-gated inventory",
                "inventory": "< 0.45, not counted as product-ready evidence",
            },
            "tier_policy": {
                "A": "explicit sense_topics, highest trust",
                "B": "primary-sense exact noun translation",
                "C": "allowlisted categories/tags from existing Kaikki fields",
                "D": "narrow translation/gloss patterns, review-gated",
            },
            "penalty_policy": {
                "secondary_sense": "0.70 multiplier for non-primary sense rows",
                "ambiguous_context": "0.70 multiplier when unrelated domain labels are present",
                "primary_translation_reject_context": "skip exact translation matches when policy-listed context labels prove the match is not food/cooking",
                "reviewed_signal_rejects": "skip lemma/source-label pairs already rejected by manual review",
            },
        },
        "row_count": int(row_count),
        "family": dict(family_summary),
        "broad_exclusions": list(broad_exclusions),
        "findings": list(findings),
        "summary": {
            "finding_counts": dict(Counter(row["level"] for row in findings)),
            "issues": [row["code"] for row in findings if row["level"] == "FAIL"],
            "warnings": [row["code"] for row in findings if row["level"] == "WARN"],
        },
        "limitations": [
            "This audit uses only existing local frequency and Kaikki/Wiktionary data.",
            "It does not write overlays, mutate packs, or change admission behavior.",
            "food/cooking can intentionally overlap animals and plants/nature.",
            "Category-derived food evidence needs review before product lift because many food labels are sense-specific.",
        ],
    }


def _combined_penalty(
    row: Mapping[str, object], row_context: set[str], policy: FoodPolicy
) -> float:
    penalty = 1.0
    if row_context & policy.ambiguous_context_labels:
        penalty *= 0.7
    if _safe_int(_sense_index(row)) > 0:
        penalty *= 0.7
    return penalty


def _primary_translation_match(translation: str, policy: FoodPolicy) -> str:
    item = _first_translation_item(translation)
    return item if item in policy.primary_translations else ""


def _primary_translation_context_rejected(
    primary: str, row_context: set[str], policy: FoodPolicy
) -> bool:
    rejected_context = policy.primary_translation_reject_context_labels.get(primary, frozenset())
    return bool(row_context & rejected_context)


def _reviewed_signal_rejected(lemma: str, source_label: str, policy: FoodPolicy) -> bool:
    return (_normalize_review_key_part(lemma), _normalize_review_key_part(source_label)) in (
        policy.reviewed_signal_rejects
    )


def _empty_family_summary() -> dict[str, object]:
    return {
        "family": FAMILY,
        "candidate_count": 0,
        "candidate_share": 0,
        "review_required_count": 0,
        "tier_counts": {},
        "confidence_band_counts": {band: 0 for band in ("high", "medium", "review", "inventory")},
        "top_source_labels": [],
        "candidate_inventory": [],
        "top_candidates": [],
        "review_candidates": [],
    }


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _confidence_map(value: object) -> dict[str, float]:
    if not isinstance(value, Mapping):
        return {}
    return {
        normalize_source_label(label): _safe_float(confidence)
        for label, confidence in value.items()
        if normalize_source_label(label)
    }


def _translation_context_map(value: object) -> dict[str, frozenset[str]]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, frozenset[str]] = {}
    for translation, labels in value.items():
        key = str(translation or "").strip().casefold()
        if not key:
            continue
        result[key] = frozenset(_normalized_list(labels))
    return result


def _reviewed_signal_rejects(value: object) -> list[tuple[str, str]]:
    rows = _mapping_rows(value)
    result: list[tuple[str, str]] = []
    for row in rows:
        lemma = _normalize_review_key_part(row.get("lemma"))
        source_label = _normalize_review_key_part(row.get("source_label"))
        if lemma and source_label:
            result.append((lemma, source_label))
    return result


def _normalize_review_key_part(value: object) -> str:
    return str(value or "").strip().casefold()


def _normalized_list(value: object) -> list[str]:
    return [normalize_source_label(item) for item in _string_list(value)]


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return []


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
