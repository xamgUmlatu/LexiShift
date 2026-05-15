from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[3]
GUI_SRC = REPO_ROOT / "apps" / "gui" / "src"
CORE_ROOT = REPO_ROOT / "core"
for candidate in (GUI_SRC, CORE_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from language_packs import (  # noqa: E402
    FrequencyPackDownloadThread,
    LanguagePackDownloadThread,
    _converter_version_for_mode,
    _file_checksums,
)
from language_packs_catalog import FrequencyPackInfo, LanguagePackInfo  # noqa: E402
from lexishift_core.frequency.sqlite import ParseConfig  # noqa: E402
from lexishift_core.helper.pack_provenance import PACK_PROVENANCE_FILENAME  # noqa: E402
from lexishift_core.helper.pack_provenance import validate_pack_provenance_file  # noqa: E402
from lexishift_core.helper.pack_source_identity import source_bundle_fields_for_pack  # noqa: E402
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
            url="https://example.com/freedict-eng-spa-2025.11.23.src.tar.xz",
            wayback_url="https://web.archive.org/web/*/https://example.com/"
            "freedict-eng-spa-2025.11.23.src.tar.xz",
            filename="freedict-eng-spa-2025.11.23.src.tar.xz",
            local_kind="file",
            required_files=("eng-spa.tei",),
            sqlite_filename="main.sqlite",
            build_mode="freedict_tei_to_sqlite",
            target_lang_code="es",
        )

        thread = LanguagePackDownloadThread(pack, str(artifact))
        thread._write_manifest(str(artifact))
        provenance_path = pack_root / PACK_PROVENANCE_FILENAME
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        assert validate_pack_provenance_file(provenance_path) == ()
        assert payload["pack_id"] == "freedict-en-es"
        assert payload["pack_kind"] == "language"
        assert payload["source"]["license_status"] == "requires_review"
        assert payload["source"]["source_version"] == "freedict-eng-spa-2025.11.23"
        assert payload["build"]["command"] == "convert_freedict_tei_to_sqlite"
        assert payload["build"]["converter_version"] == _converter_version_for_mode(
            "freedict_tei_to_sqlite"
        )
        assert payload["build"]["parser_config"]["tei_filename"] == "eng-spa.tei"
        assert payload["artifact"]["artifact_relpath"] == "main.sqlite"


def test_file_checksums_records_sha1_and_sha256() -> None:
    with TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / "source.txt"
        source_bytes = b"source artifact bytes"
        source.write_bytes(source_bytes)

        checksums = _file_checksums(source)

        assert checksums == {
            "sha1": hashlib.sha1(source_bytes).hexdigest(),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
        }


def test_language_pack_manifest_write_includes_raw_artifact_checksums() -> None:
    with TemporaryDirectory() as temp_dir:
        pack_root = Path(temp_dir) / "language_packs" / "freedict-en-es"
        artifact = pack_root / "main.sqlite"
        raw_source = pack_root / "freedict-eng-spa.src.tar.xz"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"SQLite format 3\x00")
        raw_bytes = b"freedict source archive"
        raw_source.write_bytes(raw_bytes)
        pack = LanguagePackInfo(
            pack_id="freedict-en-es",
            name="FreeDict EN-ES",
            language="English to Spanish",
            source="FreeDict",
            size="1 MB",
            url="https://example.com/freedict-eng-spa-2025.11.23.src.tar.xz",
            wayback_url="https://web.archive.org/web/*/https://example.com/"
            "freedict-eng-spa-2025.11.23.src.tar.xz",
            filename="freedict-eng-spa-2025.11.23.src.tar.xz",
            local_kind="file",
            required_files=("eng-spa.tei",),
            sqlite_filename="main.sqlite",
            build_mode="freedict_tei_to_sqlite",
            target_lang_code="es",
        )

        thread = LanguagePackDownloadThread(pack, str(raw_source))
        thread._capture_raw_artifact_checksums(raw_source)
        thread._write_manifest(str(artifact))
        payload = json.loads((pack_root / PACK_PROVENANCE_FILENAME).read_text(encoding="utf-8"))
        raw_artifact = payload["source"]["raw_artifacts"][0]

        assert payload["source"]["source_version"] == "freedict-eng-spa-2025.11.23"
        assert raw_artifact["filename"] == "freedict-eng-spa-2025.11.23.src.tar.xz"
        assert raw_artifact["sha1"] == hashlib.sha1(raw_bytes).hexdigest()
        assert raw_artifact["sha256"] == hashlib.sha256(raw_bytes).hexdigest()
        assert validate_pack_provenance_file(pack_root / PACK_PROVENANCE_FILENAME) == ()


def test_kaikki_language_pack_manifest_write_includes_explicit_dated_source_dump() -> None:
    with TemporaryDirectory() as temp_dir:
        pack_root = Path(temp_dir) / "language_packs" / "wiktionary-en-es"
        artifact = pack_root / "main.sqlite"
        raw_source = pack_root / "raw-wiktextract-data.jsonl.gz"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"SQLite format 3\x00")
        raw_source.write_bytes(b"wiktextract source")
        pack = LanguagePackInfo(
            pack_id="wiktionary-en-es",
            name="Wiktionary EN-ES",
            language="English to Spanish",
            source="Kaikki",
            size="1 MB",
            url="https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
            wayback_url="https://web.archive.org/web/*/https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
            filename="raw-wiktextract-data.jsonl.gz",
            local_kind="file",
            sqlite_filename="main.sqlite",
            source_dump="enwiktionary:2026-05-15",
            build_mode="kaikki_translations_to_sqlite",
            source_lang_code="en",
            target_lang_code="es",
        )

        thread = LanguagePackDownloadThread(pack, str(raw_source))
        thread._capture_raw_artifact_checksums(raw_source)
        thread._write_manifest(str(artifact))
        payload = json.loads((pack_root / PACK_PROVENANCE_FILENAME).read_text(encoding="utf-8"))

        assert validate_pack_provenance_file(pack_root / PACK_PROVENANCE_FILENAME) == ()
        assert payload["source"]["source_dump"] == "enwiktionary:2026-05-15"
        assert payload["build"]["parser_config"]["source_dump"] == "enwiktionary:2026-05-15"


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
            parse_config=ParseConfig(
                delimiter="\t",
                header_starts_with="ID",
                skip_prefixes=("----",),
                encoding="latin-1",
            ),
        )

        thread = FrequencyPackDownloadThread(pack, str(archive), str(artifact))
        thread._write_manifest(str(artifact))
        provenance_path = pack_root / PACK_PROVENANCE_FILENAME
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))

        assert validate_pack_provenance_file(provenance_path) == ()
        assert payload["pack_id"] == "freq-es-cde"
        assert payload["pack_kind"] == "frequency"
        assert payload["source"]["license_status"] == "requires_review"
        assert "source_version" not in payload["source"]
        assert "source_dump" not in payload["source"]
        assert payload["build"]["command"] == "convert_frequency_to_sqlite"
        assert payload["build"]["converter_version"] == _converter_version_for_mode(
            "convert_archive"
        )
        assert payload["build"]["parser_config"]["header_starts_with"] == "ID"
        assert payload["build"]["parser_config"]["encoding"] == "latin-1"
        assert payload["artifact"]["artifact_kind"] == "sqlite"


def test_frequency_convert_to_sqlite_captures_parsed_source_checksums() -> None:
    with TemporaryDirectory() as temp_dir:
        pack_root = Path(temp_dir) / "frequency_packs" / "freq-es-cde"
        artifact = pack_root / "main.sqlite"
        source = pack_root / "spanish_lemmas20k.txt"
        source.parent.mkdir(parents=True)
        source_text = "ID\tlemma\tfreq\tpos\n1\tgato\t100\tn\n"
        source_bytes = source_text.encode("latin-1")
        source.write_bytes(source_bytes)
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
            parse_config=ParseConfig(
                delimiter="\t",
                header_starts_with="ID",
                skip_prefixes=("----",),
                encoding="latin-1",
            ),
        )

        thread = FrequencyPackDownloadThread(pack, str(source), str(artifact))
        sqlite_path = thread._convert_to_sqlite(str(source))
        thread._write_manifest(sqlite_path)
        payload = json.loads((pack_root / PACK_PROVENANCE_FILENAME).read_text(encoding="utf-8"))
        raw_artifact = payload["source"]["raw_artifacts"][0]

        assert raw_artifact["filename"] == "spanish_lemmas20k.txt"
        assert "source_version" not in payload["source"]
        assert "source_dump" not in payload["source"]
        assert raw_artifact["sha1"] == hashlib.sha1(source_bytes).hexdigest()
        assert raw_artifact["sha256"] == hashlib.sha256(source_bytes).hexdigest()
        assert payload["artifact"]["metrics"] == {
            "row_count": 1,
            "distinct_lemma_count": 1,
            "pos_rows": 1,
            "topic_domain_rows": 0,
        }
        assert validate_pack_provenance_file(pack_root / PACK_PROVENANCE_FILENAME) == ()


def test_de_frequency_pack_manifest_write_includes_source_bundle() -> None:
    with TemporaryDirectory() as temp_dir:
        pack_root = Path(temp_dir) / "frequency_packs" / "freq-de-default"
        artifact = pack_root / "main.sqlite"
        archive = pack_root / "deu_news_2023_1M.tar.gz"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"SQLite format 3\x00")
        archive_bytes = b"de frequency corpus archive"
        archive.write_bytes(archive_bytes)
        pack = FrequencyPackInfo(
            pack_id="freq-de-default",
            name="German News Frequency",
            language="German",
            source="Leipzig + LanguageTool",
            size="80 MB",
            url="https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz",
            wayback_url="https://web.archive.org/web/*/https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz",
            filename="deu_news_2023_1M.tar.gz",
            sqlite_filename="main.sqlite",
            build_mode="de_frequency_pipeline",
        )

        thread = FrequencyPackDownloadThread(pack, str(archive), str(artifact))
        thread._source_bundle_fields = source_bundle_fields_for_pack(
            pack,
            component_paths={archive.name: archive},
        )
        thread._write_manifest(str(artifact))
        provenance_path = pack_root / PACK_PROVENANCE_FILENAME
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
        bundle = payload["source"]["source_bundle"]
        corpus_component = next(
            item for item in bundle["components"] if item["filename"] == archive.name
        )

        assert validate_pack_provenance_file(provenance_path) == ()
        assert bundle["bundle_id"] == "freq-de-default:de_frequency_pipeline"
        assert bundle["bundle_kind"] == "generated_frequency_pipeline"
        assert len(bundle["components"]) >= 8
        assert corpus_component["sha1"] == hashlib.sha1(archive_bytes).hexdigest()
        assert corpus_component["sha256"] == hashlib.sha256(archive_bytes).hexdigest()
        assert "source_version" not in payload["source"]
        assert "source_dump" not in payload["source"]


def test_de_frequency_build_captures_source_bundle_component_checksums() -> None:
    with TemporaryDirectory() as temp_dir:
        pack_root = Path(temp_dir) / "frequency_packs" / "freq-de-default"
        artifact = pack_root / "main.sqlite"
        archive = pack_root / "deu_news_2023_1M.tar.gz"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"SQLite format 3\x00")
        archive_bytes = b"de frequency corpus archive"
        archive.write_bytes(archive_bytes)
        pack = FrequencyPackInfo(
            pack_id="freq-de-default",
            name="German News Frequency",
            language="German",
            source="Leipzig + LanguageTool",
            size="80 MB",
            url="https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz",
            wayback_url="https://web.archive.org/web/*/https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz",
            filename="deu_news_2023_1M.tar.gz",
            sqlite_filename="main.sqlite",
            build_mode="de_frequency_pipeline",
        )
        thread = FrequencyPackDownloadThread(pack, str(archive), str(artifact))
        thread._language_packs_dir = lambda: Path(temp_dir) / "language_packs"

        def _fake_pipeline(**kwargs):
            kwargs["source_bundle_component_paths_cb"]({archive.name: archive})
            return SimpleNamespace(output_path=artifact)

        with patch(
            "lexishift_core.frequency.de.pipeline.run_de_frequency_pipeline",
            side_effect=_fake_pipeline,
        ):
            sqlite_path = thread._build_de_pipeline()
        bundle = thread._source_bundle_fields["source_bundle"]
        corpus_component = next(
            item for item in bundle["components"] if item["filename"] == archive.name
        )

    assert sqlite_path == str(artifact)
    assert corpus_component["sha1"] == hashlib.sha1(archive_bytes).hexdigest()
    assert corpus_component["sha256"] == hashlib.sha256(archive_bytes).hexdigest()


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
        assert "source_version" not in payload["source"]
        assert "source_dump" not in payload["source"]
        assert payload["build"]["command"] == "scripts/data/convert_embeddings.py"
        assert payload["build"]["converter_version"] == _converter_version_for_mode(
            "convert_to_sqlite"
        )
        assert payload["artifact"]["artifact_relpath"] == "main.sqlite"


def test_embedding_finalize_captures_prior_raw_vector_checksums() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        pack_id = "embed-xling-es"
        pack_root = root / "embedding_packs" / pack_id
        artifact = pack_root / "main.sqlite"
        raw_vector = pack_root / "wiki.es.align.vec"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"SQLite format 3\x00")
        raw_bytes = b"hola 0.1 0.2\n"
        raw_vector.write_bytes(raw_bytes)
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
        dummy._embedding_pack_paths[pack_id] = str(raw_vector)

        LanguagePackPanelTransferMixin._finalize_embedding_pack(
            dummy,
            pack_id=pack_id,
            resolved_path=str(artifact),
        )
        payload = json.loads((pack_root / PACK_PROVENANCE_FILENAME).read_text(encoding="utf-8"))
        raw_artifact = payload["source"]["raw_artifacts"][0]

        assert validate_pack_provenance_file(pack_root / PACK_PROVENANCE_FILENAME) == ()
        assert raw_artifact["filename"] == "wiki.es.align.vec"
        assert raw_artifact["sha1"] == hashlib.sha1(raw_bytes).hexdigest()
        assert raw_artifact["sha256"] == hashlib.sha256(raw_bytes).hexdigest()
        assert not raw_vector.exists()


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

    def _remove_path(self, path: str) -> None:
        Path(path).unlink(missing_ok=True)
