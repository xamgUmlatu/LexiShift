#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Mapping, Sequence


def render_prompt_smoke_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    slot_rows = _coerce_rows(report.get("slot_rows"))
    sample_requests = _coerce_rows(report.get("sample_requests"))

    lines = [
        "# en-es Semantic LLM Prompt Smoke",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Prompt spec: `{report.get('prompt_spec_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Stage: `{report.get('stage', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        f"- Temperature: `{report.get('selected_temperature', '')}`",
        "",
        "## Summary",
        "",
        f"- Active slots: `{summary.get('active_slot_count', 0)}`",
        f"- Prompt requests: `{summary.get('request_count', 0)}`",
        f"- Target families covered: `{summary.get('target_family_count', 0)}`",
        f"- Negative controls held out of prompting: `{summary.get('negative_control_count', 0)}`",
        "",
        "## Slot Matrix",
        "",
        "| Slot | Status | Target Families | Requests | Notes |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in slot_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('prompt_slot', '')}`",
                    f"`{row.get('status', '')}`",
                    str(int(row.get("target_family_count") or 0)),
                    str(int(row.get("request_count") or 0)),
                    _render_notes(row.get("notes")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Sample Requests",
            "",
        ]
    )
    for row in sample_requests:
        lines.extend(
            [
                f"### `{row.get('request_id', '')}`",
                "",
                f"- Slot: `{row.get('prompt_slot', '')}`",
                f"- Family: `{row.get('family_id', '')}`",
                f"- Trigger: `{row.get('trigger', '')}`",
                f"- Active -> Candidate: `{row.get('active_target', '')}` -> `{row.get('candidate_target', '')}`",
                f"- Model: `{row.get('model_id', '')}` @ temperature `{row.get('temperature', '')}`",
                "",
                "System prompt:",
                "",
                "```text",
                str(row.get("system_prompt") or "").strip(),
                "```",
                "",
                "User prompt:",
                "",
                "```text",
                str(row.get("user_prompt") or "").strip(),
                "```",
                "",
                "Expected row preview:",
                "",
                "```json",
                _render_json_preview(row.get("expected_row_preview")),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _coerce_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _render_notes(value: object) -> str:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        notes = [str(item).strip() for item in value if str(item).strip()]
        return "<br>".join(notes) if notes else "n/a"
    text = str(value or "").strip()
    return text or "n/a"


def _render_json_preview(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) if isinstance(value, Mapping) else "{}"


def render_prompt_bakeoff_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    artifacts = report.get("artifacts") if isinstance(report.get("artifacts"), Mapping) else {}
    request_rows = _coerce_rows(report.get("request_rows"))

    lines = [
        "# en-es Semantic LLM Prompt Bakeoff",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Prompt spec: `{report.get('prompt_spec_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Stage: `{report.get('stage', '')}`",
        f"- Execution mode: `{report.get('execution_mode', 'live')}`",
        f"- Batch id: `{report.get('batch_id', '')}`",
        f"- Source id: `{report.get('source_id', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        f"- Temperature: `{report.get('selected_temperature', '')}`",
    ]
    replay_source = str(report.get("replay_source") or "").strip()
    if replay_source:
        lines.append(f"- Replay source: `{replay_source}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Selected requests: `{summary.get('selected_request_count', 0)}`",
            f"- Accepted items: `{summary.get('accepted_item_count', 0)}`",
            f"- API errors: `{summary.get('api_error_count', 0)}`",
            f"- Invalid outputs: `{summary.get('invalid_output_count', 0)}`",
            f"- Normalized rows: `{summary.get('normalized_row_count', 0)}`",
            f"- Input tokens: `{summary.get('input_tokens', 0)}`",
            f"- Output tokens: `{summary.get('output_tokens', 0)}`",
            "",
            "## Artifacts",
            "",
            f"- Journal: `{artifacts.get('journal_jsonl', 'n/a')}`",
            f"- Raw responses: `{artifacts.get('raw_response_bundle_json', 'n/a')}`",
            f"- Intake batch: `{artifacts.get('intake_batch_json', 'n/a')}`",
            f"- Normalized batch: `{artifacts.get('normalized_batch_json', 'n/a')}`",
            "",
            "## Request Outcomes",
            "",
            "| Request | Slot | Family | Status | Output |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in request_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('request_id', '')}`",
                    f"`{row.get('prompt_slot', '')}`",
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('status', '')}`",
                    _render_request_outcome(row),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_prompt_preflight_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    env_checks = _coerce_rows(report.get("env_checks"))
    request_rows = _coerce_rows(report.get("request_rows"))
    planned_artifacts = report.get("planned_artifacts")
    if not isinstance(planned_artifacts, Mapping):
        planned_artifacts = {}

    lines = [
        "# en-es Semantic LLM Prompt Preflight",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Prompt spec: `{report.get('prompt_spec_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Stage: `{report.get('stage', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        f"- Temperature: `{report.get('selected_temperature', '')}`",
        "",
        "## Summary",
        "",
        f"- Selected requests: `{summary.get('selected_request_count', 0)}`",
        f"- Selected families: `{summary.get('selected_family_count', 0)}`",
        f"- Active slots represented: `{summary.get('selected_slot_count', 0)}`",
        f"- Current shell ready: `{summary.get('current_shell_ready', False)}`",
        f"- Sourced shell ready: `{summary.get('sourced_shell_ready', False)}`",
        f"- Any safe local path ready: `{summary.get('local_env_ready', False)}`",
        f"- Live spend blocked by default: `{summary.get('live_spend_guarded', False)}`",
        "",
        "## Environment Checks",
        "",
        "| Check | Status | Notes |",
        "| --- | --- | --- |",
    ]
    for row in env_checks:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('check_id', '')}`",
                    f"`{row.get('status', '')}`",
                    _truncate_markdown_cell(str(row.get("notes") or "n/a"), limit=120),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Planned Artifacts",
            "",
            f"- Journal: `{planned_artifacts.get('journal_jsonl', 'n/a')}`",
            f"- Raw responses: `{planned_artifacts.get('raw_response_bundle_json', 'n/a')}`",
            f"- Intake batch: `{planned_artifacts.get('intake_batch_json', 'n/a')}`",
            f"- Normalized batch: `{planned_artifacts.get('normalized_batch_json', 'n/a')}`",
            "",
            "## Selected Requests",
            "",
            "| Request | Slot | Family | Trigger | Active -> Candidate |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in request_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('request_id', '')}`",
                    f"`{row.get('prompt_slot', '')}`",
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('trigger', '')}`",
                    f"`{row.get('active_target', '')}` -> `{row.get('candidate_target', '')}`",
                ]
            )
            + " |"
        )

    command = str(report.get("live_command_example") or "").strip()
    if command:
        lines.extend(
            [
                "",
                "## Live Command",
                "",
                "```bash",
                command,
                "```",
            ]
        )
    return "\n".join(lines)


def render_prompt_cost_estimate_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    rate_info = report.get("rate_info")
    if not isinstance(rate_info, Mapping):
        rate_info = {}
    request_rows = _coerce_rows(report.get("request_rows"))

    lines = [
        "# en-es Semantic LLM Prompt Cost Estimate",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Prompt spec: `{report.get('prompt_spec_id', '')}`",
        f"- Prompt version: `{report.get('prompt_version', '')}`",
        f"- Stage: `{report.get('stage', '')}`",
        f"- Selected model: `{report.get('selected_model_id', '')}`",
        f"- Input-token heuristic: `{report.get('input_token_heuristic', '')}`",
        "",
        "## Summary",
        "",
        f"- Selected requests: `{summary.get('selected_request_count', 0)}`",
        f"- Estimated input tokens: `{summary.get('estimated_input_tokens', 0)}`",
        f"- Estimated output tokens (expected): `{summary.get('expected_output_tokens', 0)}`",
        f"- Output token ceiling: `{summary.get('max_output_tokens', 0)}`",
    ]
    if rate_info:
        lines.extend(
            [
                f"- Input rate per 1M: `{rate_info.get('input_rate_per_1m', 'n/a')}`",
                f"- Output rate per 1M: `{rate_info.get('output_rate_per_1m', 'n/a')}`",
                f"- Estimated cost (expected): `{summary.get('estimated_cost_expected', 'n/a')}`",
                f"- Estimated cost (ceiling): `{summary.get('estimated_cost_ceiling', 'n/a')}`",
            ]
        )
    else:
        lines.append("- Pricing rates: `not supplied`")

    lines.extend(
        [
            "",
            "## Request Estimates",
            "",
            "| Request | Slot | Input Tokens | Expected Output | Output Ceiling |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in request_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('request_id', '')}`",
                    f"`{row.get('prompt_slot', '')}`",
                    str(int(row.get("estimated_input_tokens") or 0)),
                    str(int(row.get("expected_output_tokens") or 0)),
                    str(int(row.get("max_output_tokens") or 0)),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_prompt_downstream_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    llm_batch = report.get("llm_batch") if isinstance(report.get("llm_batch"), Mapping) else {}
    coverage_rows = _coerce_rows(report.get("coverage_rows"))
    config_rows = _coerce_rows(report.get("configurations"))

    lines = [
        "# en-es Semantic LLM Prompt Downstream Bakeoff",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Queue: `{report.get('queue_id', '')}`",
        f"- Runtime dataset: `{report.get('dataset_id', '')}`",
        f"- Scorer: `{report.get('scorer_id', '')}`",
        f"- Min active / margin: `{report.get('min_active_score', '')}` / `{report.get('min_margin', '')}`",
        "",
        "## LLM Batch",
        "",
        f"- Batch id: `{llm_batch.get('batch_id', '')}`",
        f"- Source id: `{llm_batch.get('source_id', '')}`",
        f"- Prompt version: `{llm_batch.get('prompt_version', '')}`",
        f"- Model: `{llm_batch.get('model_id', '')}`",
        f"- Batch review state: `{llm_batch.get('review_state', '')}`",
        f"- Runtime publishable rows: `{llm_batch.get('runtime_publishable_count', 0)}` / `{llm_batch.get('row_count', 0)}`",
        "",
        "## Coverage",
        "",
        f"- Target families: `{summary.get('target_family_count', 0)}`",
        f"- Target families with LLM cues: `{summary.get('target_families_with_llm_cues', 0)}`",
        f"- Negative controls with LLM cues: `{summary.get('negative_controls_with_llm_cues', 0)}`",
        "",
        "| Family | Role | LLM Cue Rows | Prompt Slots | Sample Cue |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in coverage_rows:
        sample_texts = row.get("sample_llm_cue_texts")
        if isinstance(sample_texts, Sequence) and not isinstance(sample_texts, (str, bytes)):
            sample_value = "<br>".join(
                _truncate_markdown_cell(str(item), limit=96)
                for item in sample_texts
                if str(item).strip()
            )
        else:
            sample_value = "n/a"
        prompt_slots = row.get("prompt_slots")
        if isinstance(prompt_slots, Sequence) and not isinstance(prompt_slots, (str, bytes)):
            prompt_slot_value = ", ".join(f"`{str(item)}`" for item in prompt_slots if str(item).strip())
        else:
            prompt_slot_value = "n/a"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('trigger', '')} -> {row.get('active_target', '')}`",
                    f"`{row.get('role', '')}`",
                    str(int(row.get("llm_cue_row_count") or 0)),
                    prompt_slot_value or "n/a",
                    sample_value or "n/a",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Configuration Summary",
            "",
            "| Config | Scope | Evidence View | Harmful | False Abstain | Replace Recall | Decision Acc. | Fixed False Abstains | Introduced False Abstains |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in config_rows:
        summary_row = row.get("summary") if isinstance(row.get("summary"), Mapping) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('label', row.get('config_id', ''))}`",
                    f"`{row.get('phrase_guard_pos_scope', '')}`",
                    f"`{row.get('evidence_view', '')}`",
                    str(int(summary_row.get("harmful_replace_count") or 0)),
                    str(int(summary_row.get("false_abstain_count") or 0)),
                    _render_rate(summary_row.get("replace_recall")),
                    _render_rate(summary_row.get("decision_accuracy")),
                    ", ".join(
                        f"`{case_id}`"
                        for case_id in _normalize_string_list(
                            row.get("fixed_false_abstain_case_ids")
                        )
                    )
                    or "none",
                    ", ".join(
                        f"`{case_id}`"
                        for case_id in _normalize_string_list(
                            row.get("introduced_false_abstain_case_ids")
                        )
                    )
                    or "none",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Focus Case Outcomes",
            "",
            "| Config | Case | Gold | Predicted | Margin | Phrase | Rescue |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in config_rows:
        for case in row.get("focus_cases", ()):
            if not isinstance(case, Mapping):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row.get("config_id") or ""),
                        str(case.get("case_id") or ""),
                        str(case.get("gold_decision") or ""),
                        str(case.get("predicted_decision") or ""),
                        _render_metric(case.get("margin")),
                        "yes" if bool(case.get("phrase_preemption_hit")) else "no",
                        "yes" if bool(case.get("active_rescue_applied")) else "no",
                    ]
                )
                + " |"
            )

    recommendation = str(report.get("recommendation") or "").strip()
    if recommendation:
        lines.extend(["", "## Recommendation", "", f"- {recommendation}"])
    return "\n".join(lines)


def _render_request_outcome(row: Mapping[str, object]) -> str:
    evidence_text = str(row.get("evidence_text") or "").strip()
    if evidence_text:
        return _truncate_markdown_cell(evidence_text)
    error_text = str(row.get("error_message") or "").strip()
    if error_text:
        return _truncate_markdown_cell(error_text)
    output_text = str(row.get("output_text") or "").strip()
    if output_text:
        return _truncate_markdown_cell(output_text)
    return "n/a"


def _normalize_string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _truncate_markdown_cell(value: str, *, limit: int = 96) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _render_rate(value: object) -> str:
    try:
        return f"{float(value) * 100.0:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _render_metric(value: object) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "n/a"
