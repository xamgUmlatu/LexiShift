#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_prompt_reporting import render_prompt_smoke_markdown  # noqa: E402
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_QUEUE_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing"
    / "semantic_prompt_bakeoff_queue_en_es.json"
)
DEFAULT_SLOT_MANIFEST_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing"
    / "semantic_prompt_slot_manifest.json"
)
DEFAULT_FAMILY_INVENTORY_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing"
    / "semantic_family_inventory_en_es_v10.json"
)
DEFAULT_PROMPT_SPEC_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing"
    / "semantic_prompt_spec_en_es_v10.json"
)
DEFAULT_DATASET_PATH = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "semantic_routing_cases"
    / "en_es_sentence_veto_v10.json"
)
DEFAULT_JSON_OUT = PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_smoke_latest.json"
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_llm_prompt_smoke_latest.md"
)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render the frozen en-es prompt-bakeoff smoke bundle: active prompt slots, "
            "model defaults, and per-family prompt previews."
        )
    )
    parser.add_argument("--queue-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--slot-manifest-json", type=Path, default=DEFAULT_SLOT_MANIFEST_JSON)
    parser.add_argument("--family-inventory-json", type=Path, default=DEFAULT_FAMILY_INVENTORY_JSON)
    parser.add_argument("--prompt-spec-json", type=Path, default=DEFAULT_PROMPT_SPEC_JSON)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--stage",
        choices=("proxy", "target"),
        default="proxy",
        help="Prompt-bakeoff stage to render.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def build_prompt_smoke_report(
    *,
    queue_payload: Mapping[str, object],
    slot_manifest_payload: Mapping[str, object],
    family_inventory_payload: Mapping[str, object],
    prompt_spec_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    stage: str,
    generated_at: str | None = None,
) -> dict[str, object]:
    resolved_stage = str(stage or "").strip().lower() or "proxy"
    if resolved_stage not in {"proxy", "target"}:
        raise ValueError("stage must be `proxy` or `target`.")
    if generated_at is None:
        generated_at = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )

    queue_families = _mapping_rows(queue_payload.get("families"), "queue families")
    slot_rows = _mapping_rows(slot_manifest_payload.get("slots"), "slot manifest rows")
    inventory_rows = _mapping_rows(
        family_inventory_payload.get("families"), "family inventory rows"
    )
    dataset_families = _mapping_rows(dataset_payload.get("families"), "dataset families")
    spec_slots = _mapping_rows(prompt_spec_payload.get("slots"), "prompt spec slots")

    pair = str(prompt_spec_payload.get("pair") or "").strip() or "en-es"
    stage_defaults = prompt_spec_payload.get("stage_defaults")
    if not isinstance(stage_defaults, Mapping):
        raise ValueError("Prompt spec is missing `stage_defaults`.")
    stage_config = stage_defaults.get(resolved_stage)
    if not isinstance(stage_config, Mapping):
        raise ValueError(f"Prompt spec is missing stage defaults for {resolved_stage!r}.")

    dataset_lookup = {
        str(row.get("family_id") or "").strip(): row
        for row in dataset_families
        if str(row.get("family_id") or "").strip()
    }
    queue_lookup = {
        str(row.get("family_id") or "").strip(): row
        for row in queue_families
        if str(row.get("family_id") or "").strip()
    }
    inventory_lookup = {
        str(row.get("family_id") or "").strip(): row
        for row in inventory_rows
        if str(row.get("family_id") or "").strip()
    }
    spec_slot_lookup = {
        str(row.get("prompt_slot") or "").strip(): row
        for row in spec_slots
        if str(row.get("prompt_slot") or "").strip()
    }

    active_manifest_rows = [
        row for row in slot_rows if str(row.get("status") or "").strip().lower() == "active"
    ]
    request_rows: list[dict[str, object]] = []
    resolved_slot_rows: list[dict[str, object]] = []
    for manifest_row in active_manifest_rows:
        prompt_slot = str(manifest_row.get("prompt_slot") or "").strip()
        spec_row = spec_slot_lookup.get(prompt_slot)
        if spec_row is None:
            raise ValueError(f"Prompt spec is missing slot {prompt_slot!r}.")
        target_family_ids = _string_list(manifest_row.get("target_family_ids"))
        slot_request_count = 0
        for family_id in target_family_ids:
            queue_row = queue_lookup.get(family_id)
            dataset_row = dataset_lookup.get(family_id)
            inventory_row = inventory_lookup.get(family_id)
            if queue_row is None or dataset_row is None:
                raise ValueError(
                    f"Frozen bakeoff family {family_id!r} is missing queue or dataset."
                )
            for shadow in _mapping_rows(dataset_row.get("shadows"), f"{family_id} shadows"):
                request_rows.append(
                    build_prompt_request(
                        pair=pair,
                        stage=resolved_stage,
                        stage_config=stage_config,
                        manifest_row=manifest_row,
                        spec_row=spec_row,
                        queue_row=queue_row,
                        inventory_row=inventory_row,
                        dataset_family=dataset_row,
                        shadow_row=shadow,
                    )
                )
                slot_request_count += 1
        resolved_slot_rows.append(
            {
                "prompt_slot": prompt_slot,
                "status": str(manifest_row.get("status") or "").strip(),
                "target_family_count": len(target_family_ids),
                "request_count": slot_request_count,
                "notes": _string_list(manifest_row.get("notes")),
            }
        )

    summary = {
        "active_slot_count": len(resolved_slot_rows),
        "request_count": len(request_rows),
        "target_family_count": len(
            {
                str(row.get("family_id") or "").strip()
                for row in request_rows
                if str(row.get("family_id") or "").strip()
            }
        ),
        "negative_control_count": len(
            _string_list(queue_payload.get("default_negative_control_family_ids"))
        ),
    }
    sample_requests = _pick_slot_samples(request_rows)
    report = {
        "schema_version": 1,
        "status": "ok",
        "pair": pair,
        "generated_at": generated_at,
        "queue_id": str(queue_payload.get("queue_id") or "").strip(),
        "prompt_spec_id": str(prompt_spec_payload.get("spec_id") or "").strip(),
        "prompt_version": str(prompt_spec_payload.get("prompt_version") or "").strip(),
        "stage": resolved_stage,
        "selected_model_id": str(stage_config.get("model_id") or "").strip(),
        "selected_temperature": float(stage_config.get("temperature") or 0.0),
        "summary": summary,
        "slot_rows": resolved_slot_rows,
        "sample_requests": sample_requests,
        "request_rows": request_rows,
    }
    return report


def build_prompt_request(
    *,
    pair: str,
    stage: str,
    stage_config: Mapping[str, object],
    manifest_row: Mapping[str, object],
    spec_row: Mapping[str, object],
    queue_row: Mapping[str, object],
    inventory_row: Mapping[str, object] | None,
    dataset_family: Mapping[str, object],
    shadow_row: Mapping[str, object],
) -> dict[str, object]:
    prompt_slot = str(manifest_row.get("prompt_slot") or "").strip()
    trigger = str(dataset_family.get("trigger") or "").strip()
    active = dataset_family.get("active")
    if not isinstance(active, Mapping):
        raise ValueError("Dataset family is missing `active`.")
    active_target = str(active.get("target_lemma") or "").strip()
    candidate_target = str(shadow_row.get("target_lemma") or "").strip()
    family_id = str(dataset_family.get("family_id") or "").strip()
    input_ref = _build_input_ref(
        pair=pair,
        stage=stage,
        prompt_slot=prompt_slot,
        family_id=family_id,
        candidate_target=candidate_target,
    )
    row_id = f"{input_ref}:row"

    family_notes = _build_family_notes(queue_row=queue_row, inventory_row=inventory_row)
    family_archetype = _resolve_family_archetype(manifest_row=manifest_row)
    render_context = {
        "row_id": row_id,
        "trigger": trigger,
        "active_target": active_target,
        "candidate_target": candidate_target,
        "candidate_pos": str(shadow_row.get("canonical_pos") or "").strip(),
        "prompt_slot": prompt_slot,
        "input_ref": input_ref,
        "family_id": family_id,
        "active_sense_id": str(active.get("sense_id") or "").strip(),
        "candidate_sense_id": str(shadow_row.get("sense_id") or "").strip(),
        "stage": stage,
        "family_archetype": family_archetype,
        "active_pos": str(active.get("canonical_pos") or "").strip(),
        "active_sense_label": _extract_evidence_text(active, "sense_label"),
        "active_gloss_text": _extract_evidence_text(active, "gloss_text"),
        "candidate_sense_label": _extract_evidence_text(shadow_row, "sense_label"),
        "candidate_gloss_text": _extract_evidence_text(shadow_row, "gloss_text"),
        "family_notes": family_notes,
    }
    system_prompt = str(spec_row.get("system_prompt") or "").strip()
    user_prompt_template = str(spec_row.get("user_prompt_template") or "").strip()
    user_prompt = user_prompt_template.format(**render_context)

    expected_row_preview = {
        "row_id": row_id,
        "relation_type": str(spec_row.get("relation_type") or "").strip(),
        "trigger": trigger,
        "active_target": active_target,
        "candidate_target": candidate_target,
        "candidate_pos": str(shadow_row.get("canonical_pos") or "").strip(),
        "evidence_text": "<model-written cue text>",
        "prompt_slot": prompt_slot,
        "input_ref": input_ref,
        "metadata": {
            "family_id": family_id,
            "active_sense_id": str(active.get("sense_id") or "").strip(),
            "candidate_sense_id": str(shadow_row.get("sense_id") or "").strip(),
            "stage": stage,
            "family_archetype": family_archetype,
        },
    }

    return {
        "request_id": input_ref,
        "prompt_slot": prompt_slot,
        "family_id": family_id,
        "trigger": trigger,
        "active_target": active_target,
        "candidate_target": candidate_target,
        "candidate_pos": str(shadow_row.get("canonical_pos") or "").strip(),
        "model_id": str(stage_config.get("model_id") or "").strip(),
        "temperature": float(stage_config.get("temperature") or 0.0),
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "expected_row_preview": expected_row_preview,
    }


def _mapping_rows(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{label} must be an array of objects.")
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _extract_evidence_text(sense_row: Mapping[str, object], key: str) -> str:
    evidence_views = sense_row.get("evidence_views")
    if isinstance(evidence_views, Mapping):
        text = str(evidence_views.get(key) or "").strip()
        if text:
            return text
    return ""


def _build_family_notes(
    *,
    queue_row: Mapping[str, object],
    inventory_row: Mapping[str, object] | None,
) -> str:
    notes = [
        *_string_list(queue_row.get("notes")),
        *(
            _string_list(inventory_row.get("bucket_evidence"))
            if isinstance(inventory_row, Mapping)
            else []
        ),
    ]
    deduped: list[str] = []
    for note in notes:
        if note and note not in deduped:
            deduped.append(note)
    return " | ".join(deduped[:3]) or "No extra family notes."


def _resolve_family_archetype(*, manifest_row: Mapping[str, object]) -> str:
    target_archetypes = _string_list(manifest_row.get("target_archetypes"))
    if target_archetypes:
        return target_archetypes[0]
    return "unspecified"


def _build_input_ref(
    *,
    pair: str,
    stage: str,
    prompt_slot: str,
    family_id: str,
    candidate_target: str,
) -> str:
    pair_slug = _slug(pair)
    slot_slug = _slug(prompt_slot)
    family_slug = _slug(family_id.split(":")[-2] if ":" in family_id else family_id)
    candidate_slug = _slug(candidate_target)
    return f"{pair_slug}:{stage}:{slot_slug}:{family_slug}:{candidate_slug}"


def _slug(value: str) -> str:
    lowered = str(value or "").strip().lower()
    lowered = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode("ascii")
    normalized = _SLUG_RE.sub("-", lowered).strip("-")
    return normalized or "value"


def _pick_slot_samples(request_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    picked: list[dict[str, object]] = []
    seen_slots: set[str] = set()
    for row in request_rows:
        prompt_slot = str(row.get("prompt_slot") or "").strip()
        if not prompt_slot or prompt_slot in seen_slots:
            continue
        picked.append(dict(row))
        seen_slots.add(prompt_slot)
    return picked


def main() -> int:
    args = _parse_args()
    report = build_prompt_smoke_report(
        queue_payload=_load_json(args.queue_json),
        slot_manifest_payload=_load_json(args.slot_manifest_json),
        family_inventory_payload=_load_json(args.family_inventory_json),
        prompt_spec_payload=_load_json(args.prompt_spec_json),
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        stage=args.stage,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_prompt_smoke_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
