from __future__ import annotations

import gzip
import os
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from dataclasses import dataclass, field
import ssl
import sys
from datetime import datetime

from PySide6.QtCore import QThread, Signal, QStandardPaths

from i18n import t
from lexishift_core.frequency.sqlite import ParseConfig, convert_frequency_to_sqlite


def _app_data_root() -> str:
    base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    base_dir = base_dir or os.path.expanduser("~")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def download_log_path() -> str:
    return os.path.join(_app_data_root(), "language_pack_download.log")


def _log_download(message: str) -> None:
    try:
        stamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(download_log_path(), "a", encoding="utf-8") as handle:
            handle.write(f"[{stamp}] {message}\n")
    except OSError:
        pass


def _should_retry_insecure(exc: Exception) -> bool:
    text = str(exc)
    return (
        isinstance(exc, FileNotFoundError)
        or "base_library.zip" in text
        or "CERTIFICATE_VERIFY_FAILED" in text
        or "SSL" in text
    )


def _open_request(request: urllib.request.Request, timeout: int) -> urllib.request.addinfourl:
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except Exception as exc:
        if _should_retry_insecure(exc):
            _log_download(f"Retrying with insecure SSL context after error: {exc}")
            ctx = ssl._create_unverified_context()
            return urllib.request.urlopen(request, timeout=timeout, context=ctx)
        raise

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
    name_key: str | None = None
    language_key: str | None = None
    source_key: str | None = None
    pair_key: str | None = None

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
    parse_config: ParseConfig = field(default_factory=ParseConfig)
    index_column: str = "lemma"
    build_mode: str = "convert_archive"
    name_key: str | None = None
    language_key: str | None = None
    source_key: str | None = None

    def display_name(self) -> str:
        return t(self.name_key) if self.name_key else self.name

    def display_language(self) -> str:
        return t(self.language_key) if self.language_key else self.language

    def display_source(self) -> str:
        return t(self.source_key) if self.source_key else self.source

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
        name_key="packs.freedict_en_de",
        language_key="languages.english_german",
        source_key="providers.freedict",
    ),
    LanguagePackInfo(
        pack_id="freedict-es-en",
        name="FreeDict (ES→EN)",
        language="Spanish → English",
        source="FreeDict",
        size="119 KB",
        url="https://download.freedict.org/dictionaries/spa-eng/0.3.1/freedict-spa-eng-0.3.1.src.tar.xz",
        wayback_url="https://web.archive.org/web/*/https://download.freedict.org/dictionaries/spa-eng/0.3.1/freedict-spa-eng-0.3.1.src.tar.xz",
        filename="freedict-spa-eng-0.3.1.src.tar.xz",
        local_kind="dir",
        required_files=("spa-eng.tei",),
        source_key="providers.freedict",
    ),
    LanguagePackInfo(
        pack_id="freedict-en-es",
        name="FreeDict (EN→ES)",
        language="English → Spanish",
        source="FreeDict",
        size="3.5 MB",
        url="https://download.freedict.org/dictionaries/eng-spa/2025.11.23/freedict-eng-spa-2025.11.23.src.tar.xz",
        wayback_url="https://web.archive.org/web/*/https://download.freedict.org/dictionaries/eng-spa/2025.11.23/freedict-eng-spa-2025.11.23.src.tar.xz",
        filename="freedict-eng-spa-2025.11.23.src.tar.xz",
        local_kind="dir",
        required_files=("eng-spa.tei",),
        source_key="providers.freedict",
    ),
    LanguagePackInfo(
        pack_id="cc-cedict-zh-en",
        name="CC-CEDICT",
        language="Chinese → English",
        source="MDBG",
        size="9.7 MB",
        url="https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip",
        wayback_url="https://web.archive.org/web/20250110/https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip",
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
        size="1.6 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.en.align.vec",
        wayback_url="https://web.archive.org/web/2025/https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.en.align.vec",
        filename="wiki.en.align.vec",
        local_kind="file",
        name_key="embeddings.fasttext_en_aligned",
        language_key="languages.english_aligned",
        source_key="providers.fasttext",
        pair_key="en-ja",
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
        size="2.1 GB",
        url="https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.es.align.vec",
        wayback_url="https://web.archive.org/web/*/https://dl.fbaipublicfiles.com/fasttext/vectors-aligned/wiki.es.align.vec",
        filename="wiki.es.align.vec",
        local_kind="file",
        source_key="providers.fasttext",
        pair_key="en-es",
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
        sqlite_filename="freq-en-coca.sqlite",
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
        sqlite_filename="freq-ja-bccwj.sqlite",
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
        sqlite_filename="freq-de-default.sqlite",
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
        size="42 KB",
        url="https://www.wordfrequency.info/files/spanish/spanish_lemmas20k.txt",
        wayback_url="https://web.archive.org/web/*/https://www.wordfrequency.info/files/spanish/spanish_lemmas20k.txt",
        filename="spanish_lemmas20k.txt",
        sqlite_filename="freq-es-cde.sqlite",
        parse_config=ParseConfig(
            delimiter="\t",
            header_starts_with="ID",
            skip_prefixes=("----",),
            encoding="latin-1",
        ),
        index_column="lemma",
    ),
]


class LanguagePackDownloadThread(QThread):
    progress = Signal(str, int, int)
    completed = Signal(str, str)
    failed = Signal(str, str)

    def __init__(self, pack: LanguagePackInfo, dest_path: str, parent=None) -> None:
        super().__init__(parent)
        self._pack = pack
        self._pack_id = pack.pack_id
        self._url = pack.url
        self._dest_path = dest_path

    def run(self) -> None:
        try:
            _log_download(
                f"[{self._pack_id}] starting download url={self._url} dest={self._dest_path} "
                f"py={sys.version.split()[0]} meipass={getattr(sys, '_MEIPASS', None)}"
            )
            request = urllib.request.Request(self._url, headers={"User-Agent": "LexiShift/1.0"})
            with _open_request(request, timeout=30) as response:
                status = getattr(response, "status", None)
                _log_download(f"[{self._pack_id}] response status={status} final_url={response.geturl()}")
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                os.makedirs(os.path.dirname(self._dest_path), exist_ok=True)
                with open(self._dest_path, "wb") as handle:
                    while True:
                        if self.isInterruptionRequested():
                            self._cleanup_partial(self._dest_path)
                            self.failed.emit(self._pack_id, "cancelled")
                            return
                        chunk = response.read(1024 * 128)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(self._pack_id, downloaded, total)
            if self.isInterruptionRequested():
                self._cleanup_partial(self._dest_path)
                self.failed.emit(self._pack_id, "cancelled")
                return
            final_path = self._postprocess_download(self._dest_path)
            _log_download(f"[{self._pack_id}] completed path={final_path}")
            self.completed.emit(self._pack_id, final_path)
        except Exception as exc:
            _log_download(f"[{self._pack_id}] failed error={exc}")
            self.failed.emit(self._pack_id, str(exc))

    def _postprocess_download(self, dest_path: str) -> str:
        if dest_path.endswith(".zip"):
            target_dir = os.path.splitext(dest_path)[0]
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(dest_path, "r") as archive:
                archive.extractall(target_dir)
            return self._finalize_extracted(target_dir, dest_path)
        if dest_path.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz")):
            target_dir = dest_path
            for suffix in (".tar.gz", ".tgz", ".tar.xz", ".txz"):
                if target_dir.endswith(suffix):
                    target_dir = target_dir[: -len(suffix)]
                    break
            os.makedirs(target_dir, exist_ok=True)
            with tarfile.open(dest_path, "r:*") as archive:
                archive.extractall(target_dir)
            return self._finalize_extracted(target_dir, dest_path)
        if dest_path.endswith(".gz"):
            target_path = os.path.splitext(dest_path)[0]
            with gzip.open(dest_path, "rb") as source, open(target_path, "wb") as output:
                shutil.copyfileobj(source, output)
            return self._finalize_extracted(target_path, dest_path)
        return dest_path

    def _finalize_extracted(self, extracted_path: str, archive_path: str) -> str:
        if not self._pack.required_files:
            self._cleanup_archive(archive_path)
            return extracted_path
        target_dir = extracted_path if os.path.isdir(extracted_path) else os.path.dirname(extracted_path)
        required = list(self._pack.required_files)
        found = {}
        for root, _dirs, files in os.walk(target_dir):
            for name in files:
                if name in required and name not in found:
                    found[name] = os.path.join(root, name)
            if len(found) == len(required):
                break
        for name in required:
            src = found.get(name)
            if not src:
                continue
            dest = os.path.join(target_dir, name)
            if os.path.abspath(src) != os.path.abspath(dest):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(src, dest)
        for entry in os.listdir(target_dir):
            path = os.path.join(target_dir, entry)
            if entry in required:
                continue
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except OSError:
                pass
        self._cleanup_archive(archive_path)
        return target_dir

    def _cleanup_archive(self, archive_path: str) -> None:
        try:
            if os.path.exists(archive_path):
                os.remove(archive_path)
        except OSError:
            pass

    def _cleanup_partial(self, path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


class FrequencyPackDownloadThread(QThread):
    progress = Signal(str, int, int)
    completed = Signal(str, str)
    failed = Signal(str, str)

    def __init__(
        self,
        pack: FrequencyPackInfo,
        archive_path: str,
        sqlite_path: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._pack = pack
        self._pack_id = pack.pack_id
        self._url = pack.url
        self._archive_path = archive_path
        self._sqlite_path = sqlite_path

    def run(self) -> None:
        try:
            sqlite_path = ""
            if self._pack.build_mode == "de_frequency_pipeline":
                sqlite_path = self._build_de_pipeline()
            else:
                _log_download(
                    f"[{self._pack_id}] starting download url={self._url} dest={self._archive_path} "
                    f"py={sys.version.split()[0]} meipass={getattr(sys, '_MEIPASS', None)}"
                )
                self._download_archive()
                if self.isInterruptionRequested():
                    self._cleanup_partial(self._archive_path)
                    self.failed.emit(self._pack_id, "cancelled")
                    return
                sqlite_path = self._convert_to_sqlite(self._archive_path)
            _log_download(f"[{self._pack_id}] converted sqlite={sqlite_path}")
            self.completed.emit(self._pack_id, sqlite_path)
        except Exception as exc:
            _log_download(f"[{self._pack_id}] failed error={exc}")
            self._cleanup_partial(self._sqlite_path)
            self.failed.emit(self._pack_id, str(exc))

    def _download_archive(self) -> None:
        request = urllib.request.Request(self._url, headers={"User-Agent": "LexiShift/1.0"})
        with _open_request(request, timeout=30) as response:
            status = getattr(response, "status", None)
            _log_download(f"[{self._pack_id}] response status={status} final_url={response.geturl()}")
            total = int(response.headers.get("Content-Length") or 0)
            downloaded = 0
            os.makedirs(os.path.dirname(self._archive_path), exist_ok=True)
            with open(self._archive_path, "wb") as handle:
                while True:
                    if self.isInterruptionRequested():
                        self._cleanup_partial(self._archive_path)
                        raise RuntimeError("cancelled")
                    chunk = response.read(1024 * 128)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    self.progress.emit(self._pack_id, downloaded, total)

    def _build_de_pipeline(self) -> str:
        _log_download(
            f"[{self._pack_id}] starting DE pipeline output={self._sqlite_path} "
            f"language_packs={self._language_packs_dir()} py={sys.version.split()[0]}"
        )
        from lexishift_core.frequency.de.pipeline import run_de_frequency_pipeline

        def _progress(done: int, total: int) -> None:
            self.progress.emit(self._pack_id, int(done), int(total))

        result = run_de_frequency_pipeline(
            output_sqlite=Path(self._sqlite_path),
            language_packs_dir=self._language_packs_dir(),
            overwrite=True,
            drop_proper_nouns=True,
            progress_cb=_progress,
            cancel_cb=lambda: bool(self.isInterruptionRequested()),
        )
        if self.isInterruptionRequested():
            self._cleanup_partial(self._sqlite_path)
            raise RuntimeError("cancelled")
        self._cleanup_partial(self._archive_path)
        return str(result.output_path)

    def _language_packs_dir(self) -> Path:
        target = Path(_app_data_root()) / "language_packs"
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _convert_to_sqlite(self, archive_path: str) -> str:
        source_path, cleanup_paths = self._prepare_source(archive_path)
        os.makedirs(os.path.dirname(self._sqlite_path), exist_ok=True)
        try:
            convert_frequency_to_sqlite(
                Path(source_path),
                Path(self._sqlite_path),
                overwrite=True,
                config=self._pack.parse_config,
                index_column=self._pack.index_column,
            )
        finally:
            for path in cleanup_paths:
                self._cleanup_path(path)
        return self._sqlite_path

    def _prepare_source(self, archive_path: str) -> tuple[str, list[str]]:
        cleanup_paths: list[str] = []
        if archive_path.endswith(".zip"):
            target_dir = os.path.splitext(archive_path)[0]
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(archive_path, "r") as archive:
                archive.extractall(target_dir)
            cleanup_paths.extend([archive_path, target_dir])
            source_path = self._locate_source_file(target_dir)
            cleanup_paths.append(source_path)
            return source_path, cleanup_paths
        if archive_path.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz")):
            target_dir = archive_path
            for suffix in (".tar.gz", ".tgz", ".tar.xz", ".txz"):
                if target_dir.endswith(suffix):
                    target_dir = target_dir[: -len(suffix)]
                    break
            os.makedirs(target_dir, exist_ok=True)
            with tarfile.open(archive_path, "r:*") as archive:
                archive.extractall(target_dir)
            cleanup_paths.extend([archive_path, target_dir])
            source_path = self._locate_source_file(target_dir)
            cleanup_paths.append(source_path)
            return source_path, cleanup_paths
        if archive_path.endswith(".gz"):
            target_path = os.path.splitext(archive_path)[0]
            with gzip.open(archive_path, "rb") as source, open(target_path, "wb") as output:
                shutil.copyfileobj(source, output)
            cleanup_paths.extend([archive_path, target_path])
            return target_path, cleanup_paths
        cleanup_paths.append(archive_path)
        return archive_path, cleanup_paths

    def _locate_source_file(self, root: str) -> str:
        if self._pack.source_filename:
            for dirpath, _dirnames, filenames in os.walk(root):
                if self._pack.source_filename in filenames:
                    return os.path.join(dirpath, self._pack.source_filename)
        candidates = []
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                candidates.append(os.path.join(dirpath, name))
        if not candidates:
            raise FileNotFoundError(f"No files found in extracted archive for {self._pack_id}.")
        if len(candidates) == 1:
            return candidates[0]
        preferred = [path for path in candidates if path.lower().endswith((".tsv", ".txt", ".csv"))]
        preferred.sort()
        if preferred:
            return preferred[0]
        candidates.sort()
        return candidates[0]

    def _cleanup_path(self, path: str) -> None:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def _cleanup_partial(self, path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
