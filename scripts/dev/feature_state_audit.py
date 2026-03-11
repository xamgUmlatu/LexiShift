#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = PROJECT_ROOT / "docs" / "developer" / "feature_state_matrix.md"
KNOWN_STATUSES = {"planned", "scaffolded", "implemented", "default-on", "verified"}
NON_FEATURE_SECTIONS = {
    "Status Vocabulary",
    "Date Fields",
    "Current State Mismatches To Preserve Explicitly",
}
REQUIRED_FIELDS = (
    "Status",
    "Last documented checkpoint",
    "Last verified",
    "Default behavior",
    "Evidence",
    "Known gaps",
)
FIELD_PATTERN = re.compile(r"^-\s+([^:]+):\s*(.*)$")
DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
CODE_PATH_PATTERN = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class AuditIssue:
    section: str
    code: str
    message: str


@dataclass(frozen=True)
class AuditReport:
    matrix_path: str
    generated_at_utc: str
    section_count: int
    issue_count: int
    issues: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "matrix_path": self.matrix_path,
            "generated_at_utc": self.generated_at_utc,
            "section_count": self.section_count,
            "issue_count": self.issue_count,
            "issues": self.issues,
        }


@dataclass(frozen=True)
class Section:
    title: str
    lines: list[str]


def _parse_sections(text: str) -> list[Section]:
    sections: list[Section] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_title is not None:
                sections.append(Section(title=current_title, lines=current_lines))
            current_title = line[3:].strip()
            current_lines = []
            continue
        if current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        sections.append(Section(title=current_title, lines=current_lines))
    return sections


def _iter_evidence_paths(lines: Iterable[str]) -> Iterable[str]:
    for line in lines:
        for match in CODE_PATH_PATTERN.findall(line):
            text = str(match).strip()
            if not text or text.startswith("http"):
                continue
            yield text


def _resolve_matrix_root(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.parent.name == "developer" and resolved.parent.parent.name == "docs":
        return resolved.parents[2]
    return resolved.parent


def audit_feature_state_matrix(
    path: Path,
    *,
    assumed_existing: Iterable[Path] = (),
) -> AuditReport:
    text = path.read_text(encoding="utf-8")
    matrix_root = _resolve_matrix_root(path)
    assumed_existing_resolved = {candidate.resolve() for candidate in assumed_existing}
    sections = _parse_sections(text)
    issues: list[AuditIssue] = []
    audited_sections = 0

    for section in sections:
        if section.title in NON_FEATURE_SECTIONS:
            continue
        fields: dict[str, str] = {}
        field_lines: dict[str, list[str]] = {}
        current_field: str | None = None
        for line in section.lines:
            if line.startswith("## "):
                break
            match = FIELD_PATTERN.match(line)
            if match:
                current_field = match.group(1).strip()
                fields[current_field] = match.group(2).strip()
                field_lines.setdefault(current_field, [])
                continue
            if current_field is not None and line.startswith("  - "):
                field_lines.setdefault(current_field, []).append(line)

        if not any(field in fields for field in REQUIRED_FIELDS):
            continue
        audited_sections += 1

        for field in REQUIRED_FIELDS:
            if field not in fields:
                issues.append(
                    AuditIssue(
                        section=section.title,
                        code="MISSING_FIELD",
                        message=f"Missing required field '{field}'.",
                    )
                )

        status_text = fields.get("Status", "")
        if status_text and not any(token in status_text for token in KNOWN_STATUSES):
            issues.append(
                AuditIssue(
                    section=section.title,
                    code="INVALID_STATUS",
                    message=f"Status field does not contain a known status token: {status_text}",
                )
            )

        for field in ("Last documented checkpoint", "Last verified"):
            value = fields.get(field, "")
            if value and DATE_PATTERN.search(value) is None:
                issues.append(
                    AuditIssue(
                        section=section.title,
                        code="MISSING_DATE",
                        message=f"Field '{field}' must include an ISO date.",
                    )
                )

        for field in ("Default behavior", "Evidence", "Known gaps"):
            if field in fields and not field_lines.get(field):
                issues.append(
                    AuditIssue(
                        section=section.title,
                        code="EMPTY_LIST_FIELD",
                        message=f"Field '{field}' must include at least one bullet item.",
                    )
                )

        for evidence_path in _iter_evidence_paths(field_lines.get("Evidence", [])):
            evidence = matrix_root / evidence_path
            if not evidence.exists() and evidence.resolve() not in assumed_existing_resolved:
                issues.append(
                    AuditIssue(
                        section=section.title,
                        code="MISSING_EVIDENCE_PATH",
                        message=f"Evidence path does not exist: {evidence_path}",
                    )
                )

    report = AuditReport(
        matrix_path=str(path),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        section_count=audited_sections,
        issue_count=len(issues),
        issues=[asdict(issue) for issue in issues],
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit docs/developer/feature_state_matrix.md for required state/evidence structure."
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=DEFAULT_MATRIX,
        help="Path to the feature state matrix markdown file.",
    )
    parser.add_argument("--json-out", type=Path, help="Optional JSON report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    assumed_existing: list[Path] = []
    if args.json_out:
        assumed_existing.append((PROJECT_ROOT / args.json_out).resolve())
        assumed_existing.append(args.json_out.resolve())
    report = audit_feature_state_matrix(args.matrix, assumed_existing=assumed_existing)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"json_out: {args.json_out}")
    print(f"sections_audited: {report.section_count}")
    print(f"issues: {report.issue_count}")
    for issue in report.issues[:20]:
        print(f"- [{issue['section']}] {issue['code']}: {issue['message']}")
    if report.issue_count != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
