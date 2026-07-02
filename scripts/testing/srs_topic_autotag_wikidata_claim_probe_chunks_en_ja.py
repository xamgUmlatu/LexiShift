#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_evidence_en_ja import (  # noqa: E402
    DEFAULT_CANDIDATES_CSV,
    DEFAULT_POLICY_JSON,
    _as_mapping,
    _candidates_by_lemma,
    _load_candidates,
    _mapping_rows,
    _safe_float,
    _select_sample_rows,
    _source_summary,
    _string_list,
)
from srs_topic_autotag_wikidata_claim_probe_en_ja import (  # noqa: E402
    DEFAULT_CACHE_JSON,
    DEFAULT_EXISTING_OVERLAY_JSON,
    LANGUAGE_PAIR,
    SOURCE_ID,
    build_report as build_probe_report,
    render_markdown as render_probe_markdown,
    _covered_overlay_lemmas,
    _dedupe_evidence_rows,
    _topic_summary,
)


TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_CHUNK_DIR = TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_claim_probe_chunks_en_ja"
DEFAULT_MERGED_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_claim_probe_full_en_ja_latest.json"
)
DEFAULT_MERGED_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_topic_autotag_wikidata_claim_probe_full_en_ja_latest.md"
)
DEFAULT_TOP_N = 73752
DEFAULT_CHUNK_SIZE = 250
INCOMPLETE_CODES = {
    "wikidata_rate_limited",
    "wikidata_entity_budget_exhausted",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the en-ja Wikidata claim probe over deterministic chunks and merge "
            "the per-chunk artifacts into a full-pass evidence file."
        )
    )
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES_CSV)
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY_JSON)
    parser.add_argument("--existing-overlay-json", type=Path, default=DEFAULT_EXISTING_OVERLAY_JSON)
    parser.add_argument("--cache-json", type=Path, default=DEFAULT_CACHE_JSON)
    parser.add_argument("--chunk-dir", type=Path, default=DEFAULT_CHUNK_DIR)
    parser.add_argument("--merged-json-out", type=Path, default=DEFAULT_MERGED_JSON_OUT)
    parser.add_argument("--merged-markdown-out", type=Path, default=DEFAULT_MERGED_MARKDOWN_OUT)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--start-chunk", type=int, default=0)
    parser.add_argument("--max-chunks", type=int, default=0)
    parser.add_argument(
        "--exclude-covered",
        action="store_true",
        help=(
            "Skip lemmas already covered by the existing overlay. The default is to "
            "include covered lemmas so the full pass can find additional topics."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run chunks even if a completed chunk artifact exists.",
    )
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Skip network work and rebuild only the merged artifact.",
    )
    parser.add_argument(
        "--continue-on-incomplete",
        action="store_true",
        help="Continue after a rate-limited or budget-exhausted chunk instead of stopping for later resume.",
    )
    parser.add_argument("--offline-only", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.35)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--retry-after-seconds", type=float, default=45.0)
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--max-entity-requests-per-chunk", type=int, default=3000)
    parser.add_argument("--max-branch-targets", type=int, default=24)
    parser.add_argument("--sample-per-cell", type=int, default=4)
    parser.add_argument("--max-sample-rows", type=int, default=240)
    parser.add_argument("--fail-on-incomplete", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    candidates_csv = _resolve_path(args.candidates_csv)
    policy_json = _resolve_path(args.policy_json)
    existing_overlay_json = _resolve_path(args.existing_overlay_json)
    cache_json = _resolve_path(args.cache_json)
    chunk_dir = _resolve_path(args.chunk_dir)
    merged_json_out = _resolve_path(args.merged_json_out)
    merged_markdown_out = _resolve_path(args.merged_markdown_out)
    top_n = max(0, int(args.top_n))
    chunk_size = max(1, int(args.chunk_size))
    include_covered = not bool(args.exclude_covered)

    candidates = _load_candidates(candidates_csv, top_n=top_n)
    covered_lemmas = _covered_overlay_lemmas(existing_overlay_json)
    eligible_candidates = _eligible_probe_candidates(
        candidates,
        covered_lemmas=covered_lemmas,
        include_covered=include_covered,
    )
    chunks = _chunks(eligible_candidates, chunk_size)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    start_chunk = max(0, int(args.start_chunk))
    selected_indexes = list(range(start_chunk, len(chunks)))
    if int(args.max_chunks) > 0:
        selected_indexes = selected_indexes[: int(args.max_chunks)]

    stopped_for_incomplete = False
    if not args.merge_only:
        for chunk_index in selected_indexes:
            chunk_path = _chunk_json_path(chunk_dir, chunk_index)
            if not args.force and _completed_chunk_exists(chunk_path):
                print(f"[skip] chunk {chunk_index:04d} already complete: {chunk_path}")
                continue
            chunk_rows = chunks[chunk_index]
            lemmas = [
                str(row.get("lemma") or "") for row in chunk_rows if str(row.get("lemma") or "")
            ]
            print(
                f"[run] chunk {chunk_index:04d}/{max(len(chunks) - 1, 0):04d}: {len(lemmas)} labels"
            )
            report = build_probe_report(
                candidates_csv=candidates_csv,
                policy_json=policy_json,
                existing_overlay_json=existing_overlay_json,
                cache_json=cache_json,
                top_n=top_n,
                max_labels=len(lemmas),
                explicit_lemmas=tuple(lemmas),
                max_depth=max(0, int(args.max_depth)),
                max_entity_requests=max(0, int(args.max_entity_requests_per_chunk)),
                max_branch_targets=max(0, int(args.max_branch_targets)),
                sleep_seconds=max(0.0, float(args.sleep_seconds)),
                timeout_seconds=max(1, int(args.timeout_seconds)),
                retry_after_seconds=max(0.0, float(args.retry_after_seconds)),
                label_lookup="jawikipedia_pageprops",
                sample_per_cell=max(0, int(args.sample_per_cell)),
                max_sample_rows=max(0, int(args.max_sample_rows)),
                include_covered=True,
                offline_only=bool(args.offline_only),
            )
            report = {
                **report,
                "chunk": {
                    "chunk_index": chunk_index,
                    "chunk_size": chunk_size,
                    "label_count": len(lemmas),
                    "first_label": lemmas[0] if lemmas else "",
                    "last_label": lemmas[-1] if lemmas else "",
                    "complete": not _report_is_incomplete(report),
                },
            }
            _write_json(chunk_path, report)
            _chunk_markdown_path(chunk_dir, chunk_index).write_text(
                render_probe_markdown(report), encoding="utf-8"
            )
            if _report_is_incomplete(report):
                stopped_for_incomplete = True
                print(
                    f"[stop] chunk {chunk_index:04d} is incomplete; rerun this command later to resume."
                )
                if not args.continue_on_incomplete:
                    break

    merged_report = build_merged_report(
        chunk_dir=chunk_dir,
        expected_chunk_count=len(chunks),
        eligible_label_count=len(eligible_candidates),
        chunk_size=chunk_size,
        include_covered=include_covered,
        candidates_csv=candidates_csv,
        policy_json=policy_json,
        existing_overlay_json=existing_overlay_json,
        cache_json=cache_json,
        top_n=top_n,
        generated_at=_utc_now(),
    )
    _write_json(merged_json_out, merged_report)
    merged_markdown_out.write_text(render_markdown(merged_report), encoding="utf-8")
    print(f"[write] merged JSON: {merged_json_out}")
    print(f"[write] merged Markdown: {merged_markdown_out}")
    if args.fail_on_incomplete and (merged_report["status"] != "ok" or stopped_for_incomplete):
        return 1
    return 0


def _eligible_probe_candidates(
    candidates: Sequence[Mapping[str, object]],
    *,
    covered_lemmas: set[str],
    include_covered: bool,
) -> list[Mapping[str, object]]:
    selected: list[Mapping[str, object]] = []
    for lemma, rows in _candidates_by_lemma(candidates).items():
        if not include_covered and lemma in covered_lemmas:
            continue
        normal_rows = [
            row
            for row in rows
            if str(row.get("candidate_state") or "") == "normal_vocab"
            and str(row.get("topic_stretch_allowed") or "").lower() != "false"
        ]
        if len({str(row.get("reading") or "") for row in normal_rows}) != 1:
            continue
        selected.append(normal_rows[0])
    return sorted(
        selected,
        key=lambda row: (
            int(row.get("rank") or 0),
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
        ),
    )


def build_merged_report(
    *,
    chunk_dir: Path,
    expected_chunk_count: int,
    eligible_label_count: int,
    chunk_size: int,
    include_covered: bool,
    candidates_csv: Path,
    policy_json: Path,
    existing_overlay_json: Path,
    cache_json: Path,
    top_n: int,
    generated_at: str,
) -> dict[str, object]:
    chunk_reports = _load_chunk_reports(chunk_dir)
    complete_reports = [report for report in chunk_reports if not _report_is_incomplete(report)]
    incomplete_reports = [report for report in chunk_reports if _report_is_incomplete(report)]
    present_indexes = {_chunk_index(report) for report in chunk_reports}
    missing_indexes = [
        index for index in range(expected_chunk_count) if index not in present_indexes
    ]
    evidence_rows = _dedupe_evidence_rows(
        [row for report in chunk_reports for row in _mapping_rows(report.get("evidence_rows"))]
    )
    review_sample = _select_sample_rows(
        evidence_rows,
        sample_per_cell=4,
        max_rows=240,
        max_rows_per_source=0,
    )
    findings = [
        _finding(
            "PASS" if chunk_reports else "WARN",
            "wikidata_chunk_reports_loaded" if chunk_reports else "wikidata_chunk_reports_missing",
            f"Loaded {len(chunk_reports)} chunk report(s) from {chunk_dir}.",
        )
    ]
    if missing_indexes:
        findings.append(
            _finding(
                "WARN",
                "wikidata_chunks_missing",
                f"{len(missing_indexes)} expected chunk(s) have not been generated yet.",
            )
        )
    if incomplete_reports:
        findings.append(
            _finding(
                "WARN",
                "wikidata_chunks_incomplete",
                f"{len(incomplete_reports)} chunk report(s) are rate-limited or entity-budget-limited.",
            )
        )
    if evidence_rows:
        findings.append(
            _finding(
                "PASS",
                "wikidata_merged_evidence_present",
                f"Merged {len(evidence_rows)} evidence rows.",
            )
        )
    else:
        findings.append(
            _finding(
                "WARN", "wikidata_merged_evidence_empty", "No merged evidence rows are present yet."
            )
        )
    complete = not missing_indexes and not incomplete_reports and bool(chunk_reports)
    return {
        "schema_version": 1,
        "status": "ok" if complete else "review",
        "decision": (
            "wikidata_claim_probe_full_pass_complete"
            if complete
            else "wikidata_claim_probe_full_pass_incomplete"
        ),
        "generated_at": generated_at,
        "language_pair": LANGUAGE_PAIR,
        "inputs": {
            "candidates_csv": _repo_path(candidates_csv),
            "policy_json": _repo_path(policy_json),
            "existing_overlay_json": _repo_path(existing_overlay_json),
            "cache_json": _repo_path(cache_json),
            "chunk_dir": _repo_path(chunk_dir),
            "top_n": top_n,
            "chunk_size": chunk_size,
            "include_covered": include_covered,
        },
        "method": {
            "source": SOURCE_ID,
            "query_shape": "chunked Japanese Wikipedia pageprops QID lookup plus Wikidata EntityData claim ancestry",
            "promotion_state": "evidence_only_not_product_overlay",
            "resume_policy": "completed chunks are skipped; incomplete chunks are rerun until rate/budget warnings disappear",
        },
        "chunk_summary": {
            "expected_chunk_count": expected_chunk_count,
            "loaded_chunk_count": len(chunk_reports),
            "complete_chunk_count": len(complete_reports),
            "incomplete_chunk_count": len(incomplete_reports),
            "missing_chunk_count": len(missing_indexes),
            "missing_chunk_sample": missing_indexes[:40],
            "incomplete_chunk_indexes": [_chunk_index(report) for report in incomplete_reports],
            "eligible_label_count": eligible_label_count,
            "completed_label_count": sum(
                int(_as_mapping(report.get("chunk")).get("label_count") or 0)
                for report in complete_reports
            ),
        },
        "source_summary": _source_summary(evidence_rows),
        "topic_summary": _topic_summary(evidence_rows),
        "evidence_rows": evidence_rows,
        "review_sample": review_sample,
        "findings": findings,
        "limitations": [
            "This is a build-time full-pass evidence artifact, not a runtime dependency.",
            "Only exact Japanese Wikipedia pageprops titles are probed; generic Wikidata search is intentionally excluded.",
            "The promotion exporter still applies its stricter product-safe guard before rows can become overlay candidates.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    chunk_summary = _as_mapping(report.get("chunk_summary"))
    lines = [
        "# en-ja SRS Topic Autotag Wikidata Claim Probe Full Pass",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Expected chunks: `{chunk_summary.get('expected_chunk_count', 0)}`",
        f"- Complete chunks: `{chunk_summary.get('complete_chunk_count', 0)}`",
        f"- Incomplete chunks: `{chunk_summary.get('incomplete_chunk_count', 0)}`",
        f"- Missing chunks: `{chunk_summary.get('missing_chunk_count', 0)}`",
        f"- Eligible labels: `{chunk_summary.get('eligible_label_count', 0)}`",
        f"- Completed labels: `{chunk_summary.get('completed_label_count', 0)}`",
        f"- Evidence rows: `{len(_mapping_rows(report.get('evidence_rows')))}`",
        "",
        "## Topics",
        "",
        "| Topic | Rows | Lemmas |",
        "| --- | ---: | ---: |",
    ]
    for topic, row in _as_mapping(report.get("topic_summary")).items():
        topic_row = _as_mapping(row)
        lines.append(
            f"| `{topic}` | {topic_row.get('row_count', 0)} | {topic_row.get('lemma_count', 0)} |"
        )
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: {finding.get('message', '')}"
        )
    lines.extend(["", "## Review Sample", ""])
    lines.extend(_sample_table(_mapping_rows(report.get("review_sample"))))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Topic | Lemma | Reading | Score | Source label | Wikidata item |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        extra = _as_mapping(row.get("extra"))
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | `{row.get('reading', '')}` | "
            f"{_safe_float(row.get('score'), default=0.0):.3f} | `{row.get('source_label', '')}` | "
            f"`{extra.get('wikidata_qid', '')}` {str(extra.get('wikidata_label') or '')} |"
        )
    return lines


def _load_chunk_reports(chunk_dir: Path) -> list[Mapping[str, object]]:
    reports: list[Mapping[str, object]] = []
    for path in sorted(chunk_dir.glob("chunk_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, Mapping):
            reports.append(payload)
    return reports


def _completed_chunk_exists(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, Mapping) and not _report_is_incomplete(payload)


def _report_is_incomplete(report: Mapping[str, object]) -> bool:
    codes = {
        str(row.get("code") or "")
        for row in _mapping_rows(report.get("findings"))
        if str(row.get("level") or "") in {"WARN", "FAIL"}
    }
    return bool(codes & INCOMPLETE_CODES)


def _chunk_index(report: Mapping[str, object]) -> int:
    raw_index = _as_mapping(report.get("chunk")).get("chunk_index")
    try:
        return int(raw_index)
    except (TypeError, ValueError):
        return -1


def _chunks(values: Sequence[Mapping[str, object]], size: int) -> list[list[Mapping[str, object]]]:
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _chunk_json_path(chunk_dir: Path, chunk_index: int) -> Path:
    return chunk_dir / f"chunk_{chunk_index:04d}.json"


def _chunk_markdown_path(chunk_dir: Path, chunk_index: int) -> Path:
    return chunk_dir / f"chunk_{chunk_index:04d}.md"


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _repo_path(path: Path) -> str:
    resolved = Path(path).expanduser().resolve(strict=False)
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
