from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
import json
from pathlib import Path
import tempfile
from typing import Mapping, Sequence

from lexishift_core.helper.paths import HelperPaths
from lexishift_core.persistence.storage import VocabDataset, dataset_to_dict
from lexishift_core.replacement.core import VocabRule


@dataclass(frozen=True)
class RulegenOutput:
    rules: Sequence[VocabRule]
    snapshot: Mapping[str, object]
    target_count: int
    semantic_inventory: Mapping[str, object] | None = None


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash_text(value: str) -> str:
    return sha1(value.encode("utf-8")).hexdigest()


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        delete=False,
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _normalize_snapshot_payload(
    snapshot: Mapping[str, object],
    *,
    pair: str,
    generated_at: str,
) -> dict[str, object]:
    payload = dict(snapshot)
    payload["pair"] = str(pair or "").strip()
    payload["generated_at"] = str(generated_at or "").strip()
    return payload


def _normalize_semantic_inventory_payload(
    semantic_inventory: Mapping[str, object],
    *,
    pair: str,
    profile_id: str,
    generated_at: str,
) -> dict[str, object]:
    payload = dict(semantic_inventory)
    payload["pair"] = str(pair or "").strip()
    payload["profile_id"] = str(profile_id or "").strip() or "default"
    payload["generated_at"] = str(generated_at or "").strip()
    return payload


def _resolve_family_generated_at(
    snapshot: Mapping[str, object],
    semantic_inventory: Mapping[str, object] | None,
) -> str:
    snapshot_generated_at = str(snapshot.get("generated_at") or "").strip()
    if snapshot_generated_at:
        return snapshot_generated_at
    if semantic_inventory is not None:
        inventory_generated_at = str(semantic_inventory.get("generated_at") or "").strip()
        if inventory_generated_at:
            return inventory_generated_at
    return _now_iso()


def _build_generation_id(
    *,
    pair: str,
    profile_id: str,
    generated_at: str,
    ruleset_data: Mapping[str, object],
    snapshot_payload: Mapping[str, object],
    semantic_inventory_payload: Mapping[str, object] | None,
) -> str:
    seed_payload = {
        "pair": str(pair or "").strip(),
        "profile_id": str(profile_id or "").strip() or "default",
        "generated_at": str(generated_at or "").strip(),
        "ruleset_hash": _hash_text(_canonical_json(ruleset_data)),
        "snapshot_hash": _hash_text(_canonical_json(snapshot_payload)),
        "semantic_inventory_hash": (
            _hash_text(_canonical_json(semantic_inventory_payload))
            if semantic_inventory_payload is not None
            else None
        ),
    }
    digest = _hash_text(_canonical_json(seed_payload))
    return f"{seed_payload['pair']}:{seed_payload['profile_id']}:{digest[:16]}"


def _iter_rule_semantic_admissions(rules: Sequence[VocabRule]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, rule in enumerate(rules):
        metadata = rule.metadata
        semantic_admission = (
            dict(metadata.semantic_admission)
            if metadata is not None and isinstance(metadata.semantic_admission, Mapping)
            else None
        )
        if semantic_admission is None:
            continue
        rows.append(
            {
                "index": index,
                "source_phrase": str(rule.source_phrase or "").strip(),
                "replacement": str(rule.replacement or "").strip(),
                "semantic_admission": semantic_admission,
            }
        )
    return rows


def _validate_publication_family(
    *,
    pair: str,
    profile_id: str,
    generation_id: str,
    rules: Sequence[VocabRule],
    snapshot_payload: Mapping[str, object],
    semantic_inventory_payload: Mapping[str, object] | None,
) -> list[str]:
    errors: list[str] = []
    normalized_pair = str(pair or "").strip()
    normalized_profile_id = str(profile_id or "").strip() or "default"
    if str(snapshot_payload.get("pair") or "").strip() != normalized_pair:
        errors.append("snapshot.pair does not match requested pair")
    if str(snapshot_payload.get("generated_at") or "").strip() == "":
        errors.append("snapshot.generated_at is required")
    if str(snapshot_payload.get("generation_id") or "").strip() != generation_id:
        errors.append("snapshot.generation_id does not match manifest generation")
    snapshot_stats = snapshot_payload.get("stats")
    if isinstance(snapshot_stats, Mapping) and "rule_count" in snapshot_stats:
        try:
            snapshot_rule_count = int(snapshot_stats.get("rule_count"))
        except (TypeError, ValueError):
            errors.append("snapshot.stats.rule_count is not an integer")
        else:
            if snapshot_rule_count != len(rules):
                errors.append(
                    f"snapshot.stats.rule_count={snapshot_rule_count} does not match rules={len(rules)}"
                )

    triggers = {}
    senses = {}
    competition_sets = {}
    if semantic_inventory_payload is not None:
        if str(semantic_inventory_payload.get("pair") or "").strip() != normalized_pair:
            errors.append("semantic_inventory.pair does not match requested pair")
        if str(semantic_inventory_payload.get("profile_id") or "").strip() != normalized_profile_id:
            errors.append("semantic_inventory.profile_id does not match requested profile")
        if str(semantic_inventory_payload.get("generated_at") or "").strip() == "":
            errors.append("semantic_inventory.generated_at is required")
        if str(semantic_inventory_payload.get("generation_id") or "").strip() != generation_id:
            errors.append("semantic_inventory.generation_id does not match manifest generation")
        triggers = (
            dict(semantic_inventory_payload.get("triggers"))
            if isinstance(semantic_inventory_payload.get("triggers"), Mapping)
            else {}
        )
        senses = (
            dict(semantic_inventory_payload.get("senses"))
            if isinstance(semantic_inventory_payload.get("senses"), Mapping)
            else {}
        )
        competition_sets = (
            dict(semantic_inventory_payload.get("competition_sets"))
            if isinstance(semantic_inventory_payload.get("competition_sets"), Mapping)
            else {}
        )
        for sense_id, raw_sense in senses.items():
            if not isinstance(raw_sense, Mapping):
                errors.append(f"semantic_inventory.senses[{sense_id!r}] is not an object")
                continue
            trigger_id = str(raw_sense.get("trigger_id") or "").strip()
            if trigger_id and trigger_id not in triggers:
                errors.append(
                    f"semantic_inventory sense {sense_id!r} references missing trigger {trigger_id!r}"
                )
        for competition_set_id, raw_set in competition_sets.items():
            if not isinstance(raw_set, Mapping):
                errors.append(
                    f"semantic_inventory.competition_sets[{competition_set_id!r}] is not an object"
                )
                continue
            trigger_id = str(raw_set.get("trigger_id") or "").strip()
            active_sense_id = str(raw_set.get("active_sense_id") or "").strip()
            if trigger_id and trigger_id not in triggers:
                errors.append(
                    f"competition set {competition_set_id!r} references missing trigger {trigger_id!r}"
                )
            if active_sense_id and active_sense_id not in senses:
                errors.append(
                    f"competition set {competition_set_id!r} references missing active sense {active_sense_id!r}"
                )

    ready_pointer_count = 0
    for row in _iter_rule_semantic_admissions(rules):
        pointer = row["semantic_admission"]
        status = str(pointer.get("status") or "").strip()
        if status != "ready":
            continue
        ready_pointer_count += 1
        if semantic_inventory_payload is None:
            errors.append(
                f"rule[{row['index']}] has status=ready semantic_admission but no semantic inventory was published"
            )
            continue
        trigger_id = str(pointer.get("trigger_id") or "").strip()
        sense_id = str(pointer.get("sense_id") or "").strip()
        competition_set_id = str(pointer.get("competition_set_id") or "").strip()
        if not trigger_id or trigger_id not in triggers:
            errors.append(
                f"rule[{row['index']}] ready semantic_admission trigger_id {trigger_id!r} does not resolve"
            )
        if not sense_id or sense_id not in senses:
            errors.append(
                f"rule[{row['index']}] ready semantic_admission sense_id {sense_id!r} does not resolve"
            )
        competition_set = competition_sets.get(competition_set_id)
        if not competition_set_id or not isinstance(competition_set, Mapping):
            errors.append(
                f"rule[{row['index']}] ready semantic_admission competition_set_id {competition_set_id!r} does not resolve"
            )
        else:
            active_sense_id = str(competition_set.get("active_sense_id") or "").strip()
            if active_sense_id and sense_id and active_sense_id != sense_id:
                errors.append(
                    f"rule[{row['index']}] ready semantic_admission sense_id {sense_id!r} does not match competition set active_sense_id {active_sense_id!r}"
                )

    if semantic_inventory_payload is None and ready_pointer_count:
        errors.append("ready semantic_admission pointers require semantic inventory publication")

    return errors


def _build_artifact_manifest_entry(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "sha1": None,
            "bytes": 0,
        }
    payload = path.read_bytes()
    return {
        "path": str(path),
        "exists": True,
        "sha1": sha1(payload).hexdigest(),
        "bytes": len(payload),
    }


def _build_publication_manifest(
    *,
    paths: HelperPaths,
    pair: str,
    profile_id: str,
    generated_at: str,
    published_at: str,
    generation_id: str,
    semantic_inventory_included: bool,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": str(pair or "").strip(),
        "profile_id": str(profile_id or "").strip() or "default",
        "generated_at": str(generated_at or "").strip(),
        "published_at": str(published_at or "").strip(),
        "generation_id": generation_id,
        "artifacts": {
            "ruleset": _build_artifact_manifest_entry(
                paths.ruleset_path(pair, profile_id=profile_id)
            ),
            "snapshot": _build_artifact_manifest_entry(
                paths.snapshot_path(pair, profile_id=profile_id)
            ),
            "semantic_inventory": _build_artifact_manifest_entry(
                paths.semantic_inventory_path(pair, profile_id=profile_id)
            ),
        },
        "validation": {
            "family_valid": True,
            "semantic_inventory_included": bool(semantic_inventory_included),
            "errors": [],
        },
    }


def build_snapshot(
    *,
    rules: Sequence[VocabRule],
    pair: str,
    max_targets: int,
    max_sources: int,
    generated_at: str | None = None,
) -> Mapping[str, object]:
    mapping: dict[str, list[str]] = {}
    for rule in rules:
        lemma = str(rule.replacement or "").strip()
        source = str(rule.source_phrase or "").strip()
        if not lemma or not source:
            continue
        mapping.setdefault(lemma, [])
        if source not in mapping[lemma]:
            mapping[lemma].append(source)
    targets = []
    for lemma in sorted(mapping.keys())[:max_targets]:
        sources = mapping[lemma][:max_sources]
        targets.append({"lemma": lemma, "sources": sources})
    source_total = sum(len(sources) for sources in mapping.values())
    return {
        "version": 1,
        "generated_at": generated_at or _now_iso(),
        "pair": pair,
        "targets": targets,
        "stats": {
            "target_count": len(mapping),
            "rule_count": len(rules),
            "source_count": source_total,
        },
    }


def write_rulegen_outputs(
    *,
    paths: HelperPaths,
    pair: str,
    profile_id: str = "default",
    rules: Sequence[VocabRule],
    snapshot: Mapping[str, object],
    semantic_inventory: Mapping[str, object] | None = None,
) -> None:
    normalized_profile_id = paths.normalize_profile_id(profile_id)
    family_generated_at = _resolve_family_generated_at(snapshot, semantic_inventory)
    dataset = VocabDataset(rules=tuple(rules))
    ruleset_data = dataset_to_dict(dataset)
    snapshot_payload = _normalize_snapshot_payload(
        snapshot,
        pair=pair,
        generated_at=family_generated_at,
    )
    semantic_inventory_payload = (
        _normalize_semantic_inventory_payload(
            semantic_inventory,
            pair=pair,
            profile_id=normalized_profile_id,
            generated_at=family_generated_at,
        )
        if semantic_inventory is not None
        else None
    )
    generation_id = _build_generation_id(
        pair=pair,
        profile_id=normalized_profile_id,
        generated_at=family_generated_at,
        ruleset_data=ruleset_data,
        snapshot_payload=snapshot_payload,
        semantic_inventory_payload=semantic_inventory_payload,
    )
    snapshot_payload["generation_id"] = generation_id
    if semantic_inventory_payload is not None:
        semantic_inventory_payload["generation_id"] = generation_id
    validation_errors = _validate_publication_family(
        pair=pair,
        profile_id=normalized_profile_id,
        generation_id=generation_id,
        rules=rules,
        snapshot_payload=snapshot_payload,
        semantic_inventory_payload=semantic_inventory_payload,
    )
    if validation_errors:
        rendered = "; ".join(validation_errors)
        raise ValueError(
            f"Invalid rulegen publication family for {pair}/{normalized_profile_id}: {rendered}"
        )

    ruleset_path = paths.ruleset_path(pair, profile_id=normalized_profile_id)
    snapshot_path = paths.snapshot_path(pair, profile_id=normalized_profile_id)
    semantic_inventory_path = paths.semantic_inventory_path(pair, profile_id=normalized_profile_id)
    manifest_path = paths.publication_manifest_path(pair, profile_id=normalized_profile_id)
    _write_text_atomic(
        ruleset_path,
        json.dumps(ruleset_data, indent=2, sort_keys=True),
    )
    _write_text_atomic(
        snapshot_path,
        json.dumps(snapshot_payload, indent=2, sort_keys=True),
    )
    if semantic_inventory_payload is not None:
        _write_text_atomic(
            semantic_inventory_path,
            json.dumps(semantic_inventory_payload, indent=2, sort_keys=True),
        )
    elif semantic_inventory_path.exists():
        semantic_inventory_path.unlink()

    published_at = _now_iso()
    manifest_payload = _build_publication_manifest(
        paths=paths,
        pair=pair,
        profile_id=normalized_profile_id,
        generated_at=family_generated_at,
        published_at=published_at,
        generation_id=generation_id,
        semantic_inventory_included=semantic_inventory_payload is not None,
    )
    _write_text_atomic(
        manifest_path,
        json.dumps(manifest_payload, indent=2, sort_keys=True),
    )
