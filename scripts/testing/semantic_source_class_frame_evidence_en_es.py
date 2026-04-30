#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
EXPERIMENT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_example_frame_batches"
DEFAULT_DRAFT_ROOT = TEST_OUTPUTS_ROOT / "experiments" / "semantic_non_v10_wave_drafts"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_evidence import normalize_llm_intake_batch  # noqa: E402
from semantic_example_frame_source_adapter_support import (  # noqa: E402
    bucket_for_relation as _bucket_for_relation,
    sense_hint as _sense_hint,
    sense_id as _sense_id,
    slug as _slug,
    text_list as _text_list,
    utc_now as _utc_now,
    write_json as _write_json,
)
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_RUN_ID = "source-class-frame-non-v10-wave7-source-class-breadth-v1-latest"
DEFAULT_DATASET_JSON = (
    DEFAULT_DRAFT_ROOT
    / "en_es_source_non_v10_wave7_source_class_breadth_v1_wiktextract_supported_dataset.json"
)
DEFAULT_NORMALIZED_OUT = EXPERIMENT_ROOT / (f"en-es-{DEFAULT_RUN_ID}_normalized_evidence.json")
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_source_class_frame_evidence_wave7_source_class_breadth_v1_latest.md"
)
SOURCE_TYPE = "internal"
SOURCE_ID = "source_class_frame_evidence"
SOURCE_FAMILY = "internal_rulegen_artifact"
PROMPT_VERSION = "source-class-frame-evidence-v1"
SOURCE_VIEW = "source_backed_gloss_or_translation_sense"


@dataclass(frozen=True)
class SemanticClassDefinition:
    class_id: str
    description: str
    pattern: re.Pattern[str]
    templates: tuple[str, ...]


SEMANTIC_CLASS_DEFINITIONS = (
    SemanticClassDefinition(
        class_id="preference_interest",
        description="personal preference, liking, taste, or interest",
        pattern=re.compile(r"\b(likes|liking|preferences?)\b", re.I),
        templates=(
            "personal likes or preferences",
            "things a person likes",
            "a person's tastes or interests",
        ),
    ),
    SemanticClassDefinition(
        class_id="attraction_appeal",
        description="finding someone or something attractive or appealing",
        pattern=re.compile(r"\b(attractive|appealing)\b", re.I),
        templates=(
            "find attractive or appealing",
            "attracted to someone or something",
            "regarded as appealing",
        ),
    ),
    SemanticClassDefinition(
        class_id="disgust_repulsion",
        description="disgust, repulsion, or repulsive evaluation",
        pattern=re.compile(r"\b(disgust|repuls(?:ive|ion))\b", re.I),
        templates=(
            "causes disgust or repulsion",
            "repulsive or disgusting",
            "offensive because it causes disgust",
        ),
    ),
    SemanticClassDefinition(
        class_id="difficult_situation",
        description="difficult situation, position, dilemma, or constraint",
        pattern=re.compile(r"\b(difficult (?:situation|position)|dilemma)\b", re.I),
        templates=(
            "a difficult situation or dilemma",
            "being in a difficult fix",
            "a serious fix or predicament",
            "a constrained problem situation",
        ),
    ),
    SemanticClassDefinition(
        class_id="tight_physical_fit",
        description="physical tight fit or squeezing into a tight place",
        pattern=re.compile(r"\b(tight (?:place|space)|fit into a tight)\b", re.I),
        templates=(
            "fit into a tight place",
            "a constrained or tight position",
            "squeezed into a tight space",
        ),
    ),
    SemanticClassDefinition(
        class_id="commercial_organization",
        description="business partnership or enterprise",
        pattern=re.compile(r"\b(business partnership|business enterprise)\b", re.I),
        templates=(
            "a business partnership",
            "a commercial enterprise",
            "an organized business firm",
        ),
    ),
    SemanticClassDefinition(
        class_id="incorrectness",
        description="incorrectness, wrongness, or impropriety",
        pattern=re.compile(r"\b(incorrect|improper)\b", re.I),
        templates=(
            "incorrect or improper",
            "not correct",
            "wrong for the situation",
        ),
    ),
    SemanticClassDefinition(
        class_id="suitability",
        description="suitability, propriety, rightness, or fittingness",
        pattern=re.compile(r"\b(suitable|right|proper|fitting)\b", re.I),
        templates=(
            "suitable and proper",
            "right for the situation",
            "fitting or appropriate",
        ),
    ),
    SemanticClassDefinition(
        class_id="sports_points_scoring",
        description="points, scoring, or game scoring",
        pattern=re.compile(r"\b(points?|scoring|game)\b", re.I),
        templates=(
            "points earned in a game",
            "sports scoring points",
            "competition points",
        ),
    ),
    SemanticClassDefinition(
        class_id="sports_rule_offense",
        description="sports offense or rule violation",
        pattern=re.compile(r"\b(sports?|offen[cs]e)\b", re.I),
        templates=(
            "sports rule offense",
            "offense in sports",
            "rule violation in a sport",
        ),
    ),
    SemanticClassDefinition(
        class_id="collision_malfunction",
        description="vehicle accident, collision, violent impact, or malfunction",
        pattern=re.compile(
            r"\b(vehicle accident|computer malfunction|collid(?:e|ed|ing)|violently|"
            r"damage|destroy)\b",
            re.I,
        ),
        templates=(
            "vehicle accident or collision",
            "violent impact or crash",
            "computer malfunction or failure",
        ),
    ),
    SemanticClassDefinition(
        class_id="throwing_motion",
        description="throwing or casting by physical motion",
        pattern=re.compile(r"\b(throwing|throw)\b", re.I),
        templates=(
            "act of throwing",
            "throwing something",
            "physical throw",
        ),
    ),
    SemanticClassDefinition(
        class_id="moulded_object",
        description="moulded or molded object shape",
        pattern=re.compile(r"\b(mould|mold)\b", re.I),
        templates=(
            "object made in a mould",
            "moulded object",
            "shape made by a mould",
        ),
    ),
    SemanticClassDefinition(
        class_id="textile_fulling",
        description="making cloth denser through fulling",
        pattern=re.compile(r"\b(cloth denser|thickening cloth|cleaning and thickening)\b", re.I),
        templates=(
            "make cloth denser",
            "thicken cloth",
            "cleaning and thickening cloth",
        ),
    ),
    SemanticClassDefinition(
        class_id="stretching_lengthening",
        description="stretching or lengthening by pulling",
        pattern=re.compile(r"\b(lengthen|pulling|stretching)\b", re.I),
        templates=(
            "lengthen by pulling",
            "act of stretching",
            "make something longer by pulling",
        ),
    ),
    SemanticClassDefinition(
        class_id="dirtying_pollution",
        description="making dirty, besmirching, or polluting",
        pattern=re.compile(r"\b(make dirty|besmirch|impure|pollut(?:e|ed|ion))\b", re.I),
        templates=(
            "make dirty or impure",
            "pollute or foul something",
            "besmirch or dirty",
        ),
    ),
    SemanticClassDefinition(
        class_id="secure_fixing",
        description="fixing something securely in place",
        pattern=re.compile(r"\b(fix securely)\b", re.I),
        templates=(
            "fix securely in place",
            "attach firmly",
            "make secure",
        ),
    ),
    SemanticClassDefinition(
        class_id="quantity_dozen_count",
        description="a count equal to twelve dozen",
        pattern=re.compile(r"\b(twelve dozen)\b", re.I),
        templates=(
            "twelve dozen",
            "a gross equals twelve dozen",
            "a gross is a count for ordered goods",
            "a quantity of twelve dozen units",
        ),
    ),
    SemanticClassDefinition(
        class_id="full_capacity",
        description="fullness, maximum capacity, or containing the maximum amount",
        pattern=re.compile(
            r"\b(maximum possible amount|containing as much|as many as is possible)\b",
            re.I,
        ),
        templates=(
            "filled to maximum capacity",
            "containing the maximum possible amount",
            "full container with no more room",
        ),
    ),
    SemanticClassDefinition(
        class_id="evening_time",
        description="evening or latter part of the day",
        pattern=re.compile(
            r"\b(evening of the day|latter part of the day|nightfall|evening)\b", re.I
        ),
        templates=(
            "evening or latter part of the day",
            "time of evening before nightfall",
            "time of day called evening",
        ),
    ),
    SemanticClassDefinition(
        class_id="location_determination",
        description="determining a location",
        pattern=re.compile(r"\b(determination of location|determination of the place)\b", re.I),
        templates=(
            "determination of location",
            "location fix",
            "finding where something is",
        ),
    ),
    SemanticClassDefinition(
        class_id="repair_mending",
        description="repairing or mending something",
        pattern=re.compile(r"\b(mend|repair)\b", re.I),
        templates=(
            "mend or repair",
            "restore something broken",
            "repair by putting parts together",
        ),
    ),
    SemanticClassDefinition(
        class_id="meeting_encounter",
        description="meeting, encountering, or coming together",
        pattern=re.compile(r"\b(come face to face|encounter|come together)\b", re.I),
        templates=(
            "come together",
            "encounter someone",
            "come face to face",
        ),
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic non-authorization semantic-class evidence rows from "
            "source-backed English gloss and translation-sense text. This is a no-spend "
            "adapter and does not change runtime policy."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_JSON)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--normalized-batch-out", type=Path, default=DEFAULT_NORMALIZED_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_source_class_frame_evidence_bundle(
    *,
    dataset_payload: Mapping[str, object],
    run_id: str = DEFAULT_RUN_ID,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    intake_batch = _build_intake_batch(
        dataset_payload=dataset_payload,
        run_id=run_id,
        generated_at=generated_at,
    )
    normalized_batch = (
        normalize_llm_intake_batch(intake_batch) if intake_batch.get("items") else None
    )
    family_rows = list(
        intake_batch.get("provenance", {}).get("family_rows", ())
        if isinstance(intake_batch.get("provenance"), Mapping)
        else ()
    )
    report = _build_report(
        dataset_payload=dataset_payload,
        family_rows=family_rows,
        normalized_batch=normalized_batch,
        run_id=run_id,
        generated_at=generated_at,
    )
    return {
        "intake_batch": intake_batch,
        "normalized_batch": normalized_batch,
        "report": report,
    }


def render_source_class_frame_evidence_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Source-Class Frame Evidence Batch",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Source: `{report.get('source_id', '')}` / `{report.get('source_family', '')}`",
        f"- Matching classes: `{summary.get('matching_class_count', 0)}`",
        f"- Matching senses: `{summary.get('matching_sense_count', 0)}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Active / shadow rows: `{summary.get('active_row_count', 0)}` / `{summary.get('shadow_row_count', 0)}`",
        "",
        "## Class Coverage",
        "",
        "| Class | Matching Senses | Rows |",
        "| --- | ---: | ---: |",
    ]
    for row in report.get("class_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('semantic_class_id', '')}`",
                    str(row.get("matching_sense_count", 0)),
                    str(row.get("row_count", 0)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Source Trigger Audit",
            "",
            "| Family | Sense | Relation | Class | Target In Source | Source Text |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        family_id = str(row.get("family_id") or "").strip()
        for sense_row in row.get("sense_rows", ()):
            if not isinstance(sense_row, Mapping):
                continue
            class_ids = ", ".join(
                f"`{class_id}`" for class_id in _text_list(sense_row.get("semantic_class_ids"))
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{family_id}`",
                        f"`{sense_row.get('sense_id', '')}`",
                        f"`{sense_row.get('relation_type', '')}`",
                        class_ids or "`none`",
                        f"`{str(bool(sense_row.get('target_lemma_in_source_match_text'))).lower()}`",
                        _markdown_cell(_snippet(sense_row.get("source_match_text"))),
                    ]
                )
                + " |"
            )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    return "\n".join(lines) + "\n"


def _build_intake_batch(
    *,
    dataset_payload: Mapping[str, object],
    run_id: str,
    generated_at: str,
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_items, sense_rows = _family_items(family)
        items.extend(family_items)
        family_rows.append(_family_summary_row(family, family_items, sense_rows))
    return {
        "schema_version": 1,
        "batch_id": f"en-es:source-class-frame-evidence:{run_id}",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "source_type": SOURCE_TYPE,
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "roles": ["cue_generation", "discrimination"],
        "generated_at": generated_at,
        "ingested_at": generated_at,
        "review_state": "unreviewed",
        "model_id": "not_applicable",
        "prompt_version": PROMPT_VERSION,
        "provenance": {
            "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
            "semantic_class_ids": [
                definition.class_id for definition in SEMANTIC_CLASS_DEFINITIONS
            ],
            "source_note": (
                "Deterministic English frame rows emitted only when source-backed English "
                "gloss or translation-sense text matches a non-authorization class. Spanish "
                "target lemmas are excluded from evidence_text."
            ),
            "family_rows": family_rows,
        },
        "items": items,
    }


def _family_items(
    family: Mapping[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    active = _as_mapping(family.get("active"))
    senses = [
        ("anchor_cue", active),
        *[
            ("shadow_candidate", shadow)
            for shadow in family.get("shadows", ())
            if isinstance(shadow, Mapping)
        ],
    ]
    items: list[dict[str, object]] = []
    sense_rows: list[dict[str, object]] = []
    for relation_type, sense in senses:
        match_text = _source_match_text(sense)
        class_matches = _matching_classes(match_text)
        sense_rows.append(
            _sense_row(
                sense,
                relation_type=relation_type,
                semantic_class_ids=[definition.class_id for definition in class_matches],
                source_match_text=match_text,
            )
        )
        for definition in class_matches:
            for index, evidence_text in enumerate(definition.templates, start=1):
                items.append(
                    _item(
                        family=family,
                        active_sense=active,
                        candidate_sense=sense,
                        relation_type=relation_type,
                        definition=definition,
                        evidence_text=evidence_text,
                        index=index,
                        match_text=match_text,
                    )
                )
    return items, sense_rows


def _item(
    *,
    family: Mapping[str, object],
    active_sense: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    relation_type: str,
    definition: SemanticClassDefinition,
    evidence_text: str,
    index: int,
    match_text: str,
) -> dict[str, object]:
    family_id = str(family.get("family_id") or "").strip()
    candidate_id = _sense_id(candidate_sense)
    example_bucket = _bucket_for_relation(relation_type)
    metadata = _as_mapping(candidate_sense.get("metadata"))
    return {
        "row_id": (
            f"{_slug(family_id)}:{example_bucket}-{_slug(candidate_id)}-"
            f"{_slug(definition.class_id)}-frame-{index}"
        ),
        "relation_type": relation_type,
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active_sense.get("target_lemma") or "").strip(),
        "candidate_target": str(candidate_sense.get("target_lemma") or "").strip(),
        "active_sense_hint": _sense_hint(active_sense, note="fixed_shadow_active"),
        "candidate_sense_hint": _sense_hint(
            candidate_sense,
            note="source_semantic_class_candidate",
            metadata={
                "semantic_class_id": definition.class_id,
                "source_view": SOURCE_VIEW,
                "support_sources": _text_list(metadata.get("support_sources")),
            },
        ),
        "candidate_pos": str(candidate_sense.get("canonical_pos") or "").strip(),
        "evidence_text": evidence_text,
        "example_count": 1,
        "review_state": "unreviewed",
        "promotion_state": "proposed",
        "runtime_publishable": False,
        "roles": ["cue_generation", "discrimination"]
        if relation_type == "anchor_cue"
        else ["discrimination"],
        "metadata": {
            "family_id": family_id,
            "queue_role": "target",
            "active_sense_id": _sense_id(active_sense),
            "candidate_sense_id": candidate_id,
            "example_bucket": example_bucket,
            "semantic_class_id": definition.class_id,
            "semantic_class_description": definition.description,
            "source_view": "source_class_frame_template",
            "source_match_text": match_text,
            "template_index": int(index),
            "template_count": len(definition.templates),
        },
    }


def _source_match_text(sense: Mapping[str, object]) -> str:
    evidence_views = _as_mapping(sense.get("evidence_views"))
    metadata = _as_mapping(sense.get("metadata"))
    parts = [
        evidence_views.get("sense_label"),
        evidence_views.get("gloss_text"),
        evidence_views.get("sense_gloss_bundle"),
        metadata.get("translation_sense_text"),
    ]
    for match in metadata.get("wiktextract_translation_support_matches") or ():
        if isinstance(match, Mapping):
            parts.append(match.get("translation_sense"))
    return " | ".join(str(part or "").strip() for part in parts if str(part or "").strip())


def _matching_classes(source_text: str) -> list[SemanticClassDefinition]:
    return [
        definition
        for definition in SEMANTIC_CLASS_DEFINITIONS
        if definition.pattern.search(source_text)
    ]


def _sense_row(
    sense: Mapping[str, object],
    *,
    relation_type: str,
    semantic_class_ids: Sequence[str],
    source_match_text: str,
) -> dict[str, object]:
    target_lemma = str(sense.get("target_lemma") or "").strip()
    metadata = _as_mapping(sense.get("metadata"))
    return {
        "sense_id": _sense_id(sense),
        "relation_type": relation_type,
        "matched": bool(semantic_class_ids),
        "semantic_class_ids": list(semantic_class_ids),
        "canonical_pos": str(sense.get("canonical_pos") or "").strip(),
        "target_lemma": target_lemma,
        "support_sources": _text_list(metadata.get("support_sources")),
        "source_match_text": source_match_text,
        "target_lemma_in_source_match_text": bool(
            target_lemma and target_lemma.lower() in source_match_text.lower()
        ),
    }


def _family_summary_row(
    family: Mapping[str, object],
    items: Sequence[Mapping[str, object]],
    sense_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "selected_sense_count": len(sense_rows),
        "matching_sense_count": sum(1 for row in sense_rows if row.get("matched")),
        "row_count": len(items),
        "active_row_count": sum(1 for item in items if item.get("relation_type") == "anchor_cue"),
        "shadow_row_count": sum(
            1 for item in items if item.get("relation_type") == "shadow_candidate"
        ),
        "sense_rows": [dict(row) for row in sense_rows],
    }


def _build_report(
    *,
    dataset_payload: Mapping[str, object],
    family_rows: Sequence[Mapping[str, object]],
    normalized_batch: Mapping[str, object] | None,
    run_id: str,
    generated_at: str,
) -> dict[str, object]:
    rows = list(normalized_batch.get("rows", ())) if isinstance(normalized_batch, Mapping) else []
    class_rows = _class_rows(rows=rows, family_rows=family_rows)
    target_family_count = sum(1 for row in family_rows if row.get("row_count"))
    row_count = len(rows)
    return {
        "schema_version": 1,
        "status": "ok" if row_count else "review",
        "decision": "source_class_frame_rows_ready" if row_count else "no_rows",
        "generated_at": generated_at,
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "run_id": run_id,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip()
        if isinstance(normalized_batch, Mapping)
        else "",
        "source_id": SOURCE_ID,
        "source_family": SOURCE_FAMILY,
        "prompt_version": PROMPT_VERSION,
        "summary": {
            "family_count": len(family_rows),
            "target_family_count": target_family_count,
            "selected_sense_count": sum(
                int(row.get("selected_sense_count") or 0) for row in family_rows
            ),
            "matching_sense_count": sum(
                int(row.get("matching_sense_count") or 0) for row in family_rows
            ),
            "matching_class_count": len(class_rows),
            "row_count": row_count,
            "active_row_count": sum(1 for row in rows if row.get("relation_type") == "anchor_cue"),
            "shadow_row_count": sum(
                1 for row in rows if row.get("relation_type") == "shadow_candidate"
            ),
        },
        "class_rows": class_rows,
        "family_rows": [dict(row) for row in family_rows if int(row.get("row_count") or 0) > 0],
        "limitations": [
            "deterministic_semantic_class_frame_not_runtime_policy",
            "non_authorization_class_templates_require_heldout_validation",
            "does_not_use_heldout_sentence_text",
        ],
    }


def _class_rows(
    *,
    rows: Sequence[Mapping[str, object]],
    family_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    class_ids = sorted(
        {
            str(_as_mapping(row.get("metadata")).get("semantic_class_id") or "").strip()
            for row in rows
            if str(_as_mapping(row.get("metadata")).get("semantic_class_id") or "").strip()
        }
    )
    output: list[dict[str, object]] = []
    for class_id in class_ids:
        matching_sense_count = 0
        for family_row in family_rows:
            if not isinstance(family_row, Mapping):
                continue
            for sense_row in family_row.get("sense_rows", ()):
                if isinstance(sense_row, Mapping) and class_id in _text_list(
                    sense_row.get("semantic_class_ids")
                ):
                    matching_sense_count += 1
        output.append(
            {
                "semantic_class_id": class_id,
                "matching_sense_count": matching_sense_count,
                "row_count": sum(
                    1
                    for row in rows
                    if _as_mapping(row.get("metadata")).get("semantic_class_id") == class_id
                ),
            }
        )
    return output


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _snippet(value: object, *, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|")


def main() -> int:
    args = _parse_args()
    dataset = load_sentence_veto_dataset(args.dataset)
    bundle = build_source_class_frame_evidence_bundle(
        dataset_payload=dataset,
        run_id=str(args.run_id or "").strip() or DEFAULT_RUN_ID,
    )
    normalized = bundle["normalized_batch"]
    if isinstance(normalized, Mapping):
        _write_json(args.normalized_batch_out, normalized)
        print(f"Wrote normalized batch to {args.normalized_batch_out}")
    else:
        print("No normalized batch rows produced.")
    _write_json(args.json_out, bundle["report"])
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_source_class_frame_evidence_markdown(bundle["report"]),
        encoding="utf-8",
    )
    print(f"Wrote JSON report to {args.json_out}")
    print(f"Wrote Markdown report to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
