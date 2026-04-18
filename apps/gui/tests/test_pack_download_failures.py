from __future__ import annotations

import socket
import urllib.error

from pack_download_failures import (
    PACK_DOWNLOAD_FAILURE_NOT_FOUND,
    PACK_DOWNLOAD_FAILURE_OFFLINE,
    PACK_DOWNLOAD_FAILURE_TIMEOUT,
    PACK_DOWNLOAD_FAILURE_WRITE_FAILED,
    classify_pack_download_failure,
    parse_pack_download_failure,
    serialize_pack_download_failure,
)


def test_http_404_failure_classifies_as_not_found() -> None:
    failure = classify_pack_download_failure(
        urllib.error.HTTPError(
            url="https://example.com/missing.zip",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
    )

    assert failure.kind == PACK_DOWNLOAD_FAILURE_NOT_FOUND


def test_dns_lookup_failure_classifies_as_offline() -> None:
    failure = classify_pack_download_failure(
        urllib.error.URLError(socket.gaierror(-2, "Name or service not known"))
    )

    assert failure.kind == PACK_DOWNLOAD_FAILURE_OFFLINE


def test_timeout_failure_classifies_as_timeout() -> None:
    failure = classify_pack_download_failure(urllib.error.URLError(socket.timeout("timed out")))

    assert failure.kind == PACK_DOWNLOAD_FAILURE_TIMEOUT


def test_permission_failure_classifies_as_write_failure() -> None:
    failure = classify_pack_download_failure(PermissionError("Permission denied"))

    assert failure.kind == PACK_DOWNLOAD_FAILURE_WRITE_FAILED


def test_legacy_http_error_text_still_classifies_as_not_found() -> None:
    failure = parse_pack_download_failure("HTTP Error 404: Not Found")

    assert failure.kind == PACK_DOWNLOAD_FAILURE_NOT_FOUND


def test_serialized_failure_round_trips() -> None:
    encoded = serialize_pack_download_failure(
        classify_pack_download_failure(urllib.error.URLError(socket.timeout("timed out")))
    )

    failure = parse_pack_download_failure(encoded)

    assert failure.kind == PACK_DOWNLOAD_FAILURE_TIMEOUT
    assert "timed out" in failure.detail
