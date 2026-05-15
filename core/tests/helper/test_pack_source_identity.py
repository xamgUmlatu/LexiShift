from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.pack_source_identity import (  # noqa: E402
    classify_pack_source_identity,
    safe_pack_source_identity_fields,
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


if __name__ == "__main__":
    unittest.main()
