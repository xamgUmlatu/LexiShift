#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
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

from semantic_example_frame_evidence_support import normalize_evidence_batch_payload  # noqa: E402
from semantic_llm_prompt_downstream_en_es import DEFAULT_DATASET_PATH, _load_json  # noqa: E402
from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402


DEFAULT_BATCH_JSON = TEST_OUTPUTS_ROOT / (
    "experiments/semantic_example_frame_batches/"
    "en-es-example-frame-missing-rows-example-frame-remediation-v1-20260425a_normalized_evidence.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_leakage_audit_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_llm_example_frame_leakage_audit_latest.md"
DEFAULT_FILTERED_BATCH_OUT = TEST_OUTPUTS_ROOT / (
    "experiments/semantic_example_frame_batches/"
    "en-es-example-frame-remediation-v1-20260425a_filtered_normalized_evidence.json"
)
DEFAULT_JACCARD_THRESHOLD = 0.75
DEFAULT_MIN_CONTAINED_TOKENS = 5
_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit generated example-frame rows for benchmark sentence leakage."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--batch-json", type=Path, default=DEFAULT_BATCH_JSON)
    parser.add_argument("--jaccard-threshold", type=float, default=DEFAULT_JACCARD_THRESHOLD)
    parser.add_argument("--min-contained-tokens", type=int, default=DEFAULT_MIN_CONTAINED_TOKENS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--filtered-batch-out", type=Path, default=DEFAULT_FILTERED_BATCH_OUT)
    return parser.parse_args()


def build_example_frame_leakage_audit_report(
    *,
    dataset_payload: Mapping[str, object],
    batch_payload: Mapping[str, object],
    jaccard_threshold: float = DEFAULT_JACCARD_THRESHOLD,
    min_contained_tokens: int = DEFAULT_MIN_CONTAINED_TOKENS,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    normalized_batch = normalize_evidence_batch_payload(batch_payload)
    dataset_cases = _dataset_case_rows(dataset_payload)
    row_results = [
        _audit_row(
            row=row,
            dataset_cases=dataset_cases,
            jaccard_threshold=float(jaccard_threshold),
            min_contained_tokens=int(min_contained_tokens),
        )
        for row in normalized_batch.get("rows", ())
        if isinstance(row, Mapping)
    ]
    leaked_rows = [row for row in row_results if bool(row.get("leakage_hit"))]
    kept_rows = [
        dict(row)
        for row in normalized_batch.get("rows", ())
        if isinstance(row, Mapping)
        and str(row.get("row_id") or "").strip()
        not in {str(hit.get("row_id") or "").strip() for hit in leaked_rows}
    ]
    filtered_batch = dict(normalized_batch)
    filtered_batch["batch_id"] = f"{str(normalized_batch.get('batch_id') or '').strip()}:filtered"
    filtered_batch["row_count"] = len(kept_rows)
    filtered_batch["rows"] = kept_rows
    filtered_batch["review_state"] = (
        "review" if leaked_rows else str(normalized_batch.get("review_state") or "unreviewed")
    )
    filtered_batch["provenance"] = {
        **(
            dict(normalized_batch.get("provenance"))
            if isinstance(normalized_batch.get("provenance"), Mapping)
            else {}
        ),
        "leakage_audit": {
            "status": "review" if leaked_rows else "ok",
            "removed_row_count": len(leaked_rows),
            "jaccard_threshold": float(jaccard_threshold),
            "min_contained_tokens": int(min_contained_tokens),
        },
    }
    summary = {
        "input_row_count": len(row_results),
        "leakage_hit_count": len(leaked_rows),
        "kept_row_count": len(kept_rows),
        "jaccard_threshold": float(jaccard_threshold),
        "min_contained_tokens": int(min_contained_tokens),
    }
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "review" if leaked_rows else "ok",
        "batch_id": str(normalized_batch.get("batch_id") or "").strip(),
        "filtered_batch_id": str(filtered_batch.get("batch_id") or "").strip(),
        "summary": summary,
        "row_results": row_results,
        "leakage_rows": leaked_rows,
        "filtered_batch": filtered_batch,
        "recommendation": _build_recommendation(summary),
    }


def render_example_frame_leakage_audit_markdown(report: Mapping[str, object]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    lines = [
        "# en-es LLM Example-Frame Leakage Audit",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Batch: `{report.get('batch_id', '')}`",
        f"- Filtered batch: `{report.get('filtered_batch_id', '')}`",
        "",
        "## Summary",
        "",
        f"- Input rows: `{summary.get('input_row_count', 0)}`",
        f"- Leakage hits: `{summary.get('leakage_hit_count', 0)}`",
        f"- Kept rows: `{summary.get('kept_row_count', 0)}`",
        f"- Jaccard threshold: `{summary.get('jaccard_threshold', 0)}`",
        f"- Min contained tokens: `{summary.get('min_contained_tokens', 0)}`",
        "",
        "## Leakage Rows",
        "",
        "| Row | Family | Evidence | Matched Case | Reason | Jaccard |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in report.get("leakage_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('row_id', '')}`",
                    f"`{row.get('family_id', '')}`",
                    _cell(row.get("evidence_text")),
                    f"`{row.get('matched_case_id', '')}`",
                    f"`{row.get('reason_code', '')}`",
                    str(row.get("jaccard", 0.0)),
                ]
            )
            + " |"
        )
    if not report.get("leakage_rows"):
        lines.append("| `none` | `n/a` | n/a | `n/a` | `n/a` | 0 |")
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _audit_row(
    *,
    row: Mapping[str, object],
    dataset_cases: Sequence[Mapping[str, object]],
    jaccard_threshold: float,
    min_contained_tokens: int,
) -> dict[str, object]:
    evidence_text = str(row.get("evidence_text") or "").strip()
    evidence_tokens = _tokens(evidence_text)
    best = {
        "case_id": "",
        "sentence": "",
        "jaccard": 0.0,
        "contained": False,
        "common_sequence_length": 0,
        "common_sequence": "",
    }
    for case in dataset_cases:
        sentence = str(case.get("sentence") or "").strip()
        case_tokens = _tokens(sentence)
        jaccard = _jaccard(evidence_tokens, case_tokens)
        contained = _contains_subsequence(
            evidence_tokens,
            case_tokens,
            min_tokens=min_contained_tokens,
        ) or _contains_subsequence(case_tokens, evidence_tokens, min_tokens=min_contained_tokens)
        common_sequence = _longest_common_contiguous_sequence(evidence_tokens, case_tokens)
        common_sequence_length = len(common_sequence)
        if _leakage_rank(
            contained=contained,
            common_sequence_length=common_sequence_length,
            jaccard=jaccard,
        ) > _leakage_rank(
            contained=bool(best["contained"]),
            common_sequence_length=int(best["common_sequence_length"]),
            jaccard=float(best["jaccard"]),
        ):
            best = {
                "case_id": str(case.get("case_id") or "").strip(),
                "sentence": sentence,
                "jaccard": jaccard,
                "contained": contained,
                "common_sequence_length": common_sequence_length,
                "common_sequence": " ".join(common_sequence),
            }
    reason_code = ""
    if bool(best["contained"]):
        reason_code = "benchmark_token_sequence_contained"
    elif int(best["common_sequence_length"]) >= min_contained_tokens:
        reason_code = "benchmark_token_sequence_overlap"
    elif float(best["jaccard"]) >= jaccard_threshold:
        reason_code = "benchmark_token_jaccard_threshold"
    metadata = row.get("metadata") if isinstance(row.get("metadata"), Mapping) else {}
    return {
        "row_id": str(row.get("row_id") or "").strip(),
        "family_id": str(metadata.get("family_id") or "").strip(),
        "relation_type": str(row.get("relation_type") or "").strip(),
        "evidence_text": evidence_text,
        "leakage_hit": bool(reason_code),
        "reason_code": reason_code,
        "matched_case_id": str(best.get("case_id") or "").strip(),
        "matched_sentence": str(best.get("sentence") or "").strip(),
        "jaccard": round(float(best.get("jaccard") or 0.0), 4),
        "contained": bool(best.get("contained")),
        "common_sequence_length": int(best.get("common_sequence_length") or 0),
        "common_sequence": str(best.get("common_sequence") or "").strip(),
    }


def _dataset_case_rows(dataset_payload: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping):
                continue
            rows.append(
                {
                    "family_id": family_id,
                    "case_id": str(case.get("case_id") or "").strip(),
                    "sentence": str(case.get("sentence") or "").strip(),
                }
            )
    return rows


def _leakage_rank(
    *,
    contained: bool,
    common_sequence_length: int,
    jaccard: float,
) -> tuple[int, int, float]:
    return (
        1 if contained else 0,
        int(common_sequence_length),
        float(jaccard),
    )


def _tokens(text: str) -> list[str]:
    return [match.lower() for match in _TOKEN_RE.findall(str(text or ""))]


def _jaccard(left_tokens: Sequence[str], right_tokens: Sequence[str]) -> float:
    left = set(left_tokens)
    right = set(right_tokens)
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _contains_subsequence(
    haystack: Sequence[str],
    needle: Sequence[str],
    *,
    min_tokens: int,
) -> bool:
    if len(needle) < min_tokens or len(haystack) < len(needle):
        return False
    limit = len(haystack) - len(needle) + 1
    for index in range(limit):
        if list(haystack[index : index + len(needle)]) == list(needle):
            return True
    return False


def _longest_common_contiguous_sequence(
    left_tokens: Sequence[str],
    right_tokens: Sequence[str],
) -> list[str]:
    best: list[str] = []
    for left_index in range(len(left_tokens)):
        for right_index in range(len(right_tokens)):
            length = 0
            while (
                left_index + length < len(left_tokens)
                and right_index + length < len(right_tokens)
                and left_tokens[left_index + length] == right_tokens[right_index + length]
            ):
                length += 1
            if length > len(best):
                best = list(left_tokens[left_index : left_index + length])
    return best


def _build_recommendation(summary: Mapping[str, object]) -> str:
    if int(summary.get("leakage_hit_count") or 0) == 0:
        return "No benchmark-near-copy rows were found; the batch can be merged as-is."
    return (
        "Use the filtered batch for downstream prototype reads, and regenerate or replace the "
        "removed rows before any promotion claim."
    )


def _cell(value: object, *, limit: int = 90) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > limit:
        text = text[: limit - 3].rstrip() + "..."
    return text.replace("|", "\\|") or "n/a"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    report = build_example_frame_leakage_audit_report(
        dataset_payload=load_sentence_veto_dataset(args.dataset),
        batch_payload=_load_json(args.batch_json),
        jaccard_threshold=float(args.jaccard_threshold),
        min_contained_tokens=int(args.min_contained_tokens),
    )
    filtered_batch = report["filtered_batch"]
    _write_json(args.filtered_batch_out, filtered_batch)
    _write_json(
        args.json_out, {key: value for key, value in report.items() if key != "filtered_batch"}
    )
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(
        render_example_frame_leakage_audit_markdown(report),
        encoding="utf-8",
    )
    print(f"Wrote leakage audit JSON to {args.json_out}")
    print(f"Wrote leakage audit Markdown to {args.markdown_out}")
    print(f"Wrote filtered batch to {args.filtered_batch_out}")
    print(f"Leakage audit status: {report['status']}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
