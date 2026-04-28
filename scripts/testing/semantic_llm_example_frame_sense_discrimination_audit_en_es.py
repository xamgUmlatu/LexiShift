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

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    RuntimeSimilarityBackend,
    resolve_runtime_evidence_text,
)
from semantic_example_frame_evidence_support import (  # noqa: E402
    ACTIVE_RELATION_TYPES,
    PHRASE_RELATION_TYPES,
    SHADOW_RELATION_TYPES,
    normalize_evidence_batch_payload,
    row_family_key,
    row_sense_id,
)
from semantic_llm_prompt_downstream_en_es import DEFAULT_DATASET_PATH, _load_json  # noqa: E402
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_BATCH_JSON = TEST_OUTPUTS_ROOT / (
    "experiments/semantic_example_frame_batches/"
    "en-es-balanced-plus-source-coverage-filtered-safe-v2-20260425a_normalized_evidence.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_llm_example_frame_sense_discrimination_audit_latest.json"
)
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / (
    "semantic_llm_example_frame_sense_discrimination_audit_latest.md"
)
DEFAULT_ADMITTED_BATCH_OUT = TEST_OUTPUTS_ROOT / (
    "experiments/semantic_example_frame_batches/"
    "en-es-example-frame-sense-admitted-latest_normalized_evidence.json"
)
DEFAULT_SCORERS = ("token_jaccard", "tfidf_cosine")
DEFAULT_EVIDENCE_VIEW = "all_evidence_text"
DEFAULT_MIN_INTENDED_SCORE = 0.05
DEFAULT_MIN_MARGIN = 0.01


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit active/shadow example-frame rows for sense discrimination before merge. "
            "Rows pass only if at least one approved scorer prefers the intended sense over "
            "competing senses."
        )
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--batch-json", type=Path, default=DEFAULT_BATCH_JSON)
    parser.add_argument("--scorers", default=",".join(DEFAULT_SCORERS))
    parser.add_argument("--evidence-view", default=DEFAULT_EVIDENCE_VIEW)
    parser.add_argument("--min-intended-score", type=float, default=DEFAULT_MIN_INTENDED_SCORE)
    parser.add_argument("--min-margin", type=float, default=DEFAULT_MIN_MARGIN)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--admitted-batch-out", type=Path, default=DEFAULT_ADMITTED_BATCH_OUT)
    return parser.parse_args()


def build_example_frame_sense_discrimination_audit_report(
    *,
    dataset_payload: Mapping[str, object],
    batch_payload: Mapping[str, object],
    scorers: Sequence[str] = DEFAULT_SCORERS,
    evidence_view: str = DEFAULT_EVIDENCE_VIEW,
    min_intended_score: float = DEFAULT_MIN_INTENDED_SCORE,
    min_margin: float = DEFAULT_MIN_MARGIN,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    scorer_ids = _normalize_scorers(scorers)
    normalized_batch = normalize_evidence_batch_payload(batch_payload)
    input_rows = [row for row in normalized_batch.get("rows", ()) if isinstance(row, Mapping)]
    family_lookup = _dataset_family_lookup(dataset_payload)
    sense_texts = _dataset_sense_texts(
        family_lookup,
        evidence_view=str(evidence_view or "").strip() or DEFAULT_EVIDENCE_VIEW,
    )
    backends = _fit_scorers(
        scorer_ids=scorer_ids,
        rows=input_rows,
        sense_texts=sense_texts,
    )
    row_results = [
        _audit_row(
            row=row,
            family_lookup=family_lookup,
            sense_texts=sense_texts,
            backends=backends,
            min_intended_score=float(min_intended_score),
            min_margin=float(min_margin),
        )
        for row in input_rows
    ]
    admitted_row_ids = {
        str(row.get("row_id") or "").strip()
        for row in row_results
        if str(row.get("admission_status") or "") in {"admitted", "not_applicable"}
    }
    admitted_rows = [
        dict(row) for row in input_rows if str(row.get("row_id") or "").strip() in admitted_row_ids
    ]
    rejected_rows = [
        row for row in row_results if str(row.get("admission_status") or "") == "rejected"
    ]
    semantic_rows = [
        row
        for row in row_results
        if str(row.get("relation_type") or "") in ACTIVE_RELATION_TYPES | SHADOW_RELATION_TYPES
    ]
    passthrough_rows = [
        row for row in row_results if str(row.get("admission_status") or "") == "not_applicable"
    ]
    summary = {
        "input_row_count": len(row_results),
        "semantic_input_row_count": len(semantic_rows),
        "semantic_admitted_row_count": len(semantic_rows) - len(rejected_rows),
        "semantic_rejected_row_count": len(rejected_rows),
        "non_semantic_passthrough_row_count": len(passthrough_rows),
        "admitted_row_count": len(admitted_rows),
        "scorers": scorer_ids,
        "evidence_view": str(evidence_view or "").strip() or DEFAULT_EVIDENCE_VIEW,
        "min_intended_score": float(min_intended_score),
        "min_margin": float(min_margin),
        "rejection_reason_counts": _reason_counts(rejected_rows),
    }
    admitted_batch = _build_admitted_batch(
        normalized_batch=normalized_batch,
        admitted_rows=admitted_rows,
        summary=summary,
    )
    status = "review" if rejected_rows else "ok"
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": status,
        "batch_id": str(normalized_batch.get("batch_id") or "").strip(),
        "admitted_batch_id": str(admitted_batch.get("batch_id") or "").strip(),
        "summary": summary,
        "row_results": row_results,
        "rejected_rows": rejected_rows,
        "admitted_batch": admitted_batch,
        "recommendation": _build_recommendation(summary),
    }


def render_example_frame_sense_discrimination_audit_markdown(
    report: Mapping[str, object],
) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es LLM Example-Frame Sense-Discrimination Audit",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Admitted batch: `{report.get('admitted_batch_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Input rows: `{summary.get('input_row_count', 0)}`",
        f"- Semantic rows: `{summary.get('semantic_input_row_count', 0)}`",
        f"- Semantic admitted rows: `{summary.get('semantic_admitted_row_count', 0)}`",
        f"- Semantic rejected rows: `{summary.get('semantic_rejected_row_count', 0)}`",
        f"- Non-semantic passthrough rows: `{summary.get('non_semantic_passthrough_row_count', 0)}`",
        f"- Admitted rows: `{summary.get('admitted_row_count', 0)}`",
        f"- Scorers: `{', '.join(_as_texts(summary.get('scorers')))}`",
        f"- Evidence view: `{summary.get('evidence_view', '')}`",
        f"- Min intended score: `{summary.get('min_intended_score', 0)}`",
        f"- Min margin: `{summary.get('min_margin', 0)}`",
        f"- Rejection reasons: `{json.dumps(summary.get('rejection_reason_counts', {}), sort_keys=True)}`",
        "",
        "## Rejected Rows",
        "",
        "| Row | Family | Relation | Intended | Reason | Best Scorer | Intended | Competitor | Margin |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in report.get("rejected_rows", ()):
        if not isinstance(row, Mapping):
            continue
        best = row.get("best_result") if isinstance(row.get("best_result"), Mapping) else {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('row_id', '')}`",
                    f"`{row.get('family_id', '')}`",
                    f"`{row.get('relation_type', '')}`",
                    f"`{row.get('intended_sense_id', '')}`",
                    f"`{row.get('reason_code', '')}`",
                    f"`{best.get('scorer_id', '')}`",
                    str(best.get("intended_score", 0.0)),
                    str(best.get("strongest_competitor_score", 0.0)),
                    str(best.get("margin", 0.0)),
                ]
            )
            + " |"
        )
    if not report.get("rejected_rows"):
        lines.append("| `none` | `n/a` | `n/a` | `n/a` | `n/a` | `n/a` | 0 | 0 | 0 |")
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _audit_row(
    *,
    row: Mapping[str, object],
    family_lookup: Mapping[str, Mapping[str, object]],
    sense_texts: Mapping[str, str],
    backends: Mapping[str, RuntimeSimilarityBackend],
    min_intended_score: float,
    min_margin: float,
) -> dict[str, object]:
    relation_type = str(row.get("relation_type") or "").strip()
    family_key = row_family_key(row)
    base = {
        "row_id": str(row.get("row_id") or "").strip(),
        "family_id": family_key,
        "relation_type": relation_type,
        "evidence_text": str(row.get("evidence_text") or "").strip(),
    }
    if relation_type in PHRASE_RELATION_TYPES:
        return {
            **base,
            "admission_status": "not_applicable",
            "reason_code": "phrase_containment_not_semantic_competition",
            "scorer_results": [],
        }
    if relation_type not in ACTIVE_RELATION_TYPES | SHADOW_RELATION_TYPES:
        return {
            **base,
            "admission_status": "not_applicable",
            "reason_code": "unsupported_relation_type_passthrough",
            "scorer_results": [],
        }
    family = family_lookup.get(family_key)
    if not isinstance(family, Mapping):
        return _rejected(base, "unknown_family", [], intended_sense_id="")
    intended_sense_id = _intended_sense_id(row=row, family=family, relation_type=relation_type)
    if not intended_sense_id:
        return _rejected(base, "missing_intended_sense", [], intended_sense_id="")
    if intended_sense_id not in sense_texts:
        return _rejected(base, "unknown_intended_sense", [], intended_sense_id=intended_sense_id)
    competitor_sense_ids = [
        sense_id
        for sense_id in _family_sense_ids(family)
        if sense_id and sense_id != intended_sense_id and sense_id in sense_texts
    ]
    scorer_results = [
        _score_with_backend(
            scorer_id=scorer_id,
            backend=backend,
            evidence_text=str(row.get("evidence_text") or "").strip(),
            intended_sense_id=intended_sense_id,
            intended_text=sense_texts[intended_sense_id],
            competitor_sense_ids=competitor_sense_ids,
            sense_texts=sense_texts,
            min_intended_score=min_intended_score,
            min_margin=min_margin,
        )
        for scorer_id, backend in backends.items()
    ]
    if any(bool(result.get("passes")) for result in scorer_results):
        return {
            **base,
            "admission_status": "admitted",
            "reason_code": "sense_discrimination_passed",
            "intended_sense_id": intended_sense_id,
            "competitor_sense_ids": competitor_sense_ids,
            "best_result": _best_scorer_result(scorer_results),
            "scorer_results": scorer_results,
        }
    return _rejected(
        base,
        _reject_reason(scorer_results, min_intended_score=min_intended_score),
        scorer_results,
        intended_sense_id=intended_sense_id,
        competitor_sense_ids=competitor_sense_ids,
    )


def _score_with_backend(
    *,
    scorer_id: str,
    backend: RuntimeSimilarityBackend,
    evidence_text: str,
    intended_sense_id: str,
    intended_text: str,
    competitor_sense_ids: Sequence[str],
    sense_texts: Mapping[str, str],
    min_intended_score: float,
    min_margin: float,
) -> dict[str, object]:
    intended_score = backend.similarity(evidence_text, intended_text)
    competitor_rows = [
        {
            "sense_id": sense_id,
            "score": backend.similarity(evidence_text, sense_texts[sense_id]),
        }
        for sense_id in competitor_sense_ids
    ]
    strongest = max(competitor_rows, key=lambda row: float(row["score"]), default=None)
    strongest_score = float(strongest["score"]) if strongest else 0.0
    strongest_id = str(strongest["sense_id"]) if strongest else ""
    margin = float(intended_score) - strongest_score
    return {
        "scorer_id": scorer_id,
        "passes": intended_score >= min_intended_score and margin >= min_margin,
        "intended_sense_id": intended_sense_id,
        "intended_score": _round(intended_score),
        "strongest_competitor_sense_id": strongest_id,
        "strongest_competitor_score": _round(strongest_score),
        "margin": _round(margin),
    }


def _rejected(
    base: Mapping[str, object],
    reason_code: str,
    scorer_results: Sequence[Mapping[str, object]],
    *,
    intended_sense_id: str,
    competitor_sense_ids: Sequence[str] = (),
) -> dict[str, object]:
    return {
        **base,
        "admission_status": "rejected",
        "reason_code": reason_code,
        "intended_sense_id": intended_sense_id,
        "competitor_sense_ids": list(competitor_sense_ids),
        "best_result": _best_scorer_result(scorer_results),
        "scorer_results": list(scorer_results),
    }


def _reject_reason(
    scorer_results: Sequence[Mapping[str, object]],
    *,
    min_intended_score: float,
) -> str:
    if not scorer_results:
        return "no_scorer_results"
    best = _best_scorer_result(scorer_results)
    if float(best.get("intended_score") or 0.0) < float(min_intended_score):
        return "weak_intended_similarity"
    if float(best.get("strongest_competitor_score") or 0.0) >= float(
        best.get("intended_score") or 0.0
    ):
        return "competitor_sense_not_lower"
    return "insufficient_sense_margin"


def _best_scorer_result(results: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not results:
        return {}
    return dict(
        max(
            results,
            key=lambda row: (
                bool(row.get("passes")),
                float(row.get("margin") or 0.0),
                float(row.get("intended_score") or 0.0),
            ),
        )
    )


def _dataset_family_lookup(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
        raise ValueError("dataset payload must contain a `families` array.")
    return {
        str(family.get("family_id") or "").strip(): family
        for family in families
        if isinstance(family, Mapping) and str(family.get("family_id") or "").strip()
    }


def _dataset_sense_texts(
    family_lookup: Mapping[str, Mapping[str, object]],
    *,
    evidence_view: str,
) -> dict[str, str]:
    texts: dict[str, str] = {}
    for family in family_lookup.values():
        active = family.get("active")
        if isinstance(active, Mapping):
            _append_sense_text(texts, active, evidence_view=evidence_view)
        for shadow in family.get("shadows", ()):
            if isinstance(shadow, Mapping):
                _append_sense_text(texts, shadow, evidence_view=evidence_view)
    return texts


def _append_sense_text(
    texts: dict[str, str],
    sense: Mapping[str, object],
    *,
    evidence_view: str,
) -> None:
    sense_id = str(sense.get("sense_id") or "").strip()
    text = resolve_runtime_evidence_text(sense, evidence_view=evidence_view)
    if sense_id and text:
        texts[sense_id] = text


def _fit_scorers(
    *,
    scorer_ids: Sequence[str],
    rows: Sequence[Mapping[str, object]],
    sense_texts: Mapping[str, str],
) -> dict[str, RuntimeSimilarityBackend]:
    texts = _unique_texts(
        [
            *[str(row.get("evidence_text") or "").strip() for row in rows],
            *sense_texts.values(),
        ]
    )
    backends: dict[str, RuntimeSimilarityBackend] = {}
    for scorer_id in scorer_ids:
        backend = RuntimeSimilarityBackend(scorer_id=scorer_id)
        backend.fit(texts)
        backends[scorer_id] = backend
    return backends


def _intended_sense_id(
    *,
    row: Mapping[str, object],
    family: Mapping[str, object],
    relation_type: str,
) -> str:
    if relation_type in ACTIVE_RELATION_TYPES:
        active = family.get("active")
        if isinstance(active, Mapping):
            return str(active.get("sense_id") or "").strip()
        return row_sense_id(row, "active_sense_hint")
    return row_sense_id(row, "candidate_sense_hint")


def _family_sense_ids(family: Mapping[str, object]) -> list[str]:
    ids: list[str] = []
    active = family.get("active")
    if isinstance(active, Mapping):
        ids.append(str(active.get("sense_id") or "").strip())
    for shadow in family.get("shadows", ()):
        if isinstance(shadow, Mapping):
            ids.append(str(shadow.get("sense_id") or "").strip())
    return [sense_id for sense_id in ids if sense_id]


def _build_admitted_batch(
    *,
    normalized_batch: Mapping[str, object],
    admitted_rows: Sequence[Mapping[str, object]],
    summary: Mapping[str, object],
) -> dict[str, object]:
    admitted_batch = dict(normalized_batch)
    admitted_batch["batch_id"] = (
        f"{str(normalized_batch.get('batch_id') or '').strip()}:sense-admitted"
    )
    admitted_batch["row_count"] = len(admitted_rows)
    admitted_batch["rows"] = [dict(row) for row in admitted_rows]
    admitted_batch["review_state"] = (
        "review"
        if int(summary.get("semantic_rejected_row_count") or 0) > 0
        else str(normalized_batch.get("review_state") or "unreviewed")
    )
    admitted_batch["provenance"] = {
        **(
            dict(normalized_batch.get("provenance"))
            if isinstance(normalized_batch.get("provenance"), Mapping)
            else {}
        ),
        "sense_discrimination_audit": {
            "status": "review"
            if int(summary.get("semantic_rejected_row_count") or 0) > 0
            else "ok",
            "semantic_rejected_row_count": int(summary.get("semantic_rejected_row_count") or 0),
            "semantic_admitted_row_count": int(summary.get("semantic_admitted_row_count") or 0),
            "scorers": list(_as_texts(summary.get("scorers"))),
            "evidence_view": str(summary.get("evidence_view") or "").strip(),
            "min_intended_score": float(summary.get("min_intended_score") or 0.0),
            "min_margin": float(summary.get("min_margin") or 0.0),
        },
    }
    return admitted_batch


def _build_recommendation(summary: Mapping[str, object]) -> str:
    rejected = int(summary.get("semantic_rejected_row_count") or 0)
    if rejected <= 0:
        return (
            "All active/shadow rows pass sense-discrimination admission; use the admitted "
            "batch for merge and downstream ablation."
        )
    return (
        "Use the admitted batch only as an analysis artifact. Replace or quarantine rejected "
        "active/shadow rows before any promotion-candidate merge."
    )


def _reason_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("reason_code") or "").strip() or "unknown"
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _normalize_scorers(value: Sequence[str] | str) -> list[str]:
    values = value.split(",") if isinstance(value, str) else value
    scorers: list[str] = []
    for item in values:
        text = str(item or "").strip()
        if text and text not in scorers:
            scorers.append(text)
    if not scorers:
        raise ValueError("At least one scorer is required.")
    return scorers


def _as_texts(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _unique_texts(values: Sequence[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in unique:
            unique.append(text)
    return unique


def _round(value: float) -> float:
    return round(float(value), 6)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    report = build_example_frame_sense_discrimination_audit_report(
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        batch_payload=_load_json(args.batch_json),
        scorers=_normalize_scorers(str(args.scorers or "")),
        evidence_view=str(args.evidence_view or "").strip() or DEFAULT_EVIDENCE_VIEW,
        min_intended_score=float(args.min_intended_score),
        min_margin=float(args.min_margin),
    )
    admitted_batch = report["admitted_batch"]
    _write_json(args.admitted_batch_out, admitted_batch)
    _write_json(
        args.json_out, {key: value for key, value in report.items() if key != "admitted_batch"}
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_example_frame_sense_discrimination_audit_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote sense-discrimination audit JSON to {args.json_out}")
    print(f"Wrote sense-discrimination audit Markdown to {args.markdown_out}")
    print(f"Wrote admitted batch to {args.admitted_batch_out}")
    print(f"Sense-discrimination audit status: {report['status']}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
