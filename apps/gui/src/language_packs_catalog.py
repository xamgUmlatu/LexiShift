from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping, Sequence, TypeVar

from i18n import t
from lexishift_core.frequency.sqlite import ParseConfig, PosInventoryConfig


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

    def display_name(self) -> str:
        return t(self.name_key) if self.name_key else self.name

    def display_language(self) -> str:
        return t(self.language_key) if self.language_key else self.language

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


LANGUAGE_PACKS = [
    LanguagePackInfo(
        pack_id="wordnet-en",
        name="WordNet",
        language="English",
        source="Princeton",
        size="72.5 MB",
        url="https://en-word.net/static/english-wordnet-2025-json.zip",
        wayback_url="https://web.archive.org/web/*/https://en-word.net/static/english-wordnet-2025-json.zip",
        filename="english-wordnet-2025-json.zip",
        local_kind="dir",
        name_key="packs.wordnet",
        language_key="languages.english",
        source_key="providers.princeton",
    ),
    LanguagePackInfo(
        pack_id="moby-en",
        name="Moby Thesaurus",
        language="English",
        source="Moby",
        size="24.9 MB",
        url="https://dn790001.ca.archive.org/0/items/mobythesauruslis03202gut/mthesaur.txt",
        wayback_url="https://web.archive.org/web/*/https://dn790001.ca.archive.org/0/items/mobythesauruslis03202gut/mthesaur.txt",
        filename="mthesaur.txt",
        local_kind="file",
        name_key="packs.moby",
        language_key="languages.english",
        source_key="providers.moby",
    ),
    LanguagePackInfo(
        pack_id="openthesaurus-de",
        name="OpenThesaurus",
        language="German",
        source="OpenThesaurus",
        size="2.6 MB",
        url="https://gitlab.htl-perg.ac.at/20180016/hue_junit/-/raw/master/Thesaurus/src/openthesaurus.txt?inline=false",
        wayback_url="https://web.archive.org/web/*/https://gitlab.htl-perg.ac.at/20180016/hue_junit/-/raw/master/Thesaurus/src/openthesaurus.txt?inline=false",
        filename="openthesaurus.txt",
        local_kind="file",
        name_key="packs.openthesaurus",
        language_key="languages.german",
        source_key="providers.openthesaurus",
    ),
    LanguagePackInfo(
        pack_id="odenet-de",
        name="OdeNet",
        language="German",
        source="OdeNet",
        size="15 MB",
        url="https://raw.githubusercontent.com/hdaSprachtechnologie/odenet/refs/heads/master/odenet_oneline.xml",
        wayback_url="https://web.archive.org/web/20251101/https://raw.githubusercontent.com/hdaSprachtechnologie/odenet/refs/heads/master/odenet_oneline.xml",
        filename="odenet_oneline.xml",
        local_kind="file",
        name_key="packs.odenet",
        language_key="languages.german",
        source_key="providers.odenet",
    ),
    LanguagePackInfo(
        pack_id="jp-wordnet-sqlite",
        name="Japanese WordNet (SQLite)",
        language="Japanese",
        source="NTT",
        size="194 MB",
        url="https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn.db.gz",
        wayback_url="https://web.archive.org/web/*/https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn.db.gz",
        filename="wnjpn.db.gz",
        local_kind="file",
        name_key="packs.jp_wordnet_sqlite",
        language_key="languages.japanese",
        source_key="providers.ntt",
    ),
    LanguagePackInfo(
        pack_id="jp-wordnet",
        name="Japanese WordNet",
        language="Japanese",
        source="NTT",
        size="29.2 MB",
        url="https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn-all.tab.gz",
        wayback_url="https://web.archive.org/web/*/https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn-all.tab.gz",
        filename="wnjpn-all.tab.gz",
        local_kind="file",
        name_key="packs.jp_wordnet",
        language_key="languages.japanese",
        source_key="providers.ntt",
    ),
    LanguagePackInfo(
        pack_id="jmdict-ja-en",
        name="JMDict",
        language="Japanese → English",
        source="EDRDG",
        size="61.6 MB",
        url="https://www.edrdg.org/pub/Nihongo/JMdict_e.gz",
        wayback_url="https://web.archive.org/web/20250101/https://www.edrdg.org/pub/Nihongo/JMdict_e.gz",
        filename="JMdict_e.gz",
        local_kind="file",
        name_key="packs.jmdict",
        language_key="languages.japanese_english",
        source_key="providers.edrdg",
    ),
    LanguagePackInfo(
        pack_id="freedict-de-en",
        name="FreeDict (DE→EN)",
        language="German → English",
        source="FreeDict",
        size="449.6 MB",
        url="https://download.freedict.org/dictionaries/deu-eng/1.9-fd1/freedict-deu-eng-1.9-fd1.src.tar.xz",
        wayback_url="https://web.archive.org/web/*/https://download.freedict.org/dictionaries/deu-eng/1.9-fd1/freedict-deu-eng-1.9-fd1.src.tar.xz",
        filename="freedict-deu-eng-1.9-fd1.src.tar.xz",
        local_kind="dir",
        required_files=("deu-eng.tei",),
        sqlite_filename="main.sqlite",
        build_mode="freedict_tei_to_sqlite",
        target_lang_code="en",
        name_key="packs.freedict_de_en",
        language_key="languages.german_english",
        source_key="providers.freedict",
    ),
    LanguagePackInfo(
        pack_id="freedict-en-de",
        name="FreeDict (EN→DE)",
        language="English → German",
        source="FreeDict",
        size="364 MB",
        url="https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz",
        wayback_url="https://web.archive.org/web/*/https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz",
        filename="freedict-eng-deu-1.9-fd1.src.tar.xz",
        local_kind="dir",
        required_files=("eng-deu.tei",),
        sqlite_filename="main.sqlite",
        build_mode="freedict_tei_to_sqlite",
        target_lang_code="de",
        name_key="packs.freedict_en_de",
        language_key="languages.english_german",
        source_key="providers.freedict",
    ),
    LanguagePackInfo(
        pack_id="freedict-es-en",
        name="FreeDict (ES→EN)",
        language="Spanish → English",
        source="FreeDict",
        size="121.6 KB",
        url="https://download.freedict.org/dictionaries/spa-eng/0.3.1/freedict-spa-eng-0.3.1.src.tar.xz",
        wayback_url="https://web.archive.org/web/*/https://download.freedict.org/dictionaries/spa-eng/0.3.1/freedict-spa-eng-0.3.1.src.tar.xz",
        filename="freedict-spa-eng-0.3.1.src.tar.xz",
        local_kind="dir",
        required_files=("spa-eng.tei",),
        sqlite_filename="main.sqlite",
        build_mode="freedict_tei_to_sqlite",
        target_lang_code="en",
        source_key="providers.freedict",
        download_size_bytes=121_624,
    ),
    LanguagePackInfo(
        pack_id="freedict-en-es",
        name="FreeDict (EN→ES)",
        language="English → Spanish",
        source="FreeDict",
        size="3.72 MB",
        url="https://download.freedict.org/dictionaries/eng-spa/2025.11.23/freedict-eng-spa-2025.11.23.src.tar.xz",
        wayback_url="https://web.archive.org/web/*/https://download.freedict.org/dictionaries/eng-spa/2025.11.23/freedict-eng-spa-2025.11.23.src.tar.xz",
        filename="freedict-eng-spa-2025.11.23.src.tar.xz",
        local_kind="dir",
        required_files=("eng-spa.tei",),
        sqlite_filename="main.sqlite",
        build_mode="freedict_tei_to_sqlite",
        target_lang_code="es",
        source_key="providers.freedict",
        download_size_bytes=3_715_012,
    ),
    LanguagePackInfo(
        pack_id="wiktionary-de-en",
        name="Wiktionary (DE→EN)",
        language="German → English",
        source="Kaikki",
        size="2.54 GB",
        url="https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
        wayback_url="https://web.archive.org/web/*/https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
        filename="raw-wiktextract-data-de-en.jsonl.gz",
        local_kind="file",
        sqlite_filename="main.sqlite",
        build_mode="kaikki_glosses_to_sqlite",
        source_lang_code="de",
        gloss_language="en",
        download_size_bytes=2_535_682_507,
    ),
    LanguagePackInfo(
        pack_id="wiktionary-es-en",
        name="Wiktionary (ES→EN)",
        language="Spanish → English",
        source="Kaikki",
        size="2.67 GB",
        url="https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
        wayback_url="https://web.archive.org/web/*/https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
        filename="raw-wiktextract-data.jsonl.gz",
        local_kind="file",
        sqlite_filename="main.sqlite",
        build_mode="kaikki_glosses_to_sqlite",
        source_lang_code="es",
        gloss_language="en",
        download_size_bytes=2_665_722_104,
    ),
    LanguagePackInfo(
        pack_id="wiktionary-en-es",
        name="Wiktionary (EN→ES)",
        language="English → Spanish",
        source="Kaikki",
        size="2.67 GB",
        url="https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
        wayback_url="https://web.archive.org/web/*/https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
        filename="raw-wiktextract-data-en-es.jsonl.gz",
        local_kind="file",
        sqlite_filename="main.sqlite",
        build_mode="kaikki_translations_to_sqlite",
        source_lang_code="en",
        target_lang_code="es",
        download_size_bytes=2_665_722_104,
    ),
    LanguagePackInfo(
        pack_id="cc-cedict-zh-en",
        name="CC-CEDICT",
        language="Chinese → English",
        source="MDBG",
        size="9.7 MB",
        url="https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip",
        wayback_url="https://web.archive.org/web/*/https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip",
        filename="cedict_1_0_ts_utf-8_mdbg.zip",
        local_kind="dir",
        required_files=("cedict_ts.u8",),
        name_key="packs.cc_cedict",
        language_key="languages.chinese_english",
        source_key="providers.mdbg",
    ),
]

EMBEDDING_PACKS = [
    LanguagePackInfo(
        pack_id="embed-en-cc",
        name="fastText English (Common Crawl)",
        language="English",
        source="fastText",
        size="4.5 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.en.300.vec.gz",
        wayback_url="https://web.archive.org/web/2025/https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.en.300.vec.gz",
        filename="cc.en.300.vec.gz",
        local_kind="file",
        name_key="embeddings.fasttext_en",
        language_key="languages.english",
        source_key="providers.fasttext",
        pair_key="en-en",
    ),
    LanguagePackInfo(
        pack_id="embed-de-cc",
        name="fastText German (Common Crawl)",
        language="German",
        source="fastText",
        size="4.5 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.de.300.vec.gz",
        wayback_url="https://web.archive.org/web/2025/https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.de.300.vec.gz",
        filename="cc.de.300.vec.gz",
        local_kind="file",
        name_key="embeddings.fasttext_de",
        language_key="languages.german",
        source_key="providers.fasttext",
        pair_key="de-de",
    ),
    LanguagePackInfo(
        pack_id="embed-ja-cc",
        name="fastText Japanese (Common Crawl)",
        language="Japanese",
        source="fastText",
        size="4.2 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ja.300.vec.gz",
        wayback_url="https://web.archive.org/web/2025/https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ja.300.vec.gz",
        filename="cc.ja.300.vec.gz",
        local_kind="file",
        name_key="embeddings.fasttext_ja",
        language_key="languages.japanese",
        source_key="providers.fasttext",
        pair_key="ja-ja",
    ),
    LanguagePackInfo(
        pack_id="embed-es-cc",
        name="fastText Spanish (Common Crawl)",
        language="Spanish",
        source="fastText",
        size="1.2 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.es.300.vec.gz",
        wayback_url="https://web.archive.org/web/*/https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.es.300.vec.gz",
        filename="cc.es.300.vec.gz",
        local_kind="file",
        source_key="providers.fasttext",
        pair_key="es-es",
    ),
]

CROSS_EMBEDDING_PACKS = [
    LanguagePackInfo(
        pack_id="embed-xling-en",
        name="fastText English (Aligned)",
        language="English (Aligned)",
        source="fastText",
        size="5.69 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.en.align.vec",
        wayback_url="https://web.archive.org/web/2025/https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.en.align.vec",
        filename="wiki.en.align.vec",
        local_kind="file",
        name_key="embeddings.fasttext_en_aligned",
        language_key="languages.english_aligned",
        source_key="providers.fasttext",
        pair_key="en-ja",
        download_size_bytes=5_685_446_378,
    ),
    LanguagePackInfo(
        pack_id="embed-xling-de",
        name="fastText German (Aligned)",
        language="German (Aligned)",
        source="fastText",
        size="1.4 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.de.align.vec",
        wayback_url="https://web.archive.org/web/2025/https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.de.align.vec",
        filename="wiki.de.align.vec",
        local_kind="file",
        name_key="embeddings.fasttext_de_aligned",
        language_key="languages.german_aligned",
        source_key="providers.fasttext",
        pair_key="de-en",
    ),
    LanguagePackInfo(
        pack_id="embed-xling-ja",
        name="fastText Japanese (Aligned)",
        language="Japanese (Aligned)",
        source="fastText",
        size="1.2 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.ja.align.vec",
        wayback_url="https://web.archive.org/web/2025/https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.ja.align.vec",
        filename="wiki.ja.align.vec",
        local_kind="file",
        name_key="embeddings.fasttext_ja_aligned",
        language_key="languages.japanese_aligned",
        source_key="providers.fasttext",
        pair_key="en-ja",
    ),
    LanguagePackInfo(
        pack_id="embed-xling-es",
        name="fastText Spanish (Aligned)",
        language="Spanish (Aligned)",
        source="fastText",
        size="2.23 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.es.align.vec",
        wayback_url="https://web.archive.org/web/*/https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.es.align.vec",
        filename="wiki.es.align.vec",
        local_kind="file",
        source_key="providers.fasttext",
        pair_key="en-es",
        download_size_bytes=2_227_283_009,
    ),
]

FREQUENCY_PACKS = [
    FrequencyPackInfo(
        pack_id="freq-en-coca",
        name="COCA English Frequency (Lemmas)",
        language="English",
        source="COCA",
        size="2 MB",
        url="https://www.wordfrequency.info/samples/lemmas_60k.txt",
        wayback_url="https://web.archive.org/web/20210127204059/https://www.wordfrequency.info/samples/lemmas_60k.txt",
        filename="lemmas_60k.txt",
        sqlite_filename="main.sqlite",
        parse_config=ParseConfig(
            delimiter="\t",
            header_starts_with="rank",
            skip_prefixes=("*", "-----"),
        ),
        index_column="lemma",
        name_key="packs.freq_en_coca",
        language_key="languages.english",
        source_key="providers.coca",
    ),
    FrequencyPackInfo(
        pack_id="freq-ja-bccwj",
        name="BCCWJ Japanese Frequency (SUW)",
        language="Japanese",
        source="NINJAL",
        size="50 MB",
        url="https://repository.ninjal.ac.jp/record/3234/files/BCCWJ_frequencylist_suw_ver1_0.zip",
        wayback_url="https://web.archive.org/web/0/https://repository.ninjal.ac.jp/record/3234/files/BCCWJ_frequencylist_suw_ver1_0.zip",
        filename="BCCWJ_frequencylist_suw_ver1_0.zip",
        sqlite_filename="main.sqlite",
        source_filename="BCCWJ_frequencylist_suw_ver1_0.tsv",
        parse_config=ParseConfig(
            delimiter="\t",
            header_starts_with="rank",
            skip_prefixes=(),
        ),
        index_column="lemma",
        name_key="packs.freq_ja_bccwj",
        language_key="languages.japanese",
        source_key="providers.ninjal",
    ),
    FrequencyPackInfo(
        pack_id="freq-de-default",
        name="German News Frequency (Lemmas)",
        language="German",
        source="Leipzig + LanguageTool",
        size="~80 MB",
        url="https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz",
        wayback_url="https://web.archive.org/web/*/https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz",
        filename="deu_news_2023_1M.tar.gz",
        sqlite_filename="main.sqlite",
        build_mode="de_frequency_pipeline",
        name_key="packs.freq_de_default",
        language_key="languages.german",
        source_key="providers.leipzig_languagetool",
    ),
    FrequencyPackInfo(
        pack_id="freq-es-cde",
        name="Corpus del Espanol Frequency (sample)",
        language="Spanish",
        source="Corpus del Espanol",
        size="42.9 KB",
        url="https://www.wordfrequency.info/files/spanish/spanish_lemmas20k.txt",
        wayback_url="https://web.archive.org/web/*/https://www.wordfrequency.info/files/spanish/spanish_lemmas20k.txt",
        filename="spanish_lemmas20k.txt",
        sqlite_filename="main.sqlite",
        parse_config=ParseConfig(
            delimiter="\t",
            header_starts_with="ID",
            skip_prefixes=("----",),
            encoding="latin-1",
        ),
        index_column="lemma",
        download_size_bytes=42_922,
    ),
]


@dataclass(frozen=True)
class PackCatalogSnapshot:
    language_packs: tuple[LanguagePackInfo, ...]
    embedding_packs: tuple[LanguagePackInfo, ...]
    cross_embedding_packs: tuple[LanguagePackInfo, ...]
    frequency_packs: tuple[FrequencyPackInfo, ...]


_PackInfoT = TypeVar("_PackInfoT", LanguagePackInfo, FrequencyPackInfo)


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
    )
