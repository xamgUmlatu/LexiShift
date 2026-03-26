#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Mapping, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCRIPT = PROJECT_ROOT / "scripts" / "testing" / "rulegen_benchmark.py"
BUNDLE_VERSION = 1


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return dict(payload)


def _parse_csv_strings(text: Optional[str]) -> list[str]:
    return [item.strip() for item in str(text or "").split(",") if item.strip()]


def _compute_file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if not chunk:
                break
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _copy_file_into_bundle(*, source: Path, bundle_dir: Path, relative_path: Path) -> str:
    destination = bundle_dir / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return str(relative_path.as_posix())


def _resolve_git_head() -> Optional[str]:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def _select_pairs(
    *,
    report_payload: Mapping[str, object],
    pair_filter: Optional[set[str]],
) -> list[str]:
    raw_pairs = report_payload.get("pairs")
    if not isinstance(raw_pairs, Mapping):
        raise ValueError("Benchmark report is missing `pairs`.")
    pair_names = []
    for raw_pair in raw_pairs:
        pair = str(raw_pair or "").strip()
        if not pair:
            continue
        if pair_filter and pair not in pair_filter:
            continue
        pair_names.append(pair)
    if not pair_names:
        raise ValueError("No benchmark-report pairs matched the requested filter.")
    return sorted(pair_names)


def _extract_preset_payload(report_payload: Mapping[str, object]) -> dict[str, object]:
    raw_sweep = report_payload.get("sweep")
    if not isinstance(raw_sweep, Mapping):
        raise ValueError("Benchmark report is missing `sweep` metadata.")
    raw_preset = raw_sweep.get("preset")
    if not isinstance(raw_preset, Mapping):
        raise ValueError(
            "Portable bundle export currently requires a preset-backed benchmark artifact."
        )
    name = str(raw_preset.get("name") or "").strip()
    description = str(raw_preset.get("description") or "").strip()
    raw_args = raw_preset.get("args")
    if not name or not description or not isinstance(raw_args, Sequence):
        raise ValueError("Benchmark preset metadata is incomplete in the source artifact.")
    args = [str(item) for item in raw_args]
    if not args:
        raise ValueError("Benchmark preset metadata is missing argv tokens.")
    payload: dict[str, object] = {
        "name": name,
        "description": description,
        "args": args,
    }
    preset_file = str(raw_preset.get("preset_file") or "").strip()
    if preset_file:
        payload["preset_file"] = preset_file
    return payload


def _build_bundle_resource_manifest(
    *,
    bundle_dir: Path,
    pair: str,
    pair_report: Mapping[str, object],
) -> dict[str, object]:
    raw_resources = pair_report.get("resources")
    if not isinstance(raw_resources, Mapping):
        raise ValueError(f"Benchmark report pair `{pair}` is missing `resources`.")
    resource_manifest: dict[str, object] = {
        "checksums": dict(raw_resources.get("checksums") or {}),
    }
    for key in ("jmdict_path", "translation_dict_path", "reverse_translation_dict_path"):
        raw_source = str(raw_resources.get(key) or "").strip()
        if not raw_source:
            resource_manifest[key] = None
            continue
        source_path = Path(raw_source)
        if not source_path.exists():
            raise FileNotFoundError(
                f"Bundle export source file not found for {pair} {key}: {source_path}"
            )
        relative_path = Path("resources") / pair / source_path.name
        resource_manifest[key] = _copy_file_into_bundle(
            source=source_path,
            bundle_dir=bundle_dir,
            relative_path=relative_path,
        )
    return resource_manifest


def export_bundle(
    *,
    benchmark_json: Path,
    output_dir: Path,
    pair_filter: Optional[set[str]],
    force: bool,
) -> Path:
    report_payload = _load_json_object(benchmark_json)
    pair_names = _select_pairs(report_payload=report_payload, pair_filter=pair_filter)
    preset_payload = _extract_preset_payload(report_payload)

    if output_dir.exists():
        if not force:
            raise FileExistsError(f"Bundle output already exists: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = Path(str(report_payload.get("dataset_path") or "").strip())
    if not dataset_path.exists():
        raise FileNotFoundError(f"Benchmark dataset not found: {dataset_path}")
    dataset_rel = Path("inputs") / dataset_path.name
    dataset_bundle_path = _copy_file_into_bundle(
        source=dataset_path,
        bundle_dir=output_dir,
        relative_path=dataset_rel,
    )

    source_report_rel = Path("source") / benchmark_json.name
    source_report_bundle_path = _copy_file_into_bundle(
        source=benchmark_json,
        bundle_dir=output_dir,
        relative_path=source_report_rel,
    )

    preset_registry_path = str(preset_payload.get("preset_file") or "").strip()
    preset_registry_relpath: Optional[str] = None
    if preset_registry_path:
        preset_registry_source = Path(preset_registry_path)
        if preset_registry_source.exists():
            preset_registry_rel = Path("inputs") / preset_registry_source.name
            preset_registry_relpath = _copy_file_into_bundle(
                source=preset_registry_source,
                bundle_dir=output_dir,
                relative_path=preset_registry_rel,
            )

    raw_pairs = report_payload.get("pairs")
    assert isinstance(raw_pairs, Mapping)
    snapshot_payload: dict[str, object] = {"pairs": {}}
    pair_manifests: dict[str, object] = {}
    for pair in pair_names:
        pair_report = raw_pairs.get(pair)
        if not isinstance(pair_report, Mapping):
            raise ValueError(f"Benchmark report pair `{pair}` is missing.")
        snapshot_payload["pairs"][pair] = dict(pair_report.get("word_package_snapshot") or {})
        pair_manifests[pair] = {
            "case_count": int(pair_report.get("case_count") or 0),
            "resources": _build_bundle_resource_manifest(
                bundle_dir=output_dir,
                pair=pair,
                pair_report=pair_report,
            ),
        }

    snapshot_rel = Path("inputs") / "word_package_snapshots.json"
    snapshot_path = output_dir / snapshot_rel
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(snapshot_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manifest = {
        "bundle_version": BUNDLE_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": _resolve_git_head(),
        "benchmark_json_source": str(benchmark_json),
        "source_benchmark_json": source_report_bundle_path,
        "dataset_path": dataset_bundle_path,
        "word_package_snapshot_path": str(snapshot_rel.as_posix()),
        "pair_names": pair_names,
        "profile_id": str(report_payload.get("profile_id") or ""),
        "preset": {
            **preset_payload,
            "preset_file": preset_registry_relpath,
        },
        "pairs": pair_manifests,
    }
    manifest_path = output_dir / "bundle_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def _load_bundle_manifest(bundle_dir: Path) -> dict[str, object]:
    manifest_path = bundle_dir / "bundle_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Bundle manifest not found: {manifest_path}")
    payload = _load_json_object(manifest_path)
    version = int(payload.get("bundle_version") or 0)
    if version != BUNDLE_VERSION:
        raise ValueError(f"Unsupported bundle version {version}; expected {BUNDLE_VERSION}.")
    return payload


def validate_bundle(bundle_dir: Path) -> dict[str, object]:
    manifest = _load_bundle_manifest(bundle_dir)
    dataset_path = bundle_dir / str(manifest.get("dataset_path") or "")
    snapshot_path = bundle_dir / str(manifest.get("word_package_snapshot_path") or "")
    if not dataset_path.exists():
        raise FileNotFoundError(f"Bundle dataset not found: {dataset_path}")
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Bundle word-package snapshot not found: {snapshot_path}")
    raw_pairs = manifest.get("pairs")
    if not isinstance(raw_pairs, Mapping):
        raise ValueError("Bundle manifest is missing `pairs`.")
    for pair, raw_pair_manifest in raw_pairs.items():
        if not isinstance(raw_pair_manifest, Mapping):
            continue
        raw_resources = raw_pair_manifest.get("resources")
        if not isinstance(raw_resources, Mapping):
            raise ValueError(f"Bundle manifest pair `{pair}` is missing `resources`.")
        checksums = raw_resources.get("checksums")
        checksum_map = checksums if isinstance(checksums, Mapping) else {}
        for resource_key, checksum_key in (
            ("jmdict_path", "jmdict_sha256"),
            ("translation_dict_path", "translation_dict_sha256"),
            ("reverse_translation_dict_path", "reverse_translation_dict_sha256"),
        ):
            relpath = str(raw_resources.get(resource_key) or "").strip()
            if not relpath:
                continue
            resource_path = bundle_dir / relpath
            if not resource_path.exists():
                raise FileNotFoundError(
                    f"Bundle resource missing for pair `{pair}` {resource_key}: {resource_path}"
                )
            expected_checksum = str(checksum_map.get(checksum_key) or "").strip()
            if expected_checksum:
                actual_checksum = _compute_file_sha256(resource_path)
                if actual_checksum != expected_checksum:
                    raise ValueError(
                        f"Bundle checksum mismatch for pair `{pair}` {resource_key}: "
                        f"expected {expected_checksum}, got {actual_checksum}"
                    )
    return manifest


def _set_once(mapping: dict[str, str], *, key: str, value: str) -> None:
    existing = mapping.get(key)
    if existing is None:
        mapping[key] = value
        return
    if existing != value:
        raise ValueError(f"Conflicting bundle override for {key}: {existing} vs {value}")


def _build_resource_override_args(
    *,
    bundle_dir: Path,
    manifest: Mapping[str, object],
    selected_pairs: Sequence[str],
) -> list[str]:
    raw_pairs = manifest.get("pairs")
    assert isinstance(raw_pairs, Mapping)
    overrides: dict[str, str] = {}
    for pair in selected_pairs:
        raw_pair_manifest = raw_pairs.get(pair)
        if not isinstance(raw_pair_manifest, Mapping):
            continue
        raw_resources = raw_pair_manifest.get("resources")
        if not isinstance(raw_resources, Mapping):
            continue
        jmdict_rel = str(raw_resources.get("jmdict_path") or "").strip()
        if jmdict_rel:
            _set_once(overrides, key="--jmdict", value=str(bundle_dir / jmdict_rel))
        translation_rel = str(raw_resources.get("translation_dict_path") or "").strip()
        reverse_rel = str(raw_resources.get("reverse_translation_dict_path") or "").strip()
        if pair == "en-de" and translation_rel:
            _set_once(
                overrides,
                key="--translation-dict-en-de",
                value=str(bundle_dir / translation_rel),
            )
        if pair == "en-es":
            if translation_rel:
                _set_once(
                    overrides,
                    key="--translation-dict-en-es",
                    value=str(bundle_dir / translation_rel),
                )
            if reverse_rel:
                _set_once(
                    overrides,
                    key="--translation-dict-es-en",
                    value=str(bundle_dir / reverse_rel),
                )
        if pair == "es-en":
            if translation_rel:
                _set_once(
                    overrides,
                    key="--translation-dict-es-en",
                    value=str(bundle_dir / translation_rel),
                )
            if reverse_rel:
                _set_once(
                    overrides,
                    key="--translation-dict-en-es",
                    value=str(bundle_dir / reverse_rel),
                )
    argv: list[str] = []
    for key in (
        "--jmdict",
        "--translation-dict-en-de",
        "--translation-dict-en-es",
        "--translation-dict-es-en",
    ):
        value = overrides.get(key)
        if value is None:
            continue
        argv.extend([key, value])
    return argv


def build_bundle_run_argv(
    *,
    bundle_dir: Path,
    manifest: Mapping[str, object],
    selected_pairs: Sequence[str],
    json_output: Path,
    markdown_output: Path,
    html_output: Path,
) -> list[str]:
    raw_preset = manifest.get("preset")
    if not isinstance(raw_preset, Mapping):
        raise ValueError("Bundle manifest is missing preset metadata.")
    raw_args = raw_preset.get("args")
    if not isinstance(raw_args, Sequence):
        raise ValueError("Bundle manifest preset is missing argv tokens.")
    dataset_path = bundle_dir / str(manifest.get("dataset_path") or "")
    snapshot_path = bundle_dir / str(manifest.get("word_package_snapshot_path") or "")
    argv = [str(item) for item in raw_args]
    argv.extend(["--dataset", str(dataset_path)])
    argv.extend(["--pairs", ",".join(selected_pairs)])
    argv.extend(["--word-package-snapshot-json", str(snapshot_path)])
    argv.extend(
        _build_resource_override_args(
            bundle_dir=bundle_dir,
            manifest=manifest,
            selected_pairs=selected_pairs,
        )
    )
    argv.extend(["--json-output", str(json_output)])
    argv.extend(["--markdown-output", str(markdown_output)])
    argv.extend(["--html-output", str(html_output)])
    return argv


def run_bundle(
    *,
    bundle_dir: Path,
    pair_filter: Optional[set[str]],
    json_output: Path,
    markdown_output: Path,
    html_output: Path,
    dry_run: bool,
) -> list[str]:
    manifest = validate_bundle(bundle_dir)
    manifest_pairs = [str(item) for item in manifest.get("pair_names") or [] if str(item)]
    selected_pairs = sorted(pair_filter) if pair_filter else manifest_pairs
    if not selected_pairs:
        raise ValueError("Bundle manifest does not contain any runnable pairs.")
    argv = build_bundle_run_argv(
        bundle_dir=bundle_dir,
        manifest=manifest,
        selected_pairs=selected_pairs,
        json_output=json_output,
        markdown_output=markdown_output,
        html_output=html_output,
    )
    if dry_run:
        print("python3 scripts/testing/rulegen_benchmark.py " + " ".join(argv))
        return argv
    subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), *argv],
        cwd=PROJECT_ROOT,
        check=True,
    )
    return argv


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export and rerun portable rulegen benchmark bundles."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a portable benchmark bundle.")
    export_parser.add_argument("--benchmark-json", type=Path, required=True)
    export_parser.add_argument("--output-dir", type=Path, required=True)
    export_parser.add_argument("--pairs", help="Optional comma-separated pair filter.")
    export_parser.add_argument("--force", action="store_true")

    run_parser = subparsers.add_parser("run", help="Run the benchmark from a portable bundle.")
    run_parser.add_argument("--bundle-dir", type=Path, required=True)
    run_parser.add_argument("--pairs", help="Optional comma-separated pair filter.")
    run_parser.add_argument(
        "--json-output",
        type=Path,
        required=True,
    )
    run_parser.add_argument(
        "--markdown-output",
        type=Path,
        required=True,
    )
    run_parser.add_argument(
        "--html-output",
        type=Path,
        required=True,
    )
    run_parser.add_argument("--dry-run", action="store_true")

    validate_parser = subparsers.add_parser(
        "validate", help="Validate bundle file presence and resource checksums."
    )
    validate_parser.add_argument("--bundle-dir", type=Path, required=True)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "export":
        manifest_path = export_bundle(
            benchmark_json=args.benchmark_json,
            output_dir=args.output_dir,
            pair_filter={item.lower() for item in _parse_csv_strings(args.pairs)} or None,
            force=bool(args.force),
        )
        print(f"bundle_manifest: {manifest_path}")
        return

    if args.command == "run":
        argv_used = run_bundle(
            bundle_dir=args.bundle_dir,
            pair_filter={item.lower() for item in _parse_csv_strings(args.pairs)} or None,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
            html_output=args.html_output,
            dry_run=bool(args.dry_run),
        )
        if args.dry_run:
            print(f"argv_tokens: {len(argv_used)}")
        else:
            print(f"bundle_dir: {args.bundle_dir}")
            print(f"json_output: {args.json_output}")
            print(f"markdown_output: {args.markdown_output}")
            print(f"html_output: {args.html_output}")
        return

    if args.command == "validate":
        manifest = validate_bundle(args.bundle_dir)
        print(f"bundle_dir: {args.bundle_dir}")
        print(f"pairs: {','.join(str(item) for item in manifest.get('pair_names') or [])}")
        return

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
