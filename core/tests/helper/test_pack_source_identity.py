from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.pack_source_identity import (  # noqa: E402
    classify_pack_source_identity,
    safe_pack_source_identity_fields,
    source_bundle_fields_for_pack,
)


class TestPackSourceIdentity(unittest.TestCase):
    def test_safe_source_version_fields_are_exported_for_release_like_rows(self) -> None:
        pack = SimpleNamespace(
            pack_id="freedict-en-es",
            source="FreeDict",
            filename="freedict-eng-spa-2025.11.23.src.tar.xz",
            url="https://download.freedict.org/dictionaries/eng-spa/2025.11.23/"
            "freedict-eng-spa-2025.11.23.src.tar.xz",
            build_mode="freedict_tei_to_sqlite",
        )

        decision = classify_pack_source_identity(pack)

        self.assertEqual(decision.classification, "safe_to_write")
        self.assertEqual(
            safe_pack_source_identity_fields(pack),
            {"source_version": "freedict-eng-spa-2025.11.23"},
        )

    def test_label_only_and_policy_rows_are_not_exported_as_durable_identity(self) -> None:
        label_only_pack = SimpleNamespace(
            pack_id="freq-es-cde",
            source="Corpus del Espanol",
            filename="spanish_lemmas20k.txt",
            url="https://www.wordfrequency.info/files/spanish/spanish_lemmas20k.txt",
            build_mode="convert_archive",
        )
        policy_pack = SimpleNamespace(
            pack_id="wiktionary-en-es",
            source="Kaikki",
            filename="raw-wiktextract-data-en-es.jsonl.gz",
            url="https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
            build_mode="kaikki_translations_to_sqlite",
        )

        self.assertEqual(
            classify_pack_source_identity(label_only_pack).classification, "label_only"
        )
        self.assertEqual(classify_pack_source_identity(policy_pack).classification, "needs_policy")
        self.assertEqual(safe_pack_source_identity_fields(label_only_pack), {})
        self.assertEqual(safe_pack_source_identity_fields(policy_pack), {})

    def test_dated_kaikki_dump_identity_is_safe_but_family_label_is_not(self) -> None:
        dated_pack = SimpleNamespace(
            pack_id="wiktionary-en-es",
            source="Kaikki",
            filename="raw-wiktextract-data-en-es-2026-05-15.jsonl.gz",
            url="https://example.com/kaikki/raw-wiktextract-data-en-es-2026-05-15.jsonl.gz",
            build_mode="kaikki_translations_to_sqlite",
        )
        rolling_pack = SimpleNamespace(
            pack_id="wiktionary-en-es",
            source="Kaikki",
            filename="raw-wiktextract-data-en-es.jsonl.gz",
            url="https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
            build_mode="kaikki_translations_to_sqlite",
        )

        dated_decision = classify_pack_source_identity(dated_pack)
        rolling_decision = classify_pack_source_identity(rolling_pack)

        self.assertEqual(dated_decision.classification, "safe_to_write")
        self.assertEqual(
            safe_pack_source_identity_fields(dated_pack),
            {"source_dump": "enwiktionary:2026-05-15"},
        )
        self.assertEqual(rolling_decision.classification, "needs_policy")
        self.assertEqual(rolling_decision.candidate_value, "enwiktionary")
        self.assertEqual(safe_pack_source_identity_fields(rolling_pack), {})

    def test_invalid_kaikki_date_shape_is_not_safe_to_write(self) -> None:
        pack = SimpleNamespace(
            pack_id="wiktionary-en-es",
            source="Kaikki",
            filename="raw-wiktextract-data-en-es-2026-13-39.jsonl.gz",
            url="https://example.com/kaikki/raw-wiktextract-data-en-es-2026-13-39.jsonl.gz",
            build_mode="kaikki_translations_to_sqlite",
        )

        decision = classify_pack_source_identity(pack)

        self.assertEqual(decision.classification, "needs_policy")
        self.assertEqual(decision.candidate_value, "enwiktionary")
        self.assertEqual(safe_pack_source_identity_fields(pack), {})

    def test_de_frequency_pipeline_exports_source_bundle_fields(self) -> None:
        pack = SimpleNamespace(
            pack_id="freq-de-default",
            source="Leipzig + LanguageTool",
            filename="deu_news_2023_1M.tar.gz",
            url="https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz",
            build_mode="de_frequency_pipeline",
        )

        fields = source_bundle_fields_for_pack(pack)
        bundle = fields["source_bundle"]

        self.assertEqual(bundle["bundle_id"], "freq-de-default:de_frequency_pipeline")
        self.assertEqual(bundle["bundle_kind"], "generated_frequency_pipeline")
        component_roles = {str(item["role"]) for item in bundle["components"]}
        self.assertIn("corpus", component_roles)
        self.assertIn("lexicon_whitelist", component_roles)
        self.assertIn("pos_lexicon_primary", component_roles)
        self.assertIn("pos_tooling", component_roles)

    def test_de_frequency_source_bundle_fields_include_component_checksums(self) -> None:
        pack = SimpleNamespace(
            pack_id="freq-de-default",
            source="Leipzig + LanguageTool",
            filename="deu_news_2023_1M.tar.gz",
            url="https://downloads.wortschatz-leipzig.de/corpora/deu_news_2023_1M.tar.gz",
            build_mode="de_frequency_pipeline",
        )
        with tempfile.TemporaryDirectory() as tmp:
            corpus_path = Path(tmp) / "deu_news_2023_1M.tar.gz"
            corpus_bytes = b"corpus archive bytes"
            corpus_path.write_bytes(corpus_bytes)

            fields = source_bundle_fields_for_pack(
                pack,
                component_paths={
                    "deu_news_2023_1M.tar.gz": corpus_path,
                    "german.dict": Path(tmp) / "missing-german.dict",
                },
            )
            bundle = fields["source_bundle"]

        corpus_component = next(
            item for item in bundle["components"] if item["filename"] == "deu_news_2023_1M.tar.gz"
        )
        missing_component = next(
            item for item in bundle["components"] if item["filename"] == "german.dict"
        )
        self.assertEqual(corpus_component["sha1"], hashlib.sha1(corpus_bytes).hexdigest())
        self.assertEqual(corpus_component["sha256"], hashlib.sha256(corpus_bytes).hexdigest())
        self.assertNotIn("sha1", missing_component)
        self.assertNotIn("sha256", missing_component)


if __name__ == "__main__":
    unittest.main()
