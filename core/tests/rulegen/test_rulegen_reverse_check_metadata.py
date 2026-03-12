from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.pairs.en_es import (  # noqa: E402
    EnEsRulegenConfig,
    generate_en_es_results,
)
from lexishift_core.rulegen.pairs.es_en import (  # noqa: E402
    EsEnRulegenConfig,
    generate_es_en_results,
)


def _build_tei_entry(headword: str, quotes: list[tuple[str, str]]) -> str:
    quote_xml = "".join(
        f'<cit type="trans"><quote xml:lang="{lang}">{text}</quote></cit>' for lang, text in quotes
    )
    return f"<entry><form><orth>{headword}</orth></form><sense>{quote_xml}</sense></entry>"


def _build_tei(entries: list[str]) -> str:
    body = "".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<text><body>"
        f"{body}"
        "</body></text>"
        "</TEI>"
    )


class TestRulegenReverseCheckMetadata(unittest.TestCase):
    def test_en_es_emits_reverse_check_metadata_when_reverse_dictionary_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            forward_path = tmp_path / "spa-eng.tei"
            reverse_path = tmp_path / "eng-spa.tei"
            forward_path.write_text(
                _build_tei(
                    [
                        _build_tei_entry(
                            "casa",
                            [("en", "house"), ("en", "home")],
                        )
                    ]
                ),
                encoding="utf-8",
            )
            reverse_path.write_text(
                _build_tei(
                    [
                        _build_tei_entry(
                            "house",
                            [("es", "casa"), ("es", "hogar")],
                        ),
                        _build_tei_entry(
                            "home",
                            [("es", "casa")],
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            results = generate_en_es_results(
                ["casa"],
                config=EnEsRulegenConfig(
                    freedict_es_en_path=forward_path,
                    reverse_freedict_en_es_path=reverse_path,
                    include_variants=False,
                ),
            )

        by_source = {result.candidate.source_phrase: result for result in results}
        self.assertIn("house", by_source)
        metadata = by_source["house"].candidate.metadata
        self.assertTrue(bool(metadata.get("reverse_check_supported")))
        self.assertTrue(bool(metadata.get("reverse_check_hit")))
        self.assertEqual(metadata.get("reverse_check_rank"), 0)
        self.assertEqual(metadata.get("reverse_check_source_dict"), "freedict_en_es")
        self.assertEqual(metadata.get("reverse_check_target_norm"), "casa")
        self.assertEqual(metadata.get("reverse_check_source_norm"), "house")

    def test_en_es_marks_reverse_check_unsupported_without_reverse_dictionary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            forward_path = tmp_path / "spa-eng.tei"
            forward_path.write_text(
                _build_tei(
                    [
                        _build_tei_entry(
                            "casa",
                            [("en", "house")],
                        )
                    ]
                ),
                encoding="utf-8",
            )

            results = generate_en_es_results(
                ["casa"],
                config=EnEsRulegenConfig(
                    freedict_es_en_path=forward_path,
                    include_variants=False,
                ),
            )

        self.assertEqual(len(results), 1)
        metadata = results[0].candidate.metadata
        self.assertFalse(bool(metadata.get("reverse_check_supported")))
        self.assertFalse(bool(metadata.get("reverse_check_hit")))
        self.assertIsNone(metadata.get("reverse_check_rank"))

    def test_es_en_emits_reverse_check_metadata_when_reverse_dictionary_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            forward_path = tmp_path / "eng-spa.tei"
            reverse_path = tmp_path / "spa-eng.tei"
            forward_path.write_text(
                _build_tei(
                    [
                        _build_tei_entry(
                            "house",
                            [("es", "casa")],
                        )
                    ]
                ),
                encoding="utf-8",
            )
            reverse_path.write_text(
                _build_tei(
                    [
                        _build_tei_entry(
                            "casa",
                            [("en", "house"), ("en", "home")],
                        )
                    ]
                ),
                encoding="utf-8",
            )

            results = generate_es_en_results(
                ["house"],
                config=EsEnRulegenConfig(
                    freedict_en_es_path=forward_path,
                    reverse_freedict_es_en_path=reverse_path,
                ),
            )

        self.assertEqual(len(results), 1)
        metadata = results[0].candidate.metadata
        self.assertTrue(bool(metadata.get("reverse_check_supported")))
        self.assertTrue(bool(metadata.get("reverse_check_hit")))
        self.assertEqual(metadata.get("reverse_check_rank"), 0)
        self.assertEqual(metadata.get("reverse_check_source_dict"), "freedict_es_en")
        self.assertEqual(metadata.get("reverse_check_target_norm"), "house")
        self.assertEqual(metadata.get("reverse_check_source_norm"), "casa")


if __name__ == "__main__":
    unittest.main()
