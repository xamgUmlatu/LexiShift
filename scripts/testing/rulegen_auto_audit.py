#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from rulegen_reverse_profiles import REVERSE_CHECK_PROFILES


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "test_outputs"
BENCHMARKABLE_PAIRS = ("en-es", "en-ja", "en-de", "es-en")

PAIR_PATH_HINTS: dict[str, tuple[str, ...]] = {
    "en-es": (
        "en_es.py",
        "en-es",
        "rulegen_benchmark_en_es",
    ),
    "en-ja": (
        "en_ja.py",
        "en-ja",
        "rulegen_benchmark_en_ja",
        "jmdict",
    ),
    "en-de": (
        "en_de.py",
        "en-de",
        "rulegen_benchmark_en_de",
    ),
    "es-en": (
        "es_en.py",
        "es-en",
        "rulegen_benchmark_es_en",
    ),
}

GENERIC_QUALITY_PATH_PREFIXES: tuple[str, ...] = (
    "core/lexishift_core/rulegen/",
    "core/lexishift_core/pos/",
    "core/lexishift_core/resources/dict_loaders.py",
    "core/lexishift_core/helper/rulegen.py",
    "core/lexishift_core/helper/use_cases/rulegen_job.py",
    "core/tests/rulegen/",
    "docs/rulegen/",
    "docs/test_inputs/rulegen_",
    "scripts/testing/rulegen_benchmark.py",
    "scripts/testing/rulegen_quality_gate.py",
    "scripts/testing/rulegen_quality_gate_",
    "scripts/testing/rulegen_benchmark_triage.py",
)

META_ONLY_PATH_PREFIXES: tuple[str, ...] = (
    "scripts/testing/rulegen_pair_audit_cycle.py",
    "scripts/testing/rulegen_auto_audit.py",
    "docs/developer/",
)


def _print_command(command: list[str]) -> None:
    print(f"+ {shlex.join(command)}")


def _run_capture(command: list[str]) -> list[str]:
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _run_command(command: list[str]) -> int:
    _print_command(command)
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
    )
    return int(result.returncode)


def _parse_pairs(raw: str | None) -> list[str]:
    if raw is None:
        return []
    requested = []
    seen: set[str] = set()
    for part in str(raw).split(","):
        pair = part.strip().lower()
        if not pair or pair in seen:
            continue
        seen.add(pair)
        requested.append(pair)
    return requested


def _collect_changed_files(base_ref: str | None) -> list[str]:
    changed: set[str] = set()
    git_commands: list[list[str]] = []
    if base_ref:
        git_commands.append(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD"]
        )
    git_commands.extend(
        [
            ["git", "diff", "--name-only", "--diff-filter=ACMR"],
            ["git", "diff", "--name-only", "--cached", "--diff-filter=ACMR"],
            ["git", "ls-files", "--others", "--exclude-standard"],
        ]
    )
    for command in git_commands:
        for path in _run_capture(command):
            normalized = path.replace("\\", "/").strip()
            if normalized:
                changed.add(normalized)
    return sorted(changed)


def _infer_pairs(changed_files: list[str]) -> list[str]:
    if not changed_files:
        return []
    pairs: set[str] = set()
    generic_quality_change = False
    for path in changed_files:
        normalized = path.replace("\\", "/")
        if normalized.startswith(META_ONLY_PATH_PREFIXES):
            continue
        matched_pair = False
        for pair, hints in PAIR_PATH_HINTS.items():
            if any(hint in normalized for hint in hints):
                pairs.add(pair)
                matched_pair = True
        if matched_pair:
            continue
        if normalized.startswith(GENERIC_QUALITY_PATH_PREFIXES):
            generic_quality_change = True
    if generic_quality_change:
        return [pair for pair in BENCHMARKABLE_PAIRS]
    return [pair for pair in BENCHMARKABLE_PAIRS if pair in pairs]


def _artifact_stems(pair_suffix: str) -> dict[str, str]:
    suffix = f"_{pair_suffix}" if pair_suffix else ""
    return {
        "benchmark": f"rulegen_benchmark{suffix}",
        "triage": f"rulegen_benchmark_triage{suffix}",
        "quality_gate": f"rulegen_quality_gate{suffix}",
        "manifest": f"rulegen_auto_audit{suffix}",
    }


def _build_artifact_paths(
    *, output_dir: Path, pair_suffix: str, date_stamp: str
) -> dict[str, Path]:
    stems = _artifact_stems(pair_suffix)
    return {
        "benchmark_json_dated": output_dir / f"{stems['benchmark']}_{date_stamp}.json",
        "benchmark_md_dated": output_dir / f"{stems['benchmark']}_{date_stamp}.md",
        "benchmark_html_dated": output_dir / f"{stems['benchmark']}_{date_stamp}.html",
        "triage_json_dated": output_dir / f"{stems['triage']}_{date_stamp}.json",
        "triage_md_dated": output_dir / f"{stems['triage']}_{date_stamp}.md",
        "quality_gate_json_dated": output_dir / f"{stems['quality_gate']}_{date_stamp}.json",
        "manifest_json_dated": output_dir / f"{stems['manifest']}_{date_stamp}.json",
        "benchmark_json_latest": output_dir / f"{stems['benchmark']}_latest.json",
        "benchmark_md_latest": output_dir / f"{stems['benchmark']}_latest.md",
        "benchmark_html_latest": output_dir / f"{stems['benchmark']}_latest.html",
        "triage_json_latest": output_dir / f"{stems['triage']}_latest.json",
        "triage_md_latest": output_dir / f"{stems['triage']}_latest.md",
        "quality_gate_json_latest": output_dir / f"{stems['quality_gate']}_latest.json",
        "manifest_json_latest": output_dir / f"{stems['manifest']}_latest.json",
    }


def _copy_latest_aliases(paths: dict[str, Path]) -> None:
    alias_pairs = (
        ("benchmark_json_dated", "benchmark_json_latest"),
        ("benchmark_md_dated", "benchmark_md_latest"),
        ("benchmark_html_dated", "benchmark_html_latest"),
        ("triage_json_dated", "triage_json_latest"),
        ("triage_md_dated", "triage_md_latest"),
        ("quality_gate_json_dated", "quality_gate_json_latest"),
        ("manifest_json_dated", "manifest_json_latest"),
    )
    for source_key, latest_key in alias_pairs:
        source = paths[source_key]
        target = paths[latest_key]
        if not source.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _write_manifest(
    path: Path,
    *,
    pairs: list[str],
    pair_source: str,
    base_ref: str | None,
    changed_files: list[str],
    reverse_check_profile: str,
    command: list[str],
    artifacts: dict[str, Path],
) -> None:
    payload = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_ref": base_ref,
        "pairs": pairs,
        "pair_source": pair_source,
        "changed_files": changed_files,
        "reverse_check_profile": reverse_check_profile,
        "command": command,
        "artifacts": {key: str(value) for key, value in artifacts.items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Infer touched rulegen pairs from git changes, run the focused audit loop, "
            "and manage dated plus latest artifact aliases."
        )
    )
    parser.add_argument(
        "--pairs",
        help="Optional comma-separated pairs. If omitted, infer from changed files.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git base ref used for changed-file inference (default: origin/main).",
    )
    parser.add_argument(
        "--date-stamp",
        default=datetime.now().date().isoformat(),
        help="Date stamp appended to artifact filenames (default: today in local time).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for dated and latest audit artifacts.",
    )
    parser.add_argument(
        "--reverse-check-profile",
        choices=tuple(REVERSE_CHECK_PROFILES.keys()),
        default="default",
        help="Preset for reverse-check sweep values.",
    )
    parser.add_argument("--max-definitions-values", default="3")
    parser.add_argument("--max-rules-values", default="none,1")
    parser.add_argument("--confidence-threshold-values", default="0.0,0.05")
    parser.add_argument("--semantic-demotion-scale-values", default="1.0")
    parser.add_argument("--include-variants-values", default="false")
    parser.add_argument("--pos-scoring-values", default="true,false")
    parser.add_argument("--score-weight-pos-values", default="0.0,0.1")
    parser.add_argument("--top-runs", type=int, default=20)
    parser.add_argument("--max-configurations", type=int, default=100)
    parser.add_argument(
        "--strict-gate",
        action="store_true",
        help="Exit non-zero if the quality gate fails.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print inferred pairs, artifacts, and command without executing the audit loop.",
    )
    parser.add_argument(
        "--no-latest-alias",
        action="store_true",
        help="Do not copy dated artifacts to the corresponding *_latest aliases.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    changed_files = _collect_changed_files(args.base_ref)
    explicit_pairs = _parse_pairs(args.pairs)
    pairs = explicit_pairs or _infer_pairs(changed_files)
    pair_source = "explicit" if explicit_pairs else "auto"

    if not pairs:
        print("No rulegen-impacting pairs inferred from changed files.")
        print("Use --pairs en-es,en-ja,... to run the audit explicitly.")
        if changed_files:
            print("changed_files:")
            for path in changed_files:
                print(f"  - {path}")
        return

    pair_suffix = "_".join(pair.replace("-", "_") for pair in pairs)
    artifacts = _build_artifact_paths(
        output_dir=args.output_dir,
        pair_suffix=pair_suffix,
        date_stamp=args.date_stamp,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    reverse_profile = REVERSE_CHECK_PROFILES[args.reverse_check_profile]
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "testing" / "rulegen_pair_audit_cycle.py"),
        "--pairs",
        ",".join(pairs),
        "--max-definitions-values",
        str(args.max_definitions_values),
        "--max-rules-values",
        str(args.max_rules_values),
        "--confidence-threshold-values",
        str(args.confidence_threshold_values),
        "--semantic-demotion-scale-values",
        str(args.semantic_demotion_scale_values),
        "--include-variants-values",
        str(args.include_variants_values),
        "--pos-scoring-values",
        str(args.pos_scoring_values),
        "--score-weight-pos-values",
        str(args.score_weight_pos_values),
        "--reverse-check-enabled-values",
        reverse_profile["enabled_values"],
        "--reverse-check-match-bonus-values",
        reverse_profile["match_bonus_values"],
        "--reverse-check-near-bonus-values",
        reverse_profile["near_bonus_values"],
        "--reverse-check-near-rank-max-values",
        reverse_profile["near_rank_max_values"],
        "--reverse-check-far-hit-penalty-values",
        reverse_profile["far_hit_penalty_values"],
        "--reverse-check-miss-penalty-values",
        reverse_profile["miss_penalty_values"],
        "--top-runs",
        str(int(args.top_runs)),
        "--max-configurations",
        str(int(args.max_configurations)),
        "--benchmark-json",
        str(artifacts["benchmark_json_dated"]),
        "--benchmark-markdown",
        str(artifacts["benchmark_md_dated"]),
        "--benchmark-html",
        str(artifacts["benchmark_html_dated"]),
        "--quality-gate-json",
        str(artifacts["quality_gate_json_dated"]),
        "--triage-json",
        str(artifacts["triage_json_dated"]),
        "--triage-markdown",
        str(artifacts["triage_md_dated"]),
    ]
    if args.strict_gate:
        command.append("--strict-gate")

    print(f"pairs ({pair_source}): {', '.join(pairs)}")
    if changed_files:
        print(f"changed_files_count: {len(changed_files)}")
    print(f"date_stamp: {args.date_stamp}")
    print(f"output_dir: {args.output_dir}")
    print(f"reverse_check_profile: {args.reverse_check_profile}")
    print("dated_artifacts:")
    for key in (
        "benchmark_json_dated",
        "benchmark_md_dated",
        "benchmark_html_dated",
        "quality_gate_json_dated",
        "triage_json_dated",
        "triage_md_dated",
        "manifest_json_dated",
    ):
        print(f"  - {key}: {artifacts[key]}")

    if args.dry_run:
        _print_command(command)
        return

    rc = _run_command(command)
    if rc != 0:
        raise SystemExit(rc)

    _write_manifest(
        artifacts["manifest_json_dated"],
        pairs=pairs,
        pair_source=pair_source,
        base_ref=args.base_ref,
        changed_files=changed_files,
        reverse_check_profile=args.reverse_check_profile,
        command=command,
        artifacts=artifacts,
    )

    if not args.no_latest_alias:
        _copy_latest_aliases(artifacts)
        print("latest_aliases_updated: yes")
    else:
        print("latest_aliases_updated: no")

    print(f"manifest_json: {artifacts['manifest_json_dated']}")


if __name__ == "__main__":
    main()
