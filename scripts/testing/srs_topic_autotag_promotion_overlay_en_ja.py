#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_evidence_en_ja import (  # noqa: E402
    _as_mapping,
    _has_kaikki_weak_label_anchor,
    _lemma_is_topic_literal,
    _mapping_rows,
    _normalize_label,
    _safe_float,
    _safe_int,
    _string_list,
    _wiki_lemma_is_topic_literal,
    _wiki_title_corroborates_source_label,
)


DEFAULT_CANDIDATES_CSV = (
    PROJECT_ROOT
    / "core"
    / "lexishift_core"
    / "resources"
    / "srs"
    / "en_ja"
    / "learner_difficulty_corrected.csv"
)
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
DEFAULT_REVIEWED_OVERLAY_JSON = TEST_OUTPUTS_ROOT / "srs_jmdict_topic_overlay_en_ja_latest.json"
DEFAULT_REVIEW_LABELS_JSON = TEST_INPUTS_ROOT / "srs_jmdict_topic_review_labels_en_ja.json"
DEFAULT_AUTO_REVIEW_LABELS_JSON = TEST_INPUTS_ROOT / "srs_topic_auto_review_labels_en_ja.json"
DEFAULT_LOCAL_EVIDENCE_JSON = TEST_OUTPUTS_ROOT / "srs_topic_autotag_evidence_en_ja_latest.json"
DEFAULT_DUMP_EVIDENCE_JSON = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_dump_source_bakeoff_en_ja_latest.json"
)
DEFAULT_WIKIDATA_EVIDENCE_JSON = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_claim_probe_en_ja_latest.json"
)
DEFAULT_MANUAL_SEMANTIC_EVIDENCE_JSON = (
    TEST_OUTPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_ja_latest.json"
)
DEFAULT_OVERLAY_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_promotion_overlay_en_ja_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_promotion_overlay_report_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_autotag_promotion_overlay_en_ja_latest.md"
LANGUAGE_PAIR = "en-ja"
PROFILE_INJECTION_MIN_MEMBERSHIP = 1.0
REVIEW_ONLY_MEMBERSHIP = 0.65
RUNTIME_MEMBERSHIP = 1.0
AUTO_REVIEW_ACCEPT_DECISIONS = {
    "accept_runtime",
    "accept_strong_topic",
    "accept_topic",
}
AUTO_REVIEW_REJECT_DECISIONS = {
    "reject_secondary_or_obscure_sense",
    "reject_too_broad",
    "reject_wrong_sense",
    "reject_wrong_topic",
}
AUTO_REVIEW_REVIEW_ONLY_DECISIONS = {
    "accept_light_topic",
    "accept_review_only",
    "review_uncertain",
}

KAIKKI_STRICT_LABELS = {
    "anatomy",
    "anime",
    "astronomy",
    "aviation",
    "baseball",
    "beverages",
    "biology",
    "board games",
    "botany",
    "card games",
    "chemistry",
    "chess",
    "comics",
    "computing",
    "cooking",
    "dentistry",
    "economics",
    "entomology",
    "film",
    "finance",
    "food",
    "geography",
    "go",
    "golf",
    "history",
    "horticulture",
    "internet",
    "law",
    "literature",
    "mahjong",
    "manga",
    "mathematics",
    "medicine",
    "music",
    "pathology",
    "pharmacology",
    "physics",
    "plants",
    "politics",
    "railways",
    "shogi",
    "soccer",
    "sumo",
    "technology",
    "television",
    "tennis",
    "transport",
    "travel",
    "video games",
    "zoology",
}
KAIKKI_ANCHORED_WEAK_LABELS = {"business", "engineering", "media"}
SPLIT_PARENT_TOPIC_LABEL_REMAP = {
    "finance_business": {
        "business": "work_office",
        "commerce": "shopping_money",
        "currency": "shopping_money",
        "economics": "shopping_money",
        "finance": "shopping_money",
        "money": "shopping_money",
        "retail": "shopping_money",
        "stock market": "shopping_money",
    },
    "science_technology": {
        "astronomy": "science_math",
        "biochemistry": "science_math",
        "biology": "science_math",
        "botany": "science_math",
        "chemistry": "science_math",
        "computing": "computing_internet",
        "electricity, elec. eng.": "computing_internet",
        "electronics": "computing_internet",
        "engineering": "computing_internet",
        "genetics": "science_math",
        "geology": "science_math",
        "geometry": "science_math",
        "internet": "computing_internet",
        "mathematics": "science_math",
        "physics": "science_math",
        "software": "computing_internet",
        "technology": "computing_internet",
        "telecommunications": "computing_internet",
    },
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export a conservative en-ja SRS topic overlay candidate from reviewed "
            "JMDict rows plus strict topic-autotag evidence. This does not install "
            "or default-enable runtime topic admission."
        )
    )
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES_CSV)
    parser.add_argument("--reviewed-overlay-json", type=Path, default=DEFAULT_REVIEWED_OVERLAY_JSON)
    parser.add_argument("--review-labels-json", type=Path, default=DEFAULT_REVIEW_LABELS_JSON)
    parser.add_argument(
        "--auto-review-labels-json", type=Path, default=DEFAULT_AUTO_REVIEW_LABELS_JSON
    )
    parser.add_argument("--local-evidence-json", type=Path, default=DEFAULT_LOCAL_EVIDENCE_JSON)
    parser.add_argument("--dump-evidence-json", type=Path, default=DEFAULT_DUMP_EVIDENCE_JSON)
    parser.add_argument(
        "--wikidata-evidence-json", type=Path, default=DEFAULT_WIKIDATA_EVIDENCE_JSON
    )
    parser.add_argument(
        "--manual-semantic-evidence-json", type=Path, default=DEFAULT_MANUAL_SEMANTIC_EVIDENCE_JSON
    )
    parser.add_argument("--overlay-json-out", type=Path, default=DEFAULT_OVERLAY_JSON_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        candidates_csv=_resolve_path(args.candidates_csv),
        reviewed_overlay_json=_resolve_path(args.reviewed_overlay_json),
        review_labels_json=_resolve_path(args.review_labels_json),
        auto_review_labels_json=_resolve_path(args.auto_review_labels_json),
        local_evidence_json=_resolve_path(args.local_evidence_json),
        dump_evidence_json=_resolve_path(args.dump_evidence_json),
        wikidata_evidence_json=_resolve_path(args.wikidata_evidence_json),
        manual_semantic_evidence_json=_resolve_path(args.manual_semantic_evidence_json),
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
    candidates_csv: Path = DEFAULT_CANDIDATES_CSV,
    reviewed_overlay_json: Path = DEFAULT_REVIEWED_OVERLAY_JSON,
    review_labels_json: Path = DEFAULT_REVIEW_LABELS_JSON,
    auto_review_labels_json: Path = DEFAULT_AUTO_REVIEW_LABELS_JSON,
    local_evidence_json: Path = DEFAULT_LOCAL_EVIDENCE_JSON,
    dump_evidence_json: Path = DEFAULT_DUMP_EVIDENCE_JSON,
    wikidata_evidence_json: Path = DEFAULT_WIKIDATA_EVIDENCE_JSON,
    manual_semantic_evidence_json: Path = DEFAULT_MANUAL_SEMANTIC_EVIDENCE_JSON,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    candidates = _load_candidate_index(candidates_csv)
    reviewed_overlay = _load_json_or_empty(reviewed_overlay_json)
    review_labels = _load_json_or_empty(review_labels_json)
    auto_review_labels = _load_json_or_empty(auto_review_labels_json)
    local_evidence = _load_json_or_empty(local_evidence_json)
    dump_evidence = _load_json_or_empty(dump_evidence_json)
    wikidata_evidence = _load_json_or_empty(wikidata_evidence_json)
    manual_semantic_evidence = _load_json_or_empty(manual_semantic_evidence_json)
    manual_rejected_keys = _manual_rejected_keys(review_labels)
    auto_review_index = _auto_review_label_index(auto_review_labels)
    rows_by_key: dict[tuple[str, str], dict[str, object]] = {}
    excluded: Counter[str] = Counter()

    for row in _mapping_rows(reviewed_overlay.get("rows")):
        overlay_row = _promoted_row_from_reviewed_overlay(
            row,
            candidates=candidates,
            reviewed_overlay_json=reviewed_overlay_json,
        )
        if not overlay_row:
            excluded["reviewed_overlay:invalid_row"] += 1
            continue
        _merge_overlay_row(rows_by_key, overlay_row, preserve_existing_membership=False)

    for row in _mapping_rows(manual_semantic_evidence.get("evidence_rows")):
        promotion_rule = _autotag_promotion_rule(row)
        if not promotion_rule:
            excluded[f"{row.get('source')}:not_promotion_ready"] += 1
            continue
        key = (str(row.get("lemma") or ""), _promotion_topic(row))
        if key in manual_rejected_keys:
            excluded[f"{row.get('source')}:manual_review_rejected_key"] += 1
            continue
        overlay_row = _promoted_row_from_evidence(
            row,
            candidates=candidates,
            promotion_rule=promotion_rule,
            evidence_json=manual_semantic_evidence_json,
        )
        if not overlay_row:
            excluded[f"{row.get('source')}:invalid_row"] += 1
            continue
        _merge_overlay_row(rows_by_key, overlay_row, preserve_existing_membership=True)

    for row in _mapping_rows(dump_evidence.get("evidence_rows")):
        promotion_rule = _autotag_promotion_rule(row)
        if not promotion_rule:
            excluded[f"{row.get('source')}:not_promotion_ready"] += 1
            continue
        key = (str(row.get("lemma") or ""), _promotion_topic(row))
        if key in manual_rejected_keys:
            excluded[f"{row.get('source')}:manual_review_rejected_key"] += 1
            continue
        auto_review_label = _lookup_auto_review_label(row, topic=key[1], labels=auto_review_index)
        auto_decision = str(auto_review_label.get("decision") or "")
        if auto_decision in AUTO_REVIEW_REJECT_DECISIONS:
            excluded[f"{row.get('source')}:auto_review_rejected:{auto_decision}"] += 1
            continue
        overlay_row = _promoted_row_from_evidence(
            row,
            candidates=candidates,
            promotion_rule=promotion_rule,
            evidence_json=dump_evidence_json,
            auto_review_label=auto_review_label,
        )
        if not overlay_row:
            excluded[f"{row.get('source')}:invalid_row"] += 1
            continue
        _merge_overlay_row(rows_by_key, overlay_row, preserve_existing_membership=True)

    for row in _mapping_rows(wikidata_evidence.get("evidence_rows")):
        promotion_rule = _autotag_promotion_rule(row)
        if not promotion_rule:
            excluded[f"{row.get('source')}:not_promotion_ready"] += 1
            continue
        key = (str(row.get("lemma") or ""), _promotion_topic(row))
        if key in manual_rejected_keys:
            excluded[f"{row.get('source')}:manual_review_rejected_key"] += 1
            continue
        auto_review_label = _lookup_auto_review_label(row, topic=key[1], labels=auto_review_index)
        auto_decision = str(auto_review_label.get("decision") or "")
        if auto_decision in AUTO_REVIEW_REJECT_DECISIONS:
            excluded[f"{row.get('source')}:auto_review_rejected:{auto_decision}"] += 1
            continue
        overlay_row = _promoted_row_from_evidence(
            row,
            candidates=candidates,
            promotion_rule=promotion_rule,
            evidence_json=wikidata_evidence_json,
            auto_review_label=auto_review_label,
        )
        if not overlay_row:
            excluded[f"{row.get('source')}:invalid_row"] += 1
            continue
        _merge_overlay_row(rows_by_key, overlay_row, preserve_existing_membership=True)

    rows = sorted(rows_by_key.values(), key=lambda item: (str(item["topic"]), str(item["lemma"])))
    overlay = _topic_overlay(
        rows=rows,
        generated_at=generated_at,
        reviewed_overlay=reviewed_overlay,
        reviewed_overlay_json=reviewed_overlay_json,
        review_labels_json=review_labels_json,
        auto_review_labels=auto_review_labels,
        auto_review_labels_json=auto_review_labels_json,
        local_evidence=local_evidence,
        local_evidence_json=local_evidence_json,
        dump_evidence=dump_evidence,
        dump_evidence_json=dump_evidence_json,
        wikidata_evidence=wikidata_evidence,
        wikidata_evidence_json=wikidata_evidence_json,
        manual_semantic_evidence=manual_semantic_evidence,
        manual_semantic_evidence_json=manual_semantic_evidence_json,
        candidates_csv=candidates_csv,
        excluded=excluded,
    )
    findings = _findings(
        overlay=overlay,
        candidates=candidates,
        reviewed_overlay=reviewed_overlay,
        dump_evidence=dump_evidence,
        wikidata_evidence=wikidata_evidence,
        manual_semantic_evidence=manual_semantic_evidence,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_autotag_promotion_overlay_ready"
            if status == "ok"
            else "srs_topic_autotag_promotion_overlay_needs_review"
        ),
        "generated_at": generated_at,
        "language_pair": LANGUAGE_PAIR,
        "inputs": {
            "candidates_csv": _repo_path(candidates_csv),
            "reviewed_overlay_json": _repo_path(reviewed_overlay_json),
            "review_labels_json": _repo_path(review_labels_json),
            "auto_review_labels_json": _repo_path(auto_review_labels_json),
            "local_evidence_json": _repo_path(local_evidence_json),
            "dump_evidence_json": _repo_path(dump_evidence_json),
            "wikidata_evidence_json": _repo_path(wikidata_evidence_json),
            "manual_semantic_evidence_json": _repo_path(manual_semantic_evidence_json),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "helper_state_mutation": "none",
            "promotion_model": (
                "preserve already reviewed JMDict overlay rows; add only strict "
                "Kaikki/Wiktionary, Japanese Wikipedia dump, Wikidata claim-probe, "
                "and product-owned manual semantic lexicon evidence; never re-promote "
                "manual review rejected lemma-topic keys"
            ),
            "runtime_identity_policy": (
                "current runtime topic overlays apply by lemma, so auto-promoted rows "
                "are runtime-effective only when the lemma has one corrected reading, "
                "the candidate is normal_vocab, and topic stretch is not disabled"
            ),
        },
        "topic_overlay": overlay,
        "summary": _report_summary(overlay=overlay, findings=findings),
        "findings": findings,
        "limitations": [
            "This is a product-safe candidate overlay, not a default-enabled runtime artifact.",
            "Rows with membership below 1.0 are retained as review evidence but are not runtime-effective under the current overlay contract.",
            "The current runtime overlay key is lemma-only; reading-specific topic membership needs a runtime schema change before it can be safely admitted.",
            "This export intentionally favors precision over coverage and therefore leaves many plausible topic rows in the review-candidate pool.",
        ],
    }


def _promoted_row_from_reviewed_overlay(
    row: Mapping[str, object],
    *,
    candidates: Mapping[str, Mapping[str, object]],
    reviewed_overlay_json: Path,
) -> dict[str, object] | None:
    lemma = str(row.get("lemma") or "").strip()
    raw_topic = str(row.get("topic") or "").strip()
    topic = _promotion_topic(row)
    if not lemma or not topic:
        return None
    candidate_info = candidates.get(lemma, {})
    existing_membership = _safe_float(row.get("membership"), default=0.0)
    runtime_blockers = _runtime_blockers(
        row,
        candidate_info=candidate_info,
        respect_existing_review=True,
    )
    membership = (
        min(existing_membership, REVIEW_ONLY_MEMBERSHIP)
        if runtime_blockers
        else existing_membership
    )
    confidence_label = str(row.get("confidence_label") or "")
    if runtime_blockers:
        confidence_label = "reviewed_runtime_blocked"
    overlay_row = dict(row)
    provenance = dict(_as_mapping(row.get("provenance")))
    if topic != raw_topic:
        provenance["split_parent_topic_remap"] = _split_parent_topic_remap_note(
            row,
            raw_topic=raw_topic,
            topic=topic,
        )
    overlay_row.update(
        {
            "language_pair": LANGUAGE_PAIR,
            "lemma": lemma,
            "topic": topic,
            "membership": round(float(membership), 6),
            "confidence_label": confidence_label or ("strong" if membership >= 1.0 else "light"),
            "runtime_blockers": runtime_blockers,
            "promotion_rule": "reviewed_jmdict_overlay",
            "provenance": {
                **provenance,
                "promotion_overlay_source": _repo_path(reviewed_overlay_json),
            },
        }
    )
    return overlay_row


def _promoted_row_from_evidence(
    row: Mapping[str, object],
    *,
    candidates: Mapping[str, Mapping[str, object]],
    promotion_rule: str,
    evidence_json: Path,
    auto_review_label: Mapping[str, object] | None = None,
) -> dict[str, object] | None:
    lemma = str(row.get("lemma") or "").strip()
    raw_topic = str(row.get("topic") or "").strip()
    topic = _promotion_topic(row)
    if not lemma or not topic:
        return None
    candidate_info = candidates.get(lemma, {})
    runtime_blockers = _runtime_blockers(row, candidate_info=candidate_info)
    is_manual_runtime_source = promotion_rule == "product_owned_manual_semantic_lexicon"
    if not is_manual_runtime_source:
        auto_decision = str(_as_mapping(auto_review_label).get("decision") or "")
        if auto_decision in AUTO_REVIEW_ACCEPT_DECISIONS:
            runtime_blockers = sorted(set(runtime_blockers))
        else:
            runtime_blockers = sorted(
                set(runtime_blockers)
                | {"unreviewed_auto_topic_evidence_requires_manual_acceptance"}
            )
    else:
        auto_decision = ""
    membership = (
        RUNTIME_MEMBERSHIP
        if (
            (is_manual_runtime_source or auto_decision in AUTO_REVIEW_ACCEPT_DECISIONS)
            and not runtime_blockers
        )
        else REVIEW_ONLY_MEMBERSHIP
    )
    source = str(row.get("source") or "")
    source_label = str(row.get("source_label") or "")
    reading = str(row.get("reading") or "")
    review_id = (
        "srs-enja-autotag-"
        + hashlib.sha1(
            f"{lemma}\t{reading}\t{topic}\t{source}\t{source_label}".encode("utf-8")
        ).hexdigest()[:12]
    )
    if is_manual_runtime_source and membership >= RUNTIME_MEMBERSHIP:
        confidence_label = "strong_manual"
    elif is_manual_runtime_source:
        confidence_label = "manual_runtime_blocked"
    elif auto_decision in AUTO_REVIEW_ACCEPT_DECISIONS and membership >= RUNTIME_MEMBERSHIP:
        confidence_label = "strong_auto_reviewed"
    elif auto_decision in AUTO_REVIEW_ACCEPT_DECISIONS:
        confidence_label = "auto_reviewed_runtime_blocked"
    elif auto_decision in AUTO_REVIEW_REVIEW_ONLY_DECISIONS:
        confidence_label = "auto_reviewed_light"
    else:
        confidence_label = "auto_review_candidate"
    if is_manual_runtime_source and membership >= RUNTIME_MEMBERSHIP:
        review_decision = "manual_promote_runtime_effective"
        review_state = "product_owned_manual_runtime_effective"
    elif is_manual_runtime_source:
        review_decision = "manual_review_only_runtime_blocked"
        review_state = "review_candidate_not_runtime_effective"
    elif auto_decision in AUTO_REVIEW_ACCEPT_DECISIONS and membership >= RUNTIME_MEMBERSHIP:
        review_decision = "auto_review_accepted_runtime_effective"
        review_state = "auto_reviewed_runtime_effective"
    elif auto_decision in AUTO_REVIEW_ACCEPT_DECISIONS:
        review_decision = "auto_review_accepted_runtime_blocked"
        review_state = "auto_reviewed_runtime_blocked"
    elif auto_decision in AUTO_REVIEW_REVIEW_ONLY_DECISIONS:
        review_decision = "auto_review_accepted_light_review_only"
        review_state = "review_candidate_not_runtime_effective"
    else:
        review_decision = "auto_review_only_pending_manual_acceptance"
        review_state = "review_candidate_not_runtime_effective"
    auto_review_meta = _auto_review_metadata(auto_review_label)
    return {
        "lemma": lemma,
        "reading": reading,
        "language_pair": LANGUAGE_PAIR,
        "topic": topic,
        "membership": round(float(membership), 6),
        "confidence_label": confidence_label,
        "review_decision": review_decision,
        "review_id": review_id,
        "review_state": review_state,
        "reviewer": "codex_agent_policy_guard",
        "match_strength": "strict_source_guard",
        "source_labels": [source_label] if source_label else [],
        "primary_source_label": source_label,
        "runtime_blockers": runtime_blockers,
        "promotion_rule": promotion_rule,
        "evidence": {
            "rank": _safe_float(row.get("rank"), default=0.0),
            "core_rank": _safe_float(row.get("core_rank"), default=0.0),
            "score": _safe_float(row.get("score"), default=0.0),
            "band": str(row.get("band") or ""),
            "candidate_state": str(row.get("candidate_state") or ""),
            "topic_stretch_allowed": str(row.get("topic_stretch_allowed") or ""),
            "source": source,
            "source_label": source_label,
            "source_confidence": _safe_float(row.get("confidence"), default=0.0),
            "source_membership": _safe_float(row.get("membership"), default=0.0),
            "evidence_label": str(row.get("evidence_label") or ""),
            "reading_identity": str(_as_mapping(row.get("extra")).get("reading_identity") or ""),
            "source_topic": raw_topic,
        },
        "provenance": {
            "evidence_json": _repo_path(evidence_json),
            "promotion_state": "product_safe_candidate_not_default",
            **({"auto_review": auto_review_meta} if auto_review_meta else {}),
            "source_review_posture": str(row.get("review_posture") or ""),
            "license_note": str(row.get("license_note") or ""),
            "notes": (
                "Product-owned manual semantic evidence is runtime-effective when safe."
                if is_manual_runtime_source
                else "Auto topic evidence retained for review; not runtime-effective until manually accepted."
            ),
            **(
                {
                    "split_parent_topic_remap": _split_parent_topic_remap_note(
                        row,
                        raw_topic=raw_topic,
                        topic=topic,
                    )
                }
                if topic != raw_topic
                else {}
            ),
        },
    }


def _promotion_topic(row: Mapping[str, object]) -> str:
    topic = str(row.get("topic") or "").strip()
    labels = [str(row.get("primary_source_label") or ""), str(row.get("source_label") or "")]
    labels.extend(_string_list(row.get("source_labels")))
    return _remap_split_parent_topic(topic, labels)


def _remap_split_parent_topic(topic: str, labels: Sequence[object]) -> str:
    label_map = SPLIT_PARENT_TOPIC_LABEL_REMAP.get(topic)
    if not label_map:
        return topic
    normalized_map = {_normalize_label(label): remapped for label, remapped in label_map.items()}
    for label in labels:
        normalized = _normalize_label(label)
        if normalized in normalized_map:
            return normalized_map[normalized]
    return topic


def _split_parent_topic_remap_note(
    row: Mapping[str, object],
    *,
    raw_topic: str,
    topic: str,
) -> dict[str, object]:
    labels = [str(row.get("primary_source_label") or ""), str(row.get("source_label") or "")]
    labels.extend(_string_list(row.get("source_labels")))
    return {
        "from": raw_topic,
        "to": topic,
        "label_basis": [label for label in labels if label],
    }


def _autotag_promotion_rule(row: Mapping[str, object]) -> str:
    source = str(row.get("source") or "")
    if source == "manual_semantic_lexicon" and _is_product_safe_manual_semantic_row(row):
        return "product_owned_manual_semantic_lexicon"
    if source == "kaikki_wiktionary_topic" and _is_strict_kaikki_row(row):
        return "strict_kaikki_wiktionary_topic"
    if source == "jawikipedia_dump_category" and _is_strict_wikipedia_row(row):
        return "strict_jawikipedia_dump_category"
    if source == "wikidata_claim_probe" and _is_strict_wikidata_claim_probe_row(row):
        return "strict_wikidata_claim_probe"
    return ""


def _is_product_safe_manual_semantic_row(row: Mapping[str, object]) -> bool:
    extra = _as_mapping(row.get("extra"))
    if str(row.get("source") or "") != "manual_semantic_lexicon":
        return False
    if not str(row.get("topic") or "") or not str(row.get("source_label") or ""):
        return False
    if not bool(extra.get("manual_semantic_promotion_eligible")):
        return False
    if str(extra.get("manual_semantic_output_kind") or "") != "topic":
        return False
    if _safe_float(row.get("membership"), default=0.0) < 1.0:
        return False
    return _safe_float(row.get("confidence"), default=0.0) >= 0.95


def _is_strict_kaikki_row(row: Mapping[str, object]) -> bool:
    if _lemma_is_topic_literal(row):
        return True
    extra = _as_mapping(row.get("extra"))
    sense_index = _safe_int(extra.get("kaikki_sense_index"))
    if sense_index > 1:
        return False
    label = _normalize_label(row.get("source_label"))
    if label in KAIKKI_STRICT_LABELS:
        return True
    return label in KAIKKI_ANCHORED_WEAK_LABELS and _has_kaikki_weak_label_anchor(
        row,
        source_label=label,
    )


def _is_strict_wikipedia_row(row: Mapping[str, object]) -> bool:
    if _wiki_lemma_is_topic_literal(row):
        return True
    source_label = str(row.get("source_label") or "")
    extra = _as_mapping(row.get("extra"))
    return _wiki_title_corroborates_source_label(
        source_label,
        lemma=str(row.get("lemma") or ""),
        title=str(extra.get("wikipedia_title") or ""),
        resolved_title=str(extra.get("wikipedia_resolved_title") or ""),
    )


def _is_strict_wikidata_claim_probe_row(row: Mapping[str, object]) -> bool:
    extra = _as_mapping(row.get("extra"))
    search_match = _as_mapping(extra.get("wikidata_search_match"))
    qid = str(extra.get("wikidata_qid") or "")
    root_qid = str(extra.get("wikidata_root_qid") or "")
    path = _string_list(extra.get("wikidata_path"))
    description = str(extra.get("wikidata_description") or "").lower()
    reading_identity = str(extra.get("reading_identity") or "")
    if str(row.get("source") or "") != "wikidata_claim_probe":
        return False
    if not str(row.get("topic") or "") or not str(row.get("source_label") or ""):
        return False
    if _safe_float(row.get("confidence"), default=0.0) < 0.68:
        return False
    if _safe_float(row.get("membership"), default=0.0) < 0.72:
        return False
    if not qid.startswith("Q") or not root_qid.startswith("Q"):
        return False
    if len(path) < 2 or path[0] != qid or path[-1] != root_qid:
        return False
    if str(search_match.get("type") or "") != "jawikipedia_pageprops":
        return False
    if reading_identity not in {
        "external_exact_source_reading",
        "external_kana_exact_surface",
        "external_unique_surface_reading",
    }:
        return False
    return "disambiguation" not in description and "曖昧さ回避" not in description


def _runtime_blockers(
    row: Mapping[str, object],
    *,
    candidate_info: Mapping[str, object],
    respect_existing_review: bool = False,
) -> list[str]:
    blockers: list[str] = []
    readings = _string_list(candidate_info.get("readings"))
    if not readings:
        blockers.append("candidate_lemma_missing_from_corrected_csv")
    elif len(set(readings)) > 1:
        blockers.append("runtime_overlay_is_lemma_only_but_candidate_has_multiple_readings")
    candidate_states = set(_string_list(candidate_info.get("candidate_states")))
    if candidate_states and candidate_states != {"normal_vocab"}:
        blockers.append("candidate_state_not_all_normal_vocab")
    topic_stretch_values = set(_string_list(candidate_info.get("topic_stretch_allowed_values")))
    row_topic_stretch = str(row.get("topic_stretch_allowed") or "").strip().lower()
    if (
        "false" in {value.lower() for value in topic_stretch_values if value}
        or row_topic_stretch == "false"
    ):
        blockers.append("topic_stretch_disallowed")
    if respect_existing_review and not blockers:
        return []
    return sorted(set(blockers))


def _merge_overlay_row(
    rows_by_key: dict[tuple[str, str], dict[str, object]],
    row: Mapping[str, object],
    *,
    preserve_existing_membership: bool,
) -> None:
    key = (str(row.get("lemma") or ""), str(row.get("topic") or ""))
    if not key[0] or not key[1]:
        return
    incoming = dict(row)
    existing = rows_by_key.get(key)
    if existing is None:
        rows_by_key[key] = incoming
        return
    existing_sources = set(_string_list(_as_mapping(existing.get("evidence")).get("sources")))
    incoming_source = str(_as_mapping(incoming.get("evidence")).get("source") or "")
    incoming_sources = set(_string_list(_as_mapping(incoming.get("evidence")).get("sources")))
    source_set = sorted(
        source for source in existing_sources | incoming_sources | {incoming_source} if source
    )
    existing_labels = set(_string_list(existing.get("source_labels")))
    incoming_labels = set(_string_list(incoming.get("source_labels")))
    existing["source_labels"] = sorted(existing_labels | incoming_labels)
    existing["primary_source_label"] = str(
        existing.get("primary_source_label") or incoming.get("primary_source_label") or ""
    )
    evidence = dict(_as_mapping(existing.get("evidence")))
    evidence["sources"] = source_set
    evidence["merged_evidence_count"] = int(evidence.get("merged_evidence_count") or 1) + 1
    existing["evidence"] = evidence
    if not preserve_existing_membership and _safe_float(incoming.get("membership")) > _safe_float(
        existing.get("membership")
    ):
        existing["membership"] = incoming.get("membership")
        existing["confidence_label"] = incoming.get("confidence_label")


def _topic_overlay(
    *,
    rows: Sequence[Mapping[str, object]],
    generated_at: str,
    reviewed_overlay: Mapping[str, object],
    reviewed_overlay_json: Path,
    review_labels_json: Path,
    local_evidence: Mapping[str, object],
    local_evidence_json: Path,
    dump_evidence: Mapping[str, object],
    dump_evidence_json: Path,
    wikidata_evidence: Mapping[str, object],
    wikidata_evidence_json: Path,
    manual_semantic_evidence: Mapping[str, object],
    manual_semantic_evidence_json: Path,
    candidates_csv: Path,
    excluded: Counter[str],
    auto_review_labels: Mapping[str, object],
    auto_review_labels_json: Path,
) -> dict[str, object]:
    row_list = [dict(row) for row in rows]
    counts_by_topic = Counter(str(row.get("topic") or "") for row in row_list)
    counts_by_confidence = Counter(str(row.get("confidence_label") or "") for row in row_list)
    counts_by_rule = Counter(str(row.get("promotion_rule") or "") for row in row_list)
    runtime_effective_rows = [
        row
        for row in row_list
        if _safe_float(row.get("membership"), default=0.0) >= PROFILE_INJECTION_MIN_MEMBERSHIP
    ]
    return {
        "schema_version": 1,
        "overlay_id": "srs_topic_autotag_promotion_overlay_en_ja_product_safe_candidate_v1",
        "status": "ok" if row_list else "review",
        "decision": "topic_overlay_product_safe_candidate_ready"
        if row_list
        else "topic_overlay_candidate_needs_review",
        "generated_at": generated_at,
        "inputs": {
            "candidates_csv": _repo_path(candidates_csv),
            "reviewed_overlay_json": _repo_path(reviewed_overlay_json),
            "review_labels_json": _repo_path(review_labels_json),
            "auto_review_labels_json": _repo_path(auto_review_labels_json),
            "local_evidence_json": _repo_path(local_evidence_json),
            "dump_evidence_json": _repo_path(dump_evidence_json),
            "wikidata_evidence_json": _repo_path(wikidata_evidence_json),
            "manual_semantic_evidence_json": _repo_path(manual_semantic_evidence_json),
            "reviewed_overlay_decision": str(reviewed_overlay.get("decision") or ""),
            "local_evidence_decision": str(local_evidence.get("decision") or ""),
            "dump_evidence_decision": str(dump_evidence.get("decision") or ""),
            "wikidata_evidence_decision": str(wikidata_evidence.get("decision") or ""),
            "manual_semantic_evidence_decision": str(
                manual_semantic_evidence.get("decision") or ""
            ),
            "auto_review_labels_state": str(auto_review_labels.get("state") or ""),
        },
        "overlay_policy": {
            "runtime_policy_change": "none",
            "promotion_state": "product_safe_candidate_not_default",
            "profile_injection_min_membership": PROFILE_INJECTION_MIN_MEMBERSHIP,
            "runtime_effective_membership": RUNTIME_MEMBERSHIP,
            "review_only_membership": REVIEW_ONLY_MEMBERSHIP,
            "reading_identity_policy": "runtime-effective rows require a unique corrected reading for the lemma under the current lemma-only overlay contract",
            "manual_reject_policy": "manual review rejected lemma-topic keys are not auto-promoted",
            "auto_review_label_policy": (
                "auto rows are review-only by default; accept_runtime labels remove the manual-acceptance "
                "blocker but still obey runtime identity blockers; reject labels remove the row"
            ),
            "source_policy": {
                "reviewed_jmdict_overlay": "preserve accepted reviewed rows",
                "kaikki_wiktionary_topic": "strict first-sense or literal-topic rows retained as review candidates; runtime promotion requires manual acceptance",
                "jawikipedia_dump_category": "literal or title-corroborated rows retained as review candidates; runtime promotion requires manual acceptance",
                "wikidata_claim_probe": "exact Japanese Wikipedia pageprops QID plus structured claim path rows retained as review candidates; runtime promotion requires manual acceptance",
                "manual_semantic_lexicon": "product-owned closed-set topic collections only; facet-only collections are not promoted",
                "jmdict_field_direct": "source evidence only unless already present in the reviewed overlay",
                "jmdict_gloss_keyword": "review candidate only",
                "english_wordnet_gloss_bridge": "excluded from product-safe promotion",
            },
            "excluded_counts": dict(sorted(excluded.items())),
        },
        "summary": {
            "row_count": len(row_list),
            "runtime_effective_row_count": len(runtime_effective_rows),
            "review_only_row_count": len(row_list) - len(runtime_effective_rows),
            "counts_by_topic": dict(sorted(counts_by_topic.items())),
            "runtime_effective_counts_by_topic": dict(
                sorted(
                    Counter(str(row.get("topic") or "") for row in runtime_effective_rows).items()
                )
            ),
            "counts_by_confidence": dict(sorted(counts_by_confidence.items())),
            "counts_by_promotion_rule": dict(sorted(counts_by_rule.items())),
        },
        "rows": row_list,
        "findings": [
            _finding(
                "PASS",
                "promotion_overlay_rows_present",
                "Product-safe candidate overlay rows were generated.",
            )
            if row_list
            else _finding(
                "FAIL",
                "promotion_overlay_rows_empty",
                "No product-safe candidate rows were generated.",
            )
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    overlay = _as_mapping(report.get("topic_overlay"))
    summary = _as_mapping(overlay.get("summary"))
    rows = _mapping_rows(overlay.get("rows"))
    lines = [
        "# en-ja SRS Topic Autotag Promotion Overlay",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Overlay rows: `{summary.get('row_count', 0)}`",
        f"- Runtime-effective rows: `{summary.get('runtime_effective_row_count', 0)}`",
        f"- Review-only rows: `{summary.get('review_only_row_count', 0)}`",
        "",
        "## Coverage",
        "",
        "| Topic | Rows | Runtime-effective |",
        "| --- | ---: | ---: |",
    ]
    all_topics = sorted(
        set(_as_mapping(summary.get("counts_by_topic")))
        | set(_as_mapping(summary.get("runtime_effective_counts_by_topic")))
    )
    counts = _as_mapping(summary.get("counts_by_topic"))
    runtime_counts = _as_mapping(summary.get("runtime_effective_counts_by_topic"))
    for topic in all_topics:
        lines.append(f"| `{topic}` | {counts.get(topic, 0)} | {runtime_counts.get(topic, 0)} |")
    lines.extend(["", "## Promotion Rules", ""])
    for rule, count in _as_mapping(summary.get("counts_by_promotion_rule")).items():
        lines.append(f"- `{rule}`: `{count}`")
    lines.extend(["", "## Excluded Counts", ""])
    for reason, count in _as_mapping(
        _as_mapping(overlay.get("overlay_policy")).get("excluded_counts")
    ).items():
        lines.append(f"- `{reason}`: `{count}`")
    lines.extend(["", "## Runtime-Effective Sample", ""])
    lines.extend(
        _sample_table([row for row in rows if _safe_float(row.get("membership")) >= 1.0][:80])
    )
    lines.extend(["", "## Review-Only Sample", ""])
    lines.extend(
        _sample_table([row for row in rows if _safe_float(row.get("membership")) < 1.0][:80])
    )
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: {finding.get('message', '')}"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Topic | Lemma | Reading | Membership | Rule | Source labels | Blockers |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | "
            f"`{row.get('reading', '')}` | {row.get('membership', '')} | "
            f"`{row.get('promotion_rule', '')}` | "
            f"`{', '.join(_string_list(row.get('source_labels'))[:6])}` | "
            f"`{', '.join(_string_list(row.get('runtime_blockers'))[:4])}` |"
        )
    return lines


def _findings(
    *,
    overlay: Mapping[str, object],
    candidates: Mapping[str, Mapping[str, object]],
    reviewed_overlay: Mapping[str, object],
    dump_evidence: Mapping[str, object],
    wikidata_evidence: Mapping[str, object],
    manual_semantic_evidence: Mapping[str, object],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if candidates:
        findings.append(
            _finding(
                "PASS",
                "candidate_index_loaded",
                f"Loaded {len(candidates)} candidate lemma surfaces.",
            )
        )
    else:
        findings.append(
            _finding("FAIL", "candidate_index_empty", "No corrected candidate rows were loaded.")
        )
    if _mapping_rows(reviewed_overlay.get("rows")):
        findings.append(
            _finding("PASS", "reviewed_overlay_loaded", "Reviewed JMDict overlay rows were loaded.")
        )
    else:
        findings.append(
            _finding(
                "WARN", "reviewed_overlay_empty", "No reviewed JMDict overlay rows were loaded."
            )
        )
    if _mapping_rows(dump_evidence.get("evidence_rows")):
        findings.append(
            _finding("PASS", "dump_evidence_loaded", "Guarded dump evidence rows were loaded.")
        )
    else:
        findings.append(
            _finding("WARN", "dump_evidence_empty", "No guarded dump evidence rows were loaded.")
        )
    if _mapping_rows(wikidata_evidence.get("evidence_rows")):
        findings.append(
            _finding(
                "PASS",
                "wikidata_evidence_loaded",
                "Wikidata claim-probe evidence rows were loaded.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "wikidata_evidence_empty",
                "No Wikidata claim-probe evidence rows were loaded.",
            )
        )
    if _mapping_rows(manual_semantic_evidence.get("evidence_rows")):
        findings.append(
            _finding(
                "PASS",
                "manual_semantic_evidence_loaded",
                "Manual semantic lexicon evidence rows were loaded.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN",
                "manual_semantic_evidence_empty",
                "No manual semantic lexicon evidence rows were loaded.",
            )
        )
    if str(overlay.get("status") or "") == "ok":
        findings.append(
            _finding(
                "PASS", "promotion_overlay_ready", "Product-safe topic overlay candidate was built."
            )
        )
    else:
        findings.append(
            _finding(
                "FAIL",
                "promotion_overlay_not_ready",
                "Product-safe topic overlay candidate is empty.",
            )
        )
    return findings


def _report_summary(
    *,
    overlay: Mapping[str, object],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    overlay_summary = _as_mapping(overlay.get("summary"))
    return {
        "overlay_row_count": overlay_summary.get("row_count", 0),
        "runtime_effective_overlay_row_count": overlay_summary.get(
            "runtime_effective_row_count", 0
        ),
        "review_only_overlay_row_count": overlay_summary.get("review_only_row_count", 0),
        "overlay_counts_by_topic": overlay_summary.get("counts_by_topic", {}),
        "runtime_effective_counts_by_topic": overlay_summary.get(
            "runtime_effective_counts_by_topic", {}
        ),
        "finding_counts": dict(Counter(str(row.get("level") or "") for row in findings)),
        "warnings": [row.get("code") for row in findings if row.get("level") == "WARN"],
        "issues": [row.get("code") for row in findings if row.get("level") == "FAIL"],
    }


def _load_candidate_index(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    rows_by_lemma: dict[str, dict[str, object]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lemma = str(row.get("lemma") or "").strip()
            reading = str(row.get("reading") or "").strip()
            if not lemma:
                continue
            info = rows_by_lemma.setdefault(
                lemma,
                {
                    "readings": [],
                    "candidate_states": [],
                    "topic_stretch_allowed_values": [],
                },
            )
            if reading:
                info["readings"].append(reading)
            state = str(row.get("candidate_state") or "").strip()
            if state:
                info["candidate_states"].append(state)
            stretch = str(row.get("topic_stretch_allowed") or "").strip()
            if stretch:
                info["topic_stretch_allowed_values"].append(stretch)
    return {
        lemma: {
            "readings": sorted(set(_string_list(info.get("readings")))),
            "candidate_states": sorted(set(_string_list(info.get("candidate_states")))),
            "topic_stretch_allowed_values": sorted(
                set(_string_list(info.get("topic_stretch_allowed_values")))
            ),
        }
        for lemma, info in rows_by_lemma.items()
    }


def _manual_rejected_keys(labels_payload: Mapping[str, object]) -> set[tuple[str, str]]:
    rejected: set[tuple[str, str]] = set()
    for row in _mapping_rows(labels_payload.get("labels")):
        decision = str(row.get("decision") or "")
        if not decision.startswith("reject_"):
            continue
        lemma = str(row.get("lemma") or "").strip()
        topic = str(row.get("family_id") or row.get("family") or row.get("topic") or "").strip()
        if lemma and topic:
            rejected.add((lemma, topic))
    return rejected


def _auto_review_label_index(
    labels_payload: Mapping[str, object],
) -> dict[tuple[str, str, str], Mapping[str, object]]:
    labels: dict[tuple[str, str, str], Mapping[str, object]] = {}
    for row in _mapping_rows(labels_payload.get("labels")):
        lemma = str(row.get("lemma") or "").strip()
        reading = str(row.get("reading") or "").strip()
        topic = str(row.get("topic") or row.get("family_id") or row.get("family") or "").strip()
        decision = str(row.get("decision") or "").strip()
        if not lemma or not topic or not decision:
            continue
        labels[(lemma, reading, topic)] = row
    return labels


def _lookup_auto_review_label(
    row: Mapping[str, object],
    *,
    topic: str,
    labels: Mapping[tuple[str, str, str], Mapping[str, object]],
) -> Mapping[str, object]:
    lemma = str(row.get("lemma") or "").strip()
    reading = str(row.get("reading") or "").strip()
    return labels.get((lemma, reading, topic)) or labels.get((lemma, "", topic)) or {}


def _auto_review_metadata(label: Mapping[str, object] | None) -> dict[str, object]:
    row = _as_mapping(label)
    if not row:
        return {}
    return {
        "decision": str(row.get("decision") or ""),
        "reviewer": str(row.get("reviewer") or ""),
        "reviewed_at": str(row.get("reviewed_at") or ""),
        "reason": str(row.get("reason") or row.get("notes") or ""),
    }


def _load_json_or_empty(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = Path(path).expanduser().resolve(strict=False)
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
