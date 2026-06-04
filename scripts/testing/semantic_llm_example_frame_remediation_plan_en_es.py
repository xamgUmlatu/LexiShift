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
SCRIPT_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
for candidate in (str(CORE_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_example_frame_generation_plan_en_es import (  # noqa: E402
    DEFAULT_CHARS_PER_TOKEN,
    DEFAULT_EXPECTED_OUTPUT_TOKENS,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL_ID,
    DEFAULT_TEMPERATURE,
    _active_sense,
    _attach_token_estimates,
    _build_summary,
    _dataset_family_lookup,
    _queue_family_lookup,
    _request_row,
    _sense_id,
    _shadow_senses,
)
from semantic_llm_prompt_downstream_en_es import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_QUEUE_JSON,
    _load_json,
)
from semantic_routing_sentence_veto_helpers import _normalize_string_list  # noqa: E402
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_PROTOTYPE_JSON = (
    TEST_OUTPUTS_ROOT
    / "semantic_llm_example_frame_generation_prototype_admission_probe_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_remediation_plan_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_remediation_plan_latest.md"
PROMPT_VERSION = "example-frame-residual-remediation-v1"
SOURCE_ID = "llm_example_frame_residual_remediation"
DEFAULT_CONFIG_ID = "auto_best_remediation_guard"
AUTO_CONFIG_IDS = frozenset({"", "auto", "auto_best", DEFAULT_CONFIG_ID})
PHRASE_PROTOTYPE_CONFIG_ID = "prototype_reviewed_examples_phrase_prototype_guard"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a no-spend LLM remediation plan from residual prototype-admission failures."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--required-family-json", type=Path, default=DEFAULT_QUEUE_JSON)
    parser.add_argument("--prototype-json", type=Path, default=DEFAULT_PROTOTYPE_JSON)
    parser.add_argument("--config-id", default=DEFAULT_CONFIG_ID)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--chars-per-token", type=float, default=DEFAULT_CHARS_PER_TOKEN)
    parser.add_argument(
        "--expected-output-tokens",
        type=int,
        default=DEFAULT_EXPECTED_OUTPUT_TOKENS,
    )
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_example_frame_remediation_plan(
    *,
    dataset_payload: Mapping[str, object],
    required_family_payload: Mapping[str, object],
    prototype_payload: Mapping[str, object],
    config_id: str = DEFAULT_CONFIG_ID,
    model_id: str = DEFAULT_MODEL_ID,
    temperature: float = DEFAULT_TEMPERATURE,
    chars_per_token: float = DEFAULT_CHARS_PER_TOKEN,
    expected_output_tokens: int = DEFAULT_EXPECTED_OUTPUT_TOKENS,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be > 0")

    dataset_lookup = _dataset_family_lookup(dataset_payload)
    queue_lookup = _queue_family_lookup(required_family_payload)
    config = _prototype_config(prototype_payload, config_id=config_id)
    residuals = _build_residual_groups(config)
    request_rows = _build_request_rows(
        residuals=residuals,
        dataset_lookup=dataset_lookup,
        queue_lookup=queue_lookup,
        model_id=str(model_id or "").strip() or DEFAULT_MODEL_ID,
        temperature=float(temperature),
    )
    _attach_token_estimates(
        request_rows,
        chars_per_token=chars_per_token,
        expected_output_tokens=expected_output_tokens,
        max_output_tokens=max_output_tokens,
    )
    summary = _build_summary(
        request_rows,
        expected_output_tokens=expected_output_tokens,
        max_output_tokens=max_output_tokens,
    )
    summary["residual_false_abstain_case_count"] = sum(
        len(row["case_ids"]) for row in residuals["active_examples"].values()
    )
    summary["residual_harmful_replace_case_count"] = sum(
        len(row["case_ids"]) for row in residuals["shadow_examples"].values()
    )
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ready" if request_rows else "no_residual_failures",
        "pair": str(dataset_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(dataset_payload.get("dataset_id") or "").strip(),
        "required_family_source": str(required_family_payload.get("queue_id") or "").strip()
        or str(required_family_payload.get("inventory_id") or "").strip()
        or str(required_family_payload.get("dataset_id") or "").strip(),
        "prototype_config_id": str(config.get("config_id") or "").strip(),
        "source_id": SOURCE_ID,
        "prompt_version": PROMPT_VERSION,
        "selected_model_id": str(model_id or "").strip() or DEFAULT_MODEL_ID,
        "selected_temperature": float(temperature),
        "decision_contract": "binary_replace_or_abstain",
        "review_leakage_policy": "do_not_include_sentence_veto_case_sentences_in_prompts",
        "remediation_policy": (
            "active examples for false abstains; shadow examples for harmful replaces; "
            "phrase-control rows stay containment-only"
        ),
        "summary": summary,
        "residual_groups": residuals,
        "request_rows": request_rows,
        "recommendation": _build_recommendation(summary),
    }


def _build_request_rows(
    *,
    residuals: Mapping[str, Mapping[str, Mapping[str, object]]],
    dataset_lookup: Mapping[str, Mapping[str, object]],
    queue_lookup: Mapping[str, Mapping[str, object]],
    model_id: str,
    temperature: float,
) -> list[dict[str, object]]:
    request_rows: list[dict[str, object]] = []
    for family_id, group in sorted(residuals["active_examples"].items()):
        family = _required_family(dataset_lookup, family_id)
        request_rows.append(
            _remediation_request_row(
                family=family,
                queue_family=queue_lookup.get(family_id, {}),
                candidate_sense=_active_sense(family),
                generation_target="active_example",
                relation_type="anchor_cue",
                group=group,
                model_id=model_id,
                temperature=temperature,
            )
        )
    for key, group in sorted(residuals["shadow_examples"].items()):
        family_id = str(group.get("family_id") or "").strip()
        candidate_sense_id = str(group.get("candidate_sense_id") or "").strip()
        family = _required_family(dataset_lookup, family_id)
        shadow = _shadow_by_id(family, candidate_sense_id)
        request_rows.append(
            _remediation_request_row(
                family=family,
                queue_family=queue_lookup.get(family_id, {}),
                candidate_sense=shadow,
                generation_target="shadow_example",
                relation_type="shadow_candidate",
                group=group,
                model_id=model_id,
                temperature=temperature,
            )
        )
    return request_rows


def _remediation_request_row(
    *,
    family: Mapping[str, object],
    queue_family: Mapping[str, object],
    candidate_sense: Mapping[str, object],
    generation_target: str,
    relation_type: str,
    group: Mapping[str, object],
    model_id: str,
    temperature: float,
) -> dict[str, object]:
    row = _request_row(
        family=family,
        queue_family=queue_family,
        candidate_sense=candidate_sense,
        generation_target=generation_target,
        relation_type=relation_type,
        model_id=model_id,
        temperature=temperature,
    )
    request_id = str(row.get("request_id") or "").replace(
        "example-frame-missing",
        "example-frame-remediation",
    )
    row["request_id"] = request_id
    row["system_prompt"] = str(row.get("system_prompt") or "").replace(
        "one LexiShift semantic example frame",
        "one LexiShift residual-remediation semantic example frame",
    )
    row["user_prompt"] = "\n".join(
        [
            str(row.get("user_prompt") or "").strip(),
            "",
            "Residual remediation focus:",
            f"- failure mode: {str(group.get('failure_mode') or '').strip()}",
            f"- residual case count: {len(_case_ids(group))}",
            f"- case ids: {', '.join(_case_ids(group))}",
            "- do not copy benchmark sentences",
            "- use the active sense and competing-sense evidence as the only content anchors",
            "- residual slice tags are retained in metadata only; do not infer or echo their "
            "surface setting",
            "- prefer distinctive sense cues over generic topical settings",
        ]
    )
    row["prompt_slot"] = f"remediation_{generation_target}"
    row["remediation_context"] = {
        "failure_mode": str(group.get("failure_mode") or "").strip(),
        "case_ids": _case_ids(group),
        "slice_tags": _slice_tags(group),
    }
    preview = row.get("expected_row_preview")
    if isinstance(preview, dict):
        preview["row_id"] = _remediation_row_id(
            str(preview.get("row_id") or ""),
            generation_target=generation_target,
            case_ids=_case_ids(group),
        )
        preview["input_ref"] = request_id
        preview["prompt_slot"] = str(row["prompt_slot"])
        metadata = preview.get("metadata")
        if isinstance(metadata, dict):
            metadata["source_gap"] = str(row["prompt_slot"])
            metadata["failure_mode"] = str(group.get("failure_mode") or "").strip()
            metadata["failure_case_ids"] = _case_ids(group)
            metadata["failure_slice_tags"] = _slice_tags(group)
    return row


def _remediation_row_id(
    row_id: str,
    *,
    generation_target: str,
    case_ids: Sequence[str],
) -> str:
    normalized = str(row_id or "").strip()
    target_slug = _slug_component(generation_target.replace("_example", ""))
    case_slug = _case_group_slug(case_ids)
    remediation_slot = (
        f"remediation-{target_slug}-{case_slug}" if case_slug else (f"remediation-{target_slug}")
    )
    if ":missing:v1" in normalized:
        return normalized.replace(":missing:v1", f":{remediation_slot}:v1")
    if "missing-v1" in normalized:
        return normalized.replace("missing-v1", f"{remediation_slot}-v1")
    return f"{normalized}:{remediation_slot}" if normalized else remediation_slot


def _build_residual_groups(config: Mapping[str, object]) -> dict[str, dict[str, dict[str, object]]]:
    active_groups: dict[str, dict[str, object]] = {}
    shadow_groups: dict[str, dict[str, object]] = {}
    for row in _row_results(config):
        case_id = str(row.get("case_id") or "").strip()
        family_id = str(row.get("family_id") or "").strip()
        if not case_id or not family_id:
            continue
        gold_decision = str(row.get("gold_decision") or "").strip()
        predicted_decision = str(row.get("predicted_decision") or "").strip()
        if gold_decision == "replace" and predicted_decision != "replace":
            group = active_groups.setdefault(
                family_id,
                {
                    "family_id": family_id,
                    "failure_mode": "false_abstain_active_example_gap",
                    "case_ids": [],
                    "slice_tags": [],
                },
            )
            _append_case(group, row)
        elif gold_decision == "abstain" and predicted_decision == "replace":
            candidate_sense_id = str(row.get("gold_winner") or "").strip()
            if not candidate_sense_id:
                continue
            key = f"{family_id}|{candidate_sense_id}"
            group = shadow_groups.setdefault(
                key,
                {
                    "family_id": family_id,
                    "candidate_sense_id": candidate_sense_id,
                    "failure_mode": "harmful_replace_shadow_example_gap",
                    "case_ids": [],
                    "slice_tags": [],
                },
            )
            _append_case(group, row)
    return {
        "active_examples": active_groups,
        "shadow_examples": shadow_groups,
    }


def render_example_frame_remediation_plan_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es LLM Example-Frame Remediation Plan",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Required families: `{report.get('required_family_source', '')}`",
        f"- Prototype config: `{report.get('prototype_config_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        f"- Decision contract: `{report.get('decision_contract', '')}`",
        f"- Review leakage policy: `{report.get('review_leakage_policy', '')}`",
        "",
        "## Summary",
        "",
        f"- Requests: `{summary.get('request_count', 0)}`",
        f"- Families: `{summary.get('family_count', 0)}`",
        f"- False-abstain cases: `{summary.get('residual_false_abstain_case_count', 0)}`",
        f"- Harmful-replace cases: `{summary.get('residual_harmful_replace_case_count', 0)}`",
        f"- Estimated input tokens: `{summary.get('estimated_input_tokens', 0)}`",
        f"- Expected output tokens: `{summary.get('expected_output_tokens', 0)}`",
        f"- Max output tokens: `{summary.get('max_output_tokens', 0)}`",
        f"- Requests by target: `{json.dumps(summary.get('requests_by_generation_target', {}), sort_keys=True)}`",
        "",
        "## Request Rows",
        "",
        "| Request | Target | Family | Candidate | Failure Mode | Cases | Input Tokens |",
        "| --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in report.get("request_rows", ()):
        if not isinstance(row, Mapping):
            continue
        context = (
            row.get("remediation_context")
            if isinstance(row.get("remediation_context"), Mapping)
            else {}
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('request_id', '')}`",
                    f"`{row.get('prompt_slot', '')}`",
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('candidate_target', '')}`",
                    f"`{context.get('failure_mode', '')}`",
                    str(len(_case_ids(context))),
                    str(row.get("estimated_input_tokens", 0)),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _append_case(group: dict[str, object], row: Mapping[str, object]) -> None:
    case_ids = group["case_ids"]
    if isinstance(case_ids, list):
        case_id = str(row.get("case_id") or "").strip()
        if case_id and case_id not in case_ids:
            case_ids.append(case_id)
    tags = group["slice_tags"]
    if isinstance(tags, list):
        for tag in _normalize_string_list(row.get("slice_tags")):
            if tag not in tags:
                tags.append(tag)


def _prototype_config(payload: Mapping[str, object], *, config_id: str) -> Mapping[str, object]:
    rows = payload.get("configurations")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("prototype payload must contain a `configurations` array.")
    config_rows = [row for row in rows if isinstance(row, Mapping)]
    target = str(config_id or "").strip()
    if target in AUTO_CONFIG_IDS:
        return _best_remediation_config(config_rows)
    for row in rows:
        if isinstance(row, Mapping) and str(row.get("config_id") or "").strip() == target:
            return row
    raise ValueError(f"Prototype configuration {target!r} was not found.")


def _best_remediation_config(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    eligible_rows = [
        row
        for row in rows
        if str(row.get("config_id") or "").strip() != PHRASE_PROTOTYPE_CONFIG_ID
        and not bool(row.get("use_phrase_prototypes"))
    ]
    if not eligible_rows:
        raise ValueError("prototype payload did not contain a remediation-eligible configuration.")
    return max(eligible_rows, key=_remediation_config_sort_key)


def _remediation_config_sort_key(row: Mapping[str, object]) -> tuple[float, float, int, int, int]:
    summary = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
    return (
        float(summary.get("decision_accuracy") or 0.0),
        float(summary.get("replace_recall") or 0.0),
        -int(summary.get("harmful_replace_count") or 0),
        -int(summary.get("false_abstain_count") or 0),
        _remediation_config_preference(row),
    )


def _remediation_config_preference(row: Mapping[str, object]) -> int:
    config_id = str(row.get("config_id") or "").strip()
    if config_id == "prototype_reviewed_examples_surface_pos_rescue_guard":
        return 4
    if config_id == "prototype_reviewed_examples_phrase_containment_guard":
        return 3
    if config_id == "prototype_reviewed_examples_active_guard":
        return 2
    if config_id == "prototype_reviewed_examples_family_guard":
        return 1
    return 0


def _row_results(config: Mapping[str, object]) -> list[dict[str, object]]:
    rows = config.get("row_results")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _required_family(
    dataset_lookup: Mapping[str, Mapping[str, object]],
    family_id: str,
) -> Mapping[str, object]:
    family = dataset_lookup.get(family_id)
    if not isinstance(family, Mapping):
        raise ValueError(f"Family {family_id!r} is missing from the dataset.")
    return family


def _shadow_by_id(family: Mapping[str, object], sense_id: str) -> Mapping[str, object]:
    for shadow in _shadow_senses(family):
        if _sense_id(shadow) == sense_id:
            return shadow
    raise ValueError(
        f"Family {family.get('family_id', '')!r} is missing shadow sense {sense_id!r}."
    )


def _case_ids(group: Mapping[str, object]) -> list[str]:
    values = group.get("case_ids")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _slice_tags(group: Mapping[str, object]) -> list[str]:
    values = group.get("slice_tags")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _case_group_slug(case_ids: Sequence[str]) -> str:
    suffixes = []
    for case_id in case_ids:
        text = str(case_id or "").strip()
        if not text:
            continue
        suffixes.append(_slug_component(text.rsplit(":", maxsplit=1)[-1]))
    return "-".join(value for value in suffixes if value)[:48]


def _slug_component(value: str) -> str:
    chars = []
    prior_dash = False
    for char in str(value or "").strip().lower():
        if char.isalnum():
            chars.append(char)
            prior_dash = False
        elif not prior_dash:
            chars.append("-")
            prior_dash = True
    return "".join(chars).strip("-")


def _build_recommendation(summary: Mapping[str, object]) -> str:
    if int(summary.get("request_count") or 0) <= 0:
        return "The selected prototype configuration has no residual failures to remediate."
    return (
        "Execute this plan only after reviewing the request rows: it targets active examples for "
        "false abstains and shadow examples for harmful replaces while leaving phrase-control "
        "evidence on the containment-only path."
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    report = build_example_frame_remediation_plan(
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        required_family_payload=_load_json(args.required_family_json),
        prototype_payload=_load_json(args.prototype_json),
        config_id=str(args.config_id or "").strip() or DEFAULT_CONFIG_ID,
        model_id=str(args.model_id or "").strip() or DEFAULT_MODEL_ID,
        temperature=float(args.temperature),
        chars_per_token=float(args.chars_per_token),
        expected_output_tokens=int(args.expected_output_tokens),
        max_output_tokens=int(args.max_output_tokens),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_example_frame_remediation_plan_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
