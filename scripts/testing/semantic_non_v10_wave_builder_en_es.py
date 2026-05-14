#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402
from semantic_example_frame_source_adapter_support import slug as _slug  # noqa: E402
from semantic_non_v10_wave_builder_io import _load_json, _utc_now, _write_json  # noqa: E402
from semantic_non_v10_wave_builder_support import (  # noqa: E402
    active_visible_target_aliases as _active_visible_target_aliases,
    alternate_same_pos as _alternate_same_pos,
    eligible_rows as _eligible_rows,
    evidence_views as _evidence_views,
    missing_shape_reason as _missing_shape_reason,
    reason_counts as _reason_counts,
    selected_active_shadow_pair as _selected_active_shadow_pair,
    source_summary as _source_summary,
    temporary_sense_for_link as _temporary_sense_for_link,
    translation_sort_key as _translation_sort_key,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


DEFAULT_CANDIDATE_JSON = TEST_OUTPUTS_ROOT / "semantic_non_v10_inventory_candidates_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_non_v10_wave2_draft_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_non_v10_wave2_draft_latest.md"
DEFAULT_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
DEFAULT_DATASET_OUT = DEFAULT_DRAFT_ROOT / "en_es_source_non_v10_wave2_draft_v1_dataset.json"
DEFAULT_QUEUE_OUT = DEFAULT_DRAFT_ROOT / "semantic_source_non_v10_wave2_draft_queue_en_es_v1.json"
DEFAULT_WAVE_ID = "source_non_v10_wave2_draft_v1"
DEFAULT_WAVE_SIZE = 8
DEFAULT_MAX_SENSE_COUNT = 20
DEFAULT_MIN_WORDNET_LINK_SCORE = 0.2
SUPPORTED_POS = frozenset({"noun", "verb", "adjective", "adverb"})
FAMILY_POS_STRATEGIES = ("noun_verb", "any_cross_pos")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a bounded draft en-es active/shadow family wave from the automatic "
            "non-v10 WordNet candidate inventory and local Wiktionary translation packs."
        )
    )
    parser.add_argument("--candidate-json", type=Path, default=DEFAULT_CANDIDATE_JSON)
    parser.add_argument("--data-root", type=Path, default=Path(resolve_data_root()))
    parser.add_argument("--wiktionary-en-es-sqlite", type=Path, default=None)
    parser.add_argument("--wiktionary-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--freedict-es-en-sqlite", type=Path, default=None)
    parser.add_argument("--wordnet-dir", type=Path, default=None)
    parser.add_argument("--wave-id", default=DEFAULT_WAVE_ID)
    parser.add_argument("--wave-size", type=int, default=DEFAULT_WAVE_SIZE)
    parser.add_argument("--max-sense-count", type=int, default=DEFAULT_MAX_SENSE_COUNT)
    parser.add_argument(
        "--min-wordnet-link-score", type=float, default=DEFAULT_MIN_WORDNET_LINK_SCORE
    )
    parser.add_argument(
        "--family-pos-strategy",
        choices=FAMILY_POS_STRATEGIES,
        default="noun_verb",
        help="Translation-family shape to construct. noun_verb preserves the original control.",
    )
    parser.add_argument(
        "--allow-unsupported-translations",
        action="store_true",
        help="Allow forward-only translations without reverse Wiktionary or FreeDict support.",
    )
    parser.add_argument("--include-alternate-noun-shadow", action="store_true", default=True)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--dataset-out", type=Path, default=DEFAULT_DATASET_OUT)
    parser.add_argument("--queue-out", type=Path, default=DEFAULT_QUEUE_OUT)
    return parser.parse_args()


def build_non_v10_wave_draft_report(
    *,
    candidate_payload: Mapping[str, object],
    wiktionary_en_es_sqlite: Path,
    wiktionary_es_en_sqlite: Path | None = None,
    freedict_es_en_sqlite: Path | None = None,
    wordnet_index: WordNetIndex | None = None,
    wave_id: str = DEFAULT_WAVE_ID,
    wave_size: int = DEFAULT_WAVE_SIZE,
    max_sense_count: int = DEFAULT_MAX_SENSE_COUNT,
    min_wordnet_link_score: float = DEFAULT_MIN_WORDNET_LINK_SCORE,
    require_translation_support: bool = True,
    include_alternate_noun_shadow: bool = True,
    family_pos_strategy: str = "noun_verb",
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    selected: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    with sqlite3.connect(wiktionary_en_es_sqlite) as forward_conn:
        forward_conn.row_factory = sqlite3.Row
        reverse_conn = _connect_optional(wiktionary_es_en_sqlite)
        freedict_conn = _connect_optional(freedict_es_en_sqlite)
        try:
            for candidate in candidate_payload.get("candidates", ()):
                if not isinstance(candidate, Mapping):
                    continue
                if len(selected) >= max(0, int(wave_size)):
                    break
                trigger = str(candidate.get("trigger") or "").strip().lower()
                if not trigger:
                    continue
                sense_count = int(candidate.get("sense_count") or 0)
                if sense_count > int(max_sense_count):
                    skipped.append(
                        _skip_row(candidate, reason="candidate_too_polysemous_for_first_wave")
                    )
                    continue
                translations = _translation_rows(
                    forward_conn,
                    trigger=trigger,
                    reverse_conn=reverse_conn,
                    freedict_conn=freedict_conn,
                )
                translations = _annotate_wordnet_links(
                    translations,
                    trigger=trigger,
                    wordnet_index=wordnet_index,
                    min_link_score=min_wordnet_link_score,
                )
                family = _draft_family_for_candidate(
                    candidate,
                    translations=translations,
                    wave_id=wave_id,
                    include_alternate_noun_shadow=include_alternate_noun_shadow,
                    require_wordnet_link=wordnet_index is not None,
                    require_translation_support=require_translation_support,
                    family_pos_strategy=family_pos_strategy,
                )
                if family is None:
                    skipped.append(
                        _skip_row(
                            candidate,
                            reason=_missing_shape_reason(
                                translations,
                                require_wordnet_link=wordnet_index is not None,
                                require_translation_support=require_translation_support,
                                family_pos_strategy=family_pos_strategy,
                            ),
                        )
                    )
                    continue
                selected.append(family)
        finally:
            if reverse_conn is not None:
                reverse_conn.close()
            if freedict_conn is not None:
                freedict_conn.close()
    dataset = _draft_dataset(
        selected,
        wave_id=wave_id,
        generated_at=generated_at,
        candidate_inventory_id=str(candidate_payload.get("inventory_id") or "").strip(),
    )
    queue = _draft_queue(dataset, wave_id=wave_id, generated_at=generated_at)
    readiness = _readiness(selected=selected, requested_wave_size=wave_size)
    return {
        "schema_version": 1,
        "status": readiness["status"],
        "decision": readiness["decision"],
        "generated_at": generated_at,
        "pair": "en-es",
        "wave_id": wave_id,
        "source_candidate_inventory_id": str(candidate_payload.get("inventory_id") or "").strip(),
        "summary": {
            "requested_wave_size": int(wave_size),
            "selected_family_count": len(selected),
            "skipped_candidate_count": len(skipped),
            "families_with_alternate_noun_shadow": sum(
                1 for family in selected if bool(family.get("has_alternate_noun_shadow"))
            ),
            "families_with_reverse_support": sum(
                1 for family in selected if bool(family.get("has_reverse_support"))
            ),
            "families_with_freedict_support": sum(
                1 for family in selected if bool(family.get("has_freedict_support"))
            ),
            "families_with_wordnet_link_support": sum(
                1 for family in selected if bool(family.get("has_wordnet_link_support"))
            ),
            "family_pos_strategy": str(family_pos_strategy or "").strip() or "noun_verb",
            "skipped_reason_counts": _reason_counts(skipped),
        },
        "readiness": readiness,
        "selected_families": selected,
        "skipped_candidates": skipped[:25],
        "draft_dataset": dataset,
        "draft_queue": queue,
        "limitations": [
            "draft_translation_family_requires_review_before_quality_claims",
            "only_loader_seed_cases_generated_no_heldout_cases_in_this_step",
            "wordnet_source_admission_can_test_source_linkage_but_not_end_to_end_quality",
        ],
        "next_steps": [
            "run WordNet definition-preferred extraction on the draft dataset",
            "run source admission with ablation skipped until independent cases exist",
            "review or generate held-out active/shadow cases for the admitted draft families",
            "rerun failure-class mining once held-out validation exists for the new wave",
        ],
    }


def render_non_v10_wave_draft_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    readiness = _as_mapping(report.get("readiness"))
    lines = [
        "# en-es Non-v10 Source Wave Draft",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Wave: `{report.get('wave_id', '')}`",
        f"- Selected families: `{summary.get('selected_family_count', 0)}` / `{summary.get('requested_wave_size', 0)}`",
        f"- Reverse-supported families: `{summary.get('families_with_reverse_support', 0)}`",
        f"- FreeDict-supported families: `{summary.get('families_with_freedict_support', 0)}`",
        f"- WordNet-link-supported families: `{summary.get('families_with_wordnet_link_support', 0)}`",
        f"- Readiness reason: `{readiness.get('reason', '')}`",
        "",
        "## Draft Families",
        "",
        _family_table(report.get("selected_families", ())),
        "",
        "## Skipped Candidates",
        "",
        _skip_table(report.get("skipped_candidates", ())),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _draft_family_for_candidate(
    candidate: Mapping[str, object],
    *,
    translations: Sequence[Mapping[str, object]],
    wave_id: str,
    include_alternate_noun_shadow: bool,
    require_wordnet_link: bool,
    require_translation_support: bool,
    family_pos_strategy: str,
) -> dict[str, object] | None:
    trigger = str(candidate.get("trigger") or "").strip().lower()
    selected_pair = _selected_active_shadow_pair(
        translations,
        family_pos_strategy=family_pos_strategy,
        require_wordnet_link=require_wordnet_link,
        require_translation_support=require_translation_support,
    )
    if selected_pair is None:
        return None
    active_row, shadow_row = selected_pair
    eligible_same_pos = _eligible_rows(
        translations,
        canonical_pos=str(active_row.get("canonical_pos") or ""),
        require_wordnet_link=require_wordnet_link,
        require_translation_support=require_translation_support,
    )
    alternate_same_pos = (
        _alternate_same_pos(active_row, eligible_same_pos)
        if include_alternate_noun_shadow and str(active_row.get("canonical_pos") or "") == "noun"
        else None
    )
    active_target = str(active_row.get("translation") or "").strip()
    family_id = f"en-es:sentence-veto:{trigger}:{_slug(active_target)}"
    active_sense_id = f"{family_id}:active"
    active_visible_aliases = _active_visible_target_aliases(active_row, translations)
    active_payload = {
        **_sense_payload(
            family_id=family_id,
            trigger=trigger,
            row=active_row,
            sense_role="active",
            suffix="active",
            visible_alias_rows=active_visible_aliases,
        ),
        "sense_id": active_sense_id,
    }
    shadows = [
        _sense_payload(
            family_id=family_id,
            trigger=trigger,
            row=shadow_row,
            sense_role="shadow",
            suffix="shadow",
        )
    ]
    if alternate_same_pos is not None:
        shadows.insert(
            0,
            _sense_payload(
                family_id=family_id,
                trigger=trigger,
                row=alternate_same_pos,
                sense_role="shadow",
                suffix="shadow",
            ),
        )
    selected_rows = [active_row, shadow_row, *([alternate_same_pos] if alternate_same_pos else [])]
    has_reverse = any(bool(row.get("reverse_support")) for row in selected_rows)
    has_freedict = any(bool(row.get("freedict_support")) for row in selected_rows)
    has_wordnet = any(bool(row.get("wordnet_linked")) for row in selected_rows)
    return {
        "family_id": family_id,
        "trigger": trigger,
        "candidate_id": str(candidate.get("candidate_id") or "").strip(),
        "candidate_score": float(candidate.get("score") or 0.0),
        "candidate_complexity_band": str(candidate.get("complexity_band") or "").strip(),
        "active_translation_source": _source_summary(active_row),
        "shadow_translation_sources": [
            _source_summary(row) for row in shadows_from_rows(shadows, selected_rows)
        ],
        "has_alternate_noun_shadow": alternate_same_pos is not None,
        "has_reverse_support": has_reverse,
        "has_freedict_support": has_freedict,
        "has_wordnet_link_support": has_wordnet,
        "active_visible_target_alias_count": len(active_visible_aliases),
        "review_state": "draft_needs_target_review",
        "active": active_payload,
        "shadows": shadows,
        "cases": _loader_only_cases(
            family_id=family_id,
            trigger=trigger,
            active_sense_id=active_sense_id,
            active_row=active_row,
        ),
        "metadata": {
            "wave_id": wave_id,
            "construction_method": (
                "wiktionary_forward_translation_with_reverse_support:"
                f"{str(family_pos_strategy or '').strip() or 'noun_verb'}"
            ),
            "source_candidate": dict(candidate),
            "translation_candidates": [dict(row) for row in translations[:12]],
            "requires_independent_cases": True,
            "requires_wordnet_link": require_wordnet_link,
        },
    }


def shadows_from_rows(
    shadows: Sequence[Mapping[str, object]], selected_rows: Sequence[Mapping[str, object]]
) -> list[Mapping[str, object]]:
    shadow_targets = {str(shadow.get("target_lemma") or "") for shadow in shadows}
    return [row for row in selected_rows if str(row.get("translation") or "") in shadow_targets]


def _sense_payload(
    *,
    family_id: str,
    trigger: str,
    row: Mapping[str, object],
    sense_role: str,
    suffix: str,
    visible_alias_rows: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    target = str(row.get("translation") or "").strip()
    canonical_pos = str(row.get("canonical_pos") or "").strip()
    sense_text = str(row.get("sense_text") or "").strip()
    evidence = _evidence_views(
        trigger=trigger,
        target=target,
        row=row,
        visible_alias_rows=visible_alias_rows,
    )
    metadata = {
        "sense_role": sense_role,
        "translation_rank": int(row.get("rank") or 0),
        "translation_pos": str(row.get("pos") or "").strip(),
        "translation_sense_text": sense_text,
        "support_sources": list(row.get("support_sources") or ()),
        "reverse_support": bool(row.get("reverse_support")),
        "freedict_support": bool(row.get("freedict_support")),
        "wordnet_linked": bool(row.get("wordnet_linked")),
        "best_wordnet_link_score": float(row.get("best_wordnet_link_score") or 0.0),
        "best_wordnet_overlap": list(row.get("best_wordnet_overlap") or ()),
    }
    alias_summaries = [_source_summary(alias) for alias in visible_alias_rows]
    if alias_summaries:
        metadata["visible_target_aliases"] = alias_summaries
    return {
        "sense_id": f"{family_id}:{_slug(target)}:{suffix}",
        "target_lemma": target,
        "canonical_pos": canonical_pos,
        "evidence_views": evidence,
        "metadata": metadata,
    }


def _loader_only_cases(
    *,
    family_id: str,
    trigger: str,
    active_sense_id: str,
    active_row: Mapping[str, object],
) -> list[dict[str, object]]:
    sense_text = str(active_row.get("sense_text") or "").strip()
    case_hint = sense_text.split(";")[0].strip(". ") if sense_text else "the selected noun sense"
    return [
        {
            "case_id": f"{family_id}:draft-loader:001",
            "sentence": f"The word {trigger} is being checked for {case_hint}.",
            "source_phrase": trigger,
            "gold_winner": active_sense_id,
            "gold_decision": "replace",
            "slice_tags": [
                "non_v10_wave_draft",
                "loader_only",
                "not_quality_evaluation",
            ],
        }
    ]


def _translation_rows(
    conn: sqlite3.Connection,
    *,
    trigger: str,
    reverse_conn: sqlite3.Connection | None,
    freedict_conn: sqlite3.Connection | None,
) -> list[dict[str, object]]:
    rows = conn.execute(
        """
        SELECT
          sg.headword,
          sg.translation,
          sg.translation_lc,
          sg.pos,
          sg.raw_glosses_json,
          e.rank,
          COALESCE(tm.sense_text, tm.english_text, tm.note_text, '') AS sense_text
        FROM sense_glosses sg
        LEFT JOIN entries e
          ON e.headword_lc = sg.headword_lc
         AND e.translation_lc = sg.translation_lc
        LEFT JOIN translation_meta tm
          ON tm.entry_ord = sg.entry_ord
         AND tm.sense_ord = sg.sense_ord
         AND tm.gloss_ord = sg.gloss_ord
        WHERE sg.headword_lc = ?
        ORDER BY COALESCE(e.rank, 9999), sg.sense_ord, sg.gloss_ord
        """,
        (trigger,),
    ).fetchall()
    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for raw in rows:
        canonical_pos = _canonical_pos(raw["pos"])
        if canonical_pos not in SUPPORTED_POS:
            continue
        translation = str(raw["translation"] or "").strip()
        reverse_support = _has_reverse_support(
            reverse_conn, translation=translation, trigger=trigger
        )
        freedict_support = _has_reverse_support(
            freedict_conn, translation=translation, trigger=trigger
        )
        if not _translation_is_usable(
            translation,
            trigger=trigger,
            reverse_support=reverse_support,
            freedict_support=freedict_support,
        ):
            continue
        raw_glosses = _json_string_list(raw["raw_glosses_json"])
        key = (translation.lower(), canonical_pos)
        support_sources = ["wiktionary_en_es"]
        if reverse_support:
            support_sources.append("wiktionary_es_en")
        if freedict_support:
            support_sources.append("freedict_es_en")
        row = {
            "headword": str(raw["headword"] or "").strip(),
            "translation": translation,
            "translation_lc": str(raw["translation_lc"] or translation.lower()).strip(),
            "pos": str(raw["pos"] or "").strip(),
            "canonical_pos": canonical_pos,
            "rank": int(raw["rank"] or 9999),
            "sense_text": str(raw["sense_text"] or "").strip(),
            "raw_glosses": raw_glosses,
            "reverse_support": reverse_support,
            "freedict_support": freedict_support,
            "support_sources": support_sources,
        }
        previous = deduped.get(key)
        if previous is None or _translation_sort_key(row) < _translation_sort_key(previous):
            deduped[key] = row
    return sorted(deduped.values(), key=_translation_sort_key)


def _annotate_wordnet_links(
    translations: Sequence[Mapping[str, object]],
    *,
    trigger: str,
    wordnet_index: WordNetIndex | None,
    min_link_score: float,
) -> list[dict[str, object]]:
    annotated: list[dict[str, object]] = []
    for row in translations:
        materialized = dict(row)
        materialized.setdefault("wordnet_linked", False)
        materialized.setdefault("best_wordnet_link_score", 0.0)
        materialized.setdefault("best_wordnet_overlap", [])
        if wordnet_index is not None:
            sense = _temporary_sense_for_link(row, trigger=trigger)
            candidates = wordnet_index.candidates_for_sense(
                trigger=trigger,
                sense=sense,
                min_link_score=max(0.0, float(min_link_score)),
            )
            best = candidates[0] if candidates else None
            if best is not None:
                materialized["wordnet_linked"] = True
                materialized["best_wordnet_link_score"] = float(best.score)
                materialized["best_wordnet_overlap"] = list(best.overlap_tokens)
                materialized["best_wordnet_synset_id"] = best.synset_id
        annotated.append(materialized)
    return sorted(annotated, key=_translation_sort_key)


def _draft_dataset(
    families: Sequence[Mapping[str, object]],
    *,
    wave_id: str,
    generated_at: str,
    candidate_inventory_id: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": f"en_es_{wave_id}",
        "generated_at": generated_at,
        "description": (
            "Draft non-v10 source-backed wave constructed from automatic WordNet "
            "candidates and local Wiktionary en-es translations. Families require "
            "review and independent cases before quality claims."
        ),
        "source_candidate_inventory_id": candidate_inventory_id,
        "review_state": "draft_needs_target_review",
        "families": [_dataset_family(family) for family in families],
    }


def _dataset_family(family: Mapping[str, object]) -> dict[str, object]:
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active": dict(_as_mapping(family.get("active"))),
        "shadows": [
            dict(shadow) for shadow in family.get("shadows", ()) if isinstance(shadow, Mapping)
        ],
        "cases": [dict(case) for case in family.get("cases", ()) if isinstance(case, Mapping)],
        "metadata": dict(_as_mapping(family.get("metadata"))),
    }


def _draft_queue(
    dataset: Mapping[str, object],
    *,
    wave_id: str,
    generated_at: str,
) -> dict[str, object]:
    families = []
    for index, family in enumerate(dataset.get("families", ()), start=1):
        if not isinstance(family, Mapping):
            continue
        families.append(
            {
                "family_id": str(family.get("family_id") or "").strip(),
                "trigger": str(family.get("trigger") or "").strip(),
                "role": "target",
                "archetype": "automatic_non_v10_translation_family_draft",
                "likely_bucket": "source_coverage_probe",
                "priority_rank": index,
                "review_state": "draft_needs_target_review",
            }
        )
    return {
        "schema_version": 1,
        "queue_id": f"semantic_{wave_id}_queue_en_es",
        "pair": "en-es",
        "generated_at": generated_at,
        "source_inventory_id": "semantic_non_v10_inventory_candidates_en_es",
        "dataset_id": str(dataset.get("dataset_id") or "").strip(),
        "families": families,
    }


def _readiness(
    *, selected: Sequence[Mapping[str, object]], requested_wave_size: int
) -> dict[str, object]:
    if len(selected) >= int(requested_wave_size) and selected:
        return {
            "status": "review",
            "decision": "draft_wave_ready_for_source_linkage",
            "reason": "translation_family_draft_complete_but_unreviewed",
        }
    if selected:
        return {
            "status": "review",
            "decision": "partial_draft_wave_ready_for_source_linkage",
            "reason": "not_enough_candidate_translations_for_requested_wave_size",
        }
    return {
        "status": "review",
        "decision": "draft_wave_blocked",
        "reason": "no_candidates_with_required_translation_shape",
    }


def _family_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No draft families selected."
    lines = [
        "| Rank | Trigger | Active | Shadows | Reverse support | FreeDict support |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(materialized, start=1):
        active = _as_mapping(row.get("active"))
        shadows = [
            f"{shadow.get('target_lemma', '')} ({shadow.get('canonical_pos', '')})"
            for shadow in row.get("shadows", ())
            if isinstance(shadow, Mapping)
        ]
        lines.append(
            f"| `{index}` | `{row.get('trigger', '')}` | "
            f"`{active.get('target_lemma', '')} ({active.get('canonical_pos', '')})` | "
            f"`{', '.join(shadows)}` | `{bool(row.get('has_reverse_support'))}` | "
            f"`{bool(row.get('has_freedict_support'))}` |"
        )
    return "\n".join(lines)


def _skip_table(rows: object) -> str:
    materialized = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not materialized:
        return "No skipped candidates before the requested wave filled."
    lines = ["| Trigger | Reason |", "| --- | --- |"]
    for row in materialized[:12]:
        lines.append(f"| `{row.get('trigger', '')}` | `{row.get('reason', '')}` |")
    return "\n".join(lines)


def _skip_row(candidate: Mapping[str, object], *, reason: str) -> dict[str, object]:
    return {
        "trigger": str(candidate.get("trigger") or "").strip(),
        "candidate_id": str(candidate.get("candidate_id") or "").strip(),
        "score": float(candidate.get("score") or 0.0),
        "sense_count": int(candidate.get("sense_count") or 0),
        "reason": reason,
    }


def _translation_is_usable(
    translation: str,
    *,
    trigger: str,
    reverse_support: bool,
    freedict_support: bool,
) -> bool:
    normalized = translation.strip().lower()
    if not normalized:
        return False
    if "/" in normalized:
        return False
    if normalized == trigger.strip().lower() and not (reverse_support or freedict_support):
        return False
    return True


def _canonical_pos(value: object) -> str:
    text = str(value or "").strip().lower()
    if "noun" in text:
        return "noun"
    if "verb" in text:
        return "verb"
    if "adj" in text:
        return "adjective"
    if "adv" in text:
        return "adverb"
    return ""


def _json_string_list(value: object) -> list[str]:
    if isinstance(value, str) and value.strip():
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return [value.strip()]
        return [str(item).strip() for item in _as_sequence(payload) if str(item or "").strip()]
    return []


def _has_reverse_support(
    conn: sqlite3.Connection | None, *, translation: str, trigger: str
) -> bool:
    if conn is None:
        return False
    row = conn.execute(
        """
        SELECT 1
        FROM entries
        WHERE headword_lc = ? AND translation_lc = ?
        LIMIT 1
        """,
        (translation.strip().lower(), trigger.strip().lower()),
    ).fetchone()
    return row is not None


def _connect_optional(path: Path | None) -> sqlite3.Connection | None:
    if path is None or not path.exists():
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def main() -> int:
    args = _parse_args()
    wiktionary_en_es = args.wiktionary_en_es_sqlite or (
        args.data_root / "language_packs" / "wiktionary-en-es.sqlite"
    )
    wiktionary_es_en = args.wiktionary_es_en_sqlite or (
        args.data_root / "language_packs" / "wiktionary-es-en.sqlite"
    )
    freedict_es_en = args.freedict_es_en_sqlite or (
        args.data_root / "language_packs" / "freedict-es-en" / "main.sqlite"
    )
    wordnet_dir = args.wordnet_dir or (
        args.data_root / "language_packs" / "english-wordnet-2025-json"
    )
    wordnet_index = WordNetIndex.load(wordnet_dir) if wordnet_dir.exists() else None
    report = build_non_v10_wave_draft_report(
        candidate_payload=_load_json(args.candidate_json),
        wiktionary_en_es_sqlite=wiktionary_en_es,
        wiktionary_es_en_sqlite=wiktionary_es_en if wiktionary_es_en.exists() else None,
        freedict_es_en_sqlite=freedict_es_en if freedict_es_en.exists() else None,
        wordnet_index=wordnet_index,
        wave_id=args.wave_id,
        wave_size=args.wave_size,
        max_sense_count=args.max_sense_count,
        min_wordnet_link_score=args.min_wordnet_link_score,
        require_translation_support=not args.allow_unsupported_translations,
        include_alternate_noun_shadow=bool(args.include_alternate_noun_shadow),
        family_pos_strategy=args.family_pos_strategy,
    )
    report["artifacts"] = {
        "candidate_json": str(args.candidate_json),
        "wiktionary_en_es_sqlite": str(wiktionary_en_es),
        "wiktionary_es_en_sqlite": str(wiktionary_es_en) if wiktionary_es_en.exists() else "",
        "freedict_es_en_sqlite": str(freedict_es_en) if freedict_es_en.exists() else "",
        "wordnet_dir": str(wordnet_dir) if wordnet_dir.exists() else "",
        "draft_dataset_json": str(args.dataset_out),
        "draft_queue_json": str(args.queue_out),
    }
    _write_json(args.dataset_out, _as_mapping(report.get("draft_dataset")))
    _write_json(args.queue_out, _as_mapping(report.get("draft_queue")))
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_non_v10_wave_draft_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
