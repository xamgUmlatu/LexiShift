from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

from lexishift_core.helper.installed_packs import (
    load_installed_pack_manifest_for_artifact,
    resolve_installed_pack_artifact,
)
from lexishift_core.helper.lp_capabilities import (
    default_frequency_db_path,
    normalize_pair_key,
    resolve_pair_capability,
)


@dataclass(frozen=True)
class FrequencyPackRef:
    pair: str
    path: Path
    provider: str
    pack_id: str
    pos_source_profile: str


def build_frequency_pack_ref(pair: str, path: Path | None) -> Optional[FrequencyPackRef]:
    if path is None:
        return None
    candidate = Path(path)
    manifest = load_installed_pack_manifest_for_artifact(candidate)
    pack_id = _infer_frequency_pack_id(
        candidate, manifest_pack_id=manifest.pack_id if manifest else None
    )
    provider = _infer_frequency_pack_provider(
        pack_id, manifest_provider=manifest.provider if manifest else None
    )
    return FrequencyPackRef(
        pair=normalize_pair_key(pair),
        path=candidate,
        provider=provider,
        pack_id=pack_id,
        pos_source_profile=_infer_frequency_pos_source_profile(pack_id, provider=provider),
    )


def resolve_configured_frequency_pack(
    pair: str,
    *,
    frequency_packs_dir: Path,
    settings_frequency_pack_paths: Mapping[str, str] | None = None,
    managed_frequency_pack_ids: Sequence[str] = (),
) -> tuple[Optional[FrequencyPackRef], str]:
    capability = resolve_pair_capability(pair)
    default_db_path = default_frequency_db_path(
        capability.pair,
        frequency_packs_dir=frequency_packs_dir,
    )
    if default_db_path is None:
        return None, "no_default_declared"

    default_name = default_db_path.name
    default_pack_id = (
        Path(capability.default_frequency_db).stem if capability.default_frequency_db else ""
    )
    managed_pack_ids = {str(value).strip() for value in tuple(managed_frequency_pack_ids) if value}

    if default_pack_id and default_pack_id in managed_pack_ids:
        managed = resolve_installed_pack_artifact(frequency_packs_dir, default_pack_id)
        if managed is not None and managed.is_file():
            return build_frequency_pack_ref(capability.pair, managed), f"managed:{default_pack_id}"

    lookup_keys: list[str] = []
    if default_name.endswith(".sqlite"):
        lookup_keys.append(default_name[: -len(".sqlite")])
    lookup_keys.append(default_name)

    configured_paths = dict(settings_frequency_pack_paths or {})
    for key in lookup_keys:
        raw_path = str(configured_paths.get(key, "")).strip()
        if not raw_path:
            continue
        candidate = Path(raw_path).expanduser().resolve(strict=False)
        if candidate.is_file():
            return build_frequency_pack_ref(capability.pair, candidate), f"linked:{key}"
        if candidate.is_dir():
            nested = candidate / default_name
            if nested.is_file():
                return build_frequency_pack_ref(capability.pair, nested), f"linked_dir:{key}"

    fallback = default_db_path.expanduser().resolve(strict=False)
    if fallback.is_file():
        return build_frequency_pack_ref(capability.pair, fallback), "fallback_default"
    return None, "missing"


def _infer_frequency_pack_id(path: Path, *, manifest_pack_id: str | None = None) -> str:
    if manifest_pack_id:
        return str(manifest_pack_id).strip()
    name = path.name.strip()
    if name.endswith(".sqlite"):
        return name[: -len(".sqlite")]
    if name.endswith(".sqlite3"):
        return name[: -len(".sqlite3")]
    if name.endswith(".db"):
        return name[: -len(".db")]
    return name or path.parent.name


def _infer_frequency_pack_provider(
    pack_id: str,
    *,
    manifest_provider: str | None = None,
) -> str:
    if manifest_provider:
        return str(manifest_provider).strip().lower()
    normalized = str(pack_id or "").strip().lower()
    if normalized in {"freq-en-coca", "freq-ja-bccwj", "freq-es-cde", "freq-de-default"}:
        return normalized
    return normalized or "frequency"


def _infer_frequency_pos_source_profile(pack_id: str, *, provider: str) -> str:
    normalized = str(pack_id or "").strip().lower()
    if normalized == "freq-ja-bccwj":
        return "bccwj"
    if normalized == "freq-en-coca":
        return "compact-latin"
    if normalized == "freq-es-cde":
        return "freq-es-cde"
    if normalized == "freq-de-default":
        return "freq-de-default"
    return provider
