from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
CORE_ROOT = REPO_ROOT / "core"
for candidate in (GUI_SRC, CORE_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from language_packs import FrequencyPackDownloadThread, LanguagePackDownloadThread  # noqa: E402
from language_packs_catalog import FrequencyPackInfo, LanguagePackInfo  # noqa: E402
from lexishift_core.helper.pack_provenance import PACK_PROVENANCE_FILENAME  # noqa: E402
from lexishift_core.helper.pack_provenance import validate_pack_provenance_file  # noqa: E402
from settings_language_packs_transfer_mixin import LanguagePackPanelTransferMixin  # noqa: E402


def test_language_pack_manifest_write_creates_provenance_sidecar() -> None:
    with TemporaryDirectory() as temp_dir:
        pack_root = Path(temp_dir) / "language_packs" / "freedict-en-es"
        artifact = pack_root / "main.sqlite"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"SQLite format 3\x00")
        pack = LanguagePackInfo(
            pack_id="freedict-en-es",
            name="FreeDict EN-ES",
            language="English to Spanish",
            source="FreeDict",
            size="1 MB",
            url="https://example.com/freedict-eng-spa.src.tar.xz",
            wayback_url="https://web.archive.org/web/*/https://example.com/freedict-eng-spa.src.tar.xz",
            filename="freedict-eng-spa.src.tar.xz",
            local_kind="file",
            sqlite_filename="main.sqlite",
            build_mode="freedict_tei_to_sqlite",
        )

        thread = LanguagePackDownloadThread(pack, str(artifact))
        thread._write_manifest(str(artifact))
        provenance_path = pack_root / PACK_PROVENANCE_FILENAME
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        assert validate_pack_provenance_file(provenance_path) == ()
        assert payload["pack_id"] == "freedict-en-es"
        assert payload["pack_kind"] == "language"
        assert payload["source"]["license_status"] == "requires_review"
        assert payload["artifact"]["artifact_relpath"] == "main.sqlite"


def test_frequency_pack_manifest_write_creates_provenance_sidecar() -> None:
    with TemporaryDirectory() as temp_dir:
        pack_root = Path(temp_dir) / "frequency_packs" / "freq-es-cde"
        artifact = pack_root / "main.sqlite"
        archive = pack_root / "spanish_lemmas20k.txt"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"SQLite format 3\x00")
        pack = FrequencyPackInfo(
            pack_id="freq-es-cde",
            name="Corpus del Espanol Frequency",
            language="Spanish",
            source="Corpus del Espanol",
            size="42 KB",
            url="https://example.com/spanish_lemmas20k.txt",
            wayback_url="https://web.archive.org/web/*/https://example.com/spanish_lemmas20k.txt",
            filename="spanish_lemmas20k.txt",
            sqlite_filename="main.sqlite",
        )

        thread = FrequencyPackDownloadThread(pack, str(archive), str(artifact))
        thread._write_manifest(str(artifact))
        provenance_path = pack_root / PACK_PROVENANCE_FILENAME
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        assert validate_pack_provenance_file(provenance_path) == ()
        assert payload["pack_id"] == "freq-es-cde"
        assert payload["pack_kind"] == "frequency"
        assert payload["source"]["license_status"] == "requires_review"
        assert payload["artifact"]["artifact_kind"] == "sqlite"


def test_embedding_finalize_creates_provenance_sidecar() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_id = "embed-xling-es"
        artifact = root / "embedding_packs" / pack_id / "main.sqlite"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"SQLite format 3\x00")
        pack = LanguagePackInfo(
            pack_id=pack_id,
            name="fastText Spanish Aligned",
            language="Spanish aligned",
            source="fastText",
            size="2 GB",
            url="https://example.com/wiki.es.align.vec",
            wayback_url="https://web.archive.org/web/*/https://example.com/wiki.es.align.vec",
            filename="wiki.es.align.vec",
            local_kind="file",
            pair_key="en-es",
        )
        dummy = _DummyTransferPanel(root=root, pack_id=pack_id, pack=pack)

        LanguagePackPanelTransferMixin._finalize_embedding_pack(
            dummy,
            pack_id=pack_id,
            resolved_path=str(artifact),
        )
        provenance_path = artifact.parent / PACK_PROVENANCE_FILENAME
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        assert validate_pack_provenance_file(provenance_path) == ()
        assert payload["pack_id"] == pack_id
        assert payload["pack_kind"] == "embedding"
        assert payload["source"]["license_status"] == "requires_review"
        assert payload["artifact"]["artifact_relpath"] == "main.sqlite"


class _TextCell:
    def setText(self, value: str) -> None:
        self.text = value

    def setToolTip(self, value: str) -> None:
        self.tooltip = value


class _Button:
    def setEnabled(self, value: bool) -> None:
        self.enabled = value

    def setText(self, value: str) -> None:
        self.text = value


class _DummyTransferPanel(LanguagePackPanelTransferMixin):
    def __init__(self, *, root: Path, pack_id: str, pack: LanguagePackInfo) -> None:
        self._embedding_pack_dir = str(root / "embedding_packs")
        self._embedding_pack_paths: dict[str, str] = {}
        self._embedding_pack_info = {pack_id: pack}
        self._row = SimpleNamespace(
            status_item=_TextCell(),
            download_button=_Button(),
            use_button=_Button(),
        )

    def _embedding_row_for(self, pack_id: str):
        return self._row

    def _is_sqlite_db(self, path: str) -> bool:
        return path.endswith(".sqlite")

    def _is_app_data_path(self, path: str, *, embeddings: bool = False) -> bool:
        return embeddings and str(path).startswith(self._embedding_pack_dir)

    def _embedding_pack_pair_key(self, pack_id: str) -> str | None:
        return "en-es"

    def _is_installed_embedding_pack_entry(self, pack_id: str, path: str) -> bool:
        return True

    def _set_status_item_tone(self, *args, **kwargs) -> None:
        pass

    def _set_status_message(self, *args, **kwargs) -> None:
        pass

    def _refresh_embedding_pack_table(self) -> None:
        pass

    def _refresh_cross_embedding_pack_table(self) -> None:
        pass
