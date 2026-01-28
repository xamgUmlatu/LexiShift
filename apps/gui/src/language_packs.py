from __future__ import annotations

import gzip
import os
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal

from i18n import t

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
        size="~15 MB",
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
            request = urllib.request.Request(self._url, headers={"User-Agent": "LexiShift/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
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
            self.completed.emit(self._pack_id, final_path)
        except Exception as exc:
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
