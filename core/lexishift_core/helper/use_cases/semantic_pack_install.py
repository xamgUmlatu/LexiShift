from __future__ import annotations

from copy import deepcopy
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.helper.rulegen_outputs import build_snapshot, write_rulegen_outputs
from lexishift_core.replacement.core import RuleMetadata, VocabRule


ACTIVE_ONLY_COMPETITION_MODE = "active_only_anchor_cue"
ACTIVE_ONLY_SELECTION_POLICY = "active_only_anchor_cue_v1"
MIXED_SELECTION_POLICY = "active_only_anchor_cue_with_repaired_shadows_v1"
DEFAULT_PACK_ID = "en-es-active-only-combined-product-scope-v1"
SEMANTIC_PACK_CATALOG_ENV = "LEXISHIFT_SEMANTIC_PACK_CATALOG"
_DEV_PACK_INVENTORY_BY_PAIR_AND_ID = {
    (
        "en-es",
        DEFAULT_PACK_ID,
    ): Path(
        "docs/test_outputs/experiments/semantic_veto_source_packaging/"
        "en-es-active-only-combined-product-scope-v1-inventory-replay-latest_semantic_inventory.json"
    )
}


@dataclass(frozen=True)
class SemanticPackInstallConfig:
    pair: str
    profile_id: str = "default"
    semantic_inventory_path: Path | None = None
    semantic_inventory: Mapping[str, object] | None = None
    pack_id: str = DEFAULT_PACK_ID
    generated_at: str = ""
    copy_pack: bool = True
    dry_run: bool = False
    rule_source: str = "semantic_pack_install"
    rule_source_type: str = "semantic_veto_candidate"


def install_semantic_pack(
    paths: HelperPaths,
    *,
    config: SemanticPackInstallConfig,
) -> dict[str, object]:
    pair = str(config.pair or "").strip()
    if not pair:
        raise ValueError("pair is required")
    profile_id = paths.normalize_profile_id(config.profile_id or "default")
    generated_at = str(config.generated_at or "").strip() or _utc_now()
    resolved_inventory_path = resolve_semantic_pack_inventory_path(
        paths=paths,
        pair=pair,
        pack_id=config.pack_id,
        explicit_path=config.semantic_inventory_path,
        inline_inventory=config.semantic_inventory is not None,
    )
    raw_inventory = _load_inventory(config, resolved_inventory_path)
    source_pack_ref = ""
    if config.copy_pack:
        source_pack_ref = _semantic_pack_inventory_path(
            paths=paths,
            pair=pair,
            pack_id=config.pack_id,
        )
    inventory = normalize_semantic_inventory_for_helper(
        raw_inventory,
        pair=pair,
        profile_id=profile_id,
        generated_at=generated_at,
    )
    rules = build_rules_from_semantic_inventory(
        inventory,
        pair=pair,
        rule_source=config.rule_source,
        rule_source_type=config.rule_source_type,
    )
    snapshot = build_snapshot(
        rules=rules,
        pair=pair,
        max_targets=len(rules) or 1,
        max_sources=10,
        generated_at=generated_at,
    )
    target_paths = _target_paths(paths=paths, pair=pair, profile_id=profile_id)
    if not config.dry_run:
        if config.copy_pack:
            _write_pack_copy(
                paths=paths,
                pair=pair,
                pack_id=config.pack_id,
                raw_inventory=raw_inventory,
                normalized_inventory=inventory,
                source_path=resolved_inventory_path,
                generated_at=generated_at,
            )
        write_rulegen_outputs(
            paths=paths,
            pair=pair,
            profile_id=profile_id,
            rules=rules,
            snapshot=snapshot,
            semantic_inventory=inventory,
        )
    written = (
        {key: path.exists() for key, path in target_paths.items()}
        if not config.dry_run
        else {key: False for key in target_paths}
    )
    return {
        "schema_version": 1,
        "status": "dry_run" if config.dry_run else "ok",
        "decision": (
            "semantic_pack_materialization_preview"
            if config.dry_run
            else "semantic_pack_materialized"
        ),
        "pair": pair,
        "profile_id": profile_id,
        "pack_id": str(config.pack_id or DEFAULT_PACK_ID).strip() or DEFAULT_PACK_ID,
        "generated_at": generated_at,
        "data_root": str(paths.data_root),
        "source": {
            "semantic_inventory_path": str(resolved_inventory_path or ""),
            "semantic_inventory_sha1": _sha1_json(raw_inventory),
            "source_pack_inventory_path": str(source_pack_ref),
        },
        "summary": {
            "rule_count": len(rules),
            "trigger_count": len(_as_mapping(inventory.get("triggers"))),
            "sense_count": len(_as_mapping(inventory.get("senses"))),
            "competition_set_count": len(_as_mapping(inventory.get("competition_sets"))),
            "active_only_competition_set_count": sum(
                1
                for row in _mapping_rows(_as_mapping(inventory.get("competition_sets")).values())
                if str(row.get("selection_mode") or "") == "active_only"
            ),
            "shadowed_competition_set_count": sum(
                1
                for row in _mapping_rows(_as_mapping(inventory.get("competition_sets")).values())
                if row.get("shadow_sense_ids")
            ),
        },
        "target_paths": {key: str(path) for key, path in target_paths.items()},
        "written": written,
    }


def resolve_semantic_pack_inventory_path(
    *,
    paths: HelperPaths,
    pair: str,
    pack_id: str,
    explicit_path: Path | None = None,
    inline_inventory: bool = False,
) -> Path | None:
    if inline_inventory:
        return explicit_path
    if explicit_path is not None:
        return explicit_path.expanduser()

    normalized_pair = str(pair or "").strip()
    normalized_pack_id = str(pack_id or DEFAULT_PACK_ID).strip() or DEFAULT_PACK_ID
    installed_pack_path = Path(
        _semantic_pack_inventory_path(
            paths=paths,
            pair=normalized_pair,
            pack_id=normalized_pack_id,
        )
    )
    if installed_pack_path.exists():
        return installed_pack_path

    catalog_path = _semantic_pack_catalog_inventory_path(
        pair=normalized_pair,
        pack_id=normalized_pack_id,
    )
    if catalog_path is not None and catalog_path.exists():
        return catalog_path

    dev_relative_path = _DEV_PACK_INVENTORY_BY_PAIR_AND_ID.get(
        (normalized_pair, normalized_pack_id)
    )
    if dev_relative_path is not None:
        dev_path = _project_root() / dev_relative_path
        if dev_path.exists():
            return dev_path

    raise ValueError(
        "semantic inventory could not be resolved for "
        f"pair={normalized_pair!r}, pack_id={normalized_pack_id!r}; provide "
        "semantic_inventory_path, install a semantic pack copy under language_packs, "
        f"or configure {SEMANTIC_PACK_CATALOG_ENV}."
    )


def normalize_semantic_inventory_for_helper(
    payload: Mapping[str, object],
    *,
    pair: str,
    profile_id: str,
    generated_at: str,
) -> dict[str, object]:
    inventory = deepcopy(dict(payload))
    triggers = _mapping_copy(inventory.get("triggers"))
    competition_sets = _mapping_copy(inventory.get("competition_sets"))
    sense_trigger_ids = _sense_trigger_ids(competition_sets)
    senses: dict[str, object] = {}
    for sense_id, raw_sense in _mapping_copy(inventory.get("senses")).items():
        if not isinstance(raw_sense, Mapping):
            continue
        sense = dict(raw_sense)
        sense["sense_id"] = str(sense.get("sense_id") or sense_id)
        sense["trigger_id"] = str(sense.get("trigger_id") or sense_trigger_ids.get(sense_id) or "")
        sense["status"] = str(sense.get("status") or "ready")
        sense["provider"] = str(sense.get("provider") or "semantic_veto_source_pack")
        sense["locator"] = _as_mapping(sense.get("locator")) or {
            "provider": sense["provider"],
            "locator_kind": "opaque",
            "opaque_id": sense_id,
        }
        evidence_views = _as_mapping(sense.get("evidence_views"))
        if "sense_label" not in sense and evidence_views.get("sense_label"):
            sense["sense_label"] = str(evidence_views.get("sense_label") or "")
        if "sense_label" not in sense:
            sense["sense_label"] = str(sense.get("target_lemma") or sense_id)
        senses[sense_id] = sense
    normalized_competition_sets: dict[str, object] = {}
    for competition_set_id, raw_set in competition_sets.items():
        if not isinstance(raw_set, Mapping):
            continue
        competition_set = dict(raw_set)
        shadow_sense_ids = [
            str(item or "").strip()
            for item in _sequence_items(competition_set.get("shadow_sense_ids"))
            if str(item or "").strip()
        ]
        competition_set["competition_set_id"] = str(
            competition_set.get("competition_set_id") or competition_set_id
        )
        competition_set["status"] = "ready"
        competition_set["shadow_sense_ids"] = shadow_sense_ids
        if shadow_sense_ids:
            competition_set["selection_mode"] = "mixed"
            competition_set["selection_policy_version"] = MIXED_SELECTION_POLICY
        else:
            competition_set["selection_mode"] = "active_only"
            competition_set["selection_policy_version"] = ACTIVE_ONLY_SELECTION_POLICY
        normalized_competition_sets[competition_set_id] = competition_set
    return {
        "schema_version": 1,
        "pair": str(pair or "").strip(),
        "profile_id": str(profile_id or "").strip() or "default",
        "generated_at": generated_at,
        "capability": {
            "pointer_modes": ["trigger_only"],
            "default_unavailable_reason_code": "missing_source_sense_locator",
            "competition_mode": ACTIVE_ONLY_COMPETITION_MODE,
            "competition_reason_code": "missing_shadow_selection",
            "phrase_mode": "not_published",
            "phrase_reason_code": "missing_phrase_inventory",
        },
        "triggers": triggers,
        "senses": senses,
        "competition_sets": normalized_competition_sets,
        "phrase_sets": _mapping_copy(inventory.get("phrase_sets")),
    }


def build_rules_from_semantic_inventory(
    inventory: Mapping[str, object],
    *,
    pair: str,
    rule_source: str,
    rule_source_type: str,
) -> tuple[VocabRule, ...]:
    triggers = _as_mapping(inventory.get("triggers"))
    senses = _as_mapping(inventory.get("senses"))
    rules: list[VocabRule] = []
    for competition_set_id, competition_set in sorted(
        _as_mapping(inventory.get("competition_sets")).items()
    ):
        if not isinstance(competition_set, Mapping):
            continue
        active_sense_id = str(competition_set.get("active_sense_id") or "").strip()
        active_sense = _as_mapping(senses.get(active_sense_id))
        trigger_id = str(competition_set.get("trigger_id") or "").strip()
        trigger = _as_mapping(triggers.get(trigger_id))
        source_phrase = str(trigger.get("source_phrase") or "").strip()
        replacement = str(active_sense.get("target_lemma") or "").strip()
        if not source_phrase or not replacement:
            continue
        rules.append(
            VocabRule(
                source_phrase=source_phrase,
                replacement=replacement,
                metadata=RuleMetadata(
                    language_pair=str(pair or "").strip(),
                    source=str(rule_source or "").strip(),
                    source_type=str(rule_source_type or "").strip(),
                    semantic_admission={
                        "schema_version": 1,
                        "status": "ready",
                        "trigger_id": trigger_id,
                        "sense_id": active_sense_id,
                        "competition_set_id": str(competition_set_id),
                    },
                ),
            )
        )
    return tuple(rules)


def _load_inventory(
    config: SemanticPackInstallConfig,
    resolved_inventory_path: Path | None,
) -> Mapping[str, object]:
    if config.semantic_inventory is not None:
        return config.semantic_inventory
    if resolved_inventory_path is None:
        raise ValueError("semantic_inventory_path or semantic_inventory is required")
    payload = json.loads(resolved_inventory_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("semantic inventory must be a JSON object")
    return payload


def _semantic_pack_catalog_inventory_path(*, pair: str, pack_id: str) -> Path | None:
    catalog_path_value = str(os.environ.get(SEMANTIC_PACK_CATALOG_ENV, "") or "").strip()
    if not catalog_path_value:
        return None
    catalog_path = Path(catalog_path_value).expanduser()
    if not catalog_path.exists():
        return None
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    records: list[Mapping[str, object]] = []
    if isinstance(payload, Mapping):
        packs = payload.get("packs")
        if isinstance(packs, Mapping):
            records = [row for row in packs.values() if isinstance(row, Mapping)]
        elif isinstance(packs, Sequence) and not isinstance(packs, (str, bytes)):
            records = [row for row in packs if isinstance(row, Mapping)]
    for record in records:
        if str(record.get("pair") or "").strip() != pair:
            continue
        if str(record.get("pack_id") or "").strip() != pack_id:
            continue
        path_value = str(record.get("semantic_inventory_path") or record.get("path") or "").strip()
        if path_value:
            return Path(path_value).expanduser()
    return None


def _write_pack_copy(
    *,
    paths: HelperPaths,
    pair: str,
    pack_id: str,
    raw_inventory: Mapping[str, object],
    normalized_inventory: Mapping[str, object],
    source_path: Path | None,
    generated_at: str,
) -> None:
    pack_root = _semantic_pack_root(paths=paths, pair=pair, pack_id=pack_id)
    inventory_path = pack_root / "semantic_inventory.json"
    manifest_path = pack_root / "manifest.json"
    _write_json(inventory_path, normalized_inventory)
    _write_json(
        manifest_path,
        {
            "schema_version": 1,
            "pack_kind": "semantic_inventory_pack",
            "pack_id": str(pack_id or DEFAULT_PACK_ID).strip() or DEFAULT_PACK_ID,
            "pair": pair,
            "generated_at": generated_at,
            "source_path": str(source_path or ""),
            "raw_inventory_sha1": _sha1_json(raw_inventory),
            "normalized_inventory_sha1": _sha1_json(normalized_inventory),
            "artifacts": {
                "semantic_inventory": {
                    "path": str(inventory_path),
                    "sha1": _sha1_file(inventory_path),
                    "bytes": inventory_path.stat().st_size,
                }
            },
        },
    )


def _semantic_pack_root(*, paths: HelperPaths, pair: str, pack_id: str) -> Path:
    safe_pair = str(pair or "").replace("/", "-").replace(":", "-")
    safe_pack_id = _safe_path_segment(str(pack_id or DEFAULT_PACK_ID))
    return paths.language_packs_dir / safe_pair / "semantic_packs" / safe_pack_id


def _semantic_pack_inventory_path(*, paths: HelperPaths, pair: str, pack_id: str) -> str:
    return str(
        _semantic_pack_root(paths=paths, pair=pair, pack_id=pack_id) / "semantic_inventory.json"
    )


def _target_paths(*, paths: HelperPaths, pair: str, profile_id: str) -> dict[str, Path]:
    return {
        "ruleset": paths.ruleset_path(pair, profile_id=profile_id),
        "snapshot": paths.snapshot_path(pair, profile_id=profile_id),
        "semantic_inventory": paths.semantic_inventory_path(pair, profile_id=profile_id),
        "publication_manifest": paths.publication_manifest_path(pair, profile_id=profile_id),
    }


def _sense_trigger_ids(competition_sets: Mapping[str, object]) -> dict[str, str]:
    trigger_ids: dict[str, str] = {}
    for competition_set in _mapping_rows(competition_sets.values()):
        trigger_id = str(competition_set.get("trigger_id") or "").strip()
        active_sense_id = str(competition_set.get("active_sense_id") or "").strip()
        if active_sense_id and trigger_id:
            trigger_ids[active_sense_id] = trigger_id
        for shadow_sense_id in _sequence_items(competition_set.get("shadow_sense_ids")):
            normalized = str(shadow_sense_id or "").strip()
            if normalized and trigger_id:
                trigger_ids[normalized] = trigger_id
    return trigger_ids


def _mapping_copy(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): dict(entry) if isinstance(entry, Mapping) else entry
        for key, entry in value.items()
        if str(key).strip()
    }


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    iterable: Iterable[object]
    if isinstance(value, Mapping):
        iterable = value.values()
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        iterable = value
    elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        iterable = value
    else:
        return []
    return [item for item in iterable if isinstance(item, Mapping)]


def _sequence_items(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    _write_text_atomic(
        path,
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink()


def _sha1_json(payload: Mapping[str, object]) -> str:
    serialized = json.dumps(
        dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return sha1(serialized.encode("utf-8")).hexdigest()


def _sha1_file(path: Path) -> str:
    return sha1(path.read_bytes()).hexdigest()


def _safe_path_segment(value: str) -> str:
    return (
        "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value).strip("-")
        or DEFAULT_PACK_ID
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
