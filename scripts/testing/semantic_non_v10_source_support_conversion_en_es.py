#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
DEFAULT_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
for candidate in (str(CORE_ROOT), str(Path(__file__).resolve().parent)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_non_v10_wave_builder_support import translation_sort_key  # noqa: E402


DEFAULT_DATASET_JSON = (
    DEFAULT_DRAFT_ROOT
    / "en_es_source_non_v10_wave3_anypos_unsupported_upper_bound_selected_v1_dataset.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_non_v10_source_support_conversion_wave3_anypos_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_non_v10_source_support_conversion_wave3_anypos_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit an upper-bound non-v10 selected wave and classify what is required "
            "to convert forward-only translation rows into supported source-backed rows."
        )
    )
    parser.add_argument("--dataset-json", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_source_support_conversion_report(
    *,
    dataset_payload: Mapping[str, object],
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    families = [
        _family_support_row(family)
        for family in dataset_payload.get("families", ())
        if isinstance(family, Mapping)
    ]
    unsupported_rows = [
        row
        for family in families
        for row in family.get("unsupported_senses", ())
        if isinstance(row, Mapping)
    ]
    family_state_counts = _count_by_key(families, "support_state")
    row_state_counts = _count_by_key(unsupported_rows, "conversion_state")
    fully_supported_count = int(family_state_counts.get("already_supported", 0))
    needs_review_count = int(family_state_counts.get("needs_reviewed_source_support", 0))
    convertible_count = int(family_state_counts.get("candidate_swap_review_available", 0))
    return {
        "schema_version": 1,
        "status": "ok" if fully_supported_count == len(families) and families else "review",
        "decision": (
            "selected_wave_source_supported"
            if fully_supported_count == len(families) and families
            else "support_conversion_needed"
        ),
        "generated_at": generated_at,
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "translation_support_mode": str(
            dataset_payload.get("translation_support_mode") or ""
        ).strip(),
        "summary": {
            "family_count": len(families),
            "fully_supported_family_count": fully_supported_count,
            "candidate_swap_review_family_count": convertible_count,
            "needs_reviewed_source_support_family_count": needs_review_count,
            "selected_sense_count": sum(
                int(row.get("selected_sense_count") or 0) for row in families
            ),
            "supported_sense_count": sum(
                int(row.get("supported_sense_count") or 0) for row in families
            ),
            "unsupported_sense_count": len(unsupported_rows),
            "unsupported_active_count": sum(
                1 for row in unsupported_rows if row.get("role") == "active"
            ),
            "unsupported_shadow_count": sum(
                1 for row in unsupported_rows if row.get("role") == "shadow"
            ),
            "unsupported_rows_with_same_pos_supported_alternative": sum(
                1 for row in unsupported_rows if bool(row.get("same_pos_supported_alternatives"))
            ),
            "family_state_counts": family_state_counts,
            "unsupported_row_state_counts": row_state_counts,
        },
        "families": families,
        "limitations": [
            "conversion_audit_does_not_change_selected_family_targets",
            "same_pos_alternatives_require_review_and_re_admission_before_use",
            "forward_only_rows_are_not_promotion_evidence_without_source_support",
            "phrase_containment_coverage_is_out_of_scope_for_this_audit",
        ],
        "next_steps": _next_steps(
            unsupported_rows=unsupported_rows,
            convertible_count=convertible_count,
            needs_review_count=needs_review_count,
        ),
    }


def render_source_support_conversion_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Non-v10 Source Support Conversion Audit",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Translation support mode: `{report.get('translation_support_mode', '')}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- Fully supported families: `{summary.get('fully_supported_family_count', 0)}`",
        f"- Candidate-swap review families: `{summary.get('candidate_swap_review_family_count', 0)}`",
        f"- Needs reviewed source support: `{summary.get('needs_reviewed_source_support_family_count', 0)}`",
        f"- Supported senses: `{summary.get('supported_sense_count', 0)}` / `{summary.get('selected_sense_count', 0)}`",
        f"- Unsupported active/shadow senses: `{summary.get('unsupported_active_count', 0)}` / `{summary.get('unsupported_shadow_count', 0)}`",
        "",
        "## Family Conversion Table",
        "",
        _family_table(report.get("families", ())),
        "",
        "## Unsupported Sense Details",
        "",
        _unsupported_table(report.get("families", ())),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _family_support_row(family: Mapping[str, object]) -> dict[str, object]:
    candidate_rows = [
        row
        for row in _as_mapping(family.get("metadata")).get("translation_candidates", ())
        if isinstance(row, Mapping)
    ]
    senses = _selected_senses(family)
    selected_targets = {
        _normalize_text(sense.get("target_lemma")) for sense in senses if sense.get("target_lemma")
    }
    unsupported = [
        {
            **sense,
            "same_pos_supported_alternatives": _supported_alternatives(
                candidate_rows,
                canonical_pos=str(sense.get("canonical_pos") or ""),
                selected_target=str(sense.get("target_lemma") or ""),
                family_selected_targets=selected_targets,
            ),
        }
        for sense in senses
        if not bool(sense.get("has_translation_support"))
    ]
    for row in unsupported:
        row["conversion_state"] = (
            "candidate_swap_review_available"
            if row.get("same_pos_supported_alternatives")
            else "needs_reviewed_source_support"
        )
    if not unsupported:
        support_state = "already_supported"
    elif all(row.get("same_pos_supported_alternatives") for row in unsupported):
        support_state = "candidate_swap_review_available"
    else:
        support_state = "needs_reviewed_source_support"
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "support_state": support_state,
        "selected_sense_count": len(senses),
        "supported_sense_count": sum(
            1 for sense in senses if bool(sense.get("has_translation_support"))
        ),
        "unsupported_sense_count": len(unsupported),
        "active_target": str(_as_mapping(family.get("active")).get("target_lemma") or ""),
        "shadow_targets": [
            str(shadow.get("target_lemma") or "")
            for shadow in family.get("shadows", ())
            if isinstance(shadow, Mapping)
        ],
        "unsupported_senses": unsupported,
    }


def _selected_senses(family: Mapping[str, object]) -> list[dict[str, object]]:
    senses = []
    active = _as_mapping(family.get("active"))
    if active:
        senses.append(_sense_support_row(active, role="active"))
    for shadow in family.get("shadows", ()):
        if isinstance(shadow, Mapping):
            senses.append(_sense_support_row(shadow, role="shadow"))
    return senses


def _sense_support_row(sense: Mapping[str, object], *, role: str) -> dict[str, object]:
    metadata = _as_mapping(sense.get("metadata"))
    reverse_support = bool(metadata.get("reverse_support"))
    freedict_support = bool(metadata.get("freedict_support"))
    support_sources = list(metadata.get("support_sources") or ())
    return {
        "role": role,
        "sense_id": str(sense.get("sense_id") or "").strip(),
        "target_lemma": str(sense.get("target_lemma") or "").strip(),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "has_translation_support": reverse_support or freedict_support,
        "reverse_support": reverse_support,
        "freedict_support": freedict_support,
        "support_sources": support_sources,
        "translation_rank": int(metadata.get("translation_rank") or 0),
        "translation_sense_text": str(metadata.get("translation_sense_text") or "").strip(),
        "wordnet_linked": bool(metadata.get("wordnet_linked")),
        "best_wordnet_link_score": float(metadata.get("best_wordnet_link_score") or 0.0),
    }


def _supported_alternatives(
    candidate_rows: Sequence[Mapping[str, object]],
    *,
    canonical_pos: str,
    selected_target: str,
    family_selected_targets: set[str],
) -> list[dict[str, object]]:
    selected = _normalize_text(selected_target)
    pos = str(canonical_pos or "").strip()
    rows = [
        row
        for row in candidate_rows
        if str(row.get("canonical_pos") or "").strip() == pos
        and _normalize_text(row.get("translation")) != selected
        and _normalize_text(row.get("translation")) not in family_selected_targets
        and (bool(row.get("reverse_support")) or bool(row.get("freedict_support")))
        and bool(row.get("wordnet_linked"))
    ]
    rows = sorted(rows, key=translation_sort_key)
    return [_candidate_summary(row) for row in rows[:3]]


def _candidate_summary(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "translation": str(row.get("translation") or "").strip(),
        "canonical_pos": str(row.get("canonical_pos") or "").strip(),
        "rank": int(row.get("rank") or 0),
        "sense_text": str(row.get("sense_text") or "").strip(),
        "reverse_support": bool(row.get("reverse_support")),
        "freedict_support": bool(row.get("freedict_support")),
        "support_sources": list(row.get("support_sources") or ()),
        "best_wordnet_link_score": float(row.get("best_wordnet_link_score") or 0.0),
    }


def _family_table(rows: object) -> str:
    families = [row for row in _as_sequence(rows) if isinstance(row, Mapping)]
    if not families:
        return "No families audited."
    lines = [
        "| Trigger | State | Supported senses | Unsupported | Active | Shadows |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for family in families:
        shadows = ", ".join(str(item) for item in family.get("shadow_targets") or ())
        lines.append(
            f"| `{family.get('trigger', '')}` | `{family.get('support_state', '')}` | "
            f"`{family.get('supported_sense_count', 0)} / {family.get('selected_sense_count', 0)}` | "
            f"`{family.get('unsupported_sense_count', 0)}` | "
            f"`{family.get('active_target', '')}` | `{shadows}` |"
        )
    return "\n".join(lines)


def _unsupported_table(rows: object) -> str:
    entries = []
    for family in _as_sequence(rows):
        if not isinstance(family, Mapping):
            continue
        for sense in family.get("unsupported_senses", ()):
            if isinstance(sense, Mapping):
                entries.append((family, sense))
    if not entries:
        return "No unsupported selected senses."
    lines = [
        "| Trigger | Role | Target | POS | State | Same-POS supported alternatives |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for family, sense in entries:
        alternatives = ", ".join(
            f"{row.get('translation', '')} ({row.get('rank', '')})"
            for row in sense.get("same_pos_supported_alternatives") or ()
            if isinstance(row, Mapping)
        )
        lines.append(
            f"| `{family.get('trigger', '')}` | `{sense.get('role', '')}` | "
            f"`{sense.get('target_lemma', '')}` | `{sense.get('canonical_pos', '')}` | "
            f"`{sense.get('conversion_state', '')}` | `{alternatives or 'none'}` |"
        )
    return "\n".join(lines)


def _next_steps(
    *,
    unsupported_rows: Sequence[Mapping[str, object]],
    convertible_count: int,
    needs_review_count: int,
) -> list[str]:
    if not unsupported_rows:
        return ["rerun the supported admission sweep and add independent held-out validation"]
    steps = []
    if convertible_count:
        steps.append(
            "review same-POS supported alternatives and rerun admission if any target swaps are accepted"
        )
    if needs_review_count:
        steps.append(
            "add reverse/FreeDict/Wiktextract/reviewed translation support for rows without supported alternatives"
        )
    steps.extend(
        [
            "materialize only a supported selected wave after source support is complete",
            "add independent active/shadow and phrase held-out cases before quality claims",
        ]
    )
    return steps


def _count_by_key(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "").strip()
        if value:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _normalize_text(value: object) -> str:
    return str(value or "").strip().lower()


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def main() -> int:
    args = _parse_args()
    report = build_source_support_conversion_report(dataset_payload=_load_json(args.dataset_json))
    report["artifacts"] = {"dataset_json": str(args.dataset_json)}
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_source_support_conversion_markdown(report),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
