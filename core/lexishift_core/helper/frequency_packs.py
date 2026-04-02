from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from lexishift_core.helper.installed_packs import load_installed_pack_manifest_for_artifact
from lexishift_core.helper.lp_capabilities import normalize_pair_key


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
