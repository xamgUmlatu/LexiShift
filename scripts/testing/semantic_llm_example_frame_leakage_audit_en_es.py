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
DEFAULT_DUPLICATE_JACCARD_THRESHOLD = 0.92
DEFAULT_MIN_CONTAINED_TOKENS = 5
DEFAULT_MIN_DUPLICATE_TOKENS = 4
_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ']+")
_PERSON_REFERENCE_TOKENS = frozenset(
    {
        "he",
        "him",
        "i",
        "me",
        "she",
        "them",
        "they",
        "us",
        "we",
    }
)
_DETERMINER_TOKENS = frozenset(
    {
        "a",
        "an",
        "her",
        "hers",
        "his",
        "mine",
        "my",
        "our",
        "ours",
        "the",
        "their",
        "theirs",
        "that",
        "these",
        "this",
        "those",
        "your",
        "yours",
    }
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit generated example-frame rows for benchmark sentence leakage."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--batch-json", type=Path, default=DEFAULT_BATCH_JSON)
    parser.add_argument(
        "--prior-batch-json",
        action="append",
        default=[],
        type=Path,
        help=(
            "Optional prior normalized/raw evidence batch to compare for source-row "
            "duplicates. Repeat for multiple prior sources."
        ),
    )
    parser.add_argument("--jaccard-threshold", type=float, default=DEFAULT_JACCARD_THRESHOLD)
    parser.add_argument(
        "--duplicate-jaccard-threshold",
        type=float,
        default=DEFAULT_DUPLICATE_JACCARD_THRESHOLD,
    )
    parser.add_argument("--min-contained-tokens", type=int, default=DEFAULT_MIN_CONTAINED_TOKENS)
    parser.add_argument(
        "--min-duplicate-tokens",
        type=int,
        default=DEFAULT_MIN_DUPLICATE_TOKENS,
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--filtered-batch-out", type=Path, default=DEFAULT_FILTERED_BATCH_OUT)
    return parser.parse_args()


def build_example_frame_leakage_audit_report(
    *,
    dataset_payload: Mapping[str, object],
    batch_payload: Mapping[str, object],
    prior_batch_payloads: Sequence[Mapping[str, object]] | None = None,
    jaccard_threshold: float = DEFAULT_JACCARD_THRESHOLD,
    duplicate_jaccard_threshold: float = DEFAULT_DUPLICATE_JACCARD_THRESHOLD,
    min_contained_tokens: int = DEFAULT_MIN_CONTAINED_TOKENS,
    min_duplicate_tokens: int = DEFAULT_MIN_DUPLICATE_TOKENS,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    normalized_batch = normalize_evidence_batch_payload(batch_payload)
    input_rows = [row for row in normalized_batch.get("rows", ()) if isinstance(row, Mapping)]
    dataset_cases = _dataset_case_rows(dataset_payload)
    benchmark_results = [
        _audit_benchmark_row(
            row=row,
            dataset_cases=dataset_cases,
            jaccard_threshold=float(jaccard_threshold),
            min_contained_tokens=int(min_contained_tokens),
        )
        for row in input_rows
    ]
    duplicate_results = _audit_duplicate_rows(
        rows=input_rows,
        batch_id=str(normalized_batch.get("batch_id") or "").strip(),
        prior_batch_payloads=prior_batch_payloads or (),
        duplicate_jaccard_threshold=float(duplicate_jaccard_threshold),
        min_duplicate_tokens=int(min_duplicate_tokens),
    )
    row_results = [
        {
            **benchmark_row,
            **duplicate_results.get(str(benchmark_row.get("row_id") or "").strip(), {}),
        }
        for benchmark_row in benchmark_results
    ]
    leaked_rows = [row for row in row_results if bool(row.get("leakage_hit"))]
    duplicate_rows = [row for row in row_results if bool(row.get("duplicate_hit"))]
    rejected_rows = [
        row for row in row_results if bool(row.get("leakage_hit")) or bool(row.get("duplicate_hit"))
    ]
    rejected_row_ids = {str(hit.get("row_id") or "").strip() for hit in rejected_rows}
    kept_rows = [
        dict(row)
        for row in input_rows
        if str(row.get("row_id") or "").strip() not in rejected_row_ids
    ]
    filtered_batch = dict(normalized_batch)
    filtered_batch["batch_id"] = f"{str(normalized_batch.get('batch_id') or '').strip()}:filtered"
    filtered_batch["row_count"] = len(kept_rows)
    filtered_batch["rows"] = kept_rows
    filtered_batch["review_state"] = (
        "review" if rejected_rows else str(normalized_batch.get("review_state") or "unreviewed")
    )
    filtered_batch["provenance"] = {
        **(
            dict(normalized_batch.get("provenance"))
            if isinstance(normalized_batch.get("provenance"), Mapping)
            else {}
        ),
        "leakage_audit": {
            "status": "review" if rejected_rows else "ok",
            "removed_row_count": len(rejected_rows),
            "leakage_hit_count": len(leaked_rows),
            "duplicate_hit_count": len(duplicate_rows),
            "jaccard_threshold": float(jaccard_threshold),
            "duplicate_jaccard_threshold": float(duplicate_jaccard_threshold),
            "min_contained_tokens": int(min_contained_tokens),
            "min_duplicate_tokens": int(min_duplicate_tokens),
        },
    }
    summary = {
        "input_row_count": len(row_results),
        "leakage_hit_count": len(leaked_rows),
        "duplicate_hit_count": len(duplicate_rows),
        "rejected_row_count": len(rejected_rows),
        "kept_row_count": len(kept_rows),
        "jaccard_threshold": float(jaccard_threshold),
        "duplicate_jaccard_threshold": float(duplicate_jaccard_threshold),
        "min_contained_tokens": int(min_contained_tokens),
        "min_duplicate_tokens": int(min_duplicate_tokens),
    }
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "review" if rejected_rows else "ok",
        "batch_id": str(normalized_batch.get("batch_id") or "").strip(),
        "filtered_batch_id": str(filtered_batch.get("batch_id") or "").strip(),
        "summary": summary,
        "row_results": row_results,
        "leakage_rows": leaked_rows,
        "duplicate_rows": duplicate_rows,
        "rejected_rows": rejected_rows,
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
        f"- Duplicate hits: `{summary.get('duplicate_hit_count', 0)}`",
        f"- Rejected rows: `{summary.get('rejected_row_count', 0)}`",
        f"- Kept rows: `{summary.get('kept_row_count', 0)}`",
        f"- Jaccard threshold: `{summary.get('jaccard_threshold', 0)}`",
        f"- Duplicate jaccard threshold: `{summary.get('duplicate_jaccard_threshold', 0)}`",
        f"- Min contained tokens: `{summary.get('min_contained_tokens', 0)}`",
        f"- Min duplicate tokens: `{summary.get('min_duplicate_tokens', 0)}`",
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
    lines.extend(
        [
            "",
            "## Duplicate Rows",
            "",
            "| Row | Family | Evidence | Matched Row | Reason | Jaccard |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for row in report.get("duplicate_rows", ()):
        if not isinstance(row, Mapping):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('row_id', '')}`",
                    f"`{row.get('family_id', '')}`",
                    _cell(row.get("evidence_text")),
                    f"`{row.get('duplicate_matched_row_id', '')}`",
                    f"`{row.get('duplicate_reason_code', '')}`",
                    str(row.get("duplicate_jaccard", 0.0)),
                ]
            )
            + " |"
        )
    if not report.get("duplicate_rows"):
        lines.append("| `none` | `n/a` | n/a | `n/a` | `n/a` | 0 |")
    lines.extend(["", "## Recommendation", "", f"- {report.get('recommendation', '')}"])
    return "\n".join(lines) + "\n"


def _audit_benchmark_row(
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
        exact_contained = _contains_subsequence(
            evidence_tokens,
            case_tokens,
            min_tokens=min_contained_tokens,
        ) or _contains_subsequence(case_tokens, evidence_tokens, min_tokens=min_contained_tokens)
        canonical_evidence_tokens = _canonical_tokens(evidence_tokens)
        canonical_case_tokens = _canonical_tokens(case_tokens)
        canonical_contained = _contains_subsequence(
            canonical_evidence_tokens,
            canonical_case_tokens,
            min_tokens=min_contained_tokens,
        ) or _contains_subsequence(
            canonical_case_tokens,
            canonical_evidence_tokens,
            min_tokens=min_contained_tokens,
        )
        exact_sequence = _longest_common_contiguous_sequence(evidence_tokens, case_tokens)
        canonical_sequence = _longest_common_contiguous_sequence(
            canonical_evidence_tokens,
            canonical_case_tokens,
        )
        common_sequence = (
            canonical_sequence if len(canonical_sequence) > len(exact_sequence) else exact_sequence
        )
        common_sequence_length = len(common_sequence)
        reason_code = _leakage_reason_code(
            exact_contained=exact_contained,
            canonical_contained=canonical_contained,
            exact_sequence_length=len(exact_sequence),
            canonical_sequence_length=len(canonical_sequence),
            jaccard=jaccard,
            jaccard_threshold=jaccard_threshold,
            min_contained_tokens=min_contained_tokens,
        )
        if _leakage_rank(
            reason_code=reason_code,
            common_sequence_length=common_sequence_length,
            jaccard=jaccard,
        ) > _leakage_rank(
            reason_code=str(best.get("reason_code") or ""),
            common_sequence_length=int(best["common_sequence_length"]),
            jaccard=float(best["jaccard"]),
        ):
            best = {
                "case_id": str(case.get("case_id") or "").strip(),
                "sentence": sentence,
                "jaccard": jaccard,
                "contained": exact_contained or canonical_contained,
                "common_sequence_length": common_sequence_length,
                "common_sequence": " ".join(common_sequence),
                "reason_code": reason_code,
            }
    reason_code = str(best.get("reason_code") or "").strip()
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


def _audit_duplicate_rows(
    *,
    rows: Sequence[Mapping[str, object]],
    batch_id: str,
    prior_batch_payloads: Sequence[Mapping[str, object]],
    duplicate_jaccard_threshold: float,
    min_duplicate_tokens: int,
) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    reference_rows = _prior_duplicate_reference_rows(prior_batch_payloads)
    for row in rows:
        row_id = str(row.get("row_id") or "").strip()
        duplicate = _best_duplicate_match(
            row=row,
            reference_rows=reference_rows,
            duplicate_jaccard_threshold=duplicate_jaccard_threshold,
            min_duplicate_tokens=min_duplicate_tokens,
        )
        results[row_id] = duplicate
        reference_rows.append(_duplicate_reference_row(row=row, batch_id=batch_id))
    return results


def _prior_duplicate_reference_rows(
    prior_batch_payloads: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    reference_rows: list[dict[str, object]] = []
    for payload in prior_batch_payloads:
        normalized = normalize_evidence_batch_payload(payload)
        batch_id = str(normalized.get("batch_id") or "").strip()
        for row in normalized.get("rows", ()):
            if isinstance(row, Mapping):
                reference_rows.append(_duplicate_reference_row(row=row, batch_id=batch_id))
    return reference_rows


def _duplicate_reference_row(
    *,
    row: Mapping[str, object],
    batch_id: str,
) -> dict[str, object]:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), Mapping) else {}
    evidence_text = str(row.get("evidence_text") or "").strip()
    tokens = _canonical_tokens(_tokens(evidence_text))
    return {
        "batch_id": batch_id,
        "row_id": str(row.get("row_id") or "").strip(),
        "family_id": str(metadata.get("family_id") or "").strip(),
        "relation_type": str(row.get("relation_type") or "").strip(),
        "candidate_target": str(row.get("candidate_target") or "").strip().lower(),
        "evidence_text": evidence_text,
        "tokens": tokens,
    }


def _best_duplicate_match(
    *,
    row: Mapping[str, object],
    reference_rows: Sequence[Mapping[str, object]],
    duplicate_jaccard_threshold: float,
    min_duplicate_tokens: int,
) -> dict[str, object]:
    candidate = _duplicate_reference_row(row=row, batch_id="")
    best = {
        "duplicate_hit": False,
        "duplicate_reason_code": "",
        "duplicate_matched_batch_id": "",
        "duplicate_matched_row_id": "",
        "duplicate_jaccard": 0.0,
        "duplicate_common_sequence_length": 0,
        "duplicate_common_sequence": "",
    }
    for reference in reference_rows:
        if not _same_duplicate_scope(candidate, reference):
            continue
        candidate_tokens = [
            str(token).strip() for token in candidate.get("tokens", ()) if str(token).strip()
        ]
        reference_tokens = [
            str(token).strip() for token in reference.get("tokens", ()) if str(token).strip()
        ]
        jaccard = _jaccard(candidate_tokens, reference_tokens)
        common_sequence = _longest_common_contiguous_sequence(candidate_tokens, reference_tokens)
        contained = _contains_subsequence(
            candidate_tokens,
            reference_tokens,
            min_tokens=min_duplicate_tokens,
        ) or _contains_subsequence(
            reference_tokens,
            candidate_tokens,
            min_tokens=min_duplicate_tokens,
        )
        reason_code = _duplicate_reason_code(
            candidate_text=str(candidate.get("evidence_text") or "").strip(),
            reference_text=str(reference.get("evidence_text") or "").strip(),
            contained=contained,
            common_sequence_length=len(common_sequence),
            jaccard=jaccard,
            duplicate_jaccard_threshold=duplicate_jaccard_threshold,
            min_duplicate_tokens=min_duplicate_tokens,
        )
        if _duplicate_rank(
            reason_code=reason_code,
            common_sequence_length=len(common_sequence),
            jaccard=jaccard,
        ) > _duplicate_rank(
            reason_code=str(best.get("duplicate_reason_code") or ""),
            common_sequence_length=int(best.get("duplicate_common_sequence_length") or 0),
            jaccard=float(best.get("duplicate_jaccard") or 0.0),
        ):
            best = {
                "duplicate_hit": bool(reason_code),
                "duplicate_reason_code": reason_code,
                "duplicate_matched_batch_id": str(reference.get("batch_id") or "").strip(),
                "duplicate_matched_row_id": str(reference.get("row_id") or "").strip(),
                "duplicate_jaccard": round(jaccard, 4),
                "duplicate_common_sequence_length": len(common_sequence),
                "duplicate_common_sequence": " ".join(common_sequence),
            }
    return best


def _same_duplicate_scope(
    row: Mapping[str, object],
    reference: Mapping[str, object],
) -> bool:
    return (
        str(row.get("family_id") or "").strip() == str(reference.get("family_id") or "").strip()
        and str(row.get("relation_type") or "").strip()
        == str(reference.get("relation_type") or "").strip()
        and str(row.get("candidate_target") or "").strip()
        == str(reference.get("candidate_target") or "").strip()
    )


def _duplicate_reason_code(
    *,
    candidate_text: str,
    reference_text: str,
    contained: bool,
    common_sequence_length: int,
    jaccard: float,
    duplicate_jaccard_threshold: float,
    min_duplicate_tokens: int,
) -> str:
    if candidate_text.strip().lower() == reference_text.strip().lower():
        return "source_duplicate_exact_text"
    if contained or common_sequence_length >= min_duplicate_tokens:
        return "source_duplicate_token_sequence_contained"
    if jaccard >= duplicate_jaccard_threshold:
        return "source_near_duplicate_jaccard"
    return ""


def _duplicate_rank(
    *,
    reason_code: str,
    common_sequence_length: int,
    jaccard: float,
) -> tuple[int, int, float]:
    reason_rank = {
        "source_duplicate_exact_text": 3,
        "source_duplicate_token_sequence_contained": 2,
        "source_near_duplicate_jaccard": 1,
    }.get(reason_code, 0)
    return (reason_rank, common_sequence_length, jaccard)


def _dataset_case_rows(dataset_payload: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in dataset_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping):
                continue
            if "not_quality_evaluation" in case.get("slice_tags", ()):
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
    reason_code: str,
    common_sequence_length: int,
    jaccard: float,
) -> tuple[int, int, float]:
    return (
        _reason_rank(reason_code),
        int(common_sequence_length),
        float(jaccard),
    )


def _leakage_reason_code(
    *,
    exact_contained: bool,
    canonical_contained: bool,
    exact_sequence_length: int,
    canonical_sequence_length: int,
    jaccard: float,
    jaccard_threshold: float,
    min_contained_tokens: int,
) -> str:
    if exact_contained:
        return "benchmark_token_sequence_contained"
    if canonical_contained:
        return "benchmark_canonical_token_sequence_contained"
    if exact_sequence_length >= min_contained_tokens:
        return "benchmark_token_sequence_overlap"
    if canonical_sequence_length >= min_contained_tokens:
        return "benchmark_canonical_token_sequence_overlap"
    if jaccard >= jaccard_threshold:
        return "benchmark_token_jaccard_threshold"
    return ""


def _reason_rank(reason_code: str) -> int:
    ranks = {
        "benchmark_token_sequence_contained": 5,
        "benchmark_canonical_token_sequence_contained": 4,
        "benchmark_token_sequence_overlap": 3,
        "benchmark_canonical_token_sequence_overlap": 2,
        "benchmark_token_jaccard_threshold": 1,
    }
    return ranks.get(str(reason_code or "").strip(), 0)


def _tokens(text: str) -> list[str]:
    return [match.lower() for match in _TOKEN_RE.findall(str(text or ""))]


def _canonical_tokens(tokens: Sequence[str]) -> list[str]:
    values: list[str] = []
    for token in tokens:
        text = str(token or "").strip().lower()
        if text in _PERSON_REFERENCE_TOKENS:
            values.append("<person>")
        elif text in _DETERMINER_TOKENS:
            values.append("<det>")
        else:
            values.append(text)
    return values


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
    leakage_hit_count = int(summary.get("leakage_hit_count") or 0)
    duplicate_hit_count = int(summary.get("duplicate_hit_count") or 0)
    if leakage_hit_count == 0 and duplicate_hit_count == 0:
        return (
            "No benchmark-near-copy or source-duplicate rows were found; the batch can "
            "advance to the next admission gate."
        )
    if leakage_hit_count == 0:
        return (
            "Use the filtered batch for downstream prototype reads, and replace the "
            "source-duplicate rows before any promotion claim."
        )
    return (
        "Use the filtered batch for downstream prototype reads, and regenerate or replace the "
        "removed leakage or duplicate rows before any promotion claim."
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
        prior_batch_payloads=[_load_json(path) for path in args.prior_batch_json],
        jaccard_threshold=float(args.jaccard_threshold),
        duplicate_jaccard_threshold=float(args.duplicate_jaccard_threshold),
        min_contained_tokens=int(args.min_contained_tokens),
        min_duplicate_tokens=int(args.min_duplicate_tokens),
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
