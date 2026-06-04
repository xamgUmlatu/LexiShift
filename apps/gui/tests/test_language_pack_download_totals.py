from __future__ import annotations

from types import SimpleNamespace

from language_packs import _response_download_total_bytes  # noqa: PLC2701
from language_packs_catalog import CROSS_EMBEDDING_PACKS, FREQUENCY_PACKS, LANGUAGE_PACKS


class _Response:
    def __init__(self, content_length: str | None) -> None:
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = content_length


def test_response_download_total_prefers_content_length() -> None:
    pack = SimpleNamespace(download_size_bytes=42_922)

    total = _response_download_total_bytes(_Response("121624"), pack)

    assert total == 121_624


def test_response_download_total_falls_back_to_catalog_size() -> None:
    pack = SimpleNamespace(download_size_bytes=42_922)

    total = _response_download_total_bytes(_Response(None), pack)

    assert total == 42_922


def test_known_catalog_totals_cover_large_spanish_resource_downloads() -> None:
    packs = {
        pack.pack_id: pack for pack in (*LANGUAGE_PACKS, *CROSS_EMBEDDING_PACKS, *FREQUENCY_PACKS)
    }

    assert packs["wiktionary-es-en"].download_size_bytes == 2_665_722_104
    assert packs["freedict-es-en"].download_size_bytes == 121_624
    assert packs["embed-xling-es"].download_size_bytes == 2_227_283_009
    assert packs["freq-es-cde"].download_size_bytes == 42_922
