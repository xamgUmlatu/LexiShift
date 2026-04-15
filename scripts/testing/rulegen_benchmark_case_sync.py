#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AGGREGATE_PATH = PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases.json"
DEFAULT_SPLIT_DIR = PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases"
MANIFEST_FILENAME = "manifest.json"


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return dict(payload)


def _pair_filename(pair: str) -> str:
    normalized = str(pair or "").strip().lower()
    if not normalized:
        raise ValueError("Pair name cannot be empty.")
    return f"{normalized.replace('-', '_')}.json"


def _pair_display_name(pair: str) -> str:
    return str(pair or "").strip().lower()


def _format_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT).as_posix())
    except ValueError:
        return str(resolved.as_posix())


def split_aggregate_to_pair_files(
    *,
    aggregate_path: Path = DEFAULT_AGGREGATE_PATH,
    split_dir: Path = DEFAULT_SPLIT_DIR,
) -> Path:
    payload = _load_json_object(aggregate_path)
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, Sequence):
        raise ValueError(f"Aggregate dataset is missing `cases`: {aggregate_path}")

    pair_order: list[str] = []
    cases_by_pair: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
    for raw_case in raw_cases:
        if not isinstance(raw_case, Mapping):
            continue
        case = dict(raw_case)
        pair = str(case.get("pair") or "").strip().lower()
        if not pair:
            continue
        if pair not in cases_by_pair:
            cases_by_pair[pair] = []
            pair_order.append(pair)
        cases_by_pair[pair].append(case)

    split_dir.mkdir(parents=True, exist_ok=True)
    aggregate_metadata = {key: value for key, value in payload.items() if key != "cases"}
    manifest: dict[str, object] = {
        "version": 1,
        "aggregate_path": _format_path(aggregate_path),
        "aggregate_metadata": aggregate_metadata,
        "pair_order": pair_order,
        "pairs": {},
    }

    for pair in pair_order:
        pair_cases = cases_by_pair[pair]
        filename = _pair_filename(pair)
        pair_payload = {
            "version": aggregate_metadata.get("version", 1),
            "pair": pair,
            "name": f"LexiShift Rulegen Benchmark Cases ({_pair_display_name(pair)})",
            "description": (
                f"Pair-local development benchmark cases for {pair}. "
                "Refresh the compatibility aggregate with "
                "`python scripts/testing/rulegen_benchmark_case_sync.py merge` after edits."
            ),
            "source_aggregate": _format_path(aggregate_path),
            "breadth": aggregate_metadata.get("breadth"),
            "case_count": len(pair_cases),
            "cases": pair_cases,
        }
        pair_path = split_dir / filename
        pair_path.write_text(
            json.dumps(pair_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest["pairs"][pair] = {
            "file": filename,
            "case_count": len(pair_cases),
        }

    manifest_path = split_dir / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def merge_pair_files_to_aggregate(
    *,
    split_dir: Path = DEFAULT_SPLIT_DIR,
    aggregate_path: Path = DEFAULT_AGGREGATE_PATH,
) -> Path:
    manifest_path = split_dir / MANIFEST_FILENAME
    manifest = _load_json_object(manifest_path)
    aggregate_metadata = manifest.get("aggregate_metadata")
    if not isinstance(aggregate_metadata, Mapping):
        raise ValueError(f"Manifest is missing aggregate_metadata: {manifest_path}")
    raw_pair_order = manifest.get("pair_order")
    if not isinstance(raw_pair_order, Sequence):
        raise ValueError(f"Manifest is missing pair_order: {manifest_path}")
    raw_pairs = manifest.get("pairs")
    if not isinstance(raw_pairs, Mapping):
        raise ValueError(f"Manifest is missing pairs: {manifest_path}")

    merged_cases: list[dict[str, object]] = []
    for raw_pair in raw_pair_order:
        pair = str(raw_pair or "").strip().lower()
        if not pair:
            continue
        raw_pair_meta = raw_pairs.get(pair)
        if not isinstance(raw_pair_meta, Mapping):
            raise ValueError(f"Manifest pair metadata is missing for {pair}: {manifest_path}")
        filename = str(raw_pair_meta.get("file") or "").strip()
        if not filename:
            raise ValueError(f"Manifest pair file is missing for {pair}: {manifest_path}")
        pair_path = split_dir / filename
        pair_payload = _load_json_object(pair_path)
        raw_cases = pair_payload.get("cases")
        if not isinstance(raw_cases, Sequence):
            raise ValueError(f"Pair dataset is missing `cases`: {pair_path}")
        for raw_case in raw_cases:
            if not isinstance(raw_case, Mapping):
                continue
            merged_cases.append(dict(raw_case))

    aggregate_payload = dict(aggregate_metadata)
    aggregate_payload["cases"] = merged_cases
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_path.write_text(
        json.dumps(aggregate_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return aggregate_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Split the aggregate benchmark dataset into pair-local development files, "
            "or rebuild the aggregate from those pair-local files."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    split_parser = subparsers.add_parser("split", help="Split aggregate dataset into pair files.")
    split_parser.add_argument("--aggregate", type=Path, default=DEFAULT_AGGREGATE_PATH)
    split_parser.add_argument("--split-dir", type=Path, default=DEFAULT_SPLIT_DIR)

    merge_parser = subparsers.add_parser(
        "merge",
        help="Merge pair-local dataset files back into the compatibility aggregate.",
    )
    merge_parser.add_argument("--split-dir", type=Path, default=DEFAULT_SPLIT_DIR)
    merge_parser.add_argument("--aggregate", type=Path, default=DEFAULT_AGGREGATE_PATH)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "split":
        manifest_path = split_aggregate_to_pair_files(
            aggregate_path=args.aggregate,
            split_dir=args.split_dir,
        )
        print(f"manifest_path: {manifest_path}")
        return

    if args.command == "merge":
        aggregate_path = merge_pair_files_to_aggregate(
            split_dir=args.split_dir,
            aggregate_path=args.aggregate,
        )
        print(f"aggregate_path: {aggregate_path}")
        return

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
