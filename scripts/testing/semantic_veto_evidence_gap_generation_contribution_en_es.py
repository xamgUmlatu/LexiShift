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
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    RuntimeSimilarityBackend,
)
from semantic_veto_evidence_gap_generation_admission_en_es import (  # noqa: E402
    ACTIVE_SLOT,
    NO_WINNER_SLOT,
    SHADOW_SLOT,
)
from semantic_veto_product_quality_en_es import _repo_path  # noqa: E402


DEFAULT_REQUESTS_JSON = (
    TEST_OUTPUTS_ROOT / "semantic_veto_evidence_gap_generation_requests_en_es_latest.json"
)
DEFAULT_ADMISSION_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_admission_live_smoke_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_contribution_live_smoke_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT
    / "semantic_veto_evidence_gap_generation_contribution_live_smoke_en_es_latest.md"
)
SCORER_IDS = ("token_jaccard", "tfidf_cosine")
ACTIVE_POLLUTION_TFIDF_THRESHOLD = 0.18
ACTIVE_POLLUTION_JACCARD_THRESHOLD = 0.12


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose whether admitted evidence-gap generated items are likely to "
            "contribute to their intended active/shadow/no-winner role. This changes "
            "no runtime policy and does not promote source evidence."
        )
    )
    parser.add_argument("--generation-requests-json", type=Path, default=DEFAULT_REQUESTS_JSON)
    parser.add_argument("--admission-json", type=Path, default=DEFAULT_ADMISSION_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_evidence_gap_generation_contribution_report(
        generation_requests_payload=_load_json(args.generation_requests_json),
        admission_payload=_load_json(args.admission_json),
        generation_requests_path=args.generation_requests_json,
        admission_path=args.admission_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_evidence_gap_generation_contribution_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_evidence_gap_generation_contribution_report(
    *,
    generation_requests_payload: Mapping[str, object],
    admission_payload: Mapping[str, object],
    generation_requests_path: Path | None = None,
    admission_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    requests_by_id = {
        str(row.get("request_id") or ""): row
        for row in _mapping_rows(generation_requests_payload.get("requests"))
        if str(row.get("request_id") or "")
    }
    admitted_items = _mapping_rows(admission_payload.get("admitted_items"))
    issues = []
    if not requests_by_id:
        issues.append("missing_generation_requests")
    if not admitted_items:
        issues.append("no_admitted_generated_items")
    missing_request_ids = sorted(
        {
            str(item.get("request_id") or "")
            for item in admitted_items
            if str(item.get("request_id") or "") not in requests_by_id
        }
    )
    if missing_request_ids:
        issues.append("admitted_items_missing_request_rows")

    texts = _fit_texts(admitted_items=admitted_items, requests_by_id=requests_by_id)
    scorers = {scorer_id: RuntimeSimilarityBackend(scorer_id=scorer_id) for scorer_id in SCORER_IDS}
    for scorer in scorers.values():
        scorer.fit(texts)
    rows = [
        _contribution_row(
            item=item, request=requests_by_id[str(item.get("request_id") or "")], scorers=scorers
        )
        for item in admitted_items
        if str(item.get("request_id") or "") in requests_by_id
    ]
    status = "review" if issues else "ok"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "generated_contribution_review_queue_ready"
            if status == "ok"
            else "generated_contribution_inputs_need_repair"
        ),
        "generated_at": generated_at,
        "pair": str(
            generation_requests_payload.get("pair") or admission_payload.get("pair") or "en-es"
        ),
        "inputs": {
            "generation_requests_path": _repo_path(generation_requests_path),
            "admission_path": _repo_path(admission_path),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "source_evidence_promotion": "none",
            "scorers": list(SCORER_IDS),
            "active_pollution_tfidf_threshold": ACTIVE_POLLUTION_TFIDF_THRESHOLD,
            "active_pollution_jaccard_threshold": ACTIVE_POLLUTION_JACCARD_THRESHOLD,
            "purpose": (
                "Separate structural admission from semantic role quality before "
                "rescoring or spending on the full pilot."
            ),
        },
        "summary": _summary(rows=rows, issues=issues),
        "review_queue": _review_queue(rows),
        "row_results": rows,
        "limitations": [
            "no runtime policy change",
            "no source evidence promotion",
            "active-pollution similarity flags use generated sentences, not explanatory metadata",
            "metadata-overlap counts are reported separately because notes may contain contrast language",
            "similarity scores are diagnostics, not final semantic judgments",
            "shadow and no-winner rows still need review or downstream score contribution checks",
        ],
        "next_steps": _next_steps(rows=rows, issues=issues),
    }


def render_evidence_gap_generation_contribution_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Veto Evidence-Gap Generated Contribution",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Admitted items: `{summary.get('admitted_item_count', 0)}`",
        f"- Review-required items: `{summary.get('semantic_review_required_count', 0)}`",
        f"- Possible active-role pollution: `{summary.get('possible_active_role_pollution_count', 0)}`",
        f"- Metadata active overlap: `{summary.get('metadata_active_overlap_count', 0)}`",
        f"- New competitor target items: `{summary.get('new_competitor_target_item_count', 0)}`",
        "",
        "## Slot Summary",
        "",
        "| Slot | Items | Review required | Possible active pollution |",
        "| --- | ---: | ---: | ---: |",
    ]
    for slot_type, row in _as_mapping(summary.get("by_slot_type")).items():
        row_map = _as_mapping(row)
        lines.append(
            f"| `{_escape_md(str(slot_type))}` | {row_map.get('item_count', 0)} | "
            f"{row_map.get('semantic_review_required_count', 0)} | "
            f"{row_map.get('possible_active_role_pollution_count', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Review Queue",
            "",
            "| Item | Slot | Action | TF-IDF active sim | Jaccard active sim | Sentence |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in _mapping_rows(report.get("review_queue"))[:30]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('item_id') or ''))}`",
                    f"`{_escape_md(str(row.get('slot_type') or ''))}`",
                    f"`{_escape_md(str(row.get('recommended_action') or ''))}`",
                    str(row.get("active_similarity_tfidf_cosine") or 0.0),
                    str(row.get("active_similarity_token_jaccard") or 0.0),
                    _escape_md(str(row.get("sentence") or "")),
                ]
            )
            + " |"
        )
    if not _mapping_rows(report.get("review_queue")):
        lines.append("| _None._ |  |  |  |  |  |")
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in _as_sequence(report.get("next_steps")))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{_escape_md(str(item))}`" for item in _as_sequence(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _contribution_row(
    *,
    item: Mapping[str, object],
    request: Mapping[str, object],
    scorers: Mapping[str, RuntimeSimilarityBackend],
) -> dict[str, object]:
    generated_text = _generated_text(item)
    generated_sentence = str(item.get("sentence") or "")
    active_evidence_text = str(request.get("active_evidence_text") or "").strip()
    slot_type = str(item.get("slot_type") or request.get("slot_type") or "")
    sentence_scores = {
        scorer_id: round(float(scorer.similarity(generated_sentence, active_evidence_text)), 4)
        for scorer_id, scorer in scorers.items()
    }
    augmented_scores = {
        scorer_id: round(float(scorer.similarity(generated_text, active_evidence_text)), 4)
        for scorer_id, scorer in scorers.items()
    }
    known_shadow_targets = {
        _normalize_text(str(value))
        for value in request.get("known_shadow_targets") or ()
        if str(value)
    }
    response_target = _normalize_text(str(item.get("target_lemma") or ""))
    proposed_target = _normalize_text(str(item.get("proposed_competitor_target_lemma") or ""))
    competitor_target = response_target or proposed_target
    reasons: list[str] = []
    semantic_review_required = slot_type in {SHADOW_SLOT, NO_WINNER_SLOT}
    if semantic_review_required:
        reasons.append("non_active_slot_requires_semantic_role_review")
    possible_active_role_pollution = False
    if slot_type in {SHADOW_SLOT, NO_WINNER_SLOT} and (
        sentence_scores.get("tfidf_cosine", 0.0) >= ACTIVE_POLLUTION_TFIDF_THRESHOLD
        or sentence_scores.get("token_jaccard", 0.0) >= ACTIVE_POLLUTION_JACCARD_THRESHOLD
    ):
        possible_active_role_pollution = True
        reasons.append("possible_active_role_pollution_by_similarity")
    metadata_active_overlap = False
    if (
        slot_type in {SHADOW_SLOT, NO_WINNER_SLOT}
        and not possible_active_role_pollution
        and (
            augmented_scores.get("tfidf_cosine", 0.0) >= ACTIVE_POLLUTION_TFIDF_THRESHOLD
            or augmented_scores.get("token_jaccard", 0.0) >= ACTIVE_POLLUTION_JACCARD_THRESHOLD
        )
    ):
        metadata_active_overlap = True
        reasons.append("metadata_active_overlap_requires_note_review")
    new_competitor_target = bool(
        slot_type == SHADOW_SLOT
        and competitor_target
        and competitor_target not in known_shadow_targets
    )
    if new_competitor_target:
        reasons.append("new_competitor_target_requires_review")
    if slot_type == ACTIVE_SLOT:
        recommended_action = "candidate_active_evidence_for_rescoring"
    elif possible_active_role_pollution:
        recommended_action = "review_before_shadow_or_no_winner_use"
    elif slot_type == SHADOW_SLOT:
        recommended_action = "review_competitor_target_before_rescoring"
    else:
        recommended_action = "review_no_winner_context_before_rescoring"
    return {
        "item_id": str(item.get("item_id") or ""),
        "request_id": str(item.get("request_id") or ""),
        "family_id": str(item.get("family_id") or ""),
        "pilot_arm": str(item.get("pilot_arm") or ""),
        "slot_type": slot_type,
        "source_phrase": str(item.get("source_phrase") or request.get("trigger") or ""),
        "active_target_lemma": str(
            item.get("active_target_lemma") or request.get("active_target_lemma") or ""
        ),
        "target_lemma": str(item.get("target_lemma") or ""),
        "proposed_competitor_target_lemma": str(item.get("proposed_competitor_target_lemma") or ""),
        "competitor_sense_label": str(item.get("competitor_sense_label") or ""),
        "active_sense_contrast": str(item.get("active_sense_contrast") or ""),
        "active_mismatch_note": str(item.get("active_mismatch_note") or ""),
        "no_winner_context_class": str(item.get("no_winner_context_class") or ""),
        "runtime_trigger_note": str(item.get("runtime_trigger_note") or ""),
        "known_shadow_targets": sorted(known_shadow_targets),
        "sentence": str(item.get("sentence") or ""),
        "active_evidence_text": active_evidence_text,
        "active_similarity_token_jaccard": sentence_scores.get("token_jaccard", 0.0),
        "active_similarity_tfidf_cosine": sentence_scores.get("tfidf_cosine", 0.0),
        "augmented_active_similarity_token_jaccard": augmented_scores.get("token_jaccard", 0.0),
        "augmented_active_similarity_tfidf_cosine": augmented_scores.get("tfidf_cosine", 0.0),
        "semantic_review_required": semantic_review_required,
        "possible_active_role_pollution": possible_active_role_pollution,
        "metadata_active_overlap": metadata_active_overlap,
        "new_competitor_target": new_competitor_target,
        "recommended_action": recommended_action,
        "review_reasons": reasons,
    }


def _summary(*, rows: Sequence[Mapping[str, object]], issues: Sequence[str]) -> dict[str, object]:
    by_slot: dict[str, dict[str, int]] = {}
    for slot_type in sorted({str(row.get("slot_type") or "") for row in rows}):
        slot_rows = [row for row in rows if str(row.get("slot_type") or "") == slot_type]
        by_slot[slot_type] = {
            "item_count": len(slot_rows),
            "semantic_review_required_count": sum(
                1 for row in slot_rows if bool(row.get("semantic_review_required"))
            ),
            "possible_active_role_pollution_count": sum(
                1 for row in slot_rows if bool(row.get("possible_active_role_pollution"))
            ),
            "metadata_active_overlap_count": sum(
                1 for row in slot_rows if bool(row.get("metadata_active_overlap"))
            ),
        }
    return {
        "issues": list(issues),
        "admitted_item_count": len(rows),
        "semantic_review_required_count": sum(
            1 for row in rows if bool(row.get("semantic_review_required"))
        ),
        "possible_active_role_pollution_count": sum(
            1 for row in rows if bool(row.get("possible_active_role_pollution"))
        ),
        "metadata_active_overlap_count": sum(
            1 for row in rows if bool(row.get("metadata_active_overlap"))
        ),
        "new_competitor_target_item_count": sum(
            1 for row in rows if bool(row.get("new_competitor_target"))
        ),
        "recommended_actions": dict(
            sorted(Counter(str(row.get("recommended_action") or "") for row in rows).items())
        ),
        "by_slot_type": by_slot,
    }


def _review_queue(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in rows
        if bool(row.get("semantic_review_required"))
        or bool(row.get("possible_active_role_pollution"))
        or bool(row.get("metadata_active_overlap"))
        or bool(row.get("new_competitor_target"))
    ]


def _next_steps(*, rows: Sequence[Mapping[str, object]], issues: Sequence[str]) -> list[str]:
    if issues:
        return [
            "Repair contribution inputs before interpreting generated semantic quality.",
            "Rerun admission first if admitted_items are missing.",
        ]
    if any(bool(row.get("possible_active_role_pollution")) for row in rows):
        return [
            "Manually review possible active-role pollution before using generated shadow/no-winner items.",
            "Do not launch the full 72-request batch until role pollution is understood.",
        ]
    if any(bool(row.get("semantic_review_required")) for row in rows):
        return [
            "Review non-active generated items for semantic role correctness.",
            "Then run the downstream score-contribution harness on reviewed generated items.",
        ]
    return [
        "Run the downstream score-contribution harness on reviewed generated items.",
        "Compare high/middle/low improvement only after full-batch admission and role review.",
    ]


def _fit_texts(
    *,
    admitted_items: Sequence[Mapping[str, object]],
    requests_by_id: Mapping[str, Mapping[str, object]],
) -> list[str]:
    texts = []
    for item in admitted_items:
        request = requests_by_id.get(str(item.get("request_id") or ""))
        if request is None:
            continue
        texts.append(str(item.get("sentence") or ""))
        texts.append(_generated_text(item))
        texts.append(str(request.get("active_evidence_text") or ""))
    return [text for text in texts if text]


def _generated_text(item: Mapping[str, object]) -> str:
    parts = [
        str(item.get("sentence") or ""),
        str(item.get("evidence_note") or ""),
        str(item.get("no_winner_reason") or ""),
    ]
    return " | ".join(part for part in parts if part)


def _load_json(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [row for row in value if isinstance(row, Mapping)]
    return []


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
