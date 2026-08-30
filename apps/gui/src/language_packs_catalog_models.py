from __future__ import annotations

from dataclasses import dataclass, field

from i18n import t
from lexishift_core.frequency.sqlite import ParseConfig, PosInventoryConfig

CC_BY_4_URL = "https://creativecommons.org/licenses/by/4.0/"
CC_BY_SA_3_URL = "https://creativecommons.org/licenses/by-sa/3.0/"
CC_BY_SA_4_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
GPL_2_URL = "https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html"
GPL_3_URL = "https://www.gnu.org/licenses/gpl-3.0.en.html"
LGPL_2_1_URL = "https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html"
AUTO_DOWNLOAD_MODE = "auto-download"
MANUAL_SUPPLY_MODE = "manual-supply"
REVIEW_REQUIRED_MODE = "review-required"
EXPECTED_NOT_VERIFIED = "expected-not-verified"
VERIFIED_FROM_UPSTREAM = "verified-from-upstream"


def _frequency_pos_inventory_config(pack_id: str) -> PosInventoryConfig | None:
    normalized = str(pack_id or "").strip().lower()
    if normalized == "freq-ja-bccwj":
        return PosInventoryConfig(
            source_provider="freq-ja-bccwj",
            source_kind="frequency",
            source_profile="bccwj",
            pos_columns=("pos",),
        )
    if normalized == "freq-es-cde":
        return PosInventoryConfig(
            source_provider="freq-es-cde",
            source_kind="frequency",
            source_profile="freq-es-cde",
            pos_columns=("pos",),
        )
    if normalized == "freq-es-spalex-v1":
        return PosInventoryConfig(
            source_provider="freq-es-spalex-v1",
            source_kind="frequency",
            source_profile="spalex_only_v1",
            pos_columns=("pos",),
        )
    if normalized == "freq-en-coca":
        return PosInventoryConfig(
            source_provider="freq-en-coca",
            source_kind="frequency",
            source_profile="compact-latin",
            pos_columns=("pos",),
        )
    return None


@dataclass(frozen=True)
class LanguagePackInfo:
    pack_id: str
    name: str
    language: str
    source: str
    size: str
    url: str
    wayback_url: str
    filename: str
    local_kind: str
    required_files: tuple[str, ...] = ()
    sqlite_filename: str | None = None
    source_filename: str | None = None
    source_version: str | None = None
    source_dump: str | None = None
    build_mode: str = "download_only"
    source_lang_code: str | None = None
    target_lang_code: str | None = None
    gloss_language: str | None = None
    name_key: str | None = None
    language_key: str | None = None
    source_key: str | None = None
    pair_key: str | None = None
    download_size_bytes: int | None = None
    license_name: str = ""
    license_url: str = ""
    license_status: str = ""
    distribution_mode: str = ""
    license_notes: tuple[str, ...] = ()

    def display_name(self) -> str:
        return t(self.name_key) if self.name_key else self.name

    def display_language(self) -> str:
        return t(self.language_key) if self.language_key else self.language

    def display_source(self) -> str:
        return t(self.source_key) if self.source_key else self.source


@dataclass(frozen=True)
class FrequencyPackInfo:
    pack_id: str
    name: str
    language: str
    source: str
    size: str
    url: str
    wayback_url: str
    filename: str
    sqlite_filename: str
    source_filename: str | None = None
    source_version: str | None = None
    parse_config: ParseConfig = field(default_factory=ParseConfig)
    index_column: str = "lemma"
    build_mode: str = "convert_archive"
    name_key: str | None = None
    language_key: str | None = None
    source_key: str | None = None
    download_size_bytes: int | None = None
    license_name: str = ""
    license_url: str = ""
    license_status: str = ""
    distribution_mode: str = ""
    license_notes: tuple[str, ...] = ()

    def display_name(self) -> str:
        return t(self.name_key) if self.name_key else self.name

    def display_language(self) -> str:
        return t(self.language_key) if self.language_key else self.language

    def display_source(self) -> str:
        return t(self.source_key) if self.source_key else self.source


@dataclass(frozen=True)
class PosOverlayPackInfo:
    pack_id: str
    name: str
    language: str
    source: str
    size: str
    url: str
    wayback_url: str
    filename: str
    sqlite_filename: str
    source_urls: tuple[str, ...] = ()
    provider: str = ""
    build_mode: str = "ud_ancora_pos_overlay"
    name_key: str | None = None
    language_key: str | None = None
    source_key: str | None = None
    download_size_bytes: int | None = None
    license_name: str = ""
    license_url: str = ""
    license_status: str = ""
    distribution_mode: str = ""
    license_notes: tuple[str, ...] = ()

    def display_name(self) -> str:
        return t(self.name_key) if self.name_key else self.name

    def display_language(self) -> str:
        return t(self.language_key) if self.language_key else self.language

    def display_source(self) -> str:
        return t(self.source_key) if self.source_key else self.source


@dataclass(frozen=True)
class SemanticPackInfo:
    pack_id: str
    name: str
    pair: str
    source: str
    size: str
    url: str = ""
    wayback_url: str = ""
    filename: str = "semantic_inventory.json"
    name_key: str | None = None
    language_key: str | None = None
    source_key: str | None = None
    license_name: str = ""
    license_url: str = ""
    license_status: str = ""
    distribution_mode: str = ""
    license_notes: tuple[str, ...] = ()

    def display_name(self) -> str:
        return t(self.name_key) if self.name_key else self.name

    def display_language(self) -> str:
        return self.pair

    def display_source(self) -> str:
        return t(self.source_key) if self.source_key else self.source


@dataclass(frozen=True)
class PackTransportOverride:
    url: str | None = None
    wayback_url: str | None = None
    filename: str | None = None
    expected_content_type: str | None = None
    disabled: bool = False
    disabled_reason: str | None = None


@dataclass(frozen=True)
class PackCatalogSnapshot:
    language_packs: tuple[LanguagePackInfo, ...]
    embedding_packs: tuple[LanguagePackInfo, ...]
    cross_embedding_packs: tuple[LanguagePackInfo, ...]
    frequency_packs: tuple[FrequencyPackInfo, ...]
    pos_overlay_packs: tuple[PosOverlayPackInfo, ...]
    semantic_packs: tuple[SemanticPackInfo, ...]
