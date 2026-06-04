from __future__ import annotations

from typing import Mapping, Sequence

from semantic_example_frame_source_adapter_support import all_family_dataset as _all_family_dataset
from semantic_reverse_aux_text_pilot_en_es import build_queue_subset_dataset


def render_wordnet_example_frame_batch_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es WordNet Example-Frame Batch",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Source: `{report.get('source_id', '')}` / `{report.get('source_family', '')}`",
        f"- Scope: `{report.get('source_scope', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Min link score: `{summary.get('min_link_score', 0)}`",
        f"- Evidence mode: `{summary.get('evidence_mode', '')}`",
        "",
        "## Coverage",
        "",
        f"- Queue families: `{summary.get('queue_family_count', 0)}`",
        f"- Source families: `{summary.get('source_family_count', 0)}`",
        f"- Target families: `{summary.get('target_family_count', 0)}`",
        f"- Target families with active WordNet rows: `{summary.get('target_families_with_active_wordnet', 0)}`",
        f"- Target families with shadow WordNet rows: `{summary.get('target_families_with_shadow_wordnet', 0)}`",
        f"- Families with phrase-control examples: `{summary.get('families_with_phrase_control_examples', 0)}`",
        "",
        "| Family | Role | Active | Shadow | Phrase | Rows | Best Links |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report.get("family_rows", ()):
        if not isinstance(row, Mapping):
            continue
        link_summary = _render_link_summary(row.get("link_rows"))
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('role', '')}`",
                    str(row.get("active_wordnet_count", 0)),
                    str(row.get("shadow_wordnet_count", 0)),
                    str(row.get("phrase_control_example_count", 0)),
                    str(row.get("row_count", 0)),
                    link_summary,
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _build_source_dataset(
    *,
    queue_payload: Mapping[str, object],
    dataset_payload: Mapping[str, object],
    residual_cycle_payload: Mapping[str, object] | None,
    family_keys: Sequence[str],
    scope: str,
) -> tuple[dict[str, object], dict[str, str]]:
    if scope == "prompt_queue":
        return build_queue_subset_dataset(dataset_payload, queue_payload)
    if scope == "all_dataset_families":
        return _all_family_dataset(dataset_payload)
    if scope == "residual_semantic_gaps":
        residual_keys = _residual_semantic_gap_keys(residual_cycle_payload)
        payload, roles = _all_family_dataset(dataset_payload)
        payload["families"] = [
            family
            for family in payload.get("families", ())
            if isinstance(family, Mapping)
            and str(family.get("family_id") or "").strip() in residual_keys
        ]
        roles = {
            str(family.get("family_id") or "").strip(): roles.get(
                str(family.get("family_id") or "").strip(),
                "target",
            )
            for family in payload.get("families", ())
            if isinstance(family, Mapping)
        }
        return payload, roles
    if scope == "family_keys":
        selected_keys = {str(key or "").strip() for key in family_keys if str(key or "").strip()}
        if not selected_keys:
            raise ValueError("family_keys scope requires at least one --family-key value.")
        payload, roles = _all_family_dataset(dataset_payload)
        payload["families"] = [
            family
            for family in payload.get("families", ())
            if isinstance(family, Mapping)
            and str(family.get("family_id") or "").strip() in selected_keys
        ]
        roles = {
            str(family.get("family_id") or "").strip(): roles.get(
                str(family.get("family_id") or "").strip(),
                "target",
            )
            for family in payload.get("families", ())
            if isinstance(family, Mapping)
        }
        return payload, roles
    raise ValueError(f"unsupported source scope: {scope}")


def _build_recommendation(
    summary: Mapping[str, object],
    *,
    missing_resources: Sequence[str],
) -> str:
    if missing_resources:
        return (
            "Resolve the local English WordNet JSON pack before building WordNet "
            "example-frame evidence."
        )
    return (
        "This adapter is a real local source pass for active/shadow semantic evidence, "
        "but it intentionally does not solve phrase containment. Run the source-admission "
        "cycle before using it as a challenger, and treat missing/low-score links as source "
        "gaps rather than generated coverage."
    )


def _residual_semantic_gap_keys(payload: Mapping[str, object] | None) -> set[str]:
    residuals = payload.get("residuals") if isinstance(payload, Mapping) else {}
    if not isinstance(residuals, Mapping):
        return set()
    keys = residuals.get("semantic_gap_family_keys")
    if not isinstance(keys, Sequence) or isinstance(keys, (str, bytes)):
        return set()
    return {str(key or "").strip() for key in keys if str(key or "").strip()}


def _render_link_summary(link_rows: object) -> str:
    if not isinstance(link_rows, Sequence) or isinstance(link_rows, (str, bytes)):
        return "`n/a`"
    parts = []
    for row in link_rows:
        if not isinstance(row, Mapping):
            continue
        target = str(row.get("target_lemma") or "").strip()
        synset = str(row.get("best_wordnet_synset_id") or "").strip()
        score = row.get("best_link_score", 0.0)
        if synset:
            parts.append(f"`{target}:{synset}@{score}`")
        else:
            parts.append(f"`{target}:missing`")
    return "<br>".join(parts) if parts else "`n/a`"
