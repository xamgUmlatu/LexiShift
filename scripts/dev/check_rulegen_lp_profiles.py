#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_lp_profiles"
SCHEMA_PATH = PROFILE_DIR / "profile.schema.json"
PRESETS_PATH = PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"
PAIR_RE = re.compile(r"^[a-z]{2,3}-[a-z]{2,3}$")
MECHANISM_KEYS: tuple[str, ...] = (
    "pos_scoring",
    "variants",
    "source_frequency_prior",
    "reverse_check",
    "kaikki_live_demotion",
    "kaikki_risk_family_controls",
    "same_sense_representative_selection",
    "sense_defaultness_competition",
    "provenance_competition",
    "compiled_resources",
    "prepared_sweep_tables",
)


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path | None, payload: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json_out: {path}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _issue(*, profile: str, code: str, path: str, message: str) -> dict[str, str]:
    return {
        "profile": profile,
        "code": code,
        "path": path,
        "message": message,
    }


def _validate_string_list(
    value: object,
    *,
    profile_name: str,
    path: str,
    issues: list[dict[str, str]],
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        issues.append(
            _issue(
                profile=profile_name,
                code="INVALID_TYPE",
                path=path,
                message="expected a list of strings",
            )
        )
        return []
    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_VALUE",
                    path=f"{path}[{index}]",
                    message="expected a non-empty string",
                )
            )
            continue
        normalized.append(item.strip())
    if not allow_empty and not normalized:
        issues.append(
            _issue(
                profile=profile_name,
                code="EMPTY_LIST",
                path=path,
                message="expected at least one string value",
            )
        )
    return normalized


def _validate_lane_list(
    value: object,
    *,
    profile_name: str,
    path: str,
    issues: list[dict[str, str]],
    require_default: bool,
) -> None:
    if not isinstance(value, list):
        issues.append(
            _issue(
                profile=profile_name,
                code="INVALID_TYPE",
                path=path,
                message="expected a list of lane objects",
            )
        )
        return
    default_count = 0
    for index, lane in enumerate(value):
        lane_path = f"{path}[{index}]"
        if not isinstance(lane, dict):
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_TYPE",
                    path=lane_path,
                    message="expected an object",
                )
            )
            continue
        for key in ("lane_id", "family", "pack_id", "record_shape"):
            raw = lane.get(key)
            if not isinstance(raw, str) or not raw.strip():
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="INVALID_VALUE",
                        path=f"{lane_path}.{key}",
                        message="expected a non-empty string",
                    )
                )
        default_for_pair = lane.get("default_for_pair")
        if not isinstance(default_for_pair, bool):
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_VALUE",
                    path=f"{lane_path}.default_for_pair",
                    message="expected a boolean",
                )
            )
        elif default_for_pair:
            default_count += 1
        _validate_string_list(
            lane.get("metadata_capabilities"),
            profile_name=profile_name,
            path=f"{lane_path}.metadata_capabilities",
            issues=issues,
        )
    if require_default and default_count != 1:
        issues.append(
            _issue(
                profile=profile_name,
                code="DEFAULT_LANE_COUNT",
                path=path,
                message="expected exactly one default lane",
            )
        )
    if not require_default and default_count > 1:
        issues.append(
            _issue(
                profile=profile_name,
                code="DEFAULT_LANE_COUNT",
                path=path,
                message="expected at most one default lane",
            )
        )


def _validate_profile_object(
    value: object,
    *,
    profile_name: str,
    path: str,
    required_keys: tuple[str, ...],
    issues: list[dict[str, str]],
) -> dict[str, object]:
    if not isinstance(value, dict):
        issues.append(
            _issue(
                profile=profile_name,
                code="INVALID_TYPE",
                path=path,
                message="expected an object",
            )
        )
        return {}
    for key in required_keys:
        raw = value.get(key)
        if not isinstance(raw, str) or not raw.strip():
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_VALUE",
                    path=f"{path}.{key}",
                    message="expected a non-empty string",
                )
            )
    return value


def _validate_repo_path(
    raw_path: object,
    *,
    profile_name: str,
    path: str,
    issues: list[dict[str, str]],
) -> str | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        issues.append(
            _issue(
                profile=profile_name,
                code="INVALID_VALUE",
                path=path,
                message="expected a non-empty repo-relative path",
            )
        )
        return None
    relative = raw_path.strip()
    absolute = PROJECT_ROOT / relative
    if not absolute.exists():
        issues.append(
            _issue(
                profile=profile_name,
                code="MISSING_PATH",
                path=path,
                message=f"referenced path does not exist: {relative}",
            )
        )
        return None
    return relative


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate machine-readable rulegen LP profile inputs."
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional JSON report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    issues: list[dict[str, str]] = []
    checked_profiles = 0

    if not SCHEMA_PATH.exists():
        issues.append(
            _issue(
                profile="(schema)",
                code="MISSING_SCHEMA",
                path=str(SCHEMA_PATH.relative_to(PROJECT_ROOT)),
                message="profile schema file is missing",
            )
        )

    presets_payload = _load_json(PRESETS_PATH)
    presets = presets_payload.get("presets") if isinstance(presets_payload, dict) else None
    preset_names = set(presets.keys()) if isinstance(presets, dict) else set()
    if not preset_names:
        issues.append(
            _issue(
                profile="(presets)",
                code="INVALID_PRESETS",
                path=str(PRESETS_PATH.relative_to(PROJECT_ROOT)),
                message="benchmark presets could not be loaded",
            )
        )

    profile_paths = sorted(
        path for path in PROFILE_DIR.glob("*.json") if path.name != "profile.schema.json"
    )
    if not profile_paths:
        issues.append(
            _issue(
                profile="(profiles)",
                code="NO_PROFILES",
                path=str(PROFILE_DIR.relative_to(PROJECT_ROOT)),
                message="no LP profile JSON files were found",
            )
        )

    for profile_path in profile_paths:
        checked_profiles += 1
        profile_name = str(profile_path.relative_to(PROJECT_ROOT))
        payload = _load_json(profile_path)
        if not isinstance(payload, dict):
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_TYPE",
                    path="",
                    message="top-level profile must be an object",
                )
            )
            continue

        version = payload.get("version")
        if version != 1:
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_VERSION",
                    path="version",
                    message="expected version == 1",
                )
            )

        pair = payload.get("pair")
        if not isinstance(pair, str) or not PAIR_RE.fullmatch(pair.strip()):
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_VALUE",
                    path="pair",
                    message="expected a directional pair like en-de",
                )
            )
            pair = ""
        pair_from_name = profile_path.stem.replace("_", "-")
        if isinstance(pair, str) and pair and pair != pair_from_name:
            issues.append(
                _issue(
                    profile=profile_name,
                    code="PAIR_FILENAME_MISMATCH",
                    path="pair",
                    message=f"profile pair {pair} does not match filename {pair_from_name}",
                )
            )

        languages = payload.get("languages")
        if not isinstance(languages, dict):
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_TYPE",
                    path="languages",
                    message="expected an object",
                )
            )
        else:
            source = languages.get("source")
            target = languages.get("target")
            if not isinstance(source, str) or not source.strip():
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="INVALID_VALUE",
                        path="languages.source",
                        message="expected a non-empty string",
                    )
                )
            if not isinstance(target, str) or not target.strip():
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="INVALID_VALUE",
                        path="languages.target",
                        message="expected a non-empty string",
                    )
                )
            if (
                isinstance(pair, str)
                and pair
                and isinstance(source, str)
                and isinstance(target, str)
            ):
                expected_source, expected_target = pair.split("-", 1)
                if source != expected_source or target != expected_target:
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code="PAIR_LANGUAGE_MISMATCH",
                            path="languages",
                            message=(f"languages {source}-{target} do not match pair {pair}"),
                        )
                    )

        _validate_lane_list(
            payload.get("translation_lanes"),
            profile_name=profile_name,
            path="translation_lanes",
            issues=issues,
            require_default=True,
        )
        _validate_lane_list(
            payload.get("reverse_lanes"),
            profile_name=profile_name,
            path="reverse_lanes",
            issues=issues,
            require_default=False,
        )

        _validate_profile_object(
            payload.get("pos_profile"),
            profile_name=profile_name,
            path="pos_profile",
            required_keys=("profile_id", "dictionary_profile_id", "compatibility_profile_id"),
            issues=issues,
        )
        normalization_profile = _validate_profile_object(
            payload.get("normalization_profile"),
            profile_name=profile_name,
            path="normalization_profile",
            required_keys=("profile_id",),
            issues=issues,
        )
        _validate_string_list(
            normalization_profile.get("rule_ids"),
            profile_name=profile_name,
            path="normalization_profile.rule_ids",
            issues=issues,
        )
        metadata_family_profile = _validate_profile_object(
            payload.get("metadata_family_profile"),
            profile_name=profile_name,
            path="metadata_family_profile",
            required_keys=("profile_id",),
            issues=issues,
        )
        _validate_string_list(
            metadata_family_profile.get("family_ids"),
            profile_name=profile_name,
            path="metadata_family_profile.family_ids",
            issues=issues,
        )
        _validate_profile_object(
            payload.get("morphology_profile"),
            profile_name=profile_name,
            path="morphology_profile",
            required_keys=("profile_id", "variant_policy"),
            issues=issues,
        )

        mechanism_support = payload.get("mechanism_support")
        if not isinstance(mechanism_support, dict):
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_TYPE",
                    path="mechanism_support",
                    message="expected an object",
                )
            )
        else:
            for key in MECHANISM_KEYS:
                if not isinstance(mechanism_support.get(key), bool):
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code="INVALID_VALUE",
                            path=f"mechanism_support.{key}",
                            message="expected a boolean",
                        )
                    )

        benchmark_profile = payload.get("benchmark_profile")
        if not isinstance(benchmark_profile, dict):
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_TYPE",
                    path="benchmark_profile",
                    message="expected an object",
                )
            )
        else:
            _validate_repo_path(
                benchmark_profile.get("case_file"),
                profile_name=profile_name,
                path="benchmark_profile.case_file",
                issues=issues,
            )
            latest_benchmark_json = _validate_repo_path(
                benchmark_profile.get("latest_benchmark_json"),
                profile_name=profile_name,
                path="benchmark_profile.latest_benchmark_json",
                issues=issues,
            )
            _ = latest_benchmark_json
            preset_name = benchmark_profile.get("preset_name")
            if not isinstance(preset_name, str) or not preset_name.strip():
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="INVALID_VALUE",
                        path="benchmark_profile.preset_name",
                        message="expected a non-empty string",
                    )
                )
            elif preset_name not in preset_names:
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="UNKNOWN_PRESET",
                        path="benchmark_profile.preset_name",
                        message=f"unknown preset: {preset_name}",
                    )
                )
            wrapper_command = benchmark_profile.get("wrapper_command")
            if not isinstance(wrapper_command, str) or not wrapper_command.strip():
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="INVALID_VALUE",
                        path="benchmark_profile.wrapper_command",
                        message="expected a non-empty command string",
                    )
                )

    payload = {
        "generated_at_utc": _now_iso_utc(),
        "profile_dir": str(PROFILE_DIR.relative_to(PROJECT_ROOT)),
        "schema_path": str(SCHEMA_PATH.relative_to(PROJECT_ROOT)),
        "checked_profiles": checked_profiles,
        "issues": issues,
    }
    _write_json(args.json_out, payload)

    if issues:
        for issue in issues:
            location = f"{issue['profile']}:{issue['path']}" if issue["path"] else issue["profile"]
            print(f"[lp-profiles] {issue['code']} {location} - {issue['message']}")
        raise SystemExit(1)

    print(
        f"[check-rulegen-lp-profiles] PASS ({checked_profiles} profiles, schema present, benchmark references valid)"
    )


if __name__ == "__main__":
    main()
