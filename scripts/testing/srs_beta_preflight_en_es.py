#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
SRS_JOURNEY_ROOT = TEST_OUTPUTS_ROOT / "srs_journey"
DEFAULT_TAXONOMY = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_es.json"
)
DEFAULT_OPTIONS_HTML = PROJECT_ROOT / "apps" / "chrome-extension" / "options.html"
DEFAULT_LOCALE_ROOT = PROJECT_ROOT / "apps" / "chrome-extension" / "_locales"
DEFAULT_TAXONOMY_AUDIT = TEST_OUTPUTS_ROOT / (
    "srs_topic_preference_taxonomy_en_es_current_latest.json"
)
DEFAULT_SRS_QUALITY = TEST_OUTPUTS_ROOT / "srs_quality_latest.json"
DEFAULT_PROFILE_JOURNEY = SRS_JOURNEY_ROOT / "srs_journey_en_es_profile_latest.json"
DEFAULT_INSTALLED_JOURNEY = SRS_JOURNEY_ROOT / "srs_journey_en_es_installed_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_beta_preflight_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_beta_preflight_en_es_latest.md"

ALLOWED_VISIBILITY = {
    "strict_mvp_visible",
    "future_beta_hidden",
    "hidden_source_required",
    "future_register_hidden",
    "legal_source_gated_hidden",
}
LOCALES = ("en", "de", "ja", "zh")

MANUAL_CHECKS = (
    {
        "id": "fresh_install_helper_connection",
        "status": "PENDING",
        "check": "Fresh install can connect extension options to helper.",
        "verification": (
            "Load the beta extension/helper, open Options, refresh profiles, and confirm "
            "helper/profile status is understandable."
        ),
    },
    {
        "id": "fresh_profile_srs_initialize",
        "status": "PENDING",
        "check": "Fresh en-es profile can initialize SRS and populate the dashboard.",
        "verification": (
            "Use a throwaway beta profile, choose proficiency/topics, initialize S, and "
            "refresh Learning words."
        ),
    },
    {
        "id": "runtime_replacement_and_feedback",
        "status": "PENDING",
        "check": "Published rules replace page text and feedback syncs.",
        "verification": (
            "Open a simple English page, confirm due SRS replacements, submit Good/Easy "
            "feedback, and refresh the dashboard."
        ),
    },
    {
        "id": "auto_refresh_after_feedback",
        "status": "PENDING",
        "check": "Post-feedback auto-refresh can admit more profile-shaped words.",
        "verification": (
            "After enough successful Good/Easy feedback, confirm refresh output shows "
            "capacity, selected lemmas, and preferred-topic share."
        ),
    },
    {
        "id": "delete_story_discard_recovery",
        "status": "PENDING",
        "check": "Tester recovery paths are understandable.",
        "verification": (
            "Discard one dashboard word, then delete the throwaway profile's en-es SRS "
            "story and confirm the profile can initialize again cleanly."
        ),
    },
)

DEFERRED_ITEMS = (
    "plants_nature and travel_places_transport stay hidden from the ordinary picker.",
    "Anime, hobbies, SAT/TOEFL, and register/style controls stay deferred.",
    "Browsing-based admission remains preview/planning, not mutating production admission.",
    "Right-click discard, restore/mastered/release controls, and due-only publication remain future work.",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a read-only en-es SRS beta preflight report from existing automated "
            "artifacts plus explicit manual signoff checks."
        )
    )
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--options-html", type=Path, default=DEFAULT_OPTIONS_HTML)
    parser.add_argument("--locale-root", type=Path, default=DEFAULT_LOCALE_ROOT)
    parser.add_argument("--taxonomy-audit-json", type=Path, default=DEFAULT_TAXONOMY_AUDIT)
    parser.add_argument("--srs-quality-json", type=Path, default=DEFAULT_SRS_QUALITY)
    parser.add_argument("--profile-journey-json", type=Path, default=DEFAULT_PROFILE_JOURNEY)
    parser.add_argument("--installed-journey-json", type=Path, default=DEFAULT_INSTALLED_JOURNEY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        taxonomy_path=args.taxonomy_json,
        options_html_path=args.options_html,
        locale_root=args.locale_root,
        taxonomy_audit_path=args.taxonomy_audit_json,
        srs_quality_path=args.srs_quality_json,
        profile_journey_path=args.profile_journey_json,
        installed_journey_path=args.installed_journey_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"json_out: {args.json_out}")
    print(f"markdown_out: {args.markdown_out}")
    print(
        "summary: "
        f"status={report['summary']['status']} "
        f"pass={report['summary']['finding_counts'].get('PASS', 0)} "
        f"warn={report['summary']['finding_counts'].get('WARN', 0)} "
        f"fail={report['summary']['finding_counts'].get('FAIL', 0)} "
        f"pending={report['summary']['manual_counts'].get('PENDING', 0)}"
    )
    if args.fail_on_review and report["summary"]["status"] != "PASS":
        return 1
    return 0


def build_report(
    *,
    taxonomy_path: Path = DEFAULT_TAXONOMY,
    options_html_path: Path = DEFAULT_OPTIONS_HTML,
    locale_root: Path = DEFAULT_LOCALE_ROOT,
    taxonomy_audit_path: Path = DEFAULT_TAXONOMY_AUDIT,
    srs_quality_path: Path = DEFAULT_SRS_QUALITY,
    profile_journey_path: Path = DEFAULT_PROFILE_JOURNEY,
    installed_journey_path: Path = DEFAULT_INSTALLED_JOURNEY,
    generated_at: str | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    taxonomy = _load_json_or_none(taxonomy_path)
    options_html = _read_text_or_none(options_html_path)

    if taxonomy is None:
        findings.append(
            _finding("FAIL", "taxonomy_readable", "Taxonomy JSON is missing or invalid.")
        )
        taxonomy = {}
    else:
        findings.append(_finding("PASS", "taxonomy_readable", "Taxonomy JSON is readable."))

    if options_html is None:
        findings.append(_finding("FAIL", "options_html_readable", "Options HTML is missing."))
        options_html = ""
    else:
        findings.append(_finding("PASS", "options_html_readable", "Options HTML is readable."))

    families = [row for row in _mapping_rows(taxonomy.get("families")) if row.get("id")]
    visibility_by_id = {
        str(row.get("id")): str(row.get("mvp_picker_visibility") or "") for row in families
    }
    invalid_visibility = [
        family_id
        for family_id, visibility in visibility_by_id.items()
        if visibility not in ALLOWED_VISIBILITY
    ]
    if invalid_visibility:
        findings.append(
            _finding(
                "FAIL",
                "taxonomy_visibility_metadata_valid",
                "Some taxonomy families lack valid MVP picker visibility.",
                details=", ".join(sorted(invalid_visibility)),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "taxonomy_visibility_metadata_valid",
                "All taxonomy families declare MVP picker visibility.",
            )
        )

    strict_visible = [
        str(row.get("id"))
        for row in families
        if row.get("mvp_picker_visibility") == "strict_mvp_visible"
    ]
    picker_topics = _extract_picker_topics(options_html)
    if picker_topics == strict_visible:
        findings.append(
            _finding(
                "PASS",
                "strict_mvp_picker_matches_taxonomy",
                "Options topic picker exactly matches strict-MVP taxonomy families.",
                details=", ".join(picker_topics),
            )
        )
    else:
        findings.append(
            _finding(
                "FAIL",
                "strict_mvp_picker_mismatch",
                "Options topic picker does not match strict-MVP taxonomy families.",
                details=(f"expected={','.join(strict_visible)}; actual={','.join(picker_topics)}"),
            )
        )

    hidden_visible = [
        topic for topic in picker_topics if visibility_by_id.get(topic) != "strict_mvp_visible"
    ]
    if hidden_visible:
        findings.append(
            _finding(
                "FAIL",
                "hidden_topics_absent_from_picker",
                "Non-strict-MVP topics appear in the ordinary options picker.",
                details=", ".join(hidden_visible),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "hidden_topics_absent_from_picker",
                "Beta, hidden, register, and legal-gated families are absent from the picker.",
            )
        )

    missing_locale_keys = _missing_locale_keys(locale_root, strict_visible)
    if missing_locale_keys:
        findings.append(
            _finding(
                "FAIL",
                "strict_topic_locale_keys_present",
                "One or more strict-MVP topic chips lack locale messages.",
                details=", ".join(missing_locale_keys),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "strict_topic_locale_keys_present",
                "Every strict-MVP topic chip has locale messages.",
            )
        )

    _append_taxonomy_audit_findings(findings, taxonomy_audit_path)
    _append_quality_artifact_findings(
        findings,
        srs_quality_path,
        code_prefix="srs_quality_harness",
        artifact_label="SRS quality harness",
        require_zero_warn=True,
    )
    _append_quality_artifact_findings(
        findings,
        profile_journey_path,
        code_prefix="en_es_profile_journey",
        artifact_label="en-es profile-preference journey",
        require_zero_warn=False,
    )
    _append_quality_artifact_findings(
        findings,
        installed_journey_path,
        code_prefix="en_es_installed_journey",
        artifact_label="en-es installed-resource journey",
        require_zero_warn=False,
    )

    manual_checks = [dict(row) for row in MANUAL_CHECKS]
    summary = _summarize(findings, manual_checks)
    return {
        "version": 1,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "status": summary["status"],
        "summary": summary,
        "inputs": {
            "taxonomy_json": str(taxonomy_path),
            "options_html": str(options_html_path),
            "locale_root": str(locale_root),
            "taxonomy_audit_json": str(taxonomy_audit_path),
            "srs_quality_json": str(srs_quality_path),
            "profile_journey_json": str(profile_journey_path),
            "installed_journey_json": str(installed_journey_path),
        },
        "strict_mvp_topics": strict_visible,
        "picker_topics": picker_topics,
        "findings": findings,
        "manual_checks": manual_checks,
        "deferred_items": list(DEFERRED_ITEMS),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es SRS Beta Preflight",
        "",
        f"- Status: `{summary.get('status', 'UNKNOWN')}`",
        "- Decision: manual beta signoff is required before external testers.",
        f"- Generated: `{report.get('generated_at', '')}`",
        "",
        "## Automated Checks",
        "",
        "| Level | Code | Message | Details |",
        "| --- | --- | --- | --- |",
    ]
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            "| "
            f"`{finding.get('level', '')}` | "
            f"`{finding.get('code', '')}` | "
            f"{_markdown_cell(str(finding.get('message') or ''))} | "
            f"{_markdown_cell(str(finding.get('details') or ''))} |"
        )

    lines.extend(
        [
            "",
            "## Strict MVP Topic Picker",
            "",
            "The ordinary options-page picker should expose exactly these topics:",
            "",
        ]
    )
    for topic in report.get("strict_mvp_topics") or []:
        lines.append(f"- `{topic}`")

    lines.extend(
        [
            "",
            "## Manual Beta Signoff",
            "",
            "| Status | Check | Verification |",
            "| --- | --- | --- |",
        ]
    )
    for check in _mapping_rows(report.get("manual_checks")):
        lines.append(
            "| "
            f"`{check.get('status', '')}` | "
            f"{_markdown_cell(str(check.get('check') or ''))} | "
            f"{_markdown_cell(str(check.get('verification') or ''))} |"
        )

    lines.extend(["", "## Deferred From Beta", ""])
    for item in report.get("deferred_items") or []:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Recommended Final Commands",
            "",
            "```bash",
            "python3 scripts/testing/srs_beta_preflight_en_es.py",
            "npm --prefix scripts run quality:srs:harness",
            "npm --prefix scripts run quality:srs:summary",
            "npm --prefix scripts run quality:srs:journey:en-es:profile",
            "npm --prefix scripts run quality:srs:journey:en-es:profile:summary",
            "npm --prefix scripts run check",
            "npm --prefix scripts run build",
            "npm --prefix scripts run preflight:cws",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json_or_none(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _mapping_rows(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _extract_picker_topics(html: str) -> list[str]:
    return re.findall(r'data-srs-topic-interest="([^"]+)"', html)


def _missing_locale_keys(locale_root: Path, topic_ids: Sequence[str]) -> list[str]:
    missing: list[str] = []
    expected_keys = [f"topic_srs_{topic_id}" for topic_id in topic_ids]
    for locale in LOCALES:
        messages = _load_json_or_none(locale_root / locale / "messages.json")
        if not isinstance(messages, Mapping):
            missing.extend(f"{locale}:{key}" for key in expected_keys)
            continue
        for key in expected_keys:
            if key not in messages:
                missing.append(f"{locale}:{key}")
    return missing


def _append_taxonomy_audit_findings(findings: list[dict[str, Any]], path: Path) -> None:
    payload = _load_json_or_none(path)
    if not isinstance(payload, Mapping):
        findings.append(
            _finding("WARN", "taxonomy_audit_latest_present", "Latest taxonomy audit is missing.")
        )
        return
    summary = _as_mapping(payload.get("summary"))
    audit_findings = _mapping_rows(payload.get("findings"))
    codes = {str(row.get("code") or ""): row for row in audit_findings}
    if payload.get("status") != "ok" or summary.get("issues"):
        findings.append(
            _finding(
                "FAIL",
                "taxonomy_audit_latest_ok",
                "Latest taxonomy audit reports issues.",
                details=str(summary.get("issues") or ""),
            )
        )
    elif "family_mvp_picker_visibility_valid" not in codes:
        findings.append(
            _finding(
                "FAIL",
                "taxonomy_audit_visibility_finding_present",
                "Latest taxonomy audit does not include visibility validation.",
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "taxonomy_audit_latest_ok",
                "Latest taxonomy audit is ok and includes visibility validation.",
            )
        )


def _append_quality_artifact_findings(
    findings: list[dict[str, Any]],
    path: Path,
    *,
    code_prefix: str,
    artifact_label: str,
    require_zero_warn: bool,
) -> None:
    payload = _load_json_or_none(path)
    if not isinstance(payload, Mapping):
        findings.append(
            _finding(
                "WARN",
                f"{code_prefix}_latest_present",
                f"{artifact_label} latest artifact is missing.",
                details=str(path),
            )
        )
        return
    summary = _as_mapping(payload.get("summary"))
    fail_count = int(summary.get("fail_count") or 0)
    warn_count = int(summary.get("warn_count") or 0)
    should_fail = bool(summary.get("should_fail"))
    status = str(summary.get("status") or "UNKNOWN")
    details = f"status={status}; pass={int(summary.get('pass_count') or 0)}; warn={warn_count}; fail={fail_count}"
    if should_fail or fail_count:
        findings.append(
            _finding(
                "FAIL",
                f"{code_prefix}_latest_no_fail",
                f"{artifact_label} latest artifact has failing findings.",
                details=details,
            )
        )
    elif warn_count and require_zero_warn:
        findings.append(
            _finding(
                "WARN",
                f"{code_prefix}_latest_clean",
                f"{artifact_label} latest artifact has warnings.",
                details=details,
            )
        )
    elif warn_count:
        warning_codes = [
            _warning_detail(row)
            for row in _mapping_rows(payload.get("findings"))
            if row.get("level") == "WARN"
        ]
        findings.append(
            _finding(
                "WARN",
                f"{code_prefix}_latest_review",
                f"{artifact_label} latest artifact has review-only warnings.",
                details=", ".join(warning_codes) or details,
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                f"{code_prefix}_latest_clean",
                f"{artifact_label} latest artifact has no failing or warning findings.",
                details=details,
            )
        )


def _summarize(
    findings: Sequence[Mapping[str, Any]], manual_checks: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    finding_counts = Counter(str(row.get("level") or "UNKNOWN") for row in findings)
    manual_counts = Counter(str(row.get("status") or "UNKNOWN") for row in manual_checks)
    if finding_counts.get("FAIL", 0):
        status = "FAIL"
    elif finding_counts.get("WARN", 0) or manual_counts.get("PENDING", 0):
        status = "REVIEW"
    else:
        status = "PASS"
    return {
        "status": status,
        "finding_counts": dict(sorted(finding_counts.items())),
        "manual_counts": dict(sorted(manual_counts.items())),
    }


def _finding(level: str, code: str, message: str, details: str | None = None) -> dict[str, Any]:
    return {
        "level": level,
        "code": code,
        "message": message,
        "details": details,
    }


def _warning_detail(row: Mapping[str, Any]) -> str:
    code = str(row.get("code") or "WARN")
    details = str(row.get("details") or "").strip()
    return f"{code} ({details})" if details else code


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip() or "-"


if __name__ == "__main__":
    raise SystemExit(main())
