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
PRESETS_PATH = PROJECT_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"
PAIR_RE = re.compile(r"^[a-z]{2,3}-[a-z]{2,3}$")


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path | None, payload: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json_out: {path}")


def _pair_underscore(pair: str) -> str:
    return pair.replace("-", "_")


def _pair_class_prefix(pair: str) -> str:
    return "".join(component.capitalize() for component in pair.split("-"))


def _issue(*, profile: str, code: str, path: str, message: str) -> dict[str, str]:
    return {
        "profile": profile,
        "code": code,
        "path": path,
        "message": message,
    }


def _parse_args_list(raw_args: object) -> list[str]:
    if not isinstance(raw_args, list):
        return []
    values: list[str] = []
    for item in raw_args:
        if isinstance(item, str) and item.strip():
            values.append(item.strip())
    return values


def _collect_profile_paths(project_root: Path) -> list[Path]:
    profile_dir = project_root / "docs" / "test_inputs" / "rulegen_lp_profiles"
    return sorted(path for path in profile_dir.glob("*.json") if path.name != "profile.schema.json")


def validate_rulegen_lp_conformance(*, project_root: Path) -> dict[str, object]:
    issues: list[dict[str, str]] = []
    checked_profiles = 0

    presets_path = project_root / "docs" / "test_inputs" / "rulegen_benchmark_presets.json"
    presets_payload = _load_json(presets_path)
    presets = presets_payload.get("presets") if isinstance(presets_payload, dict) else None
    preset_map = presets if isinstance(presets, dict) else {}
    if not preset_map:
        issues.append(
            _issue(
                profile="(presets)",
                code="INVALID_PRESETS",
                path=str(presets_path.relative_to(project_root)),
                message="benchmark presets could not be loaded",
            )
        )

    profile_paths = _collect_profile_paths(project_root)
    if not profile_paths:
        issues.append(
            _issue(
                profile="(profiles)",
                code="NO_PROFILES",
                path=str(
                    (project_root / "docs" / "test_inputs" / "rulegen_lp_profiles").relative_to(
                        project_root
                    )
                ),
                message="no LP profile JSON files were found",
            )
        )

    for profile_path in profile_paths:
        checked_profiles += 1
        profile_name = str(profile_path.relative_to(project_root))
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
            continue
        pair = pair.strip()
        pair_us = _pair_underscore(pair)
        pair_class = _pair_class_prefix(pair)

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
            continue

        expected_case_file = f"docs/test_inputs/rulegen_benchmark_cases/{pair_us}.json"
        case_file = benchmark_profile.get("case_file")
        if case_file != expected_case_file:
            issues.append(
                _issue(
                    profile=profile_name,
                    code="CASE_FILE_CONVENTION_MISMATCH",
                    path="benchmark_profile.case_file",
                    message=f"expected {expected_case_file}",
                )
            )
        else:
            case_path = project_root / expected_case_file
            if not case_path.exists():
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="MISSING_CASE_FILE",
                        path="benchmark_profile.case_file",
                        message=f"missing benchmark case file: {expected_case_file}",
                    )
                )
            else:
                case_payload = _load_json(case_path)
                if not isinstance(case_payload, dict) or case_payload.get("pair") != pair:
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code="CASE_FILE_PAIR_MISMATCH",
                            path="benchmark_profile.case_file",
                            message=f"benchmark case file pair does not match {pair}",
                        )
                    )

        expected_latest_json = f"docs/test_outputs/rulegen_benchmark_{pair_us}_latest.json"
        latest_benchmark_json = benchmark_profile.get("latest_benchmark_json")
        if latest_benchmark_json != expected_latest_json:
            issues.append(
                _issue(
                    profile=profile_name,
                    code="LATEST_BENCHMARK_CONVENTION_MISMATCH",
                    path="benchmark_profile.latest_benchmark_json",
                    message=f"expected {expected_latest_json}",
                )
            )
        else:
            latest_path = project_root / expected_latest_json
            if not latest_path.exists():
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="MISSING_LATEST_BENCHMARK",
                        path="benchmark_profile.latest_benchmark_json",
                        message=f"missing latest benchmark artifact: {expected_latest_json}",
                    )
                )
            else:
                latest_payload = _load_json(latest_path)
                pairs_payload = (
                    latest_payload.get("pairs") if isinstance(latest_payload, dict) else None
                )
                if not isinstance(pairs_payload, dict) or pair not in pairs_payload:
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code="LATEST_BENCHMARK_PAIR_MISMATCH",
                            path="benchmark_profile.latest_benchmark_json",
                            message=f"benchmark artifact does not contain pair {pair}",
                        )
                    )

        preset_name = benchmark_profile.get("preset_name")
        expected_preset_name = f"{pair_us}_canonical_matrix"
        if not isinstance(preset_name, str) or not preset_name.strip():
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_PRESET_NAME",
                    path="benchmark_profile.preset_name",
                    message="expected a non-empty preset name",
                )
            )
        else:
            preset_name = preset_name.strip()
            if preset_name != expected_preset_name:
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="PRESET_NAMING_CONVENTION_MISMATCH",
                        path="benchmark_profile.preset_name",
                        message=f"expected {expected_preset_name}",
                    )
                )
            preset_payload = preset_map.get(preset_name)
            if not isinstance(preset_payload, dict):
                issues.append(
                    _issue(
                        profile=profile_name,
                        code="MISSING_PRESET",
                        path="benchmark_profile.preset_name",
                        message=f"preset {preset_name} was not found",
                    )
                )
            else:
                args_list = _parse_args_list(preset_payload.get("args"))
                if "--pairs" not in args_list:
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code="PRESET_MISSING_PAIRS_ARG",
                            path="benchmark_profile.preset_name",
                            message=f"preset {preset_name} does not declare --pairs",
                        )
                    )
                else:
                    pair_index = args_list.index("--pairs") + 1
                    pair_value = args_list[pair_index] if pair_index < len(args_list) else ""
                    if pair not in [item.strip() for item in pair_value.split(",") if item.strip()]:
                        issues.append(
                            _issue(
                                profile=profile_name,
                                code="PRESET_PAIR_MISMATCH",
                                path="benchmark_profile.preset_name",
                                message=f"preset {preset_name} does not target pair {pair}",
                            )
                        )

        wrapper_command = benchmark_profile.get("wrapper_command")
        if not isinstance(wrapper_command, str) or not wrapper_command.strip():
            issues.append(
                _issue(
                    profile=profile_name,
                    code="INVALID_WRAPPER_COMMAND",
                    path="benchmark_profile.wrapper_command",
                    message="expected a non-empty wrapper command",
                )
            )
        elif pair not in wrapper_command:
            issues.append(
                _issue(
                    profile=profile_name,
                    code="WRAPPER_COMMAND_PAIR_MISMATCH",
                    path="benchmark_profile.wrapper_command",
                    message=f"wrapper command does not mention pair {pair}",
                )
            )

        pair_module_relative = f"core/lexishift_core/rulegen/pairs/{pair_us}.py"
        pair_module_path = project_root / pair_module_relative
        if not pair_module_path.exists():
            issues.append(
                _issue(
                    profile=profile_name,
                    code="MISSING_PAIR_MODULE",
                    path=pair_module_relative,
                    message=f"missing pair module for {pair}",
                )
            )
        else:
            module_text = pair_module_path.read_text(encoding="utf-8")
            for required_token, code in (
                (f"class {pair_class}RulegenConfig", "PAIR_MODULE_CONFIG_MISSING"),
                (f"def generate_{pair_us}_results", "PAIR_MODULE_RESULTS_MISSING"),
                (f"def generate_{pair_us}_rules", "PAIR_MODULE_RULES_MISSING"),
            ):
                if required_token not in module_text:
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code=code,
                            path=pair_module_relative,
                            message=f"expected token missing: {required_token}",
                        )
                    )

        pairs_init_relative = "core/lexishift_core/rulegen/pairs/__init__.py"
        pairs_init_path = project_root / pairs_init_relative
        if not pairs_init_path.exists():
            issues.append(
                _issue(
                    profile=profile_name,
                    code="MISSING_PAIRS_INIT",
                    path=pairs_init_relative,
                    message="missing rulegen pairs export module",
                )
            )
        else:
            pairs_init_text = pairs_init_path.read_text(encoding="utf-8")
            for required_token, code in (
                (f"{pair_class}RulegenConfig", "PAIRS_INIT_CONFIG_EXPORT_MISSING"),
                (f"generate_{pair_us}_results", "PAIRS_INIT_RESULTS_EXPORT_MISSING"),
                (f"generate_{pair_us}_rules", "PAIRS_INIT_RULES_EXPORT_MISSING"),
            ):
                if required_token not in pairs_init_text:
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code=code,
                            path=pairs_init_relative,
                            message=f"expected token missing: {required_token}",
                        )
                    )

        adapters_relative = "core/lexishift_core/rulegen/adapters.py"
        adapters_path = project_root / adapters_relative
        if not adapters_path.exists():
            issues.append(
                _issue(
                    profile=profile_name,
                    code="MISSING_ADAPTERS_MODULE",
                    path=adapters_relative,
                    message="missing rulegen adapters module",
                )
            )
        else:
            adapters_text = adapters_path.read_text(encoding="utf-8")
            for required_token, code in (
                (f"{pair_class}RulegenConfig", "ADAPTERS_CONFIG_IMPORT_MISSING"),
                (f"generate_{pair_us}_results", "ADAPTERS_RESULTS_IMPORT_MISSING"),
                (f"def _run_{pair_us}_adapter", "ADAPTERS_RUNNER_MISSING"),
                (f'"{pair_us}": _run_{pair_us}_adapter', "ADAPTERS_REGISTRATION_MISSING"),
            ):
                if required_token not in adapters_text:
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code=code,
                            path=adapters_relative,
                            message=f"expected token missing: {required_token}",
                        )
                    )

        capabilities_relative = "core/lexishift_core/helper/lp_capabilities.py"
        capabilities_path = project_root / capabilities_relative
        if not capabilities_path.exists():
            issues.append(
                _issue(
                    profile=profile_name,
                    code="MISSING_LP_CAPABILITIES",
                    path=capabilities_relative,
                    message="missing pair capability registry",
                )
            )
        else:
            capabilities_text = capabilities_path.read_text(encoding="utf-8")
            for required_token, code in (
                (f'"{pair}": PairCapability(', "PAIR_CAPABILITY_ENTRY_MISSING"),
                (f'rulegen_mode="{pair_us}"', "PAIR_CAPABILITY_RULEGEN_MODE_MISSING"),
            ):
                if required_token not in capabilities_text:
                    issues.append(
                        _issue(
                            profile=profile_name,
                            code=code,
                            path=capabilities_relative,
                            message=f"expected token missing: {required_token}",
                        )
                    )

    return {
        "generated_at_utc": _now_iso_utc(),
        "profile_dir": str(
            (project_root / "docs" / "test_inputs" / "rulegen_lp_profiles").relative_to(
                project_root
            )
        ),
        "presets_path": str(presets_path.relative_to(project_root)),
        "checked_profiles": checked_profiles,
        "issues": issues,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that rulegen LP profiles line up with repo paths and naming conventions."
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional JSON report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = validate_rulegen_lp_conformance(project_root=PROJECT_ROOT)
    _write_json(args.json_out, payload)

    issues = payload.get("issues")
    if isinstance(issues, list) and issues:
        for raw_issue in issues:
            if not isinstance(raw_issue, dict):
                continue
            location = (
                f"{raw_issue.get('profile')}:{raw_issue.get('path')}"
                if raw_issue.get("path")
                else str(raw_issue.get("profile"))
            )
            print(
                f"[lp-conformance] {raw_issue.get('code')} {location} - {raw_issue.get('message')}"
            )
        raise SystemExit(1)

    print(
        "[check-rulegen-lp-conformance] PASS "
        f"({payload['checked_profiles']} profiles, conventions aligned)"
    )


if __name__ == "__main__":
    main()
