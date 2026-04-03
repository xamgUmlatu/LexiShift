from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Mapping, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_DIR = PROJECT_ROOT / "core"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Dataset payload must be an object: {path}")
    return dict(payload)


def _normalize_pair(value: object) -> str:
    return str(value or "").strip().lower()


def _resolve_dataset_source_files(path: Path) -> list[Path]:
    resolved = path.resolve()
    if resolved.is_dir():
        files = sorted(
            child.resolve()
            for child in resolved.iterdir()
            if child.is_file() and child.suffix.lower() == ".json"
        )
        if not files:
            raise ValueError(f"Dataset directory has no JSON files: {resolved}")
        return files
    if resolved.is_file():
        return [resolved]
    raise FileNotFoundError(f"Benchmark dataset not found: {resolved}")


def _normalize_dataset_cases(
    raw_cases: Sequence[object],
    *,
    default_pair: str,
) -> tuple[list[object], set[str]]:
    normalized_cases: list[object] = []
    seen_pairs: set[str] = set()
    for raw_case in raw_cases:
        if not isinstance(raw_case, Mapping):
            normalized_cases.append(raw_case)
            continue
        normalized_case = dict(raw_case)
        pair = _normalize_pair(normalized_case.get("pair") or default_pair)
        if pair:
            normalized_case["pair"] = pair
            seen_pairs.add(pair)
        normalized_cases.append(normalized_case)
    return normalized_cases, seen_pairs


def load_benchmark_dataset_payload(path: Path) -> dict[str, object]:
    source_path = path.resolve()
    source_files = _resolve_dataset_source_files(source_path)
    if len(source_files) == 1 and source_files[0] == source_path and source_path.is_file():
        payload = _load_json_object(source_path)
        raw_cases = payload.get("cases")
        if not isinstance(raw_cases, Sequence):
            raise ValueError(f"Dataset is missing `cases` list: {source_path}")
        default_pair = _normalize_pair(payload.get("pair"))
        normalized_cases, seen_pairs = _normalize_dataset_cases(
            raw_cases,
            default_pair=default_pair,
        )
        normalized_payload = dict(payload)
        normalized_payload["cases"] = normalized_cases
        if default_pair:
            normalized_payload["pair"] = default_pair
        normalized_payload["source_layout"] = "file"
        normalized_payload["source_files"] = [str(source_path)]
        normalized_payload["pairs"] = sorted(seen_pairs)
        return normalized_payload

    merged_cases: list[object] = []
    pairs: set[str] = set()
    for source_file in source_files:
        payload = _load_json_object(source_file)
        raw_cases = payload.get("cases")
        if not isinstance(raw_cases, Sequence):
            raise ValueError(f"Dataset is missing `cases` list: {source_file}")
        default_pair = _normalize_pair(payload.get("pair"))
        normalized_cases, seen_pairs = _normalize_dataset_cases(
            raw_cases,
            default_pair=default_pair,
        )
        merged_cases.extend(normalized_cases)
        pairs.update(seen_pairs)

    return {
        "version": 1,
        "name": "LexiShift Rulegen Benchmark Cases",
        "description": ("Merged rulegen benchmark dataset loaded from LP-specific source files."),
        "source_layout": "directory",
        "source_directory": str(source_path),
        "source_files": [str(source_file) for source_file in source_files],
        "pairs": sorted(pairs),
        "cases": merged_cases,
    }


def load_benchmark_dataset(
    path: Path,
    *,
    pair_filter: Optional[set[str]],
) -> tuple[dict[str, object], dict[str, list[object]]]:
    from lexishift_core.rulegen.benchmarking import RulegenBenchmarkCase

    payload = load_benchmark_dataset_payload(path)
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, Sequence):
        raise ValueError(f"Dataset is missing `cases` list: {path}")

    by_pair: dict[str, list[RulegenBenchmarkCase]] = {}
    for index, raw_case in enumerate(raw_cases):
        if not isinstance(raw_case, Mapping):
            continue
        case = RulegenBenchmarkCase.from_mapping(raw_case, index=index)
        if not case.pair or not case.target:
            continue
        if pair_filter and case.pair not in pair_filter:
            continue
        by_pair.setdefault(case.pair, []).append(case)
    return payload, by_pair


def materialize_benchmark_dataset(
    *,
    source_path: Path,
    output_path: Path,
    pair_filter: Optional[set[str]] = None,
) -> Path:
    payload = load_benchmark_dataset_payload(source_path)
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, Sequence):
        raise ValueError(f"Dataset is missing `cases` list: {source_path}")

    if pair_filter:
        filtered_cases = [
            case
            for case in raw_cases
            if isinstance(case, Mapping)
            and _normalize_pair(case.get("pair")) in {item.strip().lower() for item in pair_filter}
        ]
        payload = dict(payload)
        payload["cases"] = filtered_cases
        payload["pairs"] = sorted(
            {
                _normalize_pair(case.get("pair"))
                for case in filtered_cases
                if isinstance(case, Mapping)
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
