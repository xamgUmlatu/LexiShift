#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time
from typing import Any, Sequence
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "core"))

from lexishift_core.helper.yomitan_lookup_dictionaries import (  # noqa: E402
    YomitanDictionaryImportCancelled,
    import_yomitan_dictionary_zip,
    lookup_yomitan_dictionary,
)


DEFAULT_JSON_OUT = REPO_ROOT / "docs/test_outputs/dictionary/yomitan_performance_latest.json"
DEFAULT_MARKDOWN_OUT = REPO_ROOT / "docs/test_outputs/dictionary/yomitan_performance_latest.md"


def write_synthetic_yomitan_archive(
    path: Path,
    *,
    bank_count: int,
    terms_per_bank: int,
) -> tuple[str, ...]:
    """Write a deterministic, redistributable Yomitan format-3 term dictionary."""
    if bank_count < 2:
        raise ValueError("bank_count must be at least 2 so cancellation can be exercised.")
    if terms_per_bank < 1:
        raise ValueError("terms_per_bank must be at least 1.")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    targets: list[str] = []
    total_terms = bank_count * terms_per_bank
    target_indexes = {0, total_terms // 2, total_terms - 1}
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "index.json",
            json.dumps(
                {
                    "title": "LexiShift Synthetic Performance Dictionary",
                    "revision": "1",
                    "format": 3,
                    "author": "LexiShift test tooling",
                    "sourceLanguage": "en",
                    "targetLanguage": "en",
                    "description": "Generated performance fixture; contains no third-party data.",
                },
                separators=(",", ":"),
            ),
        )
        for bank_index in range(bank_count):
            rows: list[list[object]] = []
            for row_index in range(terms_per_bank):
                sequence = bank_index * terms_per_bank + row_index
                expression = f"synthetic-{sequence:08d}"
                if sequence in target_indexes:
                    targets.append(expression)
                rows.append(
                    [
                        expression,
                        "",
                        "common" if sequence % 17 == 0 else "",
                        "n",
                        1000 - (sequence % 1000),
                        [f"Synthetic definition {sequence}"],
                        sequence,
                        "",
                    ]
                )
            archive.writestr(
                f"term_bank_{bank_index + 1}.json",
                json.dumps(rows, separators=(",", ":")),
            )
    return tuple(targets)


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 3)


def build_report(
    *,
    work_dir: Path,
    archive_path: Path,
    bank_count: int,
    terms_per_bank: int,
    lookup_repetitions: int,
) -> dict[str, Any]:
    work_root = Path(work_dir)
    work_root.mkdir(parents=True, exist_ok=True)
    archive = Path(archive_path)

    started = time.perf_counter()
    lookup_targets = write_synthetic_yomitan_archive(
        archive,
        bank_count=bank_count,
        terms_per_bank=terms_per_bank,
    )
    generation_ms = _elapsed_ms(started)

    dictionaries_dir = work_root / "installed"
    progress_events: list[tuple[int, int]] = []
    started = time.perf_counter()
    imported = import_yomitan_dictionary_zip(
        archive,
        dictionaries_dir=dictionaries_dir,
        progress=lambda current, total: progress_events.append((current, total)),
    )
    import_ms = _elapsed_ms(started)

    started = time.perf_counter()
    repeated = import_yomitan_dictionary_zip(
        archive,
        dictionaries_dir=dictionaries_dir,
    )
    repeat_import_ms = _elapsed_ms(started)

    lookup_times_ms: list[float] = []
    lookup_failures: list[str] = []
    repetitions = max(1, int(lookup_repetitions))
    for index in range(repetitions):
        target = lookup_targets[index % len(lookup_targets)]
        started = time.perf_counter()
        result = lookup_yomitan_dictionary(
            imported.artifact_path,
            lookup_candidates=(target,),
            surface=target,
            reading="",
            sense_limit=4,
            gloss_limit=8,
        )
        lookup_times_ms.append(_elapsed_ms(started))
        if result is None:
            lookup_failures.append(target)

    cancellation_dir = work_root / "cancelled"
    cancel_requested = False

    def request_cancel_after_first_bank(_current: int, _total: int) -> None:
        nonlocal cancel_requested
        cancel_requested = True

    cancellation_observed = False
    started = time.perf_counter()
    try:
        import_yomitan_dictionary_zip(
            archive,
            dictionaries_dir=cancellation_dir,
            progress=request_cancel_after_first_bank,
            should_cancel=lambda: cancel_requested,
        )
    except YomitanDictionaryImportCancelled:
        cancellation_observed = True
    cancellation_ms = _elapsed_ms(started)
    cancellation_leftovers = (
        [path.name for path in cancellation_dir.iterdir()] if cancellation_dir.exists() else []
    )

    correctness = {
        "term_count_matches": imported.dictionary.term_count == bank_count * terms_per_bank,
        "all_banks_reported": bool(progress_events)
        and progress_events[-1] == (bank_count, bank_count),
        "repeat_import_reused_pack": repeated.dictionary.pack_id == imported.dictionary.pack_id,
        "lookups_succeeded": not lookup_failures,
        "cancellation_observed": cancellation_observed,
        "cancellation_cleaned_up": not cancellation_leftovers,
    }
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "fixture": {
            "kind": "generated_yomitan_format_3",
            "bank_count": bank_count,
            "terms_per_bank": terms_per_bank,
            "term_count": bank_count * terms_per_bank,
            "archive_bytes": archive.stat().st_size,
            "third_party_data": False,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "timings_ms": {
            "fixture_generation": generation_ms,
            "initial_import": import_ms,
            "repeat_import": repeat_import_ms,
            "lookup": {
                "repetitions": repetitions,
                "median": round(statistics.median(lookup_times_ms), 3),
                "p95": _percentile(lookup_times_ms, 0.95),
                "maximum": round(max(lookup_times_ms), 3),
            },
            "cancel_after_first_bank": cancellation_ms,
        },
        "correctness": correctness,
        "diagnostics": {
            "lookup_failures": sorted(set(lookup_failures)),
            "cancellation_leftovers": cancellation_leftovers,
        },
    }


def performance_failures(report: dict[str, Any], args: argparse.Namespace) -> list[str]:
    timings = report["timings_ms"]
    lookup = timings["lookup"]
    checks = (
        ("initial_import", timings["initial_import"], args.max_import_ms),
        ("repeat_import", timings["repeat_import"], args.max_repeat_import_ms),
        ("lookup_p95", lookup["p95"], args.max_lookup_p95_ms),
        ("cancellation", timings["cancel_after_first_bank"], args.max_cancel_ms),
    )
    return [
        f"{name} {observed:.3f} ms exceeded {limit:.3f} ms"
        for name, observed, limit in checks
        if limit is not None and observed is not None and observed > limit
    ]


def render_markdown(report: dict[str, Any], *, failures: Sequence[str] = ()) -> str:
    fixture = report["fixture"]
    timings = report["timings_ms"]
    lookup = timings["lookup"]
    correctness = report["correctness"]
    lines = [
        "# Synthetic Yomitan Dictionary Performance",
        "",
        "This report uses generated, redistributable Yomitan format-3 data. "
        "Timing budgets are optional and machine-specific; correctness is reported separately.",
        "",
        "## Fixture",
        "",
        f"- Banks: {fixture['bank_count']}",
        f"- Terms: {fixture['term_count']}",
        f"- ZIP bytes: {fixture['archive_bytes']}",
        "- Third-party data: no",
        "",
        "## Timings",
        "",
        "| Operation | Time |",
        "| --- | ---: |",
        f"| Generate fixture | {timings['fixture_generation']:.3f} ms |",
        f"| Initial import and indexing | {timings['initial_import']:.3f} ms |",
        f"| Repeat import | {timings['repeat_import']:.3f} ms |",
        f"| Lookup median ({lookup['repetitions']} runs) | {lookup['median']:.3f} ms |",
        f"| Lookup p95 | {lookup['p95']:.3f} ms |",
        f"| Cancel after first bank | {timings['cancel_after_first_bank']:.3f} ms |",
        "",
        "## Correctness",
        "",
        *[
            f"- {'PASS' if value else 'FAIL'}: {name.replace('_', ' ')}"
            for name, value in correctness.items()
        ],
    ]
    if failures:
        lines.extend(("", "## Performance budget failures", ""))
        lines.extend(f"- {failure}" for failure in failures)
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure Yomitan import and lookup using generated test data."
    )
    parser.add_argument("--banks", type=int, default=8)
    parser.add_argument("--terms-per-bank", type=int, default=25_000)
    parser.add_argument("--lookup-repetitions", type=int, default=100)
    parser.add_argument("--archive-out", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--max-import-ms", type=float)
    parser.add_argument("--max-repeat-import-ms", type=float)
    parser.add_argument("--max-lookup-p95-ms", type=float)
    parser.add_argument("--max-cancel-ms", type=float)
    return parser


def _run(args: argparse.Namespace, *, work_dir: Path, archive_path: Path) -> int:
    report = build_report(
        work_dir=work_dir,
        archive_path=archive_path,
        bank_count=args.banks,
        terms_per_bank=args.terms_per_bank,
        lookup_repetitions=args.lookup_repetitions,
    )
    failures = performance_failures(report, args)
    report["performance_budget_failures"] = failures
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(
        render_markdown(report, failures=failures),
        encoding="utf-8",
    )
    correctness_failures = [name for name, passed in report["correctness"].items() if not passed]
    print(
        f"synthetic_yomitan: terms={report['fixture']['term_count']} "
        f"import_ms={report['timings_ms']['initial_import']:.3f} "
        f"lookup_p95_ms={report['timings_ms']['lookup']['p95']:.3f}"
    )
    print(f"json_output: {args.json_out}")
    print(f"markdown_output: {args.markdown_out}")
    if correctness_failures:
        print("correctness failures: " + ", ".join(correctness_failures), file=sys.stderr)
    for failure in failures:
        print(f"performance budget failure: {failure}", file=sys.stderr)
    return 1 if correctness_failures or failures else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.banks < 2 or args.terms_per_bank < 1 or args.lookup_repetitions < 1:
        raise SystemExit("banks must be >= 2 and term/lookup counts must be >= 1")
    args.json_out = args.json_out.expanduser().resolve(strict=False)
    args.markdown_out = args.markdown_out.expanduser().resolve(strict=False)
    if args.archive_out is not None:
        archive_path = args.archive_out.expanduser().resolve(strict=False)
        with tempfile.TemporaryDirectory(prefix="lexishift-yomitan-performance-") as tmp:
            return _run(args, work_dir=Path(tmp), archive_path=archive_path)
    with tempfile.TemporaryDirectory(prefix="lexishift-yomitan-performance-") as tmp:
        work_dir = Path(tmp)
        return _run(args, work_dir=work_dir, archive_path=work_dir / "synthetic.zip")


if __name__ == "__main__":
    raise SystemExit(main())
