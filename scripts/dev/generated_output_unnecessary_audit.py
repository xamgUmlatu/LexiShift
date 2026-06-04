#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "dev_workflow"
    / "generated_output_unnecessary_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "dev_workflow"
    / "generated_output_unnecessary_latest.md"
)

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
DATE_RE = re.compile(
    r"(?<!\d)(?:20\d{2}[-_](?:0[1-9]|1[0-2])[-_](?:0[1-9]|[12]\d|3[01])"
    r"|20\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))(?!\d)"
)
SEMANTIC_REPAIR_REPORT_RE = re.compile(
    r"^docs/test_outputs/semantic_veto_llm_pilot_"
    r"(?P<kind>admission|generation_run)_en_es_repair_"
    r"(?P<run_id>20\d{6}_\d{3})\.(?P<suffix>json|md)$"
)
SEMANTIC_SOURCE_INSTALL_ROOT_RE = re.compile(
    r"^docs/test_outputs/experiments/semantic_veto_source_packaging/"
    r"(?P<pack_id>en-es-active-only-combined-full-v1-tranche-\d{3})"
    r"-product-install-data-root$"
)
MAX_REFERENCE_FILE_BYTES = 25_000_000


def build_generated_output_unnecessary_audit(root: Path) -> dict[str, object]:
    root = root.resolve()
    candidate_paths = _candidate_reference_strings(root)
    reference_index = _build_reference_index(root, candidate_paths)
    groups: list[dict[str, object]] = []
    assigned_paths: set[str] = set()

    groups.extend(
        _semantic_source_install_root_groups(
            root=root,
            reference_index=reference_index,
        )
    )
    for group in groups:
        assigned_paths.update(str(path) for path in _sequence(group.get("paths")))

    repair_groups = _semantic_repair_report_groups(
        root=root,
        reference_index=reference_index,
        assigned_paths=assigned_paths,
    )
    groups.extend(repair_groups)
    for group in repair_groups:
        assigned_paths.update(str(path) for path in _sequence(group.get("paths")))

    view_groups = _root_dated_view_groups(
        root=root,
        reference_index=reference_index,
        assigned_paths=assigned_paths,
    )
    groups.extend(view_groups)
    for group in view_groups:
        assigned_paths.update(str(path) for path in _sequence(group.get("paths")))

    groups.extend(
        _remaining_root_dated_groups(
            root=root,
            reference_index=reference_index,
            assigned_paths=assigned_paths,
        )
    )
    groups.sort(
        key=lambda group: (
            _status_sort_key(str(group["status"])),
            str(group["rule_id"]),
            str(group["group_id"]),
        )
    )
    summary = _summary(groups)
    return {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "rules": _rules(),
        "summary": summary,
        "groups": groups,
    }


def _candidate_reference_strings(root: Path) -> list[str]:
    candidates: set[str] = set()
    output_root = root / "docs" / "test_outputs"
    if output_root.exists():
        for path in output_root.iterdir():
            if path.is_file() and DATE_RE.search(path.name):
                candidates.add(_relative_path(root, path))
    source_root = output_root / "experiments" / "semantic_veto_source_packaging"
    if source_root.exists():
        for path in source_root.iterdir():
            relative = _relative_path(root, path)
            if path.is_dir() and SEMANTIC_SOURCE_INSTALL_ROOT_RE.match(relative):
                candidates.add(relative)
                candidates.update(
                    _relative_path(root, child) for child in path.rglob("*") if child.is_file()
                )
    return sorted(candidates)


def _build_reference_index(root: Path, candidates: Sequence[str]) -> dict[str, dict[str, object]]:
    index: dict[str, dict[str, object]] = {
        candidate: {
            "external_reference_paths": set(),
            "generated_output_reference_paths": set(),
        }
        for candidate in candidates
    }
    if not candidates:
        return index
    for path in _iter_text_reference_files(root):
        relative = _relative_path(root, path)
        if relative in candidates:
            continue
        text = _read_text(path)
        if not text:
            continue
        scope = "generated" if relative.startswith("docs/test_outputs/") else "external"
        for candidate in candidates:
            if _is_self_or_descendant(reference_path=relative, candidate_path=candidate):
                continue
            if candidate in text:
                key = (
                    "generated_output_reference_paths"
                    if scope == "generated"
                    else "external_reference_paths"
                )
                ref_paths = index[candidate][key]
                if isinstance(ref_paths, set):
                    ref_paths.add(relative)
    return index


def _semantic_source_install_root_groups(
    *,
    root: Path,
    reference_index: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    source_root = root / "docs" / "test_outputs" / "experiments" / "semantic_veto_source_packaging"
    if not source_root.exists():
        return []
    groups: list[dict[str, object]] = []
    for path in sorted(source_root.iterdir()):
        relative = _relative_path(root, path)
        match = SEMANTIC_SOURCE_INSTALL_ROOT_RE.match(relative)
        if not path.is_dir() or not match:
            continue
        pack_id = match.group("pack_id")
        descendants = sorted(
            _relative_path(root, child) for child in path.rglob("*") if child.is_file()
        )
        source_files = [
            f"docs/test_outputs/experiments/semantic_veto_source_packaging/{pack_id}-normalized_evidence.json",
            f"docs/test_outputs/experiments/semantic_veto_source_packaging/{pack_id}_semantic_inventory.json",
        ]
        missing_sources = [source for source in source_files if not (root / source).is_file()]
        external_refs, generated_refs = _combined_reference_paths(
            [relative, *descendants],
            reference_index,
        )
        if external_refs or generated_refs:
            status = "retain"
            rule_id = "referenced_generated_output"
            reason = "The install root or one of its files is still referenced."
        elif missing_sources:
            status = "review_only"
            rule_id = "install_root_missing_retained_source_evidence"
            reason = "Install root has no references, but retained source evidence is incomplete."
        else:
            status = "definite_prune"
            rule_id = "unreferenced_semantic_install_root_with_retained_source_evidence"
            reason = (
                "Copied install-root fixture has no references and the source evidence plus "
                "semantic inventory remain retained outside the install root."
            )
        groups.append(
            _group(
                root=root,
                status=status,
                rule_id=rule_id,
                group_id=relative,
                reason=reason,
                paths=descendants,
                external_refs=external_refs,
                generated_refs=generated_refs,
                source_evidence_paths=source_files,
                missing_source_evidence_paths=missing_sources,
            )
        )
    return groups


def _semantic_repair_report_groups(
    *,
    root: Path,
    reference_index: Mapping[str, Mapping[str, object]],
    assigned_paths: set[str],
) -> list[dict[str, object]]:
    output_root = root / "docs" / "test_outputs"
    grouped: dict[str, list[str]] = defaultdict(list)
    if not output_root.exists():
        return []
    for path in sorted(output_root.iterdir()):
        if not path.is_file():
            continue
        relative = _relative_path(root, path)
        if relative in assigned_paths:
            continue
        match = SEMANTIC_REPAIR_REPORT_RE.match(relative)
        if match:
            grouped[match.group("run_id")].append(relative)
    groups: list[dict[str, object]] = []
    for run_id, paths in sorted(grouped.items()):
        external_refs, generated_refs = _combined_reference_paths(paths, reference_index)
        if external_refs or generated_refs:
            status = "retain"
            rule_id = "referenced_generated_output"
            reason = "Dated semantic repair report is still referenced."
        else:
            status = "definite_prune"
            rule_id = "unreferenced_semantic_repair_report_bundle"
            reason = (
                "Dated semantic repair admission/generation-run report has no references; "
                "generated-row payloads are audited separately as provenance-bearing data."
            )
        groups.append(
            _group(
                root=root,
                status=status,
                rule_id=rule_id,
                group_id=f"semantic_veto_llm_pilot_repair_{run_id}",
                reason=reason,
                paths=paths,
                external_refs=external_refs,
                generated_refs=generated_refs,
            )
        )
    return groups


def _root_dated_view_groups(
    *,
    root: Path,
    reference_index: Mapping[str, Mapping[str, object]],
    assigned_paths: set[str],
) -> list[dict[str, object]]:
    output_root = root / "docs" / "test_outputs"
    if not output_root.exists():
        return []
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in sorted(output_root.iterdir()):
        if not path.is_file() or path.suffix not in {".html", ".md"}:
            continue
        relative = _relative_path(root, path)
        if relative in assigned_paths or not DATE_RE.search(path.name):
            continue
        json_counterpart = path.with_suffix(".json")
        if json_counterpart.is_file():
            grouped[path.stem].append(relative)
    groups: list[dict[str, object]] = []
    for stem, paths in sorted(grouped.items()):
        unreferenced_paths: list[str] = []
        retained_paths: list[str] = []
        retained_external_refs: set[str] = set()
        retained_generated_refs: set[str] = set()
        for relative in paths:
            external_refs, generated_refs = _combined_reference_paths([relative], reference_index)
            if external_refs or generated_refs:
                retained_paths.append(relative)
                retained_external_refs.update(external_refs)
                retained_generated_refs.update(generated_refs)
            else:
                unreferenced_paths.append(relative)
        if unreferenced_paths:
            groups.append(
                _group(
                    root=root,
                    status="definite_prune",
                    rule_id="unreferenced_root_dated_report_view_with_json_counterpart",
                    group_id=stem,
                    reason=(
                        "Dated root report view has no references and a same-stem JSON "
                        "evidence file remains retained."
                    ),
                    paths=unreferenced_paths,
                    external_refs=set(),
                    generated_refs=set(),
                    retained_counterpart_paths=[f"docs/test_outputs/{stem}.json"],
                )
            )
        if retained_paths:
            groups.append(
                _group(
                    root=root,
                    status="retain",
                    rule_id="referenced_generated_output",
                    group_id=f"{stem}:referenced_views",
                    reason="Dated root report view has a same-stem JSON file but is still referenced.",
                    paths=retained_paths,
                    external_refs=retained_external_refs,
                    generated_refs=retained_generated_refs,
                    retained_counterpart_paths=[f"docs/test_outputs/{stem}.json"],
                )
            )
    return groups


def _remaining_root_dated_groups(
    *,
    root: Path,
    reference_index: Mapping[str, Mapping[str, object]],
    assigned_paths: set[str],
) -> list[dict[str, object]]:
    output_root = root / "docs" / "test_outputs"
    if not output_root.exists():
        return []
    groups: list[dict[str, object]] = []
    for path in sorted(output_root.iterdir()):
        if not path.is_file() or not DATE_RE.search(path.name):
            continue
        relative = _relative_path(root, path)
        if relative in assigned_paths:
            continue
        external_refs, generated_refs = _combined_reference_paths([relative], reference_index)
        if external_refs or generated_refs:
            status = "retain"
            rule_id = "referenced_generated_output"
            reason = "Dated root generated output is still referenced."
        else:
            status = "review_only"
            rule_id = "unreferenced_root_dated_primary_or_provenance_output"
            reason = (
                "No references found, but this file is JSON or otherwise primary evidence; "
                "a human should confirm a surviving summary or downstream artifact first."
            )
        groups.append(
            _group(
                root=root,
                status=status,
                rule_id=rule_id,
                group_id=relative,
                reason=reason,
                paths=[relative],
                external_refs=external_refs,
                generated_refs=generated_refs,
            )
        )
    return groups


def _group(
    *,
    root: Path,
    status: str,
    rule_id: str,
    group_id: str,
    reason: str,
    paths: Sequence[str],
    external_refs: set[str],
    generated_refs: set[str],
    **extra: object,
) -> dict[str, object]:
    path_list = sorted(dict.fromkeys(paths))
    output: dict[str, object] = {
        "status": status,
        "rule_id": rule_id,
        "group_id": group_id,
        "reason": reason,
        "paths": path_list,
        "file_count": len(path_list),
        "total_file_bytes": sum(_file_size(root / path) for path in path_list),
        "external_reference_count": len(external_refs),
        "generated_output_reference_count": len(generated_refs),
        "external_reference_samples": sorted(external_refs)[:8],
        "generated_output_reference_samples": sorted(generated_refs)[:8],
    }
    output.update(extra)
    return output


def _combined_reference_paths(
    paths: Sequence[str],
    reference_index: Mapping[str, Mapping[str, object]],
) -> tuple[set[str], set[str]]:
    external_refs: set[str] = set()
    generated_refs: set[str] = set()
    for path in paths:
        refs = reference_index.get(path, {})
        external_refs.update(str(item) for item in _sequence(refs.get("external_reference_paths")))
        generated_refs.update(
            str(item) for item in _sequence(refs.get("generated_output_reference_paths"))
        )
    return external_refs, generated_refs


def _summary(groups: Sequence[Mapping[str, object]]) -> dict[str, object]:
    status_counts: dict[str, int] = defaultdict(int)
    status_file_counts: dict[str, int] = defaultdict(int)
    status_bytes: dict[str, int] = defaultdict(int)
    rule_counts: dict[str, int] = defaultdict(int)
    for group in groups:
        status = str(group.get("status"))
        rule_id = str(group.get("rule_id"))
        status_counts[status] += 1
        status_file_counts[status] += int(group.get("file_count") or 0)
        status_bytes[status] += int(group.get("total_file_bytes") or 0)
        rule_counts[rule_id] += 1
    return {
        "group_count": len(groups),
        "definite_prune_group_count": status_counts.get("definite_prune", 0),
        "definite_prune_file_count": status_file_counts.get("definite_prune", 0),
        "definite_prune_bytes": status_bytes.get("definite_prune", 0),
        "review_only_group_count": status_counts.get("review_only", 0),
        "retain_group_count": status_counts.get("retain", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "rule_counts": dict(sorted(rule_counts.items())),
    }


def render_generated_output_unnecessary_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# Generated Output Unnecessary File Audit",
        "",
        "Status: generated evidence",
        "Role: Generated evidence",
        f"Last updated: {_date_from_generated_at(report.get('generated_at_utc'))}",
        "Purpose: identify generated-output groups that are mechanically safe to prune.",
        "",
        "This audit is intentionally conservative. `definite_prune` means the rule found "
        "no exact non-output references and no retained generated-output provenance references.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "group_count",
        "definite_prune_group_count",
        "definite_prune_file_count",
        "definite_prune_bytes",
        "review_only_group_count",
        "retain_group_count",
    ):
        lines.append(f"| `{key}` | {summary.get(key, 0)} |")
    _append_group_table(lines, "Definite Prune Groups", report, "definite_prune")
    _append_group_table(lines, "Review-Only Groups", report, "review_only")
    _append_group_table(lines, "Retained Groups", report, "retain")
    _append_rules(lines, report)
    return "\n".join(lines).rstrip() + "\n"


def _append_group_table(
    lines: list[str],
    title: str,
    report: Mapping[str, object],
    status: str,
) -> None:
    lines.extend(
        [
            "",
            f"## {title}",
            "",
            "| Rule | Files | Bytes | Reason | Sample Paths | Reference Samples |",
            "| --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    rows = [
        _as_mapping(group)
        for group in _sequence(report.get("groups"))
        if _as_mapping(group).get("status") == status
    ]
    if not rows:
        lines.append("| _None detected._ | 0 | 0 |  |  |  |")
        return
    for group in rows[:80]:
        samples = "<br>".join(f"`{path}`" for path in _sequence(group.get("paths"))[:4])
        refs = [
            *[f"`{path}`" for path in _sequence(group.get("external_reference_samples"))[:3]],
            *[
                f"`{path}`"
                for path in _sequence(group.get("generated_output_reference_samples"))[:3]
            ],
        ]
        lines.append(
            "| "
            f"`{group.get('rule_id')}` | "
            f"{group.get('file_count')} | "
            f"{group.get('total_file_bytes')} | "
            f"{group.get('reason')} | "
            f"{samples} | "
            f"{'<br>'.join(refs)} |"
        )


def _append_rules(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(["", "## Rules", "", "| Rule | Posture | Description |", "| --- | --- | --- |"])
    for rule in _sequence(report.get("rules")):
        item = _as_mapping(rule)
        lines.append(
            f"| `{item.get('rule_id')}` | {item.get('posture')} | {item.get('description')} |"
        )


def _rules() -> list[dict[str, str]]:
    return [
        {
            "rule_id": "unreferenced_root_dated_report_view_with_json_counterpart",
            "posture": "definite_prune",
            "description": (
                "A root-level dated `.html` or `.md` generated report view has no references "
                "and a same-stem JSON evidence file remains."
            ),
        },
        {
            "rule_id": "unreferenced_semantic_repair_report_bundle",
            "posture": "definite_prune",
            "description": (
                "A dated semantic-veto LLM pilot repair admission/generation-run report "
                "bundle has no references. Generated-row payloads are not included."
            ),
        },
        {
            "rule_id": "unreferenced_semantic_install_root_with_retained_source_evidence",
            "posture": "definite_prune",
            "description": (
                "A copied semantic install-root fixture has no references and matching "
                "top-level normalized evidence plus semantic inventory remain."
            ),
        },
        {
            "rule_id": "unreferenced_root_dated_primary_or_provenance_output",
            "posture": "review_only",
            "description": (
                "A dated root generated output has no references, but may be primary JSON "
                "evidence or provenance data."
            ),
        },
        {
            "rule_id": "install_root_missing_retained_source_evidence",
            "posture": "review_only",
            "description": (
                "An unreferenced install-root fixture lacks the retained source-evidence "
                "counterparts required for automatic pruning."
            ),
        },
        {
            "rule_id": "referenced_generated_output",
            "posture": "retain",
            "description": "The path is still referenced by docs, tests, scripts, or retained outputs.",
        },
    ]


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


def _is_self_or_descendant(*, reference_path: str, candidate_path: str) -> bool:
    return reference_path == candidate_path or reference_path.startswith(f"{candidate_path}/")


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


def _status_sort_key(status: str) -> int:
    return {"definite_prune": 0, "review_only": 1, "retain": 2}.get(status, 9)


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
            "Audit generated outputs for mechanically safe prune groups. The audit is "
            "read-only except for requested JSON/Markdown report files."
        )
    )
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_generated_output_unnecessary_audit(args.root)
    _write_json(args.json_out, report)
    _write_markdown(args.markdown_out, render_generated_output_unnecessary_markdown(report))
    summary = _as_mapping(report.get("summary"))
    print(f"groups: {summary.get('group_count')}")
    print(f"definite_prune_groups: {summary.get('definite_prune_group_count')}")
    print(f"definite_prune_files: {summary.get('definite_prune_file_count')}")
    print(f"review_only_groups: {summary.get('review_only_group_count')}")
    print(f"retain_groups: {summary.get('retain_group_count')}")


if __name__ == "__main__":
    main()
