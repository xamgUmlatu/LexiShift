from __future__ import annotations

from dataclasses import replace
from typing import Mapping, Sequence, TypeVar

from language_packs_catalog_data import (
    CROSS_EMBEDDING_PACKS,
    EMBEDDING_PACKS,
    FREQUENCY_PACKS,
    LANGUAGE_PACKS,
    POS_OVERLAY_PACKS,
    SEMANTIC_PACKS,
)
from language_packs_catalog_models import (
    FrequencyPackInfo,
    LanguagePackInfo,
    PackCatalogSnapshot,
    PackTransportOverride,
    PosOverlayPackInfo,
    SemanticPackInfo,
    AUTO_DOWNLOAD_MODE as AUTO_DOWNLOAD_MODE,
    MANUAL_SUPPLY_MODE as MANUAL_SUPPLY_MODE,
    _frequency_pos_inventory_config as _frequency_pos_inventory_config,
)

_PackInfoT = TypeVar(
    "_PackInfoT",
    LanguagePackInfo,
    FrequencyPackInfo,
    PosOverlayPackInfo,
    SemanticPackInfo,
)


def _normalized_transport_value(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    normalized = raw.strip()
    return normalized or None


def _normalized_transport_flag(raw: object) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, int):
        return raw == 1
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"", "0", "false", "no", "off"}:
            return False
    return False


def _coerce_transport_override(
    raw: PackTransportOverride | Mapping[str, object],
) -> PackTransportOverride:
    if isinstance(raw, PackTransportOverride):
        return raw
    return PackTransportOverride(
        url=_normalized_transport_value(raw.get("url")),
        wayback_url=_normalized_transport_value(raw.get("wayback_url")),
        filename=_normalized_transport_value(raw.get("filename")),
        expected_content_type=_normalized_transport_value(raw.get("expected_content_type")),
        disabled=_normalized_transport_flag(raw.get("disabled")),
        disabled_reason=_normalized_transport_value(raw.get("disabled_reason")),
    )


def _normalize_transport_overrides(
    source_overrides: Mapping[str, PackTransportOverride | Mapping[str, object]] | None,
) -> dict[str, PackTransportOverride]:
    normalized: dict[str, PackTransportOverride] = {}
    if not source_overrides:
        return normalized
    for raw_pack_id, raw_override in source_overrides.items():
        pack_id = str(raw_pack_id or "").strip()
        if not pack_id or raw_override is None:
            continue
        override = _coerce_transport_override(raw_override)
        if (
            override.url is None
            and override.wayback_url is None
            and override.filename is None
            and override.expected_content_type is None
            and not override.disabled
            and override.disabled_reason is None
        ):
            continue
        normalized[pack_id] = override
    return normalized


def _apply_transport_overrides(
    packs: Sequence[_PackInfoT],
    *,
    source_overrides: Mapping[str, PackTransportOverride],
) -> tuple[_PackInfoT, ...]:
    result: list[_PackInfoT] = []
    for pack in packs:
        override = source_overrides.get(str(pack.pack_id))
        if override is None:
            result.append(pack)
            continue
        updates: dict[str, str] = {}
        if override.url is not None:
            updates["url"] = override.url
        if override.wayback_url is not None:
            updates["wayback_url"] = override.wayback_url
        if override.filename is not None:
            updates["filename"] = override.filename
        result.append(replace(pack, **updates) if updates else pack)
    return tuple(result)


def build_pack_catalogs(
    *,
    source_overrides: Mapping[str, PackTransportOverride | Mapping[str, object]] | None = None,
) -> PackCatalogSnapshot:
    normalized_overrides = _normalize_transport_overrides(source_overrides)
    return PackCatalogSnapshot(
        language_packs=_apply_transport_overrides(
            LANGUAGE_PACKS,
            source_overrides=normalized_overrides,
        ),
        embedding_packs=_apply_transport_overrides(
            EMBEDDING_PACKS,
            source_overrides=normalized_overrides,
        ),
        cross_embedding_packs=_apply_transport_overrides(
            CROSS_EMBEDDING_PACKS,
            source_overrides=normalized_overrides,
        ),
        frequency_packs=_apply_transport_overrides(
            FREQUENCY_PACKS,
            source_overrides=normalized_overrides,
        ),
        pos_overlay_packs=_apply_transport_overrides(
            POS_OVERLAY_PACKS,
            source_overrides=normalized_overrides,
        ),
        semantic_packs=_apply_transport_overrides(
            SEMANTIC_PACKS,
            source_overrides=normalized_overrides,
        ),
    )
