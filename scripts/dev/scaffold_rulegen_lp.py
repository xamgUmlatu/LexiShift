#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
from string import Template
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates" / "rulegen_lp"
PAIR_RE = re.compile(r"^([a-z]{2,3})-([a-z]{2,3})$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold the rulegen onboarding package for a new language pair."
    )
    parser.add_argument("--pair", required=True, help="Directional pair key, for example en-fr.")
    parser.add_argument(
        "--translation-family",
        required=True,
        help="Primary forward source family, for example freedict or kaikki.",
    )
    parser.add_argument(
        "--translation-pack-id",
        required=True,
        help="Primary forward pack id, for example freedict-fr-en.",
    )
    parser.add_argument(
        "--reverse-family",
        help="Optional reverse source family, for example freedict or kaikki.",
    )
    parser.add_argument(
        "--reverse-pack-id",
        help="Optional reverse pack id, for example freedict-en-fr.",
    )
    parser.add_argument(
        "--translation-record-shape",
        help="Optional explicit forward record shape override.",
    )
    parser.add_argument(
        "--reverse-record-shape",
        help="Optional explicit reverse record shape override.",
    )
    parser.add_argument(
        "--with-roadmap",
        action="store_true",
        help="Also create docs/language_pairs/<pair>_workstream_roadmap.md from the checklist template.",
    )
    parser.add_argument(
        "--with-code-stubs",
        action="store_true",
        help="Also create a pair-module stub and a skipped starter test from templates.",
    )
    parser.add_argument(
        "--with-integration-handoff",
        action="store_true",
        help="Also create docs/language_pairs/<pair>_integration_handoff.md with central wiring follow-ups.",
    )
    parser.add_argument(
        "--with-benchmark-preset-starter",
        action="store_true",
        help="Also create docs/language_pairs/<pair>_benchmark_preset_starter.md with a starter preset snippet.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite scaffolded files if they already exist.",
    )
    return parser.parse_args()


def _normalize_pair(pair: str) -> tuple[str, str, str]:
    raw = str(pair or "").strip().lower()
    match = PAIR_RE.fullmatch(raw)
    if match is None:
        raise ValueError(f"invalid pair {pair!r}; expected directional form like en-fr")
    return raw, match.group(1), match.group(2)


def _pair_underscore(pair: str) -> str:
    return pair.replace("-", "_")


def _pair_class_prefix(pair: str) -> str:
    return "".join(component.capitalize() for component in pair.split("-"))


def infer_record_shape(*, family: str, reverse: bool) -> str:
    normalized = str(family or "").strip().lower()
    if normalized == "freedict":
        return "freedict_gloss_ordered"
    if normalized == "kaikki":
        return (
            "wiktionary_kaikki_translation_ordered"
            if reverse
            else "wiktionary_kaikki_gloss_ordered"
        )
    return "TODO_record_shape"


def _profile_id(pair: str, suffix: str) -> str:
    return f"{_pair_underscore(pair)}_{suffix}"


def build_profile_payload(
    *,
    pair: str,
    translation_family: str,
    translation_pack_id: str,
    reverse_family: str | None = None,
    reverse_pack_id: str | None = None,
    translation_record_shape: str | None = None,
    reverse_record_shape: str | None = None,
) -> dict[str, Any]:
    normalized_pair, source_lang, target_lang = _normalize_pair(pair)
    translation_family_norm = str(translation_family or "").strip().lower()
    reverse_family_norm = str(reverse_family or "").strip().lower() if reverse_family else None

    forward_lane = {
        "lane_id": "canonical_primary",
        "family": translation_family_norm,
        "pack_id": str(translation_pack_id).strip(),
        "record_shape": str(
            translation_record_shape
            or infer_record_shape(family=translation_family_norm, reverse=False)
        ),
        "default_for_pair": True,
        "metadata_capabilities": ["TODO_metadata_capability"],
    }
    reverse_lanes: list[dict[str, Any]] = []
    if reverse_pack_id:
        reverse_lanes.append(
            {
                "lane_id": "canonical_reverse",
                "family": reverse_family_norm or "TODO_reverse_family",
                "pack_id": str(reverse_pack_id).strip(),
                "record_shape": str(
                    reverse_record_shape
                    or infer_record_shape(
                        family=reverse_family_norm or "",
                        reverse=True,
                    )
                ),
                "default_for_pair": True,
                "metadata_capabilities": ["TODO_metadata_capability"],
            }
        )

    return {
        "version": 1,
        "pair": normalized_pair,
        "languages": {
            "source": source_lang,
            "target": target_lang,
        },
        "translation_lanes": [forward_lane],
        "reverse_lanes": reverse_lanes,
        "pos_profile": {
            "profile_id": _profile_id(normalized_pair, "pos_v1"),
            "dictionary_profile_id": "TODO_dictionary_profile_id",
            "compatibility_profile_id": "default_pos_compatibility_v1",
        },
        "normalization_profile": {
            "profile_id": _profile_id(normalized_pair, "normalization_v1"),
            "rule_ids": ["TODO_normalization_rule"],
        },
        "metadata_family_profile": {
            "profile_id": _profile_id(normalized_pair, "metadata_families_v1"),
            "family_ids": ["TODO_family_id"],
        },
        "morphology_profile": {
            "profile_id": _profile_id(normalized_pair, "morphology_v1"),
            "variant_policy": "TODO_variant_policy",
        },
        "mechanism_support": {
            "pos_scoring": False,
            "variants": False,
            "source_frequency_prior": False,
            "reverse_check": False,
            "kaikki_live_demotion": False,
            "kaikki_risk_family_controls": False,
            "same_sense_representative_selection": False,
            "sense_defaultness_competition": False,
            "provenance_competition": False,
            "compiled_resources": False,
            "prepared_sweep_tables": False,
        },
        "benchmark_profile": {
            "case_file": f"docs/test_inputs/rulegen_benchmark_cases/{_pair_underscore(normalized_pair)}.json",
            "preset_name": f"{_pair_underscore(normalized_pair)}_canonical_matrix",
            "wrapper_command": f"python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs {normalized_pair}",
            "latest_benchmark_json": f"docs/test_outputs/rulegen_benchmark_{_pair_underscore(normalized_pair)}_latest.json",
        },
    }


def build_benchmark_case_payload(*, pair: str) -> dict[str, Any]:
    normalized_pair, _, _ = _normalize_pair(pair)
    return {
        "version": 1,
        "pair": normalized_pair,
        "description": f"LexiShift rulegen benchmark cases for {normalized_pair}.",
        "cases": [],
    }


def render_workstream_roadmap(*, pair: str, template_text: str | None = None) -> str:
    normalized_pair, _, target_lang = _normalize_pair(pair)
    today = date.today().isoformat()
    template = template_text
    if template is None:
        template_path = PROJECT_ROOT / "docs" / "rulegen" / "lp_onboarding_checklist_template.md"
        template = template_path.read_text(encoding="utf-8")
    lines = template.splitlines()
    body_start = 0
    for index, line in enumerate(lines):
        if line.startswith("## Copy Rules"):
            body_start = index
            break
    body = "\n".join(lines[body_start:]).replace("<source-target>", normalized_pair)
    body = body.replace("<target>", target_lang)
    return _render_template(
        "workstream_roadmap.md.tmpl",
        pair=normalized_pair,
        today=today,
        checklist_body=body,
    )


def render_pair_module_stub(
    *,
    pair: str,
    translation_family: str,
    translation_pack_id: str,
    reverse_family: str | None = None,
    reverse_pack_id: str | None = None,
) -> str:
    normalized_pair, _, _ = _normalize_pair(pair)
    reverse_summary = (
        f"{str(reverse_family or '').strip().lower()} / {str(reverse_pack_id).strip()}"
        if reverse_pack_id
        else "none yet"
    )
    return _render_template(
        "pair_module.py.tmpl",
        pair=normalized_pair,
        pair_underscore=_pair_underscore(normalized_pair),
        pair_class_prefix=_pair_class_prefix(normalized_pair),
        translation_family=str(translation_family or "").strip().lower(),
        translation_pack_id=str(translation_pack_id).strip(),
        reverse_summary=reverse_summary,
    )


def render_pair_test_stub(*, pair: str) -> str:
    normalized_pair, _, _ = _normalize_pair(pair)
    return _render_template(
        "pair_test.py.tmpl",
        pair=normalized_pair,
        pair_underscore=_pair_underscore(normalized_pair),
        pair_class_prefix=_pair_class_prefix(normalized_pair),
    )


def render_integration_handoff(
    *,
    pair: str,
    translation_family: str,
    translation_pack_id: str,
    translation_record_shape: str | None = None,
    reverse_family: str | None = None,
    reverse_pack_id: str | None = None,
    reverse_record_shape: str | None = None,
    with_roadmap: bool = False,
) -> str:
    normalized_pair, _, _ = _normalize_pair(pair)
    translation_family_norm = str(translation_family or "").strip().lower()
    translation_shape = str(
        translation_record_shape
        or infer_record_shape(family=translation_family_norm, reverse=False)
    )
    if reverse_pack_id:
        reverse_family_norm = str(reverse_family or "").strip().lower() or "TODO_reverse_family"
        reverse_shape = str(
            reverse_record_shape or infer_record_shape(family=reverse_family_norm, reverse=True)
        )
        reverse_summary = (
            f"{reverse_family_norm} / {str(reverse_pack_id).strip()} ({reverse_shape})"
        )
    else:
        reverse_summary = "none yet"
    roadmap_line = (
        f"- `docs/language_pairs/{_pair_underscore(normalized_pair)}_workstream_roadmap.md`"
        if with_roadmap
        else "- roadmap not scaffolded in this run"
    )
    return _render_template(
        "integration_handoff.md.tmpl",
        today=date.today().isoformat(),
        pair=normalized_pair,
        pair_underscore=_pair_underscore(normalized_pair),
        pair_class_prefix=_pair_class_prefix(normalized_pair),
        translation_family=translation_family_norm,
        translation_pack_id=str(translation_pack_id).strip(),
        translation_record_shape=translation_shape,
        reverse_summary=reverse_summary,
        roadmap_line=roadmap_line,
        preset_name=f"{_pair_underscore(normalized_pair)}_canonical_matrix",
        wrapper_command=f"python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs {normalized_pair}",
    )


def render_benchmark_preset_starter(
    *,
    pair: str,
    reverse_pack_id: str | None = None,
) -> str:
    normalized_pair, _, _ = _normalize_pair(pair)
    return _render_template(
        "benchmark_preset_starter.md.tmpl",
        today=date.today().isoformat(),
        pair=normalized_pair,
        preset_name=f"{_pair_underscore(normalized_pair)}_canonical_matrix",
        wrapper_command=f"python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs {normalized_pair}",
        reverse_enabled_values="false,true" if reverse_pack_id else "false",
    )


def _render_template(template_name: str, **context: str) -> str:
    template_path = TEMPLATE_ROOT / template_name
    template_text = template_path.read_text(encoding="utf-8")
    return Template(template_text).substitute(**context)


def _write_json(path: Path, payload: dict[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scaffold_rulegen_lp(
    *,
    project_root: Path,
    pair: str,
    translation_family: str,
    translation_pack_id: str,
    reverse_family: str | None = None,
    reverse_pack_id: str | None = None,
    translation_record_shape: str | None = None,
    reverse_record_shape: str | None = None,
    with_roadmap: bool = False,
    with_code_stubs: bool = False,
    with_integration_handoff: bool = False,
    with_benchmark_preset_starter: bool = False,
    force: bool = False,
) -> dict[str, str]:
    normalized_pair, _, _ = _normalize_pair(pair)
    pair_us = _pair_underscore(normalized_pair)

    profile_path = project_root / "docs" / "test_inputs" / "rulegen_lp_profiles" / f"{pair_us}.json"
    cases_path = (
        project_root / "docs" / "test_inputs" / "rulegen_benchmark_cases" / f"{pair_us}.json"
    )
    created: dict[str, str] = {}

    profile_payload = build_profile_payload(
        pair=normalized_pair,
        translation_family=translation_family,
        translation_pack_id=translation_pack_id,
        reverse_family=reverse_family,
        reverse_pack_id=reverse_pack_id,
        translation_record_shape=translation_record_shape,
        reverse_record_shape=reverse_record_shape,
    )
    _write_json(profile_path, profile_payload, force=force)
    created["profile"] = str(profile_path.relative_to(project_root))

    cases_payload = build_benchmark_case_payload(pair=normalized_pair)
    _write_json(cases_path, cases_payload, force=force)
    created["benchmark_cases"] = str(cases_path.relative_to(project_root))

    if with_roadmap:
        roadmap_path = project_root / "docs" / "language_pairs" / f"{pair_us}_workstream_roadmap.md"
        _write_text(
            roadmap_path,
            render_workstream_roadmap(pair=normalized_pair),
            force=force,
        )
        created["roadmap"] = str(roadmap_path.relative_to(project_root))

    if with_code_stubs:
        pair_module_path = (
            project_root / "core" / "lexishift_core" / "rulegen" / "pairs" / f"{pair_us}.py"
        )
        _write_text(
            pair_module_path,
            render_pair_module_stub(
                pair=normalized_pair,
                translation_family=translation_family,
                translation_pack_id=translation_pack_id,
                reverse_family=reverse_family,
                reverse_pack_id=reverse_pack_id,
            ),
            force=force,
        )
        created["pair_module"] = str(pair_module_path.relative_to(project_root))

        pair_test_path = (
            project_root / "core" / "tests" / "rulegen" / f"test_rulegen_{pair_us}_scaffold.py"
        )
        _write_text(
            pair_test_path,
            render_pair_test_stub(pair=normalized_pair),
            force=force,
        )
        created["pair_test"] = str(pair_test_path.relative_to(project_root))

    if with_integration_handoff:
        integration_handoff_path = (
            project_root / "docs" / "language_pairs" / f"{pair_us}_integration_handoff.md"
        )
        _write_text(
            integration_handoff_path,
            render_integration_handoff(
                pair=normalized_pair,
                translation_family=translation_family,
                translation_pack_id=translation_pack_id,
                translation_record_shape=translation_record_shape,
                reverse_family=reverse_family,
                reverse_pack_id=reverse_pack_id,
                reverse_record_shape=reverse_record_shape,
                with_roadmap=with_roadmap,
            ),
            force=force,
        )
        created["integration_handoff"] = str(integration_handoff_path.relative_to(project_root))

    if with_benchmark_preset_starter:
        benchmark_preset_starter_path = (
            project_root / "docs" / "language_pairs" / f"{pair_us}_benchmark_preset_starter.md"
        )
        _write_text(
            benchmark_preset_starter_path,
            render_benchmark_preset_starter(
                pair=normalized_pair,
                reverse_pack_id=reverse_pack_id,
            ),
            force=force,
        )
        created["benchmark_preset_starter"] = str(
            benchmark_preset_starter_path.relative_to(project_root)
        )

    return created


def main() -> None:
    args = parse_args()
    created = scaffold_rulegen_lp(
        project_root=PROJECT_ROOT,
        pair=args.pair,
        translation_family=args.translation_family,
        translation_pack_id=args.translation_pack_id,
        reverse_family=args.reverse_family,
        reverse_pack_id=args.reverse_pack_id,
        translation_record_shape=args.translation_record_shape,
        reverse_record_shape=args.reverse_record_shape,
        with_roadmap=bool(args.with_roadmap),
        with_code_stubs=bool(args.with_code_stubs),
        with_integration_handoff=bool(args.with_integration_handoff),
        with_benchmark_preset_starter=bool(args.with_benchmark_preset_starter),
        force=bool(args.force),
    )
    for key, path in created.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
