#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "dev_workflow"
    / "experiment_payload_retention_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "dev_workflow"
    / "experiment_payload_retention_latest.md"
)
EXPERIMENTS_RELATIVE = "docs/test_outputs/experiments"
TEXT_REFERENCE_SUFFIXES = {
    ".cfg",
    ".cjs",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rst",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
EXCLUDED_REFERENCE_PREFIXES = (
    ".git/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    "apps/gui/build/",
    "apps/gui/dist/",
    "docs/_site/",
    "docs/vendor/bundle/",
    "node_modules/",
    "packaging/build/",
    "packaging/output/",
)
GENERATED_REFERENCE_EXCLUDED_PREFIXES = ("docs/test_outputs/dev_workflow/",)
MAX_REFERENCE_FILE_BYTES = 25_000_000
MAX_REFERENCE_SAMPLES = 8
MAX_LARGEST_FILES = 5
IGNORED_EXPERIMENT_FILE_NAMES = {".DS_Store", ".DS_Store?", "Thumbs.db", "desktop.ini"}


def build_experiment_payload_retention_audit(root: Path) -> dict[str, object]:
    root = root.resolve()
    experiment_root = root / EXPERIMENTS_RELATIVE
    family_specs = _family_specs(root, experiment_root)
    reference_index = _build_family_reference_index(root, family_specs)
    families = [
        _family_report(root=root, family_spec=family_spec, reference_index=reference_index)
        for family_spec in family_specs
    ]
    families.sort(
        key=lambda family: (
            _posture_sort_key(str(family["retention_posture"])),
            -int(family["total_file_bytes"]),
            str(family["family"]),
        )
    )
    summary = _summary(families)
    return {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "experiment_root": EXPERIMENTS_RELATIVE,
        "posture_definitions": _posture_definitions(),
        "summary": summary,
        "families": families,
    }


def _family_specs(root: Path, experiment_root: Path) -> list[dict[str, object]]:
    if not experiment_root.exists():
        return []
    specs: list[dict[str, object]] = []
    root_files = [
        _relative_path(root, path)
        for path in sorted(experiment_root.iterdir())
        if path.is_file() and path.name not in IGNORED_EXPERIMENT_FILE_NAMES
    ]
    if root_files:
        specs.append(
            {
                "family": "_root_files",
                "family_path": f"{EXPERIMENTS_RELATIVE}/[root_files]",
                "file_paths": root_files,
                "directory_paths": [],
                "virtual_root": True,
            }
        )
    for path in sorted(experiment_root.iterdir()):
        if not path.is_dir():
            continue
        family_path = _relative_path(root, path)
        specs.append(
            {
                "family": path.name,
                "family_path": family_path,
                "file_paths": sorted(
                    _relative_path(root, item)
                    for item in path.rglob("*")
                    if item.is_file() and item.name not in IGNORED_EXPERIMENT_FILE_NAMES
                ),
                "directory_paths": sorted(
                    _relative_path(root, item) for item in path.rglob("*") if item.is_dir()
                ),
                "virtual_root": False,
            }
        )
    return specs


def _build_family_reference_index(
    root: Path,
    family_specs: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    family_paths = [str(spec["family_path"]) for spec in family_specs]
    family_by_path = {str(spec["family_path"]): spec for spec in family_specs}
    index: dict[str, dict[str, object]] = {
        family_path: {
            "external_reference_paths": set(),
            "generated_output_reference_paths": set(),
            "other_experiment_reference_paths": set(),
            "self_family_reference_paths": set(),
            "reference_samples": [],
        }
        for family_path in family_paths
    }
    if not family_paths:
        return index
    candidate_to_family = _candidate_to_family(family_specs)
    for path in _iter_text_reference_files(root):
        relative = _relative_path(root, path)
        text = _read_text(path)
        if not text:
            continue
        for candidate, family_path in candidate_to_family.items():
            if candidate not in text:
                continue
            family_spec = family_by_path[family_path]
            bucket = _reference_bucket(
                reference_path=relative,
                candidate_path=candidate,
                family_spec=family_spec,
            )
            if bucket is None:
                continue
            refs = index[family_path][bucket]
            if isinstance(refs, set):
                refs.add(relative)
            samples = index[family_path]["reference_samples"]
            if isinstance(samples, list) and len(samples) < MAX_REFERENCE_SAMPLES:
                samples.append(
                    {
                        "reference_path": relative,
                        "referenced_path": candidate,
                        "scope": bucket.removesuffix("_reference_paths"),
                    }
                )
    return index


def _candidate_to_family(family_specs: Sequence[Mapping[str, object]]) -> dict[str, str]:
    candidates: dict[str, str] = {}
    for family_spec in family_specs:
        family_path = str(family_spec["family_path"])
        if not bool(family_spec.get("virtual_root")):
            candidates[family_path] = family_path
        for relative in _sequence(family_spec.get("directory_paths")):
            candidates[str(relative)] = family_path
        for relative in _sequence(family_spec.get("file_paths")):
            candidates[str(relative)] = family_path
    return dict(sorted(candidates.items(), key=lambda item: (-len(item[0]), item[0])))


def _reference_bucket(
    *,
    reference_path: str,
    candidate_path: str,
    family_spec: Mapping[str, object],
) -> str | None:
    if reference_path == candidate_path:
        return None
    if reference_path.startswith(f"{candidate_path}/"):
        return None
    if _is_family_member(reference_path, family_spec):
        return "self_family_reference_paths"
    if reference_path.startswith(f"{EXPERIMENTS_RELATIVE}/"):
        return "other_experiment_reference_paths"
    if reference_path.startswith("docs/test_outputs/"):
        return "generated_output_reference_paths"
    return "external_reference_paths"


def _is_family_member(reference_path: str, family_spec: Mapping[str, object]) -> bool:
    file_paths = {str(path) for path in _sequence(family_spec.get("file_paths"))}
    if reference_path in file_paths:
        return True
    if bool(family_spec.get("virtual_root")):
        return False
    family_path = str(family_spec["family_path"])
    return reference_path.startswith(f"{family_path}/")


def _family_report(
    *,
    root: Path,
    family_spec: Mapping[str, object],
    reference_index: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    family_path = str(family_spec["family_path"])
    file_paths = sorted(str(path) for path in _sequence(family_spec.get("file_paths")))
    file_sizes = [(relative, _file_size(root / relative)) for relative in file_paths]
    refs = _as_mapping(reference_index.get(family_path))
    external_refs = set(str(item) for item in _sequence(refs.get("external_reference_paths")))
    generated_refs = set(
        str(item) for item in _sequence(refs.get("generated_output_reference_paths"))
    )
    experiment_refs = set(
        str(item) for item in _sequence(refs.get("other_experiment_reference_paths"))
    )
    self_refs = set(str(item) for item in _sequence(refs.get("self_family_reference_paths")))
    posture, reason = _retention_posture(
        external_refs=external_refs,
        generated_refs=generated_refs,
        experiment_refs=experiment_refs,
        self_refs=self_refs,
    )
    flags = _family_flags(
        family_path=family_path,
        file_paths=file_paths,
        file_sizes=file_sizes,
        posture=posture,
        external_reference_count=len(external_refs),
    )
    return {
        "family": str(family_spec["family"]),
        "family_path": family_path,
        "retention_posture": posture,
        "retention_reason": reason,
        "file_count": len(file_paths),
        "directory_count": len(_sequence(family_spec.get("directory_paths"))),
        "total_file_bytes": sum(size for _, size in file_sizes),
        "extension_counts": _extension_counts(file_paths),
        "review_flags": flags,
        "largest_files": _largest_files(file_sizes),
        "external_reference_count": len(external_refs),
        "generated_output_reference_count": len(generated_refs),
        "other_experiment_reference_count": len(experiment_refs),
        "self_family_reference_count": len(self_refs),
        "external_reference_samples": sorted(external_refs)[:MAX_REFERENCE_SAMPLES],
        "generated_output_reference_samples": sorted(generated_refs)[:MAX_REFERENCE_SAMPLES],
        "other_experiment_reference_samples": sorted(experiment_refs)[:MAX_REFERENCE_SAMPLES],
        "self_family_reference_samples": sorted(self_refs)[:MAX_REFERENCE_SAMPLES],
        "reference_samples": _sequence(refs.get("reference_samples")),
    }


def _family_flags(
    *,
    family_path: str,
    file_paths: Sequence[str],
    file_sizes: Sequence[tuple[str, int]],
    posture: str,
    external_reference_count: int,
) -> list[str]:
    flags: set[str] = set()
    total_bytes = sum(size for _, size in file_sizes)
    if len(file_paths) >= 100:
        flags.add("large_file_count")
    if total_bytes >= 100_000_000:
        flags.add("large_byte_count")
    if any(path.endswith("_raw_responses.json") for path in file_paths):
        flags.add("raw_response_bundle")
    if any(path.endswith("_generated_rows.json") for path in file_paths):
        flags.add("generated_rows_bundle")
    if any("-data-root/" in path for path in file_paths):
        flags.add("install_or_runtime_fixture_root")
    if any(Path(path).name.startswith("latest") for path in file_paths):
        flags.add("latest_named_payload")
    if family_path.endswith("_batches"):
        flags.add("batch_payload_family")
    if posture == "generated_linked":
        flags.add("generated_only_route")
    if len(file_paths) >= 50 and external_reference_count <= 1:
        flags.add("large_family_low_external_refs")
    return sorted(flags)


def _retention_posture(
    *,
    external_refs: set[str],
    generated_refs: set[str],
    experiment_refs: set[str],
    self_refs: set[str],
) -> tuple[str, str]:
    if external_refs:
        return (
            "routed",
            "At least one non-generated source, doc, test, or script references this family.",
        )
    if generated_refs:
        return (
            "generated_linked",
            "Only generated-output files outside the experiment tree reference this family.",
        )
    if experiment_refs:
        return (
            "experiment_linked",
            "Only another experiment payload family references this family.",
        )
    if self_refs:
        return (
            "self_linked_review",
            "References are internal to the family; no outside route was found.",
        )
    return (
        "unrouted_review",
        "No exact references were found outside the files themselves.",
    )


def _summary(families: Sequence[Mapping[str, object]]) -> dict[str, object]:
    posture_counts: Counter[str] = Counter(str(family["retention_posture"]) for family in families)
    flag_counts: Counter[str] = Counter(
        str(flag) for family in families for flag in _sequence(family.get("review_flags"))
    )
    return {
        "family_count": len(families),
        "file_count": sum(int(family.get("file_count") or 0) for family in families),
        "total_file_bytes": sum(int(family.get("total_file_bytes") or 0) for family in families),
        "routed_family_count": posture_counts.get("routed", 0),
        "generated_linked_family_count": posture_counts.get("generated_linked", 0),
        "experiment_linked_family_count": posture_counts.get("experiment_linked", 0),
        "self_linked_review_family_count": posture_counts.get("self_linked_review", 0),
        "unrouted_review_family_count": posture_counts.get("unrouted_review", 0),
        "posture_counts": dict(sorted(posture_counts.items())),
        "review_flag_counts": dict(sorted(flag_counts.items())),
    }


def render_experiment_payload_retention_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# Experiment Payload Retention Audit",
        "",
        "Status: generated evidence",
        "Role: Generated evidence",
        f"Last updated: {_date_from_generated_at(report.get('generated_at_utc'))}",
        "Purpose: classify experiment payload families by exact-reference routing and "
        "retention-review posture.",
        "",
        "This report is read-only. It does not approve deletion; `unrouted_review` means "
        "a human should inspect provenance and surviving summaries before any cleanup.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "family_count",
        "file_count",
        "total_file_bytes",
        "routed_family_count",
        "generated_linked_family_count",
        "experiment_linked_family_count",
        "self_linked_review_family_count",
        "unrouted_review_family_count",
    ):
        lines.append(f"| `{key}` | {summary.get(key, 0)} |")
    _append_family_table(lines, report)
    _append_largest_files(lines, report)
    _append_postures(lines, report)
    return "\n".join(lines).rstrip() + "\n"


def _append_family_table(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Family Retention Posture",
            "",
            "| Family | Files | Bytes | Posture | External | Generated | Other Exp. | "
            "Self | Flags | Reference Samples |",
            "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    families = [_as_mapping(item) for item in _sequence(report.get("families"))]
    if not families:
        lines.append("| _None detected._ | 0 | 0 |  | 0 | 0 | 0 | 0 |  |  |")
        return
    for family in families[:80]:
        samples = _reference_sample_text(family)
        flags = "<br>".join(f"`{flag}`" for flag in _sequence(family.get("review_flags"))[:6])
        lines.append(
            "| "
            f"`{family.get('family')}` | "
            f"{family.get('file_count')} | "
            f"{family.get('total_file_bytes')} | "
            f"`{family.get('retention_posture')}` | "
            f"{family.get('external_reference_count')} | "
            f"{family.get('generated_output_reference_count')} | "
            f"{family.get('other_experiment_reference_count')} | "
            f"{family.get('self_family_reference_count')} | "
            f"{flags} | "
            f"{samples} |"
        )


def _reference_sample_text(family: Mapping[str, object]) -> str:
    samples = []
    for sample in _sequence(family.get("reference_samples"))[:4]:
        item = _as_mapping(sample)
        reference_path = item.get("reference_path")
        referenced_path = item.get("referenced_path")
        scope = item.get("scope")
        samples.append(f"`{reference_path}` -> `{referenced_path}` ({scope})")
    return "<br>".join(samples)


def _append_largest_files(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Largest Files By Family",
            "",
            "| Family | Largest Files |",
            "| --- | --- |",
        ]
    )
    for family in _sequence(report.get("families"))[:80]:
        item = _as_mapping(family)
        files = [
            f"`{entry.get('path')}` ({entry.get('bytes')} bytes)"
            for entry in [_as_mapping(value) for value in _sequence(item.get("largest_files"))]
        ]
        lines.append(f"| `{item.get('family')}` | {'<br>'.join(files)} |")


def _append_postures(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Retention Postures",
            "",
            "| Posture | Meaning |",
            "| --- | --- |",
        ]
    )
    for posture in _sequence(report.get("posture_definitions")):
        item = _as_mapping(posture)
        lines.append(f"| `{item.get('posture')}` | {item.get('description')} |")


def _posture_definitions() -> list[dict[str, str]]:
    return [
        {
            "posture": "routed",
            "description": (
                "Referenced by at least one non-generated doc, test, script, or source file."
            ),
        },
        {
            "posture": "generated_linked",
            "description": (
                "Referenced only by generated-output files outside `docs/test_outputs/experiments`."
            ),
        },
        {
            "posture": "experiment_linked",
            "description": "Referenced only by another experiment payload family.",
        },
        {
            "posture": "self_linked_review",
            "description": "Referenced only inside the same experiment payload family.",
        },
        {
            "posture": "unrouted_review",
            "description": "No exact references found; requires human provenance review.",
        },
    ]


def _extension_counts(file_paths: Sequence[str]) -> dict[str, int]:
    counts: Counter[str] = Counter(Path(path).suffix or "[no suffix]" for path in file_paths)
    return dict(sorted(counts.items()))


def _largest_files(file_sizes: Sequence[tuple[str, int]]) -> list[dict[str, object]]:
    largest = sorted(file_sizes, key=lambda item: (-item[1], item[0]))[:MAX_LARGEST_FILES]
    return [{"path": path, "bytes": size} for path, size in largest]


def _iter_text_reference_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = _relative_path(root, path)
        if _is_excluded_reference_path(relative):
            continue
        if relative.startswith("docs/test_outputs/") and relative.startswith(
            GENERATED_REFERENCE_EXCLUDED_PREFIXES
        ):
            continue
        if path.suffix not in TEXT_REFERENCE_SUFFIXES:
            continue
        if _file_size(path) > MAX_REFERENCE_FILE_BYTES:
            continue
        files.append(path)
    files.sort(key=lambda item: _relative_path(root, item))
    return files


def _is_excluded_reference_path(relative_path: str) -> bool:
    return any(
        relative_path == prefix.rstrip("/") or relative_path.startswith(prefix)
        for prefix in EXCLUDED_REFERENCE_PREFIXES
    )


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"json_out: {path}")


def _write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"markdown_out: {path}")


def _date_from_generated_at(value: object) -> str:
    text = str(value or "")
    return text[:10] if len(text) >= 10 else datetime.now(timezone.utc).date().isoformat()


def _posture_sort_key(posture: str) -> int:
    return {
        "unrouted_review": 0,
        "self_linked_review": 1,
        "experiment_linked": 2,
        "generated_linked": 3,
        "routed": 4,
    }.get(posture, 9)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return []
    if isinstance(value, Sequence):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    return []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify docs/test_outputs/experiments payload families by exact-reference "
            "routing and retention-review posture. The audit is read-only except for "
            "requested JSON/Markdown report files."
        )
    )
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_experiment_payload_retention_audit(args.root)
    _write_json(args.json_out, report)
    _write_markdown(args.markdown_out, render_experiment_payload_retention_markdown(report))
    summary = _as_mapping(report.get("summary"))
    print(f"families: {summary.get('family_count')}")
    print(f"files: {summary.get('file_count')}")
    print(f"routed_families: {summary.get('routed_family_count')}")
    print(f"generated_linked_families: {summary.get('generated_linked_family_count')}")
    print(f"experiment_linked_families: {summary.get('experiment_linked_family_count')}")
    print(f"self_linked_review_families: {summary.get('self_linked_review_family_count')}")
    print(f"unrouted_review_families: {summary.get('unrouted_review_family_count')}")


if __name__ == "__main__":
    main()
