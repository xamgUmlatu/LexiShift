#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.srs.learner_difficulty import (  # noqa: E402
    CORRECTED_LEARNER_DIFFICULTY_CSV_ENV_BY_PAIR,
    resolve_corrected_learner_difficulty_csv_path,
)
from lexishift_core.srs.topic_overlay import (  # noqa: E402
    resolve_preview_profile_topic_overlay,
)

REPORT_SCHEMA_VERSION = 1
DEFAULT_JSON_OUT = PROJECT_ROOT / "docs" / "test_outputs" / "srs_e2e_pipeline_readiness_latest.json"
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_e2e_pipeline_readiness_latest.md"
)

PAIR_CONFIGS = {
    "en-ja": {
        "resource_dir": "en_ja",
        "difficulty_csv": PROJECT_ROOT
        / "core"
        / "lexishift_core"
        / "resources"
        / "srs"
        / "en_ja"
        / "learner_difficulty_corrected.csv",
        "topic_overlay": PROJECT_ROOT
        / "core"
        / "lexishift_core"
        / "resources"
        / "srs"
        / "en_ja"
        / "topic_overlays"
        / "srs_topic_autotag_promotion_overlay_en_ja_latest.json",
        "canonical_topic_overlay": PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "srs_topic_autotag_promotion_overlay_en_ja_latest.json",
        "sample_pack": PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "srs_admission_random_ux_sample_pack_en_ja_latest.json",
        "resolver_topic": "computing_internet",
        "min_difficulty_rows": 70000,
        "min_runtime_topic_rows": 700,
        "min_runtime_topics": 10,
    },
    "en-es": {
        "resource_dir": "en_es",
        "difficulty_csv": PROJECT_ROOT
        / "core"
        / "lexishift_core"
        / "resources"
        / "srs"
        / "en_es"
        / "learner_difficulty_corrected.csv",
        "topic_overlay": PROJECT_ROOT
        / "core"
        / "lexishift_core"
        / "resources"
        / "srs"
        / "en_es"
        / "topic_overlays"
        / "srs_topic_reviewed_overlay_merged_en_es_latest.json",
        "canonical_topic_overlay": PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "srs_topic_reviewed_overlay_merged_en_es_latest.json",
        "sample_pack": PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "srs_admission_random_ux_sample_pack_en_es_latest.json",
        "resolver_topic": "animals",
        "min_difficulty_rows": 40000,
        "min_runtime_topic_rows": 2000,
        "min_runtime_topics": 15,
    },
    "en-de": {
        "resource_dir": "en_de",
        "difficulty_csv": PROJECT_ROOT
        / "core"
        / "lexishift_core"
        / "resources"
        / "srs"
        / "en_de"
        / "learner_difficulty_corrected.csv",
        "topic_overlay": PROJECT_ROOT
        / "core"
        / "lexishift_core"
        / "resources"
        / "srs"
        / "en_de"
        / "topic_overlays"
        / "srs_topic_reviewed_overlay_merged_en_de_latest.json",
        "canonical_topic_overlay": PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "srs_topic_reviewed_overlay_merged_en_de_latest.json",
        "sample_pack": PROJECT_ROOT
        / "docs"
        / "test_outputs"
        / "srs_admission_random_ux_sample_pack_en_de_latest.json",
        "resolver_topic": "animals",
        "min_difficulty_rows": 60000,
        "min_runtime_topic_rows": 1200,
        "min_runtime_topics": 15,
    },
}


def main() -> int:
    args = parse_args()
    report = build_report()
    write_report(
        report,
        json_out=Path(args.json_out).expanduser().resolve(strict=False),
        markdown_out=Path(args.markdown_out).expanduser().resolve(strict=False),
    )
    summary = report["summary"]
    print(
        "summary: "
        f"status={summary['status']} pass={summary['pass_count']} "
        f"warn={summary['warn_count']} fail={summary['fail_count']}"
    )
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    return 1 if summary["fail_count"] else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check pre-runtime SRS E2E pipeline readiness for final LP data."
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def build_report() -> dict[str, Any]:
    pair_reports = {}
    findings: list[dict[str, Any]] = []
    for pair, config in PAIR_CONFIGS.items():
        pair_report = build_pair_report(pair, config)
        pair_reports[pair] = pair_report
        findings.extend(pair_report["findings"])

    srs_quality = inspect_srs_quality()
    findings.extend(srs_quality["findings"])
    summary = summarize_findings(findings)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "pairs": pair_reports,
        "srs_quality": srs_quality,
        "findings": findings,
    }


def build_pair_report(pair: str, config: Mapping[str, object]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    difficulty = inspect_difficulty_csv(pair, config)
    findings.extend(difficulty["findings"])
    topic_overlay = inspect_topic_overlay(pair, config)
    findings.extend(topic_overlay["findings"])
    resolver = inspect_resolvers(pair, config)
    findings.extend(resolver["findings"])
    sample_pack = inspect_sample_pack(pair, config)
    findings.extend(sample_pack["findings"])
    return {
        "difficulty": without_findings(difficulty),
        "topic_overlay": without_findings(topic_overlay),
        "resolver": without_findings(resolver),
        "sample_pack": without_findings(sample_pack),
        "findings": findings,
    }


def inspect_difficulty_csv(pair: str, config: Mapping[str, object]) -> dict[str, Any]:
    path = Path(config["difficulty_csv"])
    min_rows = int(config["min_difficulty_rows"])
    findings: list[dict[str, Any]] = []
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "findings": [
                finding(
                    "FAIL", pair, "DIFFICULTY_CSV_MISSING", "Packaged difficulty CSV is missing."
                )
            ],
        }

    rows = load_csv_rows(path)
    scores = [safe_float(row.get("score")) for row in rows]
    valid_scores = [value for value in scores if value is not None and 0.0 <= value <= 1.0]
    resolved_path = resolve_packaged_difficulty_path(pair)
    if len(rows) >= min_rows and len(valid_scores) == len(rows):
        findings.append(
            finding(
                "PASS",
                pair,
                "DIFFICULTY_CSV_READY",
                "Packaged difficulty CSV exists and has valid 0..1 scores.",
                f"rows={len(rows)} min_required={min_rows}",
            )
        )
    else:
        findings.append(
            finding(
                "FAIL",
                pair,
                "DIFFICULTY_CSV_INVALID",
                "Packaged difficulty CSV row count or score range is invalid.",
                f"rows={len(rows)} valid_scores={len(valid_scores)} min_required={min_rows}",
            )
        )
    if resolved_path == path.resolve(strict=False):
        findings.append(
            finding(
                "PASS",
                pair,
                "DIFFICULTY_RESOLVER_PACKAGED",
                "Default difficulty resolver chooses the packaged CSV.",
                str(resolved_path),
            )
        )
    else:
        findings.append(
            finding(
                "FAIL",
                pair,
                "DIFFICULTY_RESOLVER_NOT_PACKAGED",
                "Default difficulty resolver did not choose the packaged CSV.",
                f"resolved={resolved_path} expected={path}",
            )
        )
    return {
        "path": str(path),
        "exists": True,
        "row_count": len(rows),
        "score_min": min(valid_scores) if valid_scores else None,
        "score_max": max(valid_scores) if valid_scores else None,
        "first_lemma": rows[0].get("lemma") if rows else None,
        "last_lemma": rows[-1].get("lemma") if rows else None,
        "resolved_default_path": str(resolved_path) if resolved_path else None,
        "findings": findings,
    }


def resolve_packaged_difficulty_path(pair: str) -> Path | None:
    env_names = tuple(CORRECTED_LEARNER_DIFFICULTY_CSV_ENV_BY_PAIR.values())
    previous = {name: os.environ.get(name) for name in env_names}
    try:
        for name in env_names:
            os.environ.pop(name, None)
        resolved = resolve_corrected_learner_difficulty_csv_path(language_pair=pair)
        return resolved.resolve(strict=False) if resolved else None
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def inspect_topic_overlay(pair: str, config: Mapping[str, object]) -> dict[str, Any]:
    path = Path(config["topic_overlay"])
    canonical = Path(config["canonical_topic_overlay"])
    min_rows = int(config["min_runtime_topic_rows"])
    min_topics = int(config["min_runtime_topics"])
    findings: list[dict[str, Any]] = []
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "findings": [
                finding("FAIL", pair, "TOPIC_OVERLAY_MISSING", "Packaged topic overlay is missing.")
            ],
        }
    payload = load_json_object(path)
    rows = mapping_rows(payload.get("rows"))
    runtime_rows = [
        row
        for row in rows
        if str(row.get("language_pair") or "").strip() == pair
        and (safe_float(row.get("membership")) or 0.0) >= 1.0
        and not bool(row.get("runtime_excluded"))
    ]
    topics = sorted({str(row.get("topic") or "") for row in runtime_rows if row.get("topic")})
    lemmas = {
        str(row.get("lemma") or "").strip()
        for row in runtime_rows
        if str(row.get("lemma") or "").strip()
    }
    if (
        payload.get("status") == "ok"
        and len(runtime_rows) >= min_rows
        and len(topics) >= min_topics
    ):
        findings.append(
            finding(
                "PASS",
                pair,
                "TOPIC_OVERLAY_READY",
                "Packaged topic overlay is ready for runtime topic preferences.",
                f"runtime_rows={len(runtime_rows)} topics={len(topics)}",
            )
        )
    else:
        findings.append(
            finding(
                "FAIL",
                pair,
                "TOPIC_OVERLAY_INVALID",
                "Packaged topic overlay status, row count, or topic coverage is invalid.",
                (
                    f"status={payload.get('status')} runtime_rows={len(runtime_rows)} "
                    f"min_rows={min_rows} topics={len(topics)} min_topics={min_topics}"
                ),
            )
        )
    if canonical.exists() and path.read_bytes() == canonical.read_bytes():
        findings.append(
            finding(
                "PASS",
                pair,
                "TOPIC_OVERLAY_MATCHES_CANONICAL",
                "Packaged topic overlay matches the latest canonical test-output artifact.",
            )
        )
    else:
        findings.append(
            finding(
                "WARN",
                pair,
                "TOPIC_OVERLAY_CANONICAL_MISMATCH",
                "Packaged topic overlay does not byte-match the canonical test-output artifact.",
                f"packaged={path} canonical={canonical}",
            )
        )
    return {
        "path": str(path),
        "exists": True,
        "status": payload.get("status"),
        "overlay_id": payload.get("overlay_id"),
        "row_count": len(rows),
        "runtime_row_count": len(runtime_rows),
        "runtime_lemma_count": len(lemmas),
        "runtime_topic_count": len(topics),
        "runtime_topic_counts": dict(
            sorted(Counter(str(row.get("topic") or "") for row in runtime_rows).items())
        ),
        "canonical_path": str(canonical),
        "byte_matches_canonical": canonical.exists()
        and path.read_bytes() == canonical.read_bytes(),
        "findings": findings,
    }


def inspect_resolvers(pair: str, config: Mapping[str, object]) -> dict[str, Any]:
    topic = str(config["resolver_topic"])
    resource_dir = str(config["resource_dir"])
    with tempfile.TemporaryDirectory(prefix="lexishift-e2e-resolver-") as tmp:
        root = Path(tmp)
        paths = SimpleNamespace(srs_dir=root / "srs", data_root=root / "data")
        payload, diagnostics = resolve_preview_profile_topic_overlay(
            paths,
            pair=pair,
            profile_context={"interests": [topic]},
        )
    source_path = str(diagnostics.get("source_path") or "")
    expected_fragment = f"core/lexishift_core/resources/srs/{resource_dir}/topic_overlays/"
    findings: list[dict[str, Any]] = []
    if payload and diagnostics.get("status") == "active" and expected_fragment in source_path:
        findings.append(
            finding(
                "PASS",
                pair,
                "TOPIC_RESOLVER_PACKAGED_FALLBACK",
                "Topic overlay resolver falls back to packaged resources when helper overlays are absent.",
                source_path,
            )
        )
    else:
        findings.append(
            finding(
                "FAIL",
                pair,
                "TOPIC_RESOLVER_NOT_PACKAGED",
                "Topic overlay resolver did not use packaged resources in an empty helper root.",
                json.dumps(diagnostics, ensure_ascii=False, sort_keys=True),
            )
        )
    return {
        "requested_topic": topic,
        "status": diagnostics.get("status"),
        "overlay_id": diagnostics.get("overlay_id"),
        "source_path": source_path,
        "diagnostics": diagnostics,
        "findings": findings,
    }


def inspect_sample_pack(pair: str, config: Mapping[str, object]) -> dict[str, Any]:
    path = Path(config["sample_pack"])
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "findings": [
                finding(
                    "FAIL",
                    pair,
                    "ADMISSION_SAMPLE_PACK_MISSING",
                    "Admission UX sample pack artifact is missing.",
                )
            ],
        }
    payload = load_json_object(path)
    summary = dict(payload.get("summary") or {})
    status = str(summary.get("status") or "")
    warn_count = int(summary.get("warn_count") or 0)
    fail_count = int(summary.get("fail_count") or 0)
    topic_count = int(summary.get("topic_scenario_count") or 0)
    mover_count = int(summary.get("topic_scenarios_with_movers") or 0)
    findings: list[dict[str, Any]] = []
    if status == "PASS" and warn_count == 0 and fail_count == 0:
        findings.append(
            finding(
                "PASS",
                pair,
                "ADMISSION_SAMPLE_PACK_PASS",
                "Admission UX sample pack is passing.",
                f"draws={summary.get('draw_count_total')}",
            )
        )
    else:
        findings.append(
            finding(
                "FAIL",
                pair,
                "ADMISSION_SAMPLE_PACK_NOT_PASSING",
                "Admission UX sample pack is not passing.",
                json.dumps(summary, ensure_ascii=False, sort_keys=True),
            )
        )
    if topic_count > 0 and mover_count == topic_count:
        findings.append(
            finding(
                "PASS",
                pair,
                "ADMISSION_TOPIC_MOVERS_PRESENT",
                "Every topic-profile sample scenario produced topic-driven movement.",
                f"{mover_count}/{topic_count}",
            )
        )
    else:
        findings.append(
            finding(
                "FAIL",
                pair,
                "ADMISSION_TOPIC_MOVERS_MISSING",
                "Some topic-profile sample scenarios did not produce topic-driven movement.",
                f"{mover_count}/{topic_count}",
            )
        )
    return {
        "path": str(path),
        "exists": True,
        "generated_at": payload.get("generated_at"),
        "summary": summary,
        "inputs": payload.get("inputs") or {},
        "findings": findings,
    }


def inspect_srs_quality() -> dict[str, Any]:
    path = PROJECT_ROOT / "docs" / "test_outputs" / "srs_quality_latest.json"
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "findings": [
                finding("FAIL", None, "SRS_QUALITY_MISSING", "SRS quality artifact is missing.")
            ],
        }
    payload = load_json_object(path)
    summary = dict(payload.get("summary") or {})
    supported_pairs = [str(pair) for pair in payload.get("supported_pairs") or []]
    expected_pairs = sorted(PAIR_CONFIGS)
    findings: list[dict[str, Any]] = []
    if summary.get("status") == "PASS" and int(summary.get("fail_count") or 0) == 0:
        findings.append(
            finding(
                "PASS",
                None,
                "SRS_QUALITY_PASS",
                "SRS quality harness is passing.",
                json.dumps(summary, ensure_ascii=False, sort_keys=True),
            )
        )
    else:
        findings.append(
            finding(
                "FAIL",
                None,
                "SRS_QUALITY_NOT_PASSING",
                "SRS quality harness is not passing.",
                json.dumps(summary, ensure_ascii=False, sort_keys=True),
            )
        )
    if sorted(supported_pairs) == expected_pairs:
        findings.append(
            finding(
                "PASS",
                None,
                "SRS_QUALITY_ALL_PAIRS",
                "SRS quality harness covers all final LPs.",
                ",".join(supported_pairs),
            )
        )
    else:
        findings.append(
            finding(
                "FAIL",
                None,
                "SRS_QUALITY_PAIR_GAP",
                "SRS quality harness does not cover all final LPs.",
                f"supported={supported_pairs} expected={expected_pairs}",
            )
        )
    return {
        "path": str(path),
        "exists": True,
        "summary": summary,
        "supported_pairs": supported_pairs,
        "findings": findings,
    }


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def safe_float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def finding(
    level: str,
    pair: str | None,
    code: str,
    message: str,
    details: str | None = None,
) -> dict[str, object]:
    return {
        "level": level,
        "pair": pair,
        "code": code,
        "message": message,
        "details": details,
    }


def summarize_findings(findings: Sequence[Mapping[str, object]]) -> dict[str, object]:
    counts = Counter(str(item.get("level") or "").upper() for item in findings)
    fail_count = int(counts.get("FAIL", 0))
    warn_count = int(counts.get("WARN", 0))
    pass_count = int(counts.get("PASS", 0))
    return {
        "status": "FAIL" if fail_count else "WARN" if warn_count else "PASS",
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
    }


def without_findings(value: Mapping[str, object]) -> dict[str, object]:
    return {key: item for key, item in value.items() if key != "findings"}


def write_report(report: Mapping[str, object], *, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_markdown(report), encoding="utf-8")


def render_markdown(report: Mapping[str, object]) -> str:
    summary = dict(report.get("summary") or {})
    lines = [
        "# SRS E2E Pipeline Readiness",
        "",
        f"- Status: {summary.get('status')}",
        (
            f"- Findings: pass={summary.get('pass_count')} "
            f"warn={summary.get('warn_count')} fail={summary.get('fail_count')}"
        ),
        "",
        "## Pair Readiness",
        "",
    ]
    pairs = dict(report.get("pairs") or {})
    for pair in sorted(pairs):
        pair_report = dict(pairs[pair])
        difficulty = dict(pair_report.get("difficulty") or {})
        overlay = dict(pair_report.get("topic_overlay") or {})
        resolver = dict(pair_report.get("resolver") or {})
        sample = dict(pair_report.get("sample_pack") or {})
        sample_summary = dict(sample.get("summary") or {})
        lines.extend(
            [
                f"### {pair}",
                (
                    f"- Difficulty rows: `{difficulty.get('row_count')}` "
                    f"score range `{difficulty.get('score_min')}`-`{difficulty.get('score_max')}`"
                ),
                (
                    f"- Topic overlay: `{overlay.get('runtime_row_count')}` runtime rows, "
                    f"`{overlay.get('runtime_topic_count')}` topics"
                ),
                (
                    f"- Resolver source: `{resolver.get('source_path')}` "
                    f"status=`{resolver.get('status')}`"
                ),
                (
                    f"- Admission sample: `{sample_summary.get('status')}` "
                    f"draws=`{sample_summary.get('draw_count_total')}` "
                    "topic movers="
                    f"`{sample_summary.get('topic_scenarios_with_movers')}`/"
                    f"`{sample_summary.get('topic_scenario_count')}`"
                ),
                "",
            ]
        )
    srs_quality = dict(report.get("srs_quality") or {})
    lines.extend(
        [
            "## SRS Quality",
            "",
            f"- Summary: `{dict(srs_quality.get('summary') or {})}`",
            f"- Supported pairs: `{', '.join(str(pair) for pair in srs_quality.get('supported_pairs') or [])}`",
            "",
            "## Findings",
            "",
        ]
    )
    for item in report.get("findings") or []:
        row = dict(item)
        lines.append(
            f"- `{row.get('level')}` `{row.get('code')}`"
            + (f" `{row.get('pair')}`" if row.get("pair") else "")
            + f": {row.get('message')}"
        )
        if row.get("details"):
            lines.append(f"  - {row.get('details')}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
