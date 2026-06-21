from __future__ import annotations

import hashlib
import gzip
import inspect
import os
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path
import ssl
import sys
from datetime import datetime
from typing import Mapping

from PySide6.QtCore import QThread, Signal, QStandardPaths

from lexishift_core.frequency.sqlite import (
    convert_frequency_to_sqlite,
)
from lexishift_core.helper.installed_packs import (
    write_installed_pack_manifest,
)
from lexishift_core.helper.pack_artifact_metrics import sqlite_artifact_metrics_for_pack
from lexishift_core.helper.pack_provenance import write_app_managed_pack_provenance
from lexishift_core.helper.pack_source_identity import (
    safe_pack_source_identity_fields,
    source_bundle_fields_for_pack,
)
from lexishift_core.resources.freedict_sqlite import convert_freedict_tei_to_sqlite
from lexishift_core.resources.kaikki_sqlite import convert_kaikki_glosses_to_sqlite
from lexishift_core.resources.kaikki_sqlite import convert_kaikki_translations_to_sqlite
from language_packs_catalog import (
    CROSS_EMBEDDING_PACKS,
    EMBEDDING_PACKS,
    FREQUENCY_PACKS,
    FrequencyPackInfo,
    LANGUAGE_PACKS,
    LanguagePackInfo,
    PackCatalogSnapshot,
    PackTransportOverride,
    POS_OVERLAY_PACKS,
    PosOverlayPackInfo,
    SEMANTIC_PACKS,
    SemanticPackInfo,
    _frequency_pos_inventory_config,
    build_pack_catalogs,
)
from lexishift_core.pos.ud_ancora import build_ud_ancora_pos_overlay
from pack_download_failures import encode_pack_download_failure

__all__ = [
    "CROSS_EMBEDDING_PACKS",
    "EMBEDDING_PACKS",
    "FREQUENCY_PACKS",
    "LANGUAGE_PACKS",
    "POS_OVERLAY_PACKS",
    "SEMANTIC_PACKS",
    "PackCatalogSnapshot",
    "PackTransportOverride",
    "FrequencyPackDownloadThread",
    "FrequencyPackInfo",
    "LanguagePackDownloadThread",
    "LanguagePackInfo",
    "PosOverlayPackDownloadThread",
    "PosOverlayPackInfo",
    "SemanticPackInfo",
    "build_pack_catalogs",
]

_CONFIRMED_CATALOG_LICENSE_STATUSES = frozenset(
    {
        "verified-from-upstream",
        "source-stack-audited",
        "local-reference",
    }
)
_REVIEW_CATALOG_LICENSE_STATUSES = frozenset(
    {
        "",
        "expected-not-verified",
        "manual-review-required",
        "requires_review",
        "requires-review",
    }
)


def provenance_license_status_for_pack(pack: object) -> str:
    status = str(getattr(pack, "license_status", "") or "").strip().lower()
    if status in _CONFIRMED_CATALOG_LICENSE_STATUSES:
        return "confirmed"
    if status in {"not_redistributable", "not-redistributable"}:
        return "not_redistributable"
    if status in {"internal_only", "internal-only"}:
        return "internal_only"
    if status in _REVIEW_CATALOG_LICENSE_STATUSES:
        return "requires_review"
    return "requires_review"


def _build_command_for_mode(build_mode: str) -> str:
    commands = {
        "download_only": "download_only",
        "freedict_tei_to_sqlite": "convert_freedict_tei_to_sqlite",
        "kaikki_glosses_to_sqlite": "convert_kaikki_glosses_to_sqlite",
        "kaikki_translations_to_sqlite": "convert_kaikki_translations_to_sqlite",
        "convert_archive": "convert_frequency_to_sqlite",
        "de_frequency_pipeline": "run_de_frequency_pipeline",
        "en_frequency_pipeline": "run_en_frequency_pipeline",
        "spalex_frequency_pipeline": "build_spalex_frequency_pack",
        "ud_ancora_pos_overlay": "build_ud_ancora_pos_overlay",
        "convert_to_sqlite": "scripts/data/convert_embeddings.py",
    }
    normalized = str(build_mode or "").strip()
    return commands.get(normalized, normalized)


def _language_parser_config(pack: LanguagePackInfo) -> dict[str, object]:
    build_mode = str(pack.build_mode or "").strip()
    if build_mode == "freedict_tei_to_sqlite":
        return {
            "target_lang": str(pack.target_lang_code or "").strip(),
            "tei_filename": pack.required_files[0] if pack.required_files else "",
        }
    if build_mode == "kaikki_glosses_to_sqlite":
        return {
            "source_lang_code": str(pack.source_lang_code or "").strip().lower() or "es",
            "gloss_language": str(pack.gloss_language or "").strip().lower() or "en",
            "source_dump": _kaikki_source_dump_for_pack(pack),
        }
    if build_mode == "kaikki_translations_to_sqlite":
        target_lang = str(pack.target_lang_code or "").strip().lower()
        return {
            "source_lang_code": str(pack.source_lang_code or "").strip().lower(),
            "target_lang_code": target_lang,
            "translation_language": str(pack.gloss_language or target_lang).strip().lower(),
            "source_dump": _kaikki_source_dump_for_pack(pack),
        }
    return {}


def _kaikki_source_dump_for_pack(pack: LanguagePackInfo) -> str:
    return str(pack.source_dump or "enwiktionary").strip() or "enwiktionary"


def _known_download_size_bytes(pack: object) -> int:
    raw_size = getattr(pack, "download_size_bytes", None)
    if raw_size is None:
        return 0
    try:
        size = int(raw_size)
    except (TypeError, ValueError):
        return 0
    return max(0, size)


def _response_download_total_bytes(response: object, pack: object) -> int:
    headers = getattr(response, "headers", {})
    raw_total = None
    if hasattr(headers, "get"):
        raw_total = headers.get("Content-Length")
    try:
        total = int(raw_total or 0)
    except (TypeError, ValueError):
        total = 0
    return total if total > 0 else _known_download_size_bytes(pack)


def _frequency_parser_config(pack: FrequencyPackInfo) -> dict[str, object]:
    if str(pack.build_mode or "").strip() == "de_frequency_pipeline":
        return {"drop_proper_nouns": True}
    if str(pack.build_mode or "").strip() == "en_frequency_pipeline":
        return {
            "source": "leipzig_words",
            "lang": "en",
            "min_lemma_count": 2,
            "lemmatized": True,
            "pos_policy": "none",
        }
    if str(pack.build_mode or "").strip() == "spalex_frequency_pipeline":
        return {
            "primary_source": "spalex_word_info_csv",
            "rank_policy": "spalex_zipf_then_prevalence",
            "runtime_pmw": "rank_descending_commonness_score",
            "current_seed": "none",
            "pos_policy": "none",
            "topic_policy": "none",
        }
    config = pack.parse_config
    parser_config: dict[str, object] = {
        "delimiter": config.delimiter,
        "header_starts_with": config.header_starts_with,
        "skip_prefixes": list(config.skip_prefixes),
        "encoding": config.encoding,
        "errors": config.errors,
        "index_column": pack.index_column,
    }
    pos_inventory = _frequency_pos_inventory_config(pack.pack_id)
    if pos_inventory is not None:
        parser_config["pos_inventory"] = {
            "source_provider": pos_inventory.source_provider,
            "source_kind": pos_inventory.source_kind,
            "source_profile": pos_inventory.source_profile,
            "pos_columns": list(pos_inventory.pos_columns),
        }
    return parser_config


def _file_checksums(path: str | Path) -> dict[str, str]:
    file_path = Path(path)
    if not file_path.is_file():
        return {}
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    with file_path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            sha1.update(chunk)
            sha256.update(chunk)
    return {
        "sha1": sha1.hexdigest(),
        "sha256": sha256.hexdigest(),
    }


def _converter_version_for_mode(build_mode: str) -> str:
    normalized = str(build_mode or "").strip()
    converter_sources = {
        "freedict_tei_to_sqlite": (
            "lexishift_core.resources.freedict_sqlite",
            convert_freedict_tei_to_sqlite,
        ),
        "kaikki_glosses_to_sqlite": (
            "lexishift_core.resources.kaikki_sqlite",
            convert_kaikki_glosses_to_sqlite,
        ),
        "kaikki_translations_to_sqlite": (
            "lexishift_core.resources.kaikki_sqlite",
            convert_kaikki_translations_to_sqlite,
        ),
        "convert_archive": (
            "lexishift_core.frequency.sqlite",
            convert_frequency_to_sqlite,
        ),
    }
    if normalized in converter_sources:
        label, converter = converter_sources[normalized]
        source_file = inspect.getsourcefile(converter)
        return _source_file_version(label, source_file)
    if normalized == "de_frequency_pipeline":
        from lexishift_core.frequency.de.pipeline import run_de_frequency_pipeline

        source_file = inspect.getsourcefile(run_de_frequency_pipeline)
        return _source_file_version("lexishift_core.frequency.de.pipeline", source_file)
    if normalized == "en_frequency_pipeline":
        from lexishift_core.frequency.en.pipeline import run_en_frequency_pipeline

        source_file = inspect.getsourcefile(run_en_frequency_pipeline)
        return _source_file_version("lexishift_core.frequency.en.pipeline", source_file)
    if normalized == "spalex_frequency_pipeline":
        from lexishift_core.frequency.es.spalex import build_spalex_frequency_pack

        source_file = inspect.getsourcefile(build_spalex_frequency_pack)
        return _source_file_version("lexishift_core.frequency.es.spalex", source_file)
    if normalized == "ud_ancora_pos_overlay":
        source_file = inspect.getsourcefile(build_ud_ancora_pos_overlay)
        return _source_file_version("lexishift_core.pos.ud_ancora", source_file)
    if normalized == "convert_to_sqlite":
        return _source_file_version(
            "scripts.data.convert_embeddings",
            _repo_relative_file("scripts/data/convert_embeddings.py"),
        )
    return ""


def _source_file_version(label: str, path: str | Path | None) -> str:
    if not path:
        return ""
    digest = _file_checksums(path).get("sha256", "")
    if not digest:
        return ""
    return f"source_sha256:{label}:{digest}"


def _repo_relative_file(relative_path: str) -> Path:
    this_file = Path(__file__).resolve()
    for root in (this_file.parents[3], this_file.parents[2]):
        candidate = root / relative_path
        if candidate.exists():
            return candidate
    return this_file.parents[3] / relative_path


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


class LanguagePackDownloadThread(QThread):
    progress = Signal(str, int, int)
    completed = Signal(str, str)
    failed = Signal(str, str)

    def __init__(
        self,
        pack: LanguagePackInfo,
        dest_path: str,
        parent=None,
        *,
        pack_kind: str = "language",
        write_manifest_on_complete: bool = True,
    ) -> None:
        super().__init__(parent)
        self._pack = pack
        self._pack_id = pack.pack_id
        self._url = pack.url
        self._dest_path = dest_path
        self._pack_kind = str(pack_kind or "language")
        self._write_manifest_on_complete = bool(write_manifest_on_complete)
        self._raw_artifact_sha1 = ""
        self._raw_artifact_sha256 = ""

    def run(self) -> None:
        try:
            _log_download(
                f"[{self._pack_id}] starting download url={self._url} dest={self._dest_path} "
                f"py={sys.version.split()[0]} meipass={getattr(sys, '_MEIPASS', None)}"
            )
            # TODO(kaikki-cache): Kaikki managed packs currently download their raw dump into
            # each pack root independently. Cache large raw archives by shared source URL/hash
            # and link pack-local filenames to that shared blob so users do not re-download the
            # same multi-GB Wiktextract dump for every Kaikki-derived pack.
            request = urllib.request.Request(self._url, headers={"User-Agent": "LexiShift/1.0"})
            with _open_request(request, timeout=30) as response:
                status = getattr(response, "status", None)
                _log_download(
                    f"[{self._pack_id}] response status={status} final_url={response.geturl()}"
                )
                total = _response_download_total_bytes(response, self._pack)
                downloaded = 0
                os.makedirs(os.path.dirname(self._dest_path), exist_ok=True)
                with open(self._dest_path, "wb") as handle:
                    while True:
                        if self.isInterruptionRequested():
                            self._cleanup_partial(self._dest_path)
                            self.failed.emit(
                                self._pack_id, encode_pack_download_failure("cancelled")
                            )
                            return
                        chunk = response.read(1024 * 128)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(self._pack_id, downloaded, total)
            if self.isInterruptionRequested():
                self._cleanup_partial(self._dest_path)
                self.failed.emit(self._pack_id, encode_pack_download_failure("cancelled"))
                return
            self._capture_raw_artifact_checksums(self._dest_path)
            final_path = self._build_local_artifact(self._dest_path)
            if self._write_manifest_on_complete:
                self._write_manifest(final_path)
            _log_download(f"[{self._pack_id}] completed path={final_path}")
            self.completed.emit(self._pack_id, final_path)
        except Exception as exc:
            _log_download(f"[{self._pack_id}] failed error={exc}")
            sqlite_path = self._pack.sqlite_filename
            if sqlite_path:
                self._cleanup_partial(str(Path(self._dest_path).with_name(sqlite_path)))
            self.failed.emit(self._pack_id, encode_pack_download_failure(exc))

    def _build_local_artifact(self, dest_path: str) -> str:
        if self._pack.build_mode == "freedict_tei_to_sqlite":
            return self._build_freedict_sqlite(dest_path)
        if self._pack.build_mode == "kaikki_glosses_to_sqlite":
            return self._build_kaikki_glosses_sqlite(dest_path)
        if self._pack.build_mode == "kaikki_translations_to_sqlite":
            return self._build_kaikki_translations_sqlite(dest_path)
        return self._postprocess_download(dest_path)

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
        target_dir = os.path.dirname(archive_path)
        os.makedirs(target_dir, exist_ok=True)
        required = list(self._pack.required_files)
        found = {}
        search_root = (
            extracted_path if os.path.isdir(extracted_path) else os.path.dirname(extracted_path)
        )
        for root, _dirs, files in os.walk(search_root):
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
                if os.path.exists(dest):
                    os.remove(dest)
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

    def _write_manifest(self, final_path: str) -> None:
        pack_root = Path(self._dest_path).parent
        artifact_path = self._manifest_artifact_path(Path(final_path))
        write_installed_pack_manifest(
            pack_root.parent,
            pack_id=self._pack_id,
            pack_kind=self._pack_kind,
            provider=str(self._pack.source or "").strip().lower(),
            local_kind=self._pack.local_kind,
            build_mode=self._pack.build_mode,
            artifact_path=artifact_path,
            source_filename=self._pack.source_filename or self._pack.filename,
            sqlite_filename=self._pack.sqlite_filename,
            required_files=self._pack.required_files,
            raw_retained=False,
        )
        write_app_managed_pack_provenance(
            pack_root=pack_root,
            pack_id=self._pack_id,
            pack_kind=self._pack_kind,
            provider=str(self._pack.source or "").strip().lower(),
            source_name=str(self._pack.source or "").strip(),
            source_url=str(self._pack.url or "").strip(),
            wayback_url=self._pack.wayback_url,
            license_status=provenance_license_status_for_pack(self._pack),
            build_mode=self._pack.build_mode,
            build_command=_build_command_for_mode(self._pack.build_mode),
            converter_version=_converter_version_for_mode(self._pack.build_mode),
            parser_config=_language_parser_config(self._pack),
            artifact_path=artifact_path,
            source_filename=self._pack.source_filename or self._pack.filename,
            sqlite_filename=self._pack.sqlite_filename,
            required_files=self._pack.required_files,
            raw_artifact_sha1=self._raw_artifact_sha1 or None,
            raw_artifact_sha256=self._raw_artifact_sha256 or None,
            **safe_pack_source_identity_fields(self._pack),
        )

    def _capture_raw_artifact_checksums(self, path: str | Path) -> None:
        checksums = _file_checksums(path)
        self._raw_artifact_sha1 = checksums.get("sha1", "")
        self._raw_artifact_sha256 = checksums.get("sha256", "")

    def _manifest_artifact_path(self, final_path: Path) -> Path:
        if self._pack.local_kind == "dir" and len(self._pack.required_files) == 1:
            candidate = final_path / self._pack.required_files[0]
            if candidate.exists():
                return candidate
        return final_path

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

    def _build_kaikki_glosses_sqlite(self, archive_path: str) -> str:
        sqlite_filename = self._pack.sqlite_filename or f"{Path(archive_path).stem}.sqlite"
        output_path = str(Path(archive_path).with_name(sqlite_filename))
        source_lang_code = str(self._pack.source_lang_code or "").strip().lower() or "es"
        gloss_language = str(self._pack.gloss_language or "").strip().lower() or "en"
        metadata = convert_kaikki_glosses_to_sqlite(
            Path(archive_path),
            Path(output_path),
            source_lang_code=source_lang_code,
            gloss_language=gloss_language,
            source_provider=self._pack.pack_id,
            source_dump=_kaikki_source_dump_for_pack(self._pack),
            overwrite=True,
        )
        _log_download(
            f"[{self._pack_id}] converted sqlite={output_path} "
            f"selected_records={int(metadata.get('selected_records', 0))} "
            f"inserted_sense_rows={int(metadata.get('inserted_sense_rows', 0))}"
        )
        self._cleanup_archive(archive_path)
        return output_path

    def _build_kaikki_translations_sqlite(self, archive_path: str) -> str:
        sqlite_filename = self._pack.sqlite_filename or f"{Path(archive_path).stem}.sqlite"
        output_path = str(Path(archive_path).with_name(sqlite_filename))
        source_lang_code = str(self._pack.source_lang_code or "").strip().lower()
        target_lang_code = str(self._pack.target_lang_code or "").strip().lower()
        if not source_lang_code or not target_lang_code:
            raise ValueError(f"Missing Kaikki translation build config for pack '{self._pack_id}'")
        metadata = convert_kaikki_translations_to_sqlite(
            Path(archive_path),
            Path(output_path),
            source_lang_code=source_lang_code,
            target_lang_code=target_lang_code,
            translation_language=str(self._pack.gloss_language or target_lang_code),
            source_provider=self._pack.pack_id,
            source_dump=_kaikki_source_dump_for_pack(self._pack),
            overwrite=True,
        )
        _log_download(
            f"[{self._pack_id}] converted sqlite={output_path} "
            f"selected_records={int(metadata.get('selected_records', 0))} "
            f"inserted_sense_rows={int(metadata.get('inserted_sense_rows', 0))}"
        )
        self._cleanup_archive(archive_path)
        return output_path

    def _build_freedict_sqlite(self, archive_path: str) -> str:
        sqlite_filename = self._pack.sqlite_filename or f"{Path(archive_path).stem}.sqlite"
        output_path = str(Path(archive_path).with_name(sqlite_filename))
        target_lang_code = str(self._pack.target_lang_code or "").strip().lower()
        tei_filename = self._pack.required_files[0] if self._pack.required_files else ""
        metadata = convert_freedict_tei_to_sqlite(
            Path(archive_path),
            Path(output_path),
            target_lang=target_lang_code,
            tei_filename=tei_filename,
            overwrite=True,
        )
        _log_download(
            f"[{self._pack_id}] converted sqlite={output_path} "
            f"pair_count={int(metadata.get('pair_count', 0))} "
            f"headword_count={int(metadata.get('headword_count', 0))}"
        )
        self._cleanup_archive(archive_path)
        return output_path


class PosOverlayPackDownloadThread(QThread):
    progress = Signal(str, int, int)
    completed = Signal(str, str)
    failed = Signal(str, str)

    def __init__(
        self,
        pack: PosOverlayPackInfo,
        source_dir: str,
        sqlite_path: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._pack = pack
        self._pack_id = pack.pack_id
        self._source_dir = Path(source_dir)
        self._sqlite_path = Path(sqlite_path)

    def run(self) -> None:
        try:
            _log_download(
                f"[{self._pack_id}] starting POS overlay build source_dir={self._source_dir} "
                f"sqlite={self._sqlite_path} py={sys.version.split()[0]}"
            )
            source_paths = self._download_sources()
            if self.isInterruptionRequested():
                self._cleanup_partial(self._sqlite_path)
                self.failed.emit(self._pack_id, encode_pack_download_failure("cancelled"))
                return
            metadata = build_ud_ancora_pos_overlay(
                source_paths=tuple(source_paths),
                output_sqlite=self._sqlite_path,
                pack_id=self._pack_id,
                provider=self._pack.provider,
                overwrite=True,
                write_sidecars=True,
            )
            _log_download(
                f"[{self._pack_id}] POS overlay built rows={metadata.get('row_count', 0)}"
            )
            self.completed.emit(self._pack_id, str(self._sqlite_path))
        except Exception as exc:  # noqa: BLE001
            _log_download(f"[{self._pack_id}] POS overlay failed error={exc}")
            self._cleanup_partial(self._sqlite_path)
            self.failed.emit(self._pack_id, encode_pack_download_failure(exc))

    def _download_sources(self) -> list[Path]:
        urls = tuple(self._pack.source_urls or (self._pack.url,))
        if not urls:
            raise ValueError(f"No POS overlay source URLs configured for {self._pack_id}.")
        self._source_dir.mkdir(parents=True, exist_ok=True)
        source_paths: list[Path] = []
        total = len(urls)
        for index, url in enumerate(urls, start=1):
            if self.isInterruptionRequested():
                raise RuntimeError("cancelled")
            filename = Path(str(url).split("?", 1)[0]).name
            if not filename:
                raise ValueError(f"Could not infer filename from URL: {url}")
            target = self._source_dir / filename
            request = urllib.request.Request(str(url), headers={"User-Agent": "LexiShift/1.0"})
            with _open_request(request, timeout=60) as response:
                status = getattr(response, "status", None)
                _log_download(
                    f"[{self._pack_id}] POS source status={status} final_url={response.geturl()}"
                )
                with target.open("wb") as handle:
                    while True:
                        if self.isInterruptionRequested():
                            raise RuntimeError("cancelled")
                        chunk = response.read(1024 * 128)
                        if not chunk:
                            break
                        handle.write(chunk)
            source_paths.append(target)
            self.progress.emit(self._pack_id, index, total)
        return source_paths

    def _cleanup_partial(self, path: str | Path) -> None:
        try:
            if Path(path).exists():
                Path(path).unlink()
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
        self._raw_artifact_sha1 = ""
        self._raw_artifact_sha256 = ""
        self._source_bundle_fields: dict[str, Mapping[str, object]] = {}

    def run(self) -> None:
        try:
            sqlite_path = ""
            if self._pack.build_mode == "de_frequency_pipeline":
                sqlite_path = self._build_de_pipeline()
            elif self._pack.build_mode == "en_frequency_pipeline":
                sqlite_path = self._build_en_pipeline()
            elif self._pack.build_mode == "spalex_frequency_pipeline":
                sqlite_path = self._build_spalex_pipeline()
            else:
                _log_download(
                    f"[{self._pack_id}] starting download url={self._url} dest={self._archive_path} "
                    f"py={sys.version.split()[0]} meipass={getattr(sys, '_MEIPASS', None)}"
                )
                self._download_archive()
                if self.isInterruptionRequested():
                    self._cleanup_partial(self._archive_path)
                    self.failed.emit(self._pack_id, encode_pack_download_failure("cancelled"))
                    return
                sqlite_path = self._convert_to_sqlite(self._archive_path)
            if self._pack.build_mode != "spalex_frequency_pipeline":
                self._write_manifest(sqlite_path)
            _log_download(f"[{self._pack_id}] converted sqlite={sqlite_path}")
            self.completed.emit(self._pack_id, sqlite_path)
        except Exception as exc:
            _log_download(f"[{self._pack_id}] failed error={exc}")
            self._cleanup_partial(self._sqlite_path)
            self.failed.emit(self._pack_id, encode_pack_download_failure(exc))

    def _download_archive(self) -> None:
        request = urllib.request.Request(self._url, headers={"User-Agent": "LexiShift/1.0"})
        with _open_request(request, timeout=30) as response:
            status = getattr(response, "status", None)
            _log_download(
                f"[{self._pack_id}] response status={status} final_url={response.geturl()}"
            )
            total = _response_download_total_bytes(response, self._pack)
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

        def _capture_source_bundle(component_paths: Mapping[str, Path]) -> None:
            self._source_bundle_fields = source_bundle_fields_for_pack(
                self._pack,
                component_paths=component_paths,
            )

        result = run_de_frequency_pipeline(
            output_sqlite=Path(self._sqlite_path),
            language_packs_dir=self._language_packs_dir(),
            overwrite=True,
            drop_proper_nouns=True,
            progress_cb=_progress,
            cancel_cb=lambda: bool(self.isInterruptionRequested()),
            source_bundle_component_paths_cb=_capture_source_bundle,
        )
        if self.isInterruptionRequested():
            self._cleanup_partial(self._sqlite_path)
            raise RuntimeError("cancelled")
        self._cleanup_partial(self._archive_path)
        return str(result.output_path)

    def _build_en_pipeline(self) -> str:
        _log_download(
            f"[{self._pack_id}] starting EN pipeline output={self._sqlite_path} "
            f"language_packs={self._language_packs_dir()} py={sys.version.split()[0]}"
        )
        from lexishift_core.frequency.en.pipeline import run_en_frequency_pipeline

        def _progress(done: int, total: int) -> None:
            self.progress.emit(self._pack_id, int(done), int(total))

        def _capture_source_bundle(component_paths: Mapping[str, Path]) -> None:
            self._source_bundle_fields = source_bundle_fields_for_pack(
                self._pack,
                component_paths=component_paths,
            )

        result = run_en_frequency_pipeline(
            output_sqlite=Path(self._sqlite_path),
            language_packs_dir=self._language_packs_dir(),
            overwrite=True,
            progress_cb=_progress,
            cancel_cb=lambda: bool(self.isInterruptionRequested()),
            source_bundle_component_paths_cb=_capture_source_bundle,
        )
        if self.isInterruptionRequested():
            self._cleanup_partial(self._sqlite_path)
            raise RuntimeError("cancelled")
        self._cleanup_partial(self._archive_path)
        return str(result.output_path)

    def _build_spalex_pipeline(self) -> str:
        _log_download(
            f"[{self._pack_id}] starting SPALEX pipeline output={self._sqlite_path} "
            f"py={sys.version.split()[0]}"
        )
        self._download_archive()
        if self.isInterruptionRequested():
            self._cleanup_partial(self._archive_path)
            raise RuntimeError("cancelled")
        self._capture_raw_artifact_checksums(self._archive_path)
        from lexishift_core.frequency.es.spalex import build_spalex_frequency_pack

        metadata = build_spalex_frequency_pack(
            spalex_csv=Path(self._archive_path),
            current_frequency_db=None,
            output_sqlite=Path(self._sqlite_path),
            kaikki_forward_db=None,
            pack_id=self._pack_id,
            provider=self._pack_id,
            source_mode="spalex_only",
            overwrite=True,
            write_sidecars=True,
        )
        _log_download(
            f"[{self._pack_id}] SPALEX pipeline"
            f" rows={int(metadata.get('row_count', 0))}"
            f" pos_rows={int(metadata.get('metrics', {}).get('pos_rows', 0))}"
            f" topic_rows={int(metadata.get('metrics', {}).get('topic_domain_rows', 0))}"
        )
        self._cleanup_partial(self._archive_path)
        return self._sqlite_path

    def _language_packs_dir(self) -> Path:
        target = Path(_app_data_root()) / "language_packs"
        target.mkdir(parents=True, exist_ok=True)
        return target

    def _write_manifest(self, sqlite_path: str) -> None:
        pack_root = Path(self._sqlite_path).parent
        artifact_path = Path(sqlite_path)
        source_bundle_fields = self._source_bundle_fields or source_bundle_fields_for_pack(
            self._pack
        )
        write_installed_pack_manifest(
            pack_root.parent,
            pack_id=self._pack_id,
            pack_kind="frequency",
            provider=str(self._pack.source or "").strip().lower(),
            local_kind="file",
            build_mode=self._pack.build_mode,
            artifact_path=artifact_path,
            source_filename=self._pack.source_filename or self._pack.filename,
            sqlite_filename=self._pack.sqlite_filename,
            raw_retained=False,
        )
        write_app_managed_pack_provenance(
            pack_root=pack_root,
            pack_id=self._pack_id,
            pack_kind="frequency",
            provider=str(self._pack.source or "").strip().lower(),
            source_name=str(self._pack.source or "").strip(),
            source_url=str(self._pack.url or "").strip(),
            wayback_url=self._pack.wayback_url,
            license_status=provenance_license_status_for_pack(self._pack),
            build_mode=self._pack.build_mode,
            build_command=_build_command_for_mode(self._pack.build_mode),
            converter_version=_converter_version_for_mode(self._pack.build_mode),
            parser_config=_frequency_parser_config(self._pack),
            artifact_path=artifact_path,
            source_filename=self._pack.source_filename or self._pack.filename,
            sqlite_filename=self._pack.sqlite_filename,
            raw_artifact_sha1=self._raw_artifact_sha1 or None,
            raw_artifact_sha256=self._raw_artifact_sha256 or None,
            artifact_metrics=sqlite_artifact_metrics_for_pack(
                pack_kind="frequency",
                artifact_path=artifact_path,
            ),
            **safe_pack_source_identity_fields(self._pack),
            **source_bundle_fields,
        )

    def _convert_to_sqlite(self, archive_path: str) -> str:
        source_path, cleanup_paths = self._prepare_source(archive_path)
        self._capture_raw_artifact_checksums(source_path)
        os.makedirs(os.path.dirname(self._sqlite_path), exist_ok=True)
        try:
            pos_inventory = _frequency_pos_inventory_config(self._pack_id)
            metadata = convert_frequency_to_sqlite(
                Path(source_path),
                Path(self._sqlite_path),
                overwrite=True,
                config=self._pack.parse_config,
                index_column=self._pack.index_column,
                pos_inventory=pos_inventory,
            )
            if pos_inventory is not None:
                _log_download(
                    f"[{self._pack_id}] pos_inventory"
                    f" rows_with_pos={int(metadata.get('rows_with_pos', 0))}"
                    f" rows_without_pos={int(metadata.get('rows_without_pos', 0))}"
                    f" unknown_pos_inventory_size={int(metadata.get('unknown_pos_inventory_size', 0))}"
                )
        finally:
            for path in cleanup_paths:
                self._cleanup_path(path)
        return self._sqlite_path

    def _capture_raw_artifact_checksums(self, path: str | Path) -> None:
        checksums = _file_checksums(path)
        self._raw_artifact_sha1 = checksums.get("sha1", "")
        self._raw_artifact_sha256 = checksums.get("sha256", "")

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
