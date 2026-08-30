#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = PROJECT_ROOT / "docs/test_inputs/srs_topic_family_registry.json"
DEFAULT_PAIR_MATRIX = PROJECT_ROOT / "docs/test_inputs/srs_topic_pair_support_matrix.json"
DEFAULT_TAXONOMIES = {
    "en-ja": PROJECT_ROOT / "docs/test_inputs/srs_topic_preference_taxonomy_en_ja.json",
    "en-es": PROJECT_ROOT / "docs/test_inputs/srs_topic_preference_taxonomy_en_es.json",
}
DEFAULT_EN_ES_RUNTIME_OVERLAY = (
    PROJECT_ROOT / "docs/test_outputs/srs_topic_reviewed_overlay_merged_en_es_latest.json"
)
DEFAULT_OPTIONS_HTML = PROJECT_ROOT / "apps/chrome-extension/options.html"
DEFAULT_TOPIC_SUPPORT_JS = PROJECT_ROOT / "apps/chrome-extension/options/core/srs_topic_support.js"
DEFAULT_JSON_OUT = PROJECT_ROOT / "docs/test_outputs/srs_topic_family_registry_latest.json"
DEFAULT_MARKDOWN_OUT = PROJECT_ROOT / "docs/test_outputs/srs_topic_family_registry_latest.md"

TOPIC_STATE_KEYS = (
    "picker_supported_topics",
    "hidden_overlay_topics",
    "planned_source_required_topics",
    "not_applicable_topics",
)
REGISTER_STATE_KEYS = ("future_register_topics",)
ALLOWED_AXES = {"topic", "register"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate canonical SRS topic/register ids against per-LP support, "
            "topic taxonomies, and the extension topic-chip support contract."
        )
    )
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--pair-matrix-json", type=Path, default=DEFAULT_PAIR_MATRIX)
    parser.add_argument("--options-html", type=Path, default=DEFAULT_OPTIONS_HTML)
    parser.add_argument("--topic-support-js", type=Path, default=DEFAULT_TOPIC_SUPPORT_JS)
    parser.add_argument(
        "--en-es-runtime-overlay-json",
        type=Path,
        default=DEFAULT_EN_ES_RUNTIME_OVERLAY,
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        registry_path=args.registry_json,
        pair_matrix_path=args.pair_matrix_json,
        taxonomy_paths=DEFAULT_TAXONOMIES,
        options_html_path=args.options_html,
        topic_support_js_path=args.topic_support_js,
        en_es_runtime_overlay_path=args.en_es_runtime_overlay_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    pair_matrix_path: Path = DEFAULT_PAIR_MATRIX,
    taxonomy_paths: Mapping[str, Path] = DEFAULT_TAXONOMIES,
    options_html_path: Path = DEFAULT_OPTIONS_HTML,
    topic_support_js_path: Path = DEFAULT_TOPIC_SUPPORT_JS,
    en_es_runtime_overlay_path: Path = DEFAULT_EN_ES_RUNTIME_OVERLAY,
    generated_at: str | None = None,
) -> dict[str, object]:
    registry = _load_json(registry_path)
    pair_matrix = _load_json(pair_matrix_path)
    taxonomy_payloads = {
        pair: _load_json(path) for pair, path in taxonomy_paths.items() if path.exists()
    }
    findings: list[dict[str, object]] = []
    findings.extend(validate_registry(registry))
    findings.extend(validate_pair_matrix(registry, pair_matrix))
    findings.extend(validate_taxonomies(registry, pair_matrix, taxonomy_payloads))
    findings.extend(validate_extension_support(pair_matrix, topic_support_js_path))
    findings.extend(validate_options_picker(pair_matrix, options_html_path))
    findings.extend(validate_runtime_overlay(pair_matrix, en_es_runtime_overlay_path))
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_topic_family_registry_validated"
            if status == "ok"
            else "srs_topic_family_registry_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "registry_json": _repo_path(registry_path),
            "pair_matrix_json": _repo_path(pair_matrix_path),
            "taxonomy_json": {
                pair: _repo_path(path) for pair, path in sorted(taxonomy_paths.items())
            },
            "options_html": _repo_path(options_html_path),
            "topic_support_js": _repo_path(topic_support_js_path),
            "en_es_runtime_overlay_json": _repo_path(en_es_runtime_overlay_path),
        },
        "registry": _registry_summary(registry),
        "pair_support": _pair_support_summary(pair_matrix),
        "findings": findings,
        "summary": {
            "finding_counts": dict(Counter(row["level"] for row in findings)),
            "issues": [row["code"] for row in findings if row["level"] == "FAIL"],
            "warnings": [row["code"] for row in findings if row["level"] == "WARN"],
        },
    }


def validate_registry(registry: Mapping[str, object]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    families = _mapping_rows(registry.get("families"))
    family_ids = [_token(row.get("id")) for row in families]
    duplicates = _duplicates(family_ids)
    if int(registry.get("schema_version") or 0) >= 1:
        findings.append(_finding("PASS", "registry_schema_present", "Registry schema is present."))
    else:
        findings.append(_finding("FAIL", "registry_schema_missing", "Registry schema is missing."))
    if families and not duplicates and all(family_ids):
        findings.append(_finding("PASS", "registry_family_ids_unique", "Family ids are unique."))
    else:
        findings.append(
            _finding(
                "FAIL",
                "registry_family_ids_invalid",
                "Family ids are missing or duplicated.",
                details=", ".join(duplicates),
            )
        )
    metadata_failures: list[str] = []
    family_set = {family_id for family_id in family_ids if family_id}
    for index, row in enumerate(families):
        family_id = _token(row.get("id")) or f"index:{index}"
        axis = _token(row.get("axis"))
        if axis not in ALLOWED_AXES:
            metadata_failures.append(f"{family_id}.axis")
        for field in ("display_name", "ux_group", "pair_scope", "semantic_summary"):
            if not str(row.get(field) or "").strip():
                metadata_failures.append(f"{family_id}.{field}")
        parent = _token(row.get("parent_family"))
        if parent and parent not in family_set:
            metadata_failures.append(f"{family_id}.parent_family:{parent}")
        for child in _string_list(row.get("split_children")):
            if child not in family_set:
                metadata_failures.append(f"{family_id}.split_child:{child}")
    if metadata_failures:
        findings.append(
            _finding(
                "FAIL",
                "registry_family_metadata_invalid",
                "Registry families must declare stable metadata and valid parent/child links.",
                details=", ".join(metadata_failures),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "registry_family_metadata_valid",
                "Registry families declare stable metadata and valid parent/child links.",
            )
        )
    lifecycle = _as_mapping(registry.get("lifecycle_policy"))
    if lifecycle.get("family_ids_are_append_only") is True:
        findings.append(
            _finding("PASS", "registry_ids_append_only", "Canonical family ids are append-only.")
        )
    else:
        findings.append(
            _finding(
                "FAIL",
                "registry_ids_not_append_only",
                "Canonical family ids must be explicitly append-only.",
            )
        )
    return findings


def validate_pair_matrix(
    registry: Mapping[str, object],
    pair_matrix: Mapping[str, object],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    families = {str(row.get("id") or ""): row for row in _mapping_rows(registry.get("families"))}
    topic_ids = {family_id for family_id, row in families.items() if row.get("axis") == "topic"}
    register_ids = {
        family_id for family_id, row in families.items() if row.get("axis") == "register"
    }
    pairs = _as_mapping(pair_matrix.get("pairs"))
    if int(pair_matrix.get("schema_version") or 0) >= 1 and pairs:
        findings.append(_finding("PASS", "pair_matrix_schema_present", "Pair matrix is present."))
    else:
        findings.append(_finding("FAIL", "pair_matrix_schema_missing", "Pair matrix is missing."))
    for pair, pair_payload in sorted(pairs.items()):
        pair_config = _as_mapping(pair_payload)
        findings.extend(
            _validate_pair_support_partition(
                pair=str(pair),
                pair_config=pair_config,
                families=families,
                topic_ids=topic_ids,
                register_ids=register_ids,
            )
        )
    return findings


def validate_taxonomies(
    registry: Mapping[str, object],
    pair_matrix: Mapping[str, object],
    taxonomy_payloads: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    registry_by_id = {
        str(row.get("id") or ""): row for row in _mapping_rows(registry.get("families"))
    }
    matrix_pairs = _as_mapping(pair_matrix.get("pairs"))
    for pair, taxonomy in sorted(taxonomy_payloads.items()):
        families = _mapping_rows(taxonomy.get("families"))
        family_ids = [_token(row.get("id")) for row in families]
        unknown = sorted({family_id for family_id in family_ids if family_id not in registry_by_id})
        if unknown:
            findings.append(
                _finding(
                    "FAIL",
                    f"{pair}_taxonomy_unknown_families",
                    "Taxonomy contains families outside the canonical registry.",
                    details=", ".join(unknown),
                )
            )
        else:
            findings.append(
                _finding(
                    "PASS",
                    f"{pair}_taxonomy_families_registered",
                    "Taxonomy family ids are registered canonical ids.",
                )
            )
        mismatch_details: list[str] = []
        for row in families:
            family_id = _token(row.get("id"))
            canonical = _as_mapping(registry_by_id.get(family_id))
            if not canonical:
                continue
            for field in ("display_name", "axis", "ux_group", "pair_scope"):
                actual = row.get(field)
                if actual is None:
                    continue
                if str(actual) != str(canonical.get(field)):
                    mismatch_details.append(
                        f"{family_id}.{field}:taxonomy={actual!s}:registry={canonical.get(field)!s}"
                    )
        if mismatch_details:
            findings.append(
                _finding(
                    "FAIL",
                    f"{pair}_taxonomy_registry_metadata_mismatch",
                    "Taxonomy metadata conflicts with the canonical registry.",
                    details=", ".join(mismatch_details),
                )
            )
        else:
            findings.append(
                _finding(
                    "PASS",
                    f"{pair}_taxonomy_registry_metadata_aligned",
                    "Taxonomy metadata is aligned where it declares canonical fields.",
                )
            )
        matrix_config = _as_mapping(matrix_pairs.get(pair))
        matrix_ids = _all_pair_family_ids(matrix_config)
        taxonomy_not_in_matrix = sorted(
            {family_id for family_id in family_ids if family_id not in matrix_ids}
        )
        if taxonomy_not_in_matrix:
            findings.append(
                _finding(
                    "FAIL",
                    f"{pair}_taxonomy_not_represented_in_pair_matrix",
                    "Taxonomy families must be represented in the pair support matrix.",
                    details=", ".join(taxonomy_not_in_matrix),
                )
            )
        else:
            findings.append(
                _finding(
                    "PASS",
                    f"{pair}_taxonomy_represented_in_pair_matrix",
                    "Taxonomy families are represented in the pair support matrix.",
                )
            )
        strict_visible = [
            _token(row.get("id"))
            for row in families
            if _token(row.get("mvp_picker_visibility")) == "strict_mvp_visible"
        ]
        if strict_visible:
            matrix_picker = _string_list(matrix_config.get("picker_supported_topics"))
            if strict_visible == matrix_picker:
                findings.append(
                    _finding(
                        "PASS",
                        f"{pair}_strict_visible_matches_pair_picker",
                        "Strict visible taxonomy topics match pair picker support.",
                    )
                )
            else:
                findings.append(
                    _finding(
                        "FAIL",
                        f"{pair}_strict_visible_picker_mismatch",
                        "Strict visible taxonomy topics do not match pair picker support.",
                        details=f"taxonomy={strict_visible}; matrix={matrix_picker}",
                    )
                )
    return findings


def validate_extension_support(
    pair_matrix: Mapping[str, object],
    topic_support_js_path: Path = DEFAULT_TOPIC_SUPPORT_JS,
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if not topic_support_js_path.exists():
        return [
            _finding(
                "FAIL",
                "extension_topic_support_missing",
                "Extension topic support JS was not found.",
                details=_repo_path(topic_support_js_path),
            )
        ]
    source = topic_support_js_path.read_text(encoding="utf-8")
    pairs = _as_mapping(pair_matrix.get("pairs"))
    mismatches: list[str] = []
    for pair, pair_payload in sorted(pairs.items()):
        expected = sorted(_string_list(_as_mapping(pair_payload).get("picker_supported_topics")))
        actual = sorted(_extract_js_supported_topics(source, str(pair)))
        if actual != expected:
            mismatches.append(f"{pair}:js={actual}:matrix={expected}")
    if mismatches:
        findings.append(
            _finding(
                "FAIL",
                "extension_topic_support_pair_matrix_mismatch",
                "Extension topic-chip support must mirror the pair support matrix.",
                details="; ".join(mismatches),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                "extension_topic_support_pair_matrix_aligned",
                "Extension topic-chip support mirrors the pair support matrix.",
            )
        )
    return findings


def validate_options_picker(
    pair_matrix: Mapping[str, object],
    options_html_path: Path = DEFAULT_OPTIONS_HTML,
) -> list[dict[str, object]]:
    if not options_html_path.exists():
        return [
            _finding(
                "FAIL",
                "options_topic_picker_missing",
                "Options HTML was not found.",
                details=_repo_path(options_html_path),
            )
        ]
    html = options_html_path.read_text(encoding="utf-8")
    actual = re.findall(r'data-srs-topic-interest="([^"]+)"', html)
    en_es_config = _as_mapping(_as_mapping(pair_matrix.get("pairs")).get("en-es"))
    expected = _string_list(en_es_config.get("picker_supported_topics"))
    if actual == expected:
        return [
            _finding(
                "PASS",
                "options_topic_picker_matches_en_es_strict_picker",
                "Current visible topic picker matches the strict en-es MVP picker set.",
            )
        ]
    return [
        _finding(
            "FAIL",
            "options_topic_picker_mismatch",
            "Current visible topic picker does not match the strict en-es MVP picker set.",
            details=f"options={actual}; matrix={expected}",
        )
    ]


def validate_runtime_overlay(
    pair_matrix: Mapping[str, object],
    en_es_runtime_overlay_path: Path = DEFAULT_EN_ES_RUNTIME_OVERLAY,
) -> list[dict[str, object]]:
    if not en_es_runtime_overlay_path.exists():
        return [
            _finding(
                "WARN",
                "en_es_runtime_overlay_missing",
                "en-es runtime overlay artifact is missing; skipping overlay support check.",
                details=_repo_path(en_es_runtime_overlay_path),
            )
        ]
    payload = _load_json(en_es_runtime_overlay_path)
    counts = _as_mapping(
        _as_mapping(payload.get("summary")).get("runtime_effective_counts_by_topic")
    )
    actual = {str(key) for key in counts}
    en_es_config = _as_mapping(_as_mapping(pair_matrix.get("pairs")).get("en-es"))
    required_topics = set(
        _string_list(en_es_config.get("picker_supported_topics"))
        + _string_list(en_es_config.get("hidden_overlay_topics"))
    )
    optional_registers = set(_string_list(en_es_config.get("future_register_topics")))
    allowed = required_topics | optional_registers
    missing_required = sorted(required_topics - actual)
    unexpected = sorted(actual - allowed)
    if not missing_required and not unexpected:
        return [
            _finding(
                "PASS",
                "en_es_runtime_overlay_matches_supported_runtime_topics",
                "en-es runtime overlay rows stay within supported topics and hidden registers.",
            )
        ]
    return [
        _finding(
            "FAIL",
            "en_es_runtime_overlay_topic_mismatch",
            "en-es runtime overlay rows differ from supported topics and hidden registers.",
            details=f"missing_required={missing_required}; unexpected={unexpected}",
        )
    ]


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [
        "# SRS Topic Family Registry",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        "",
        "## Pair Support",
        "",
        "| Pair | Picker Topics | Hidden Overlay | Planned | Registers Hidden | Not Applicable |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    pair_support = _as_mapping(report.get("pair_support"))
    for pair in sorted(pair_support):
        row = _as_mapping(pair_support[pair])
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{pair}`",
                    str(len(_string_list(row.get("picker_supported_topics")))),
                    str(len(_string_list(row.get("hidden_overlay_topics")))),
                    str(len(_string_list(row.get("planned_source_required_topics")))),
                    str(len(_string_list(row.get("future_register_topics")))),
                    str(len(_string_list(row.get("not_applicable_topics")))),
                )
            )
            + " |"
        )
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        line = f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: {finding.get('message', '')}"
        details = str(finding.get("details") or "").strip()
        if details:
            line += f" Details: {details}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def _validate_pair_support_partition(
    *,
    pair: str,
    pair_config: Mapping[str, object],
    families: Mapping[str, Mapping[str, object]],
    topic_ids: set[str],
    register_ids: set[str],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    all_state_values: dict[str, str] = {}
    duplicates: list[str] = []
    unknown: list[str] = []
    wrong_axis: list[str] = []
    for state in TOPIC_STATE_KEYS + REGISTER_STATE_KEYS:
        expected_axis = "register" if state in REGISTER_STATE_KEYS else "topic"
        for family_id in _string_list(pair_config.get(state)):
            if family_id in all_state_values:
                duplicates.append(f"{family_id}:{all_state_values[family_id]}+{state}")
            all_state_values[family_id] = state
            family = families.get(family_id)
            if not family:
                unknown.append(f"{state}:{family_id}")
                continue
            if family.get("axis") != expected_axis:
                wrong_axis.append(f"{state}:{family_id}:{family.get('axis')}")
    if duplicates or unknown or wrong_axis:
        findings.append(
            _finding(
                "FAIL",
                f"{pair}_pair_support_state_invalid",
                "Pair support states must be unique, registered, and axis-correct.",
                details="; ".join(duplicates + unknown + wrong_axis),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                f"{pair}_pair_support_state_valid",
                "Pair support states are unique, registered, and axis-correct.",
            )
        )
    target = _pair_target_language(pair)
    applicable_topics = {
        family_id
        for family_id in topic_ids
        if _family_applies_to_target(families[family_id], target)
    }
    not_applicable_topics = {
        family_id
        for family_id in topic_ids
        if not _family_applies_to_target(families[family_id], target)
    }
    declared_applicable = set()
    for state in (
        "picker_supported_topics",
        "hidden_overlay_topics",
        "planned_source_required_topics",
    ):
        declared_applicable.update(_string_list(pair_config.get(state)))
    declared_not_applicable = set(_string_list(pair_config.get("not_applicable_topics")))
    missing_applicable = sorted(applicable_topics - declared_applicable)
    extra_applicable = sorted(declared_applicable - applicable_topics)
    missing_not_applicable = sorted(not_applicable_topics - declared_not_applicable)
    extra_not_applicable = sorted(declared_not_applicable - not_applicable_topics)
    if missing_applicable or extra_applicable or missing_not_applicable or extra_not_applicable:
        findings.append(
            _finding(
                "FAIL",
                f"{pair}_canonical_topic_partition_incomplete",
                "Pair topic support must partition the canonical topic palette.",
                details=(
                    f"missing_applicable={missing_applicable}; "
                    f"extra_applicable={extra_applicable}; "
                    f"missing_not_applicable={missing_not_applicable}; "
                    f"extra_not_applicable={extra_not_applicable}"
                ),
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                f"{pair}_canonical_topic_partition_complete",
                "Pair topic support partitions the canonical topic palette.",
            )
        )
    declared_registers = set(_string_list(pair_config.get("future_register_topics")))
    missing_registers = sorted(register_ids - declared_registers)
    extra_registers = sorted(declared_registers - register_ids)
    if missing_registers or extra_registers:
        findings.append(
            _finding(
                "FAIL",
                f"{pair}_canonical_register_partition_incomplete",
                "Pair register support must account for canonical register families.",
                details=f"missing={missing_registers}; extra={extra_registers}",
            )
        )
    else:
        findings.append(
            _finding(
                "PASS",
                f"{pair}_canonical_register_partition_complete",
                "Pair register support accounts for canonical register families.",
            )
        )
    return findings


def _extract_js_supported_topics(source: str, pair: str) -> list[str]:
    pattern = re.compile(
        rf'"{re.escape(pair)}"\s*:\s*new Set\(\s*\[(?P<body>.*?)\]\s*\)',
        flags=re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        return []
    return re.findall(r'"([^"]+)"', match.group("body"))


def _all_pair_family_ids(pair_config: Mapping[str, object]) -> set[str]:
    family_ids: set[str] = set()
    for state in TOPIC_STATE_KEYS + REGISTER_STATE_KEYS:
        family_ids.update(_string_list(pair_config.get(state)))
    return family_ids


def _family_applies_to_target(family: Mapping[str, object], target_language: str) -> bool:
    scope = str(family.get("pair_scope") or "").strip()
    if scope == "all_supported_pairs":
        return True
    if scope.startswith("target_language:"):
        return scope.split(":", 1)[1] == target_language
    return False


def _pair_target_language(pair: str) -> str:
    parts = pair.split("-", 1)
    return parts[1] if len(parts) == 2 else ""


def _registry_summary(registry: Mapping[str, object]) -> dict[str, object]:
    families = _mapping_rows(registry.get("families"))
    counts = Counter(str(row.get("axis") or "") for row in families)
    return {
        "registry_id": str(registry.get("registry_id") or ""),
        "family_count": len(families),
        "counts_by_axis": dict(counts),
        "family_ids": [_token(row.get("id")) for row in families],
    }


def _pair_support_summary(pair_matrix: Mapping[str, object]) -> dict[str, object]:
    summary: dict[str, object] = {}
    for pair, pair_payload in sorted(_as_mapping(pair_matrix.get("pairs")).items()):
        pair_config = _as_mapping(pair_payload)
        summary[str(pair)] = {
            state: _string_list(pair_config.get(state))
            for state in TOPIC_STATE_KEYS + REGISTER_STATE_KEYS
        }
    return summary


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _token(value: object) -> str:
    return str(value or "").strip()


def _duplicates(values: Sequence[str]) -> list[str]:
    counts = Counter(value for value in values if value)
    return sorted(value for value, count in counts.items() if count > 1)


def _finding(
    level: str,
    code: str,
    message: str,
    *,
    details: str = "",
) -> dict[str, object]:
    row: dict[str, object] = {
        "level": level,
        "code": code,
        "message": message,
    }
    if details:
        row["details"] = details
    return row


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(Path(path).resolve())


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
