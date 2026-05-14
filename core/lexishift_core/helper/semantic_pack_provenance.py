from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path
import tempfile
from typing import Mapping
import os

from lexishift_core.helper.pack_provenance import PACK_PROVENANCE_FILENAME


def build_semantic_pack_lineage(
    *,
    pair: str,
    pack_id: str,
    raw_inventory: Mapping[str, object],
    normalized_inventory: Mapping[str, object],
    source_path: Path | None,
    generated_at: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": str(pair or "").strip(),
        "pack_id": str(pack_id or "").strip(),
        "generated_at": str(generated_at or "").strip(),
        "source_inventory_path": str(source_path or ""),
        "source_inventory_sha1": _sha1_json(raw_inventory),
        "source_inventory_generated_at": str(raw_inventory.get("generated_at") or ""),
        "source_inventory_generation_id": str(raw_inventory.get("generation_id") or ""),
        "source_inventory_pair": str(raw_inventory.get("pair") or ""),
        "source_inventory_profile_id": str(raw_inventory.get("profile_id") or ""),
        "normalized_inventory_sha1": _sha1_json(normalized_inventory),
        "trigger_count": len(_as_mapping(normalized_inventory.get("triggers"))),
        "sense_count": len(_as_mapping(normalized_inventory.get("senses"))),
        "competition_set_count": len(_as_mapping(normalized_inventory.get("competition_sets"))),
        "phrase_set_count": len(_as_mapping(normalized_inventory.get("phrase_sets"))),
    }


def write_semantic_pack_provenance(
    *,
    pack_root: Path,
    inventory_path: Path,
    pair: str,
    pack_id: str,
    raw_inventory: Mapping[str, object],
    normalized_inventory: Mapping[str, object],
    source_path: Path | None,
    generated_at: str,
) -> Path:
    provenance_path = Path(pack_root) / PACK_PROVENANCE_FILENAME
    payload = build_semantic_pack_provenance_payload(
        inventory_path=inventory_path,
        pair=pair,
        pack_id=pack_id,
        raw_inventory=raw_inventory,
        normalized_inventory=normalized_inventory,
        source_path=source_path,
        generated_at=generated_at,
    )
    _write_json(provenance_path, payload)
    return provenance_path


def build_semantic_pack_provenance_payload(
    *,
    inventory_path: Path,
    pair: str,
    pack_id: str,
    raw_inventory: Mapping[str, object],
    normalized_inventory: Mapping[str, object],
    source_path: Path | None,
    generated_at: str,
) -> dict[str, object]:
    lineage = build_semantic_pack_lineage(
        pair=pair,
        pack_id=pack_id,
        raw_inventory=raw_inventory,
        normalized_inventory=normalized_inventory,
        source_path=source_path,
        generated_at=generated_at,
    )
    source_artifact_filename = (
        Path(source_path).name if source_path is not None else "inline_semantic_inventory.json"
    )
    source: dict[str, object] = {
        "source_name": f"{str(pair or '').strip()} semantic inventory",
        "license_status": "internal_only",
        "local_source_path": str(source_path or "inline:semantic_inventory"),
        "raw_artifacts": [
            {
                "filename": source_artifact_filename,
                "sha1": str(lineage["source_inventory_sha1"]),
            }
        ],
    }
    return {
        "schema_version": 1,
        "pack_id": str(pack_id or "").strip(),
        "pack_kind": "semantic_inventory_pack",
        "provider": "semantic_pack_install",
        "source": source,
        "build": {
            "build_mode": "semantic_pack_install",
            "command": "install_semantic_pack",
        },
        "artifact": {
            "artifact_relpath": Path(inventory_path).name,
            "artifact_kind": "semantic_inventory",
            "sha1": _sha1_file(Path(inventory_path)),
        },
        "lineage": lineage,
    }


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


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
