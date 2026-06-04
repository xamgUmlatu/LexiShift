#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.pair_resources import resolve_pair_translation_packs  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths, resolve_data_root  # noqa: E402
from lexishift_core.helper.translation_packs import TranslationPackRef  # noqa: E402
from lexishift_core.resources.dict_loaders import (  # noqa: E402
    load_translation_gloss_records_by_translation_ordered,
    load_translation_gloss_records_ordered,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    BenchmarkShadowTarget,
    build_benchmark_shadow_targets,
    build_en_es_shadow_inventory,
)
from rulegen_benchmark_dataset import load_benchmark_dataset_payload  # noqa: E402


DEFAULT_DATASET_PATH = (
    PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases" / "en_es.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_shadow_inventory_en_es_latest.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an en-es shadow inventory from reviewed rulegen benchmark triggers and "
            "installed forward/reverse translation packs."
        )
    )
    parser.add_argument(
        "--benchmark-dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Benchmark dataset JSON to mine reviewed trigger phrases from.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(resolve_data_root()),
        help="LexiShift data root (default: helper resolve_data_root()).",
    )
    parser.add_argument(
        "--translation-dict",
        type=Path,
        default=None,
        help="Optional explicit forward translation pack path for en-es.",
    )
    parser.add_argument(
        "--reverse-translation-dict",
        type=Path,
        default=None,
        help="Optional explicit reverse translation pack path for en-es.",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Optional benchmark target filter. Repeat to include multiple targets.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Output Markdown artifact path.",
    )
    return parser.parse_args()


def _build_pack_record(pack: TranslationPackRef | None) -> dict[str, object] | None:
    if pack is None:
        return None
    return {
        "path": str(pack.path),
        "exists": pack.path.exists(),
        "provider": pack.provider,
        "pack_id": pack.pack_id,
        "direction": pack.direction,
    }


def _collect_cases(dataset_payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_cases = dataset_payload.get("cases")
    if not isinstance(raw_cases, Sequence) or isinstance(raw_cases, (str, bytes)):
        raise ValueError("Benchmark dataset is missing a `cases` list.")
    return [dict(case) for case in raw_cases if isinstance(case, Mapping)]


def _collect_reviewed_triggers(targets: Sequence[BenchmarkShadowTarget]) -> list[str]:
    seen: dict[str, None] = {}
    for target in targets:
        for trigger in target.reviewed_triggers:
            seen.setdefault(trigger, None)
    return list(seen.keys())


def _build_report(
    *,
    dataset_payload: Mapping[str, object],
    benchmark_targets: Sequence[BenchmarkShadowTarget],
    data_root: Path,
    forward_pack: TranslationPackRef | None,
    reverse_pack: TranslationPackRef | None,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    missing_resources: list[str] = []
    if forward_pack is None or not forward_pack.path.exists():
        missing_resources.append("forward_translation_pack")
    if reverse_pack is None or not reverse_pack.path.exists():
        missing_resources.append("reverse_translation_pack")
    report: dict[str, object] = {
        "schema_version": 1,
        "pair": "en-es",
        "generated_at": generated_at,
        "status": "missing_resources" if missing_resources else "ok",
        "benchmark_dataset": {
            "path": str(Path(str(dataset_payload.get("source_files", [DEFAULT_DATASET_PATH])[0]))),
            "target_count": len(benchmark_targets),
            "reviewed_trigger_count": sum(
                len(target.reviewed_triggers) for target in benchmark_targets
            ),
            "targets": [target.target for target in benchmark_targets],
        },
        "resource_status": {
            "data_root": str(data_root),
            "forward_pack": _build_pack_record(forward_pack),
            "reverse_pack": _build_pack_record(reverse_pack),
            "missing_resources": missing_resources,
        },
    }
    if missing_resources:
        report["inventory"] = None
        return report

    forward_records_by_target = load_translation_gloss_records_ordered(
        forward_pack.path,
        target_lang="en",
        headwords=[target.target for target in benchmark_targets],
    )
    reverse_records_by_source = load_translation_gloss_records_ordered(
        reverse_pack.path,
        target_lang="es",
        headwords=_collect_reviewed_triggers(benchmark_targets),
    )
    target_reverse_records_by_target = load_translation_gloss_records_by_translation_ordered(
        reverse_pack.path,
        translations=[target.target for target in benchmark_targets],
    )
    report["inventory"] = build_en_es_shadow_inventory(
        benchmark_targets=benchmark_targets,
        forward_records_by_target=forward_records_by_target,
        reverse_records_by_source=reverse_records_by_source,
        target_reverse_records_by_target=target_reverse_records_by_target,
        forward_provider=forward_pack.provider,
        reverse_provider=reverse_pack.provider,
    )
    return report


def _render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# en-es Semantic Shadow Inventory",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
    ]
    benchmark_dataset = report.get("benchmark_dataset")
    if isinstance(benchmark_dataset, Mapping):
        lines.extend(
            [
                f"- Benchmark targets: `{benchmark_dataset.get('target_count', 0)}`",
                f"- Reviewed triggers: `{benchmark_dataset.get('reviewed_trigger_count', 0)}`",
            ]
        )
    resource_status = report.get("resource_status")
    if isinstance(resource_status, Mapping):
        lines.extend(
            [
                f"- Data root: `{resource_status.get('data_root', '')}`",
                "",
                "## Resources",
            ]
        )
        for label in ("forward_pack", "reverse_pack"):
            pack = resource_status.get(label)
            if isinstance(pack, Mapping):
                lines.append(
                    f"- `{label}`: `{pack.get('path', '')}` (`exists={pack.get('exists', False)}`, provider=`{pack.get('provider', '')}`)"
                )
            else:
                lines.append(f"- `{label}`: missing")
        missing = resource_status.get("missing_resources")
        if isinstance(missing, Sequence) and not isinstance(missing, (str, bytes)) and missing:
            lines.extend(
                [
                    "",
                    "## Missing Resources",
                    *(f"- `{item}`" for item in missing),
                ]
            )
    inventory = report.get("inventory")
    if not isinstance(inventory, Mapping):
        return "\n".join(lines) + "\n"

    summary = inventory.get("summary")
    if isinstance(summary, Mapping):
        lines.extend(
            [
                "",
                "## Summary",
                f"- Triggers scanned: `{summary.get('trigger_count', 0)}`",
                f"- Triggers with active candidates: `{summary.get('triggers_with_active_candidates', 0)}`",
                f"- Triggers with shadow candidates: `{summary.get('triggers_with_shadow_candidates', 0)}`",
                (
                    "- Triggers with promoted shadow candidates: "
                    f"`{summary.get('triggers_with_promoted_shadow_candidates', 0)}`"
                ),
            ]
        )
    targets = inventory.get("targets")
    if isinstance(targets, Sequence) and not isinstance(targets, (str, bytes)):
        lines.extend(["", "## Promotion Preview"])
        preview_count = 0
        for target_row in targets:
            if not isinstance(target_row, Mapping):
                continue
            target = str(target_row.get("target") or "").strip()
            trigger_entries = target_row.get("trigger_entries")
            if not isinstance(trigger_entries, Sequence) or isinstance(
                trigger_entries, (str, bytes)
            ):
                continue
            for trigger_entry in trigger_entries:
                if not isinstance(trigger_entry, Mapping):
                    continue
                promoted = trigger_entry.get("promoted_shadow_candidates")
                if (
                    not isinstance(promoted, Sequence)
                    or isinstance(promoted, (str, bytes))
                    or not promoted
                ):
                    continue
                trigger = str(trigger_entry.get("trigger") or "").strip()
                shadow_targets = [
                    str(candidate.get("target") or "").strip()
                    for candidate in promoted
                    if isinstance(candidate, Mapping) and str(candidate.get("target") or "").strip()
                ]
                if not shadow_targets:
                    continue
                lines.append(f"- `{target}` / `{trigger}` -> `{', '.join(shadow_targets)}`")
                preview_count += 1
                if preview_count >= 20:
                    break
            if preview_count >= 20:
                break
        if preview_count == 0:
            lines.append("- No promoted shadow candidates yet.")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parse_args()
    dataset_payload = load_benchmark_dataset_payload(args.benchmark_dataset)
    benchmark_targets = build_benchmark_shadow_targets(
        _collect_cases(dataset_payload),
        targets=args.target,
    )
    helper_paths = build_helper_paths(args.data_root)
    forward_pack, reverse_pack = resolve_pair_translation_packs(
        helper_paths,
        pair="en-es",
        translation_dict_path=args.translation_dict,
        reverse_translation_dict_path=args.reverse_translation_dict,
    )
    report = _build_report(
        dataset_payload=dataset_payload,
        benchmark_targets=benchmark_targets,
        data_root=Path(args.data_root).expanduser().resolve(strict=False),
        forward_pack=forward_pack,
        reverse_pack=reverse_pack,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
