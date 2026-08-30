from __future__ import annotations

import hashlib
import inspect
import os
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from language_packs_catalog import (
    FrequencyPackInfo,
    LanguagePackInfo,
    _frequency_pos_inventory_config,
)
from lexishift_core.frequency.sqlite import convert_frequency_to_sqlite
from lexishift_core.pos.ud_ancora import build_ud_ancora_pos_overlay
from lexishift_core.resources.freedict_sqlite import convert_freedict_tei_to_sqlite
from lexishift_core.resources.kaikki_sqlite import convert_kaikki_glosses_to_sqlite
from lexishift_core.resources.kaikki_sqlite import convert_kaikki_translations_to_sqlite

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
