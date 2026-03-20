#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DOCS: tuple[str, ...] = (
    "AGENTS.md",
    "README.md",
    "docs/README.md",
    "docs/architecture/README.md",
    "docs/developer/README.md",
    "docs/developer/developer_reference.md",
    "docs/developer/ai_workflow.md",
    "docs/developer/genai_workflow_architecture.md",
    "docs/developer/documentation_governance.md",
    "docs/developer/documentation_grooming_workstream.md",
    "docs/developer/project_health_gate_structure.md",
    "docs/developer/project_health_remediation_workstream.md",
    "scripts/README.md",
)
METADATA_REQUIRED_DOCS: tuple[str, ...] = tuple(
    relative_doc for relative_doc in CANONICAL_DOCS if relative_doc != "AGENTS.md"
)
PROJECT_ROOT_PREFIXES: tuple[str, ...] = (
    "docs/",
    "scripts/",
    "apps/",
    "core/",
    ".github/",
)
ROOT_FILE_REFERENCES: set[str] = {
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements-build.txt",
    ".pre-commit-config.yaml",
}
PATH_SUFFIXES: tuple[str, ...] = (
    ".md",
    ".py",
    ".js",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".mmd",
    ".txt",
    ".html",
    ".svg",
    ".sh",
    ".iss",
    ".spec",
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
METADATA_FIELD_RE = re.compile(r"^(Status|Role|Last updated):\s*(.+)$", re.MULTILINE)
ROLE_VALUES: tuple[str, ...] = (
    "Canonical current",
    "Mixed",
    "Planning / WIP",
    "Draft decision log",
    "Runbook / operational",
    "Generated evidence",
    "Archive / legacy",
)
ROLE_VALUES_NORMALIZED = {value.casefold() for value in ROLE_VALUES}
METADATA_HEAD_LINE_LIMIT = 20


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_candidate(raw: str) -> str:
    value = str(raw or "").strip()
    value = value.strip("()[]{}<>\"'")
    value = value.rstrip(".,;:!?")
    if "#" in value:
        value = value.split("#", 1)[0]
    return value.strip()


def _candidate_has_placeholders(candidate: str) -> bool:
    return "<" in candidate or ">" in candidate or "*" in candidate or "..." in candidate


def _looks_like_project_path(candidate: str) -> bool:
    if not candidate:
        return False
    if "://" in candidate or candidate.startswith(("mailto:", "data:")):
        return False
    if _candidate_has_placeholders(candidate):
        return False
    if any(char.isspace() for char in candidate):
        return False
    if candidate in ROOT_FILE_REFERENCES:
        return True
    if candidate.startswith(("./", "../")):
        return True
    if candidate.startswith(PROJECT_ROOT_PREFIXES):
        return True
    if candidate.endswith("/") and "/" in candidate:
        return True
    return candidate.endswith(PATH_SUFFIXES)


def _looks_like_explicit_project_path(candidate: str) -> bool:
    if not candidate:
        return False
    if candidate in ROOT_FILE_REFERENCES:
        return True
    return candidate.startswith(PROJECT_ROOT_PREFIXES) or candidate.startswith(("./", "../"))


def _should_audit_code_span(candidate: str) -> bool:
    if not candidate:
        return False
    if _looks_like_explicit_project_path(candidate):
        return True
    return candidate.endswith(".md") and _looks_like_project_path(candidate)


def _resolve_within_project(candidate_path: Path) -> Path | None:
    resolved = candidate_path.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError:
        return None
    return resolved


def _resolve_candidate(doc_path: Path, candidate: str) -> Path | None:
    if not _looks_like_project_path(candidate):
        return None
    if candidate in ROOT_FILE_REFERENCES or candidate.startswith(PROJECT_ROOT_PREFIXES):
        return _resolve_within_project(PROJECT_ROOT / candidate)
    if candidate.startswith(("./", "../")):
        return _resolve_within_project(doc_path.parent / candidate)

    candidates: list[Path] = [doc_path.parent / candidate]

    doc_parts = doc_path.relative_to(PROJECT_ROOT).parts
    if doc_parts and doc_parts[0] == "docs":
        candidates.append(PROJECT_ROOT / "docs" / candidate)
    if doc_parts and doc_parts[0] == "scripts":
        candidates.append(PROJECT_ROOT / "scripts" / candidate)

    resolved_candidates = [
        resolved for item in candidates if (resolved := _resolve_within_project(item)) is not None
    ]
    for resolved in resolved_candidates:
        if resolved.exists():
            return resolved

    if "/" not in candidate:
        if not candidate.endswith(".md"):
            return None
        return resolved_candidates[0] if resolved_candidates else None
    return resolved_candidates[0] if resolved_candidates else None


def _collect_references(doc_path: Path) -> set[str]:
    content = doc_path.read_text(encoding="utf-8")
    references: set[str] = set()

    for match in MARKDOWN_LINK_RE.finditer(content):
        candidate = _strip_candidate(match.group(1))
        if candidate:
            references.add(candidate)

    for match in CODE_SPAN_RE.finditer(content):
        candidate = _strip_candidate(match.group(1))
        if _should_audit_code_span(candidate):
            references.add(candidate)

    return references


def _extract_top_metadata_fields(text: str) -> dict[str, str]:
    head = "\n".join(text.splitlines()[:METADATA_HEAD_LINE_LIMIT])
    return {
        str(match.group(1)).strip(): str(match.group(2)).strip()
        for match in METADATA_FIELD_RE.finditer(head)
    }


def _metadata_issues(doc_path: Path) -> list[dict[str, str]]:
    text = doc_path.read_text(encoding="utf-8")
    fields = _extract_top_metadata_fields(text)
    issues: list[dict[str, str]] = []

    for field in ("Status", "Role", "Last updated"):
        if field not in fields:
            issues.append({"code": "MISSING_METADATA_FIELD", "field": field})

    role = fields.get("Role", "")
    if role and role.strip("` ").casefold() not in ROLE_VALUES_NORMALIZED:
        issues.append({"code": "INVALID_ROLE", "field": "Role", "value": role})

    return issues


def _write_json(path: Path | None, payload: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json_out: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that canonical routing/policy docs carry required metadata and "
            "reference existing repo paths."
        )
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional JSON report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    missing_docs: list[str] = []
    metadata_failures: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    checked_reference_count = 0

    for relative_doc in CANONICAL_DOCS:
        doc_path = PROJECT_ROOT / relative_doc
        if not doc_path.exists():
            missing_docs.append(relative_doc)
            continue

        if relative_doc in METADATA_REQUIRED_DOCS:
            issues = _metadata_issues(doc_path)
            if issues:
                metadata_failures.append({"doc": relative_doc, "issues": issues})

        for raw_reference in sorted(_collect_references(doc_path)):
            resolved = _resolve_candidate(doc_path, raw_reference)
            if resolved is None:
                continue
            checked_reference_count += 1
            if not resolved.exists():
                failures.append(
                    {
                        "doc": relative_doc,
                        "reference": raw_reference,
                        "resolved_path": str(resolved.relative_to(PROJECT_ROOT)),
                    }
                )

    payload: dict[str, object] = {
        "version": 1,
        "generated_at_utc": _now_iso_utc(),
        "canonical_docs_checked": len(CANONICAL_DOCS),
        "metadata_docs_checked": len(METADATA_REQUIRED_DOCS),
        "checked_reference_count": checked_reference_count,
        "missing_docs": missing_docs,
        "metadata_failures": metadata_failures,
        "failures": failures,
    }
    _write_json(args.json_out, payload)

    if missing_docs:
        print("[check-doc-references] Missing canonical docs:")
        for entry in missing_docs:
            print(f"  - {entry}")
        raise SystemExit(1)

    if metadata_failures:
        print("[check-doc-references] Canonical docs missing required metadata:")
        for failure in metadata_failures:
            issue_labels = ", ".join(
                (
                    issue["field"]
                    if issue["code"] == "MISSING_METADATA_FIELD"
                    else f"{issue['field']}={issue.get('value', '')}"
                )
                for issue in failure["issues"]
            )
            print(f"  - {failure['doc']}: {issue_labels}")
        raise SystemExit(1)

    if failures:
        print("[check-doc-references] Missing referenced paths in canonical docs:")
        for failure in failures:
            print(
                "  - "
                f"{failure['doc']}: {failure['reference']} "
                f"(resolved {failure['resolved_path']})"
            )
        raise SystemExit(1)

    print(
        f"[check-doc-references] PASS ({len(CANONICAL_DOCS)} docs, {checked_reference_count} references checked)"
    )


if __name__ == "__main__":
    main()
