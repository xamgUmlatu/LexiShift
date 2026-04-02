from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from lexishift_core.helper.installed_packs import (
    load_installed_pack_manifest_for_artifact,
    resolve_installed_pack_artifact,
)
from lexishift_core.helper.lp_capabilities import normalize_pair_key


@dataclass(frozen=True)
class EmbeddingPackRef:
    pair: str
    path: Path
    provider: str
    pack_id: str
    source_profile: str


def resolve_embedding_pack_artifact(
    base_dir: Path,
    *,
    pack_id: str,
    configured_path: Path | None = None,
) -> Optional[Path]:
    resolved = resolve_installed_pack_artifact(base_dir, pack_id)
    if resolved is not None:
        return resolved
    if configured_path is None:
        return None
    candidate = Path(configured_path)
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


def build_embedding_pack_ref(
    pair: str,
    path: Path | None,
    *,
    pack_id: str | None = None,
) -> Optional[EmbeddingPackRef]:
    if path is None:
        return None
    candidate = Path(path)
    manifest = load_installed_pack_manifest_for_artifact(candidate)
    resolved_pack_id = (
        str(manifest.pack_id).strip()
        if manifest is not None and str(manifest.pack_id).strip()
        else str(pack_id or "").strip() or _infer_embedding_pack_id(candidate)
    )
    provider = (
        str(manifest.provider).strip().lower()
        if manifest is not None and str(manifest.provider).strip()
        else _infer_embedding_provider(resolved_pack_id)
    )
    return EmbeddingPackRef(
        pair=normalize_pair_key(pair),
        path=candidate,
        provider=provider,
        pack_id=resolved_pack_id,
        source_profile=_infer_embedding_source_profile(resolved_pack_id, provider=provider),
    )


def _infer_embedding_pack_id(path: Path) -> str:
    name = path.name.strip()
    for suffix in (".sqlite", ".sqlite3", ".db", ".vec", ".bin"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    if name:
        return name
    return path.parent.name


def _infer_embedding_provider(pack_id: str) -> str:
    normalized = str(pack_id or "").strip().lower()
    if (
        normalized.startswith("embed-")
        or normalized.startswith("wiki.")
        or normalized.startswith("cc.")
    ):
        return "fasttext"
    return normalized or "embedding"


def _infer_embedding_source_profile(pack_id: str, *, provider: str) -> str:
    normalized = str(pack_id or "").strip().lower()
    if normalized.startswith("embed-xling-") or ".align" in normalized:
        return f"{provider}-aligned"
    return f"{provider}-monolingual"
