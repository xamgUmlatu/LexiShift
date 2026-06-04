from __future__ import annotations

import shutil
from pathlib import Path
from typing import Mapping

from lexishift_core.helper.installed_packs import load_installed_pack_manifest_for_artifact
from lexishift_core.helper.pair_resources import (
    resolve_pair_frequency_pack,
    resolve_pair_resources as resolve_helper_pair_resources,
    resolve_stopwords_path as resolve_helper_stopwords_path,
    resolve_pair_translation_packs,
)
from lexishift_core.helper.paths import HelperPaths, build_helper_paths

ROLE_REF_STABLE_1 = "@stable_1"
ROLE_REF_STABLE_2 = "@stable_2"
ROLE_REF_DIFFICULT_1 = "@difficult_1"
ROLE_REF_GROWTH_1 = "@growth_1"
ROLE_REF_GROWTH_2 = "@growth_2"


def installed_pair_resources_available(pair: str) -> bool:
    installed_paths = build_helper_paths()
    jmdict_path, translation_dict_path, frequency_db = resolve_helper_pair_resources(
        installed_paths,
        pair=pair,
        jmdict_path=None,
        set_source_db=None,
    )
    translation_pack, reverse_translation_pack = resolve_pair_translation_packs(
        installed_paths,
        pair=pair,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=None,
    )
    frequency_pack = resolve_pair_frequency_pack(
        installed_paths,
        pair=pair,
        set_source_db=frequency_db,
    )
    required = [frequency_pack.path if frequency_pack else frequency_db]
    if jmdict_path is not None:
        required.append(jmdict_path)
    if translation_pack is not None:
        required.append(translation_pack.path)
    if reverse_translation_pack is not None:
        required.append(reverse_translation_pack.path)
    return all(
        path is not None and Path(path).exists() and Path(path).is_file() for path in required
    )


def build_initial_role_assignments(
    initialize_payload: Mapping[str, object] | None,
) -> dict[str, str]:
    diagnostics = (
        initialize_payload.get("bootstrap_diagnostics", {})
        if isinstance(initialize_payload, Mapping)
        else {}
    )
    preview = (
        diagnostics.get("initial_active_preview", []) if isinstance(diagnostics, Mapping) else []
    )
    ordered = [str(item).strip() for item in preview if str(item).strip()]
    assignments: dict[str, str] = {}
    if len(ordered) >= 1:
        assignments[ROLE_REF_STABLE_1] = ordered[0]
    if len(ordered) >= 2:
        assignments[ROLE_REF_STABLE_2] = ordered[1]
    if len(ordered) >= 3:
        assignments[ROLE_REF_DIFFICULT_1] = ordered[2]
    return assignments


def update_role_assignments_from_refresh(
    assignments: Mapping[str, str],
    *,
    phase_label: str,
    refresh_payload: Mapping[str, object] | None,
) -> dict[str, str]:
    updated = dict(assignments)
    selected = (
        (refresh_payload.get("admission_refresh", {}) or {}).get("selected_lemmas", [])
        if isinstance(refresh_payload, Mapping)
        else []
    )
    selected_lemmas = [str(item).strip() for item in selected if str(item).strip()]
    if phase_label == "high_retention_growth":
        if len(selected_lemmas) >= 1:
            updated[ROLE_REF_GROWTH_1] = selected_lemmas[0]
        if len(selected_lemmas) >= 2:
            updated[ROLE_REF_GROWTH_2] = selected_lemmas[1]
    return updated


def cohort_map_from_role_assignments(
    base: Mapping[str, str] | None = None,
    assignments: Mapping[str, str] | None = None,
) -> dict[str, str]:
    updated = dict(base or {})
    assignments = assignments or {}
    for ref in (ROLE_REF_STABLE_1, ROLE_REF_STABLE_2):
        lemma = str(assignments.get(ref, "") or "").strip()
        if lemma:
            updated[lemma] = "stable"
    lemma = str(assignments.get(ROLE_REF_DIFFICULT_1, "") or "").strip()
    if lemma:
        updated[lemma] = "difficult"
    for ref in (ROLE_REF_GROWTH_1, ROLE_REF_GROWTH_2):
        lemma = str(assignments.get(ref, "") or "").strip()
        if lemma:
            updated[lemma] = "frontier"
    return updated


def scenario_cohorts_from_role_assignments(
    assignments: Mapping[str, str] | None = None,
) -> dict[str, list[str]]:
    assignments = assignments or {}
    return {
        "stable": [
            lemma
            for lemma in (
                assignments.get(ROLE_REF_STABLE_1, ""),
                assignments.get(ROLE_REF_STABLE_2, ""),
            )
            if lemma
        ],
        "difficult": [lemma for lemma in (assignments.get(ROLE_REF_DIFFICULT_1, ""),) if lemma],
        "frontier": [
            lemma
            for lemma in (
                assignments.get(ROLE_REF_GROWTH_1, ""),
                assignments.get(ROLE_REF_GROWTH_2, ""),
            )
            if lemma
        ],
    }


def is_role_ref(value: str) -> bool:
    return str(value or "").startswith("@")


def installed_candidate_universe_from_bootstrap_audit(
    initialize_payload: Mapping[str, object] | None,
) -> list[dict[str, object]]:
    audit = (
        initialize_payload.get("bootstrap_audit", {})
        if isinstance(initialize_payload, Mapping)
        else {}
    )
    candidates = audit.get("candidates", []) if isinstance(audit, Mapping) else []
    if not isinstance(candidates, list):
        return []
    return [dict(candidate) for candidate in candidates if isinstance(candidate, Mapping)]


def stage_installed_pair_resources(paths: HelperPaths, *, pair: str) -> dict[str, Path | None]:
    installed_paths = build_helper_paths()
    jmdict_path, translation_dict_path, frequency_db = resolve_helper_pair_resources(
        installed_paths,
        pair=pair,
        jmdict_path=None,
        set_source_db=None,
    )
    translation_pack, reverse_translation_pack = resolve_pair_translation_packs(
        installed_paths,
        pair=pair,
        translation_dict_path=translation_dict_path,
        reverse_translation_dict_path=None,
    )
    frequency_pack = resolve_pair_frequency_pack(
        installed_paths,
        pair=pair,
        set_source_db=frequency_db,
    )
    stopwords_path = resolve_helper_stopwords_path(installed_paths, pair=pair)
    resources: dict[str, Path | None] = {
        "frequency_db": _stage_optional_pack_artifact(
            frequency_pack.path if frequency_pack else frequency_db,
            paths.frequency_packs_dir,
        ),
        "jmdict_path": _stage_optional_file(jmdict_path, paths.language_packs_dir),
        "translation_dict_path": _stage_optional_pack_artifact(
            translation_pack.path if translation_pack else translation_dict_path,
            paths.language_packs_dir,
        ),
        "reverse_translation_dict_path": _stage_optional_pack_artifact(
            reverse_translation_pack.path if reverse_translation_pack else None,
            paths.language_packs_dir,
        ),
    }
    if stopwords_path is not None:
        _stage_optional_file(stopwords_path, paths.srs_dir / "stopwords")
    return resources


def _stage_optional_file(source: Path | None, destination_dir: Path) -> Path | None:
    if source is None:
        return None
    source_path = Path(source)
    if not source_path.exists() or not source_path.is_file():
        return None
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source_path.name
    if destination.exists() or destination.is_symlink():
        destination.unlink()
    try:
        destination.symlink_to(source_path)
    except OSError:
        shutil.copy2(source_path, destination)
    return destination


def _stage_optional_pack_artifact(source: Path | None, destination_dir: Path) -> Path | None:
    if source is None:
        return None
    source_path = Path(source)
    if not source_path.exists():
        return None
    manifest = load_installed_pack_manifest_for_artifact(source_path)
    if manifest is None:
        return _stage_optional_file(source_path, destination_dir)
    source_pack_root = source_path if source_path.is_dir() else source_path.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_pack_root = destination_dir / manifest.pack_id
    _remove_existing_path(destination_pack_root)
    try:
        destination_pack_root.symlink_to(source_pack_root, target_is_directory=True)
    except OSError:
        shutil.copytree(source_pack_root, destination_pack_root)
    if manifest.artifact_relpath == ".":
        return destination_pack_root
    return destination_pack_root / manifest.artifact_relpath


def _remove_existing_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)
