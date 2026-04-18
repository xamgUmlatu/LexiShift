from __future__ import annotations

from dataclasses import dataclass
import errno
import gzip
import json
import re
import socket
import ssl
import tarfile
import urllib.error
import zipfile

PACK_DOWNLOAD_FAILURE_CANCELLED = "cancelled"
PACK_DOWNLOAD_FAILURE_OFFLINE = "offline"
PACK_DOWNLOAD_FAILURE_TIMEOUT = "timeout"
PACK_DOWNLOAD_FAILURE_NOT_FOUND = "not_found"
PACK_DOWNLOAD_FAILURE_BLOCKED = "blocked"
PACK_DOWNLOAD_FAILURE_SOURCE_UNAVAILABLE = "source_unavailable"
PACK_DOWNLOAD_FAILURE_WRITE_FAILED = "write_failed"
PACK_DOWNLOAD_FAILURE_PROCESSING_FAILED = "processing_failed"
PACK_DOWNLOAD_FAILURE_UNKNOWN = "unknown"

_PACK_DOWNLOAD_FAILURE_KINDS = frozenset(
    {
        PACK_DOWNLOAD_FAILURE_CANCELLED,
        PACK_DOWNLOAD_FAILURE_OFFLINE,
        PACK_DOWNLOAD_FAILURE_TIMEOUT,
        PACK_DOWNLOAD_FAILURE_NOT_FOUND,
        PACK_DOWNLOAD_FAILURE_BLOCKED,
        PACK_DOWNLOAD_FAILURE_SOURCE_UNAVAILABLE,
        PACK_DOWNLOAD_FAILURE_WRITE_FAILED,
        PACK_DOWNLOAD_FAILURE_PROCESSING_FAILED,
        PACK_DOWNLOAD_FAILURE_UNKNOWN,
    }
)

_ARCHIVE_MIRROR_FAILURE_KINDS = frozenset(
    {
        PACK_DOWNLOAD_FAILURE_NOT_FOUND,
        PACK_DOWNLOAD_FAILURE_BLOCKED,
        PACK_DOWNLOAD_FAILURE_SOURCE_UNAVAILABLE,
    }
)

_OFFLINE_TEXT_SNIPPETS = (
    "temporary failure in name resolution",
    "name or service not known",
    "nodename nor servname provided",
    "no address associated with hostname",
    "network is unreachable",
    "connection refused",
    "no route to host",
    "failed to establish a new connection",
)
_TIMEOUT_TEXT_SNIPPETS = ("timed out", "timeout")
_BLOCKED_TEXT_SNIPPETS = (
    "certificate_verify_failed",
    "certificate verify failed",
    "tlsv1 alert",
    "handshake failure",
)
_WRITE_FAILURE_TEXT_SNIPPETS = (
    "permission denied",
    "read-only file system",
    "no space left on device",
    "disk full",
)
_PROCESSING_FAILURE_TEXT_SNIPPETS = (
    "no files found in extracted archive",
    "file is not a zip file",
    "not a gzipped file",
    "unexpected end of data",
    "invalid compressed data",
    "truncated",
    "checksum error",
)
_HTTP_ERROR_RE = re.compile(r"http error (\d{3})", re.IGNORECASE)


@dataclass(frozen=True)
class PackDownloadFailure:
    kind: str
    detail: str


def classify_pack_download_failure(error: object) -> PackDownloadFailure:
    if isinstance(error, PackDownloadFailure):
        return error

    detail = _normalize_detail(error)
    lowered = detail.lower()

    if lowered == "cancelled":
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_CANCELLED, detail)

    if isinstance(error, urllib.error.HTTPError):
        return _classify_http_error(error, detail)

    if isinstance(error, urllib.error.URLError):
        reason = getattr(error, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_TIMEOUT, detail)
        if isinstance(reason, socket.gaierror):
            return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_OFFLINE, detail)
        reason_text = str(reason or "").lower()
        if _contains_any(reason_text, _TIMEOUT_TEXT_SNIPPETS):
            return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_TIMEOUT, detail)
        if _contains_any(reason_text, _OFFLINE_TEXT_SNIPPETS):
            return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_OFFLINE, detail)
        if _contains_any(reason_text, _BLOCKED_TEXT_SNIPPETS):
            return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_BLOCKED, detail)
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_SOURCE_UNAVAILABLE, detail)

    if isinstance(error, (TimeoutError, socket.timeout)):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_TIMEOUT, detail)

    if isinstance(error, socket.gaierror):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_OFFLINE, detail)

    if isinstance(error, ssl.SSLError):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_BLOCKED, detail)

    if isinstance(error, PermissionError):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_WRITE_FAILED, detail)

    if isinstance(
        error,
        (
            zipfile.BadZipFile,
            zipfile.LargeZipFile,
            tarfile.TarError,
            gzip.BadGzipFile,
            EOFError,
        ),
    ):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_PROCESSING_FAILED, detail)

    if isinstance(error, OSError) and getattr(error, "errno", None) in {
        errno.EACCES,
        errno.EPERM,
        errno.ENOSPC,
        errno.EROFS,
    }:
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_WRITE_FAILED, detail)

    if _contains_any(lowered, _TIMEOUT_TEXT_SNIPPETS):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_TIMEOUT, detail)
    if _contains_any(lowered, _OFFLINE_TEXT_SNIPPETS):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_OFFLINE, detail)
    if _contains_any(lowered, _BLOCKED_TEXT_SNIPPETS):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_BLOCKED, detail)
    if _contains_any(lowered, _WRITE_FAILURE_TEXT_SNIPPETS):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_WRITE_FAILED, detail)
    if _contains_any(lowered, _PROCESSING_FAILURE_TEXT_SNIPPETS):
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_PROCESSING_FAILED, detail)
    http_status = _http_status_from_detail(detail)
    if http_status is not None:
        return _classify_http_status(http_status, detail)

    return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_UNKNOWN, detail)


def serialize_pack_download_failure(failure: PackDownloadFailure) -> str:
    normalized = classify_pack_download_failure(failure)
    return json.dumps(
        {
            "kind": normalized.kind,
            "detail": normalized.detail,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def encode_pack_download_failure(error: object) -> str:
    return serialize_pack_download_failure(classify_pack_download_failure(error))


def parse_pack_download_failure(message: str) -> PackDownloadFailure:
    payload_text = str(message or "").strip()
    if not payload_text:
        return PackDownloadFailure(PACK_DOWNLOAD_FAILURE_UNKNOWN, "unknown error")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return classify_pack_download_failure(payload_text)
    if not isinstance(payload, dict):
        return classify_pack_download_failure(payload_text)
    kind = str(payload.get("kind") or "").strip().lower()
    detail = _normalize_detail(payload.get("detail"))
    if kind in _PACK_DOWNLOAD_FAILURE_KINDS:
        return PackDownloadFailure(kind, detail)
    return classify_pack_download_failure(detail)


def pack_download_failure_supports_archive_mirror(failure: PackDownloadFailure) -> bool:
    normalized = classify_pack_download_failure(failure)
    return normalized.kind in _ARCHIVE_MIRROR_FAILURE_KINDS


def _classify_http_error(error: urllib.error.HTTPError, detail: str) -> PackDownloadFailure:
    code = int(getattr(error, "code", 0) or 0)
    return _classify_http_status(code, detail)


def _classify_http_status(code: int, detail: str) -> PackDownloadFailure:
    if code in {404, 410}:
        kind = PACK_DOWNLOAD_FAILURE_NOT_FOUND
    elif code in {403, 451}:
        kind = PACK_DOWNLOAD_FAILURE_BLOCKED
    elif code in {408, 504}:
        kind = PACK_DOWNLOAD_FAILURE_TIMEOUT
    elif 400 <= code < 600:
        kind = PACK_DOWNLOAD_FAILURE_SOURCE_UNAVAILABLE
    else:
        kind = PACK_DOWNLOAD_FAILURE_UNKNOWN
    return PackDownloadFailure(kind, detail)


def _normalize_detail(error: object) -> str:
    if isinstance(error, BaseException):
        detail = str(error).strip()
        if detail:
            return detail
        return error.__class__.__name__
    detail = str(error or "").strip()
    return detail or "unknown error"


def _contains_any(text: str, snippets: tuple[str, ...]) -> bool:
    return any(snippet in text for snippet in snippets)


def _http_status_from_detail(detail: str) -> int | None:
    match = _HTTP_ERROR_RE.search(detail)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


__all__ = [
    "PackDownloadFailure",
    "PACK_DOWNLOAD_FAILURE_BLOCKED",
    "PACK_DOWNLOAD_FAILURE_CANCELLED",
    "PACK_DOWNLOAD_FAILURE_NOT_FOUND",
    "PACK_DOWNLOAD_FAILURE_OFFLINE",
    "PACK_DOWNLOAD_FAILURE_PROCESSING_FAILED",
    "PACK_DOWNLOAD_FAILURE_SOURCE_UNAVAILABLE",
    "PACK_DOWNLOAD_FAILURE_TIMEOUT",
    "PACK_DOWNLOAD_FAILURE_UNKNOWN",
    "PACK_DOWNLOAD_FAILURE_WRITE_FAILED",
    "classify_pack_download_failure",
    "encode_pack_download_failure",
    "pack_download_failure_supports_archive_mirror",
    "parse_pack_download_failure",
    "serialize_pack_download_failure",
]
