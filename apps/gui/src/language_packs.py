from __future__ import annotations

import gzip
import os
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path
import ssl
import sys
from datetime import datetime

from PySide6.QtCore import QThread, Signal, QStandardPaths

from lexishift_core.frequency.sqlite import (
    convert_frequency_to_sqlite,
)
from language_packs_catalog import (
    CROSS_EMBEDDING_PACKS,
    EMBEDDING_PACKS,
    FREQUENCY_PACKS,
    LANGUAGE_PACKS,
    FrequencyPackInfo,
    LanguagePackInfo,
    _frequency_pos_inventory_config,
)


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
                _log_download(
                    f"[{self._pack_id}] response status={status} final_url={response.geturl()}"
                )
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
        target_dir = (
            extracted_path if os.path.isdir(extracted_path) else os.path.dirname(extracted_path)
        )
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
            _log_download(
                f"[{self._pack_id}] response status={status} final_url={response.geturl()}"
            )
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
