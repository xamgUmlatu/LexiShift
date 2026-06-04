from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_INPUTS_ROOT = DOCS_ROOT / "test_inputs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_product_quality_en_es import (  # noqa: E402
    _as_mapping,
    _mapping_rows,
    _repo_path,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_PILOT_FAMILY_COUNT = 58
SOURCE_BAND_ORDER = (
    "zipf_5_plus_very_common",
    "zipf_4_to_5_common",
    "zipf_3_to_4_mid",
    "zipf_below_3_rare",
    "missing",
)
PRIMARY_SOURCE_BAND_ORDER = tuple(band for band in SOURCE_BAND_ORDER if band != "missing")


def build_full_family_human_review_packet(
    *,
    dataset_payload: Mapping[str, object],
    wordnet_index: WordNetIndex | None = None,
    sense_rows_by_source: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
    weakness_taxonomy: Mapping[str, object] | None = None,
    dataset_path: Path | None = None,
    wordnet_dir: Path | None = None,
    weakness_taxonomy_path: Path | None = None,
    pilot_family_count: int = DEFAULT_PILOT_FAMILY_COUNT,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    all_families = _mapping_rows(dataset_payload.get("families"))
    selected_families = _select_pilot_families(
        all_families, pilot_family_count=max(1, int(pilot_family_count))
    )
    review_rows = [
        _family_review_row(
            family=family,
            index=index,
            wordnet_index=wordnet_index,
            sense_rows_by_source=sense_rows_by_source,
        )
        for index, family in enumerate(selected_families, start=1)
    ]
    case_rows = [
        case for family in review_rows for case in _mapping_rows(family.get("case_review_rows"))
    ]
    packet_weaknesses = _packet_weaknesses(review_rows=review_rows, case_rows=case_rows)
    weakness_counts = _weakness_counts(
        review_rows=review_rows,
        case_rows=case_rows,
        packet_weaknesses=packet_weaknesses,
    )
    weakness_severity_counts = _weakness_severity_counts(
        weakness_counts=weakness_counts,
        weakness_taxonomy=weakness_taxonomy or {},
    )
    checks = _checks(
        all_families=all_families,
        review_rows=review_rows,
        requested_count=max(1, int(pilot_family_count)),
    )
    issues = [key for key, value in checks.items() if not value]
    return {
        "schema_version": 1,
        "pair": str(dataset_payload.get("pair") or "en-es"),
        "status": "review" if issues else "ok",
        "decision": (
            "full_family_human_review_packet_ready"
            if not issues
            else "full_family_human_review_packet_incomplete"
        ),
        "generated_at": generated_at,
        "inputs": {
            "dataset_path": _repo_path(dataset_path),
            "dataset_id": str(dataset_payload.get("dataset_id") or ""),
            "wordnet_dir": _repo_path(wordnet_dir),
            "wordnet_source_file_count": int(wordnet_index.source_file_count)
            if wordnet_index is not None
            else None,
            "weakness_taxonomy_path": _repo_path(weakness_taxonomy_path),
            "weakness_taxonomy_id": str(_as_mapping(weakness_taxonomy).get("taxonomy_id") or ""),
        },
        "methodology": {
            "runtime_policy_change": "none",
            "score_promotion": "none",
            "review_unit": "source_target_family_and_case_row",
            "selection": _selection_methodology(
                requested_count=max(1, int(pilot_family_count)),
                dataset_family_count=len(all_families),
            ),
            "review_authority": "user_review_required_for_all_semantic_ground_truth",
            "trusted_row_rule": (
                "No row can be counted as trusted until human_review_status is "
                "approved_by_user and active_sense_status is aligned or explicitly "
                "accepted as a diagnostic exception."
            ),
        },
        "review_options": {
            "human_review_status": [
                "pending_user_review",
                "approved_by_user",
                "rejected_by_user",
                "needs_rewrite",
                "diagnostic_only",
            ],
            "active_sense_status": [
                "pending_user_review",
                "aligned",
                "uncertain",
                "mismatched",
                "diagnostic_exception",
            ],
            "row_quality_status": [
                "pending_user_review",
                "trusted",
                "weak_context",
                "active_sense_uncertain",
                "active_sense_mismatch",
                "no_winner_template_control",
                "source_mapping_questionable",
                "diagnostic_only",
            ],
            "no_winner_subtype": [
                "mention_only_template_control",
                "metalinguistic",
                "named_entity_or_title",
                "phrase_collision",
                "nonsemantic_fragment",
                "realistic_negative_context",
                "not_applicable",
            ],
        },
        "weakness_taxonomy": _public_weakness_taxonomy(weakness_taxonomy or {}),
        "summary": {
            "dataset_family_count": len(all_families),
            "review_family_count": len(review_rows),
            "review_case_count": len(case_rows),
            "pilot_family_count_requested": max(1, int(pilot_family_count)),
            "source_band_counts": dict(
                sorted(Counter(row["source_zipf_band_en"] for row in review_rows).items())
            ),
            "case_type_counts": dict(
                sorted(Counter(row["manual_case_type"] for row in case_rows).items())
            ),
            "human_review_status_counts": dict(
                sorted(Counter(row["human_review_status"] for row in review_rows).items())
            ),
            "active_sense_status_counts": dict(
                sorted(Counter(row["active_sense_status"] for row in review_rows).items())
            ),
            "proposed_row_quality_status_counts": dict(
                sorted(Counter(row["proposed_row_quality_status"] for row in case_rows).items())
            ),
            "weakness_counts": dict(sorted(weakness_counts.items())),
            "weakness_severity_counts": dict(sorted(weakness_severity_counts.items())),
            "packet_weaknesses": packet_weaknesses,
            "trusted_family_count": 0,
            "trusted_case_count": 0,
        },
        "e2e_checks": checks,
        "family_review_rows": review_rows,
        "limitations": [
            "packet_is_for_user_review_not_scoring_promotion",
            "agent_proposals_are_not_ground_truth",
            "candidate_wordnet_senses_may_not_cover_rulegen_dictionary_source",
            _selection_limitation(
                requested_count=max(1, int(pilot_family_count)),
                dataset_family_count=len(all_families),
            ),
        ],
        "next_steps": [
            "User reviews active sense alignment for each source-target family.",
            "User approves, rejects, or rewrites each generated case row.",
            "Approved decisions become a separate reviewed-decision artifact before scoring.",
            "Score surfaces should split pending, approved, rejected, and diagnostic-only rows.",
        ],
    }


def _selection_methodology(*, requested_count: int, dataset_family_count: int) -> str:
    if requested_count >= dataset_family_count:
        return (
            "Full representative-packet review: include every frozen sampled family, "
            "preserving the deterministic representative sample order and source-band "
            "coverage before any trusted scoring or band-formula claims."
        )
    return (
        "Round-robin pilot selection across source Zipf bands from the frozen dataset "
        "order, so the review packet tests the review format across common, mid, rare, "
        "and missing-band cases."
    )


def _selection_limitation(*, requested_count: int, dataset_family_count: int) -> str:
    if requested_count >= dataset_family_count:
        return "full_packet_still_requires_manual_or_user_approval_before_trusted_scoring"
    return "round_robin_pilot_tests_review_format_not_population_accuracy"


def _select_pilot_families(
    families: Sequence[Mapping[str, object]], *, pilot_family_count: int
) -> list[Mapping[str, object]]:
    by_band_and_shadow: dict[str, dict[str, list[Mapping[str, object]]]] = defaultdict(
        lambda: {"with_shadow": [], "without_shadow": []}
    )
    for family in families:
        shadow_key = "with_shadow" if _mapping_rows(family.get("shadows")) else "without_shadow"
        by_band_and_shadow[_family_source_band(family)][shadow_key].append(family)
    for by_shadow in by_band_and_shadow.values():
        for bucket in by_shadow.values():
            bucket.sort(key=_pilot_family_sort_key)
    selected: list[Mapping[str, object]] = []
    seen: set[str] = set()
    _select_from_bands(
        by_band_and_shadow=by_band_and_shadow,
        selected=selected,
        seen=seen,
        source_bands=PRIMARY_SOURCE_BAND_ORDER,
        pilot_family_count=pilot_family_count,
    )
    if len(selected) < pilot_family_count:
        _select_from_bands(
            by_band_and_shadow=by_band_and_shadow,
            selected=selected,
            seen=seen,
            source_bands=SOURCE_BAND_ORDER,
            pilot_family_count=pilot_family_count,
        )
    return selected


def _select_from_bands(
    *,
    by_band_and_shadow: dict[str, dict[str, list[Mapping[str, object]]]],
    selected: list[Mapping[str, object]],
    seen: set[str],
    source_bands: Sequence[str],
    pilot_family_count: int,
) -> None:
    passes = ("with_shadow", "without_shadow")
    while len(selected) < pilot_family_count:
        made_progress = False
        for pass_key in passes:
            for band in source_bands:
                if len(selected) >= pilot_family_count:
                    break
                bucket = by_band_and_shadow.get(band, {}).get(pass_key, [])
                while bucket:
                    family = bucket.pop(0)
                    family_id = str(family.get("family_id") or "")
                    if family_id not in seen:
                        selected.append(family)
                        seen.add(family_id)
                        made_progress = True
                        break
        if not made_progress:
            break


def _pilot_family_sort_key(family: Mapping[str, object]) -> tuple[object, ...]:
    polysemy = _family_dimension(family, "polysemy_band")
    pos_shape = _family_dimension(family, "pos_shape")
    cases = _mapping_rows(family.get("cases"))
    natural_case_count = sum(
        1
        for case in cases
        if "WordNet example" in str(case.get("notes") or "")
        and not _case_weaknesses(
            case_type=_first_dimension(case, "manual_case_type"),
            sentence=str(case.get("sentence") or ""),
            source_phrase=str(case.get("source_phrase") or ""),
            duplicate_sentence=False,
            shadow_target="",
        )
    )
    return (
        0 if polysemy == "high_10_plus" else 1,
        0 if pos_shape == "cross_pos_polysemy" else 1,
        0 if polysemy != "missing" else 1,
        0 if pos_shape != "missing" else 1,
        -natural_case_count,
        str(family.get("family_id") or ""),
    )


def _family_review_row(
    *,
    family: Mapping[str, object],
    index: int,
    wordnet_index: WordNetIndex | None,
    sense_rows_by_source: Mapping[str, Sequence[Mapping[str, object]]] | None,
) -> dict[str, object]:
    active = _as_mapping(family.get("active"))
    trigger = str(family.get("trigger") or "").strip()
    target = str(active.get("target_lemma") or "").strip()
    cases = _mapping_rows(family.get("cases"))
    sentence_counts = Counter(str(case.get("sentence") or "") for case in cases)
    source_band = _family_source_band(family)
    target_band = _family_dimension(family, "target_zipf_band_es")
    polysemy_band = _family_dimension(family, "polysemy_band")
    pos_shape = _family_dimension(family, "pos_shape")
    sense_rows = _wordnet_senses(
        source=trigger,
        wordnet_index=wordnet_index,
        sense_rows_by_source=sense_rows_by_source,
    )
    active_sense_status = "pending_user_review"
    human_review_status = "pending_user_review"
    shadow_target_by_id = {
        str(shadow.get("sense_id") or ""): str(shadow.get("target_lemma") or "")
        for shadow in _mapping_rows(family.get("shadows"))
    }
    case_review_rows = [
        _case_review_row(
            case=case,
            active_sense_status=active_sense_status,
            duplicate_sentence=sentence_counts[str(case.get("sentence") or "")] > 1,
            shadow_target=shadow_target_by_id.get(str(case.get("gold_winner") or ""), ""),
        )
        for case in cases
    ]
    family_weaknesses = _family_weaknesses(
        source_band=source_band,
        case_review_rows=case_review_rows,
    )
    return {
        "review_id": f"full_family_review:{index:03d}",
        "family_id": str(family.get("family_id") or ""),
        "trigger": trigger,
        "target_lemma": target,
        "source_zipf_band_en": source_band,
        "target_zipf_band_es": target_band,
        "polysemy_band": polysemy_band,
        "pos_shape": pos_shape,
        "human_review_status": human_review_status,
        "active_sense_status": active_sense_status,
        "row_quality_status": "pending_user_review",
        "active_evidence": dict(active),
        "shadow_evidence": [dict(row) for row in _mapping_rows(family.get("shadows"))],
        "candidate_wordnet_senses": [
            _sense_payload(row, rank=rank) for rank, row in enumerate(sense_rows[:8], start=1)
        ],
        "agent_proposal": {
            "active_sense_status": "pending_user_review",
            "row_quality_status": "pending_user_review",
            "weaknesses": family_weaknesses,
            "reason": (
                "Agent cannot certify semantic ground truth. User must decide whether "
                f"{trigger} really maps to {target} in the active evidence."
            ),
        },
        "agent_pretriage_weaknesses": family_weaknesses,
        "user_review": _blank_family_review(),
        "case_review_rows": case_review_rows,
    }


def _case_review_row(
    *,
    case: Mapping[str, object],
    active_sense_status: str,
    duplicate_sentence: bool = False,
    shadow_target: str = "",
) -> dict[str, object]:
    case_type = _first_dimension(case, "manual_case_type")
    proposed_quality = _proposed_row_quality(case_type)
    notes = str(case.get("notes") or "")
    sentence = str(case.get("sentence") or "")
    no_winner_subtype = _no_winner_subtype(case_type=case_type, sentence=sentence)
    weaknesses = _case_weaknesses(
        case_type=case_type,
        sentence=sentence,
        source_phrase=str(case.get("source_phrase") or ""),
        duplicate_sentence=duplicate_sentence,
        shadow_target=shadow_target,
    )
    return {
        "case_id": str(case.get("case_id") or ""),
        "sentence": sentence,
        "source_phrase": str(case.get("source_phrase") or ""),
        "gold_decision": str(case.get("gold_decision") or ""),
        "gold_winner": str(case.get("gold_winner") or ""),
        "manual_case_type": case_type,
        "human_review_status": "pending_user_review",
        "active_sense_status": active_sense_status,
        "row_quality_status": "pending_user_review",
        "proposed_row_quality_status": proposed_quality,
        "context_source": _context_source(case_type, notes),
        "evidence_source": "wordnet_or_rulegen_family_evidence",
        "no_winner_subtype": no_winner_subtype,
        "agent_pretriage_weaknesses": weaknesses,
        "agent_notes": notes,
        "user_review": _blank_case_review(case_type=case_type),
    }


def _proposed_row_quality(case_type: str) -> str:
    if case_type == "phrase_no_winner":
        return "no_winner_template_control"
    if case_type == "shadow_negative":
        return "pending_user_review"
    if case_type == "positive_active":
        return "pending_user_review"
    return "diagnostic_only"


def _no_winner_subtype(*, case_type: str, sentence: str) -> str:
    if case_type != "phrase_no_winner":
        return "not_applicable"
    lower = str(sentence or "").lower()
    if "file named" in lower or "spreadsheet column" in lower:
        return "nonsemantic_fragment"
    if "tab labeled" in lower or "saved search query" in lower:
        return "metalinguistic"
    return "mention_only_template_control"


def _context_source(case_type: str, notes: str) -> str:
    if case_type == "phrase_no_winner":
        return "agent_draft_browser_like_no_winner_template"
    if "source-adapted WordNet example" in notes:
        return "agent_draft_from_source_adapted_wordnet_example"
    if "exact WordNet example" in notes:
        return "agent_draft_from_exact_wordnet_example"
    if "definition fallback" in notes:
        return "agent_draft_definition_fallback"
    return "agent_draft_deterministic_template"


def _family_weaknesses(
    *,
    source_band: str,
    case_review_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    weaknesses = ["active_target_sense_not_audited"]
    if source_band == "missing":
        weaknesses.append("source_form_artifact_risk")
    if any(
        "evidence_context_overlap_risk" in _sequence(row.get("agent_pretriage_weaknesses"))
        for row in case_review_rows
    ):
        weaknesses.append("evidence_context_overlap_risk")
    return sorted(dict.fromkeys(weaknesses))


def _case_weaknesses(
    *,
    case_type: str,
    sentence: str,
    source_phrase: str,
    duplicate_sentence: bool,
    shadow_target: str,
) -> list[str]:
    text = str(sentence or "").strip()
    lower = text.lower()
    weaknesses: list[str] = []
    if duplicate_sentence:
        weaknesses.append("duplicate_case_sentence")
    if case_type == "positive_active" and (
        lower.startswith("the article used")
        or "same sense as the spanish target" in lower
        or lower.startswith("readers understood")
    ):
        weaknesses.append("active_context_template_circular")
        weaknesses.append("evidence_context_overlap_risk")
    if case_type == "shadow_negative" and lower.startswith("in this sentence"):
        weaknesses.append("shadow_negative_synthetic_definition_context")
        weaknesses.append("evidence_context_overlap_risk")
    if case_type == "shadow_negative" and "alternate sense" in str(shadow_target or "").lower():
        weaknesses.append("shadow_competitor_target_not_reviewed")
    if case_type == "phrase_no_winner" and "vocabulary term" in lower:
        weaknesses.append("phrase_no_winner_template_control_only")
    if case_type == "phrase_no_winner" and not _contains_source_as_token(
        sentence=sentence,
        source_phrase=source_phrase,
    ):
        weaknesses.append("no_winner_token_boundary_artifact")
    return sorted(dict.fromkeys(weaknesses))


def _contains_source_as_token(*, sentence: str, source_phrase: str) -> bool:
    source_phrase = str(source_phrase or "").strip()
    if not source_phrase:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(source_phrase)}(?!\w)", str(sentence or ""), re.I))


def _packet_weaknesses(
    *,
    review_rows: Sequence[Mapping[str, object]],
    case_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    weaknesses = []
    polysemy_bands = {str(row.get("polysemy_band") or "") for row in review_rows}
    pos_shapes = {str(row.get("pos_shape") or "") for row in review_rows}
    case_types = {str(row.get("manual_case_type") or "") for row in case_rows}
    if "high_10_plus" not in polysemy_bands or "cross_pos_polysemy" not in pos_shapes:
        weaknesses.append("pilot_not_hard_case_representative")
    if not {"positive_active", "shadow_negative", "phrase_no_winner"}.issubset(case_types):
        weaknesses.append("pilot_not_hard_case_representative")
    return sorted(dict.fromkeys(weaknesses))


def _weakness_counts(
    *,
    review_rows: Sequence[Mapping[str, object]],
    case_rows: Sequence[Mapping[str, object]],
    packet_weaknesses: Sequence[str],
) -> Counter[str]:
    counter: Counter[str] = Counter()
    counter.update(str(item) for item in packet_weaknesses)
    for row in review_rows:
        counter.update(str(item) for item in _sequence(row.get("agent_pretriage_weaknesses")))
    for row in case_rows:
        counter.update(str(item) for item in _sequence(row.get("agent_pretriage_weaknesses")))
    return counter


def _weakness_severity_counts(
    *,
    weakness_counts: Mapping[str, int],
    weakness_taxonomy: Mapping[str, object],
) -> Counter[str]:
    severity_by_id = {
        str(row.get("id") or ""): str(row.get("severity") or "unknown")
        for row in _mapping_rows(weakness_taxonomy.get("weakness_types"))
    }
    counter: Counter[str] = Counter()
    for weakness_id, count in weakness_counts.items():
        counter[severity_by_id.get(str(weakness_id), "unknown")] += int(count or 0)
    return counter


def _public_weakness_taxonomy(value: Mapping[str, object]) -> dict[str, object]:
    return {
        "taxonomy_id": str(value.get("taxonomy_id") or ""),
        "purpose": str(value.get("purpose") or ""),
        "weakness_types": [
            {
                "id": str(row.get("id") or ""),
                "scope": str(row.get("scope") or ""),
                "severity": str(row.get("severity") or ""),
                "detection": str(row.get("detection") or ""),
                "meaning": str(row.get("meaning") or ""),
                "avoid_by": str(row.get("avoid_by") or ""),
                "review_action": str(row.get("review_action") or ""),
            }
            for row in _mapping_rows(value.get("weakness_types"))
        ],
    }


def _wordnet_senses(
    *,
    source: str,
    wordnet_index: WordNetIndex | None,
    sense_rows_by_source: Mapping[str, Sequence[Mapping[str, object]]] | None,
) -> list[Mapping[str, object]]:
    if sense_rows_by_source is not None:
        return [dict(row) for row in sense_rows_by_source.get(source, [])]
    if wordnet_index is None:
        return []
    entry = wordnet_index.entries_by_word.get(source)
    if not isinstance(entry, Mapping):
        return []
    rows: list[Mapping[str, object]] = []
    for pos_key, section in entry.items():
        if not isinstance(section, Mapping):
            continue
        for sense_rank, raw_sense in enumerate(_sequence(section.get("sense")), start=1):
            if not isinstance(raw_sense, Mapping):
                continue
            synset_id = str(raw_sense.get("synset") or "").strip()
            synset = wordnet_index.synsets_by_id.get(synset_id)
            if not isinstance(synset, Mapping):
                continue
            definitions = _text_list(synset.get("definition"))
            examples = [*_text_list(synset.get("example")), *_text_list(raw_sense.get("sent"))]
            rows.append(
                {
                    "synset_id": synset_id,
                    "pos": str(pos_key or ""),
                    "sense_rank": sense_rank,
                    "definition": definitions[0] if definitions else "",
                    "examples": examples,
                    "members": _text_list(synset.get("members")),
                }
            )
    return sorted(rows, key=lambda row: (int(row.get("sense_rank") or 999), str(row.get("pos"))))


def _sense_payload(row: Mapping[str, object], *, rank: int) -> dict[str, object]:
    return {
        "candidate_rank": rank,
        "synset_id": str(row.get("synset_id") or ""),
        "pos": str(row.get("pos") or ""),
        "sense_rank": int(row.get("sense_rank") or rank),
        "definition": str(row.get("definition") or ""),
        "examples": [str(item) for item in _sequence(row.get("examples"))[:4]],
        "members": [str(item) for item in _sequence(row.get("members"))[:12]],
        "user_review": {
            "matches_active_target": "",
            "notes": "",
        },
    }


def _blank_family_review() -> dict[str, str]:
    return {
        "human_review_status": "",
        "active_sense_status": "",
        "active_sense_notes": "",
        "corrected_active_evidence": "",
        "family_disposition": "",
        "reviewer": "",
        "reviewed_at": "",
    }


def _blank_case_review(*, case_type: str) -> dict[str, str]:
    return {
        "human_review_status": "",
        "gold_decision": "",
        "row_quality_status": "",
        "no_winner_subtype": "" if case_type == "phrase_no_winner" else "not_applicable",
        "corrected_sentence": "",
        "notes": "",
        "reviewer": "",
        "reviewed_at": "",
    }


def _checks(
    *,
    all_families: Sequence[Mapping[str, object]],
    review_rows: Sequence[Mapping[str, object]],
    requested_count: int,
) -> dict[str, bool]:
    case_rows = [
        case for family in review_rows for case in _mapping_rows(family.get("case_review_rows"))
    ]
    bands = {str(row.get("source_zipf_band_en") or "") for row in review_rows}
    return {
        "dataset_families_available": bool(all_families),
        "requested_review_families_selected": len(review_rows)
        == min(len(all_families), requested_count),
        "all_families_pending_user_review": all(
            row.get("human_review_status") == "pending_user_review" for row in review_rows
        ),
        "all_cases_pending_user_review": all(
            row.get("human_review_status") == "pending_user_review" for row in case_rows
        ),
        "no_trusted_rows_without_user_review": not any(
            row.get("row_quality_status") == "trusted" for row in case_rows
        ),
        "phrase_no_winner_rows_subtyped": all(
            row.get("no_winner_subtype") != ""
            for row in case_rows
            if row.get("manual_case_type") == "phrase_no_winner"
        ),
        "shadow_negative_rows_present": any(
            row.get("manual_case_type") == "shadow_negative" for row in case_rows
        ),
        "multiple_source_bands_present": len(bands) >= 2,
    }


def _family_source_band(family: Mapping[str, object]) -> str:
    return _family_dimension(family, "source_zipf_band_en") or "missing"


def _family_dimension(family: Mapping[str, object], key: str) -> str:
    for case in _mapping_rows(family.get("cases")):
        value = _first_dimension(case, key)
        if value:
            return value
    return "missing"


def _first_dimension(case: Mapping[str, object], key: str) -> str:
    values = _as_mapping(case.get("slice_dimensions")).get(key, [])
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)) and values:
        return str(values[0] or "")
    return ""


def _sequence(value: object) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(value)


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(item) for item in _sequence(value) if str(item).strip()]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
