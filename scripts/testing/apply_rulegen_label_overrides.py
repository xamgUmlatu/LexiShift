#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping


def _normalize_phrase(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return " ".join(text.split())


def _normalize_unique(values: object) -> list[str]:
    if not isinstance(values, list):
        values = list(values) if values is not None else []
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        phrase = _normalize_phrase(value)
        if not phrase or phrase in seen:
            continue
        seen.add(phrase)
        normalized.append(phrase)
    return normalized


def _ensure_list_field(case: dict[str, object], key: str) -> list[str]:
    values = _normalize_unique(case.get(key, []))
    case[key] = values
    return values


def _remove_phrase(values: list[str], phrase: str) -> None:
    while phrase in values:
        values.remove(phrase)


def _add_phrase(values: list[str], phrase: str) -> None:
    if phrase and phrase not in values:
        values.append(phrase)


def _resolve_case(
    *,
    case_index: Mapping[tuple[str, str], dict[str, object]],
    target_index: Mapping[tuple[str, str], dict[str, object]],
    pair: str,
    case_id: str,
    target: str,
) -> dict[str, object] | None:
    if case_id:
        hit = case_index.get((pair, case_id))
        if hit is not None:
            return hit
    if target:
        return target_index.get((pair, target))
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Apply rulegen label overrides (exported from rulegen benchmark HTML) to benchmark dataset cases."
        )
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("docs/test_inputs/rulegen_benchmark_cases.json"),
        help="Benchmark dataset JSON to update.",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        required=True,
        help="Label overrides JSON exported from the HTML dashboard.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path. Default: <dataset stem>_updated.json beside dataset.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write updates back to --dataset path.",
    )
    args = parser.parse_args()

    if args.in_place and args.output is not None:
        raise ValueError("Use either --in-place or --output, not both.")

    dataset_payload = json.loads(args.dataset.read_text(encoding="utf-8"))
    if not isinstance(dataset_payload, dict):
        raise ValueError(f"Dataset must be a JSON object: {args.dataset}")
    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError(f"Dataset missing `cases` list: {args.dataset}")

    labels_payload = json.loads(args.labels.read_text(encoding="utf-8"))
    if not isinstance(labels_payload, dict):
        raise ValueError(f"Labels payload must be a JSON object: {args.labels}")
    label_cases = labels_payload.get("cases")
    if not isinstance(label_cases, list):
        raise ValueError(f"Labels payload missing `cases` list: {args.labels}")

    case_index: dict[tuple[str, str], dict[str, object]] = {}
    target_index: dict[tuple[str, str], dict[str, object]] = {}
    for case in raw_cases:
        if not isinstance(case, dict):
            continue
        pair = str(case.get("pair") or "").strip().lower()
        case_id = str(case.get("case_id") or case.get("id") or "").strip()
        target = str(case.get("target") or "").strip()
        if pair and case_id:
            case_index[(pair, case_id)] = case
        if pair and target:
            target_index.setdefault((pair, target), case)

    touched_cases = 0
    resolved_cases = 0
    skipped_cases = 0
    decisions_applied = 0
    decisions_ignored = 0

    for entry in label_cases:
        if not isinstance(entry, dict):
            continue
        pair = str(entry.get("pair") or "").strip().lower()
        case_id = str(entry.get("case_id") or "").strip()
        target = str(entry.get("target") or "").strip()
        decisions = entry.get("decisions")
        if not pair or not isinstance(decisions, dict):
            continue

        case = _resolve_case(
            case_index=case_index,
            target_index=target_index,
            pair=pair,
            case_id=case_id,
            target=target,
        )
        if case is None:
            skipped_cases += 1
            continue

        resolved_cases += 1
        expected_any = _ensure_list_field(case, "expected_any")
        expected_top1_any = _ensure_list_field(case, "expected_top1_any")
        forbidden_top1 = _ensure_list_field(case, "forbidden_top1")
        forbidden_any = _ensure_list_field(case, "forbidden_any")
        applied_in_case = 0

        for raw_phrase, raw_label in decisions.items():
            phrase = _normalize_phrase(raw_phrase)
            label = str(raw_label or "").strip().lower()
            if not phrase or label not in {"green", "black", "neutral"}:
                decisions_ignored += 1
                continue

            if label == "green":
                _add_phrase(expected_any, phrase)
                _remove_phrase(forbidden_top1, phrase)
                _remove_phrase(forbidden_any, phrase)
            elif label == "black":
                _add_phrase(forbidden_any, phrase)
                _remove_phrase(expected_any, phrase)
                _remove_phrase(expected_top1_any, phrase)
            else:
                _remove_phrase(expected_any, phrase)
                _remove_phrase(expected_top1_any, phrase)
                _remove_phrase(forbidden_top1, phrase)
                _remove_phrase(forbidden_any, phrase)
            applied_in_case += 1
            decisions_applied += 1

        if applied_in_case > 0:
            touched_cases += 1

        case["expected_any"] = _normalize_unique(expected_any)
        case["expected_top1_any"] = _normalize_unique(expected_top1_any)
        case["forbidden_top1"] = _normalize_unique(forbidden_top1)
        case["forbidden_any"] = _normalize_unique(forbidden_any)

    if args.in_place:
        output_path = args.dataset
    elif args.output is not None:
        output_path = args.output
    else:
        output_path = args.dataset.with_name(f"{args.dataset.stem}_updated{args.dataset.suffix}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dataset_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"dataset: {args.dataset}")
    print(f"labels: {args.labels}")
    print(f"output: {output_path}")
    print(f"cases_total: {len(raw_cases)}")
    print(f"cases_resolved: {resolved_cases}")
    print(f"cases_touched: {touched_cases}")
    print(f"cases_skipped: {skipped_cases}")
    print(f"decisions_applied: {decisions_applied}")
    print(f"decisions_ignored: {decisions_ignored}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"error: {exc}") from exc
