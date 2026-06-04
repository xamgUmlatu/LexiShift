from __future__ import annotations

import gzip
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.resources.dict_loaders import load_freedict_sqlite_gloss_records_ordered  # noqa: E402
from lexishift_core.resources.kaikki_sqlite import (  # noqa: E402
    convert_kaikki_glosses_to_sqlite,
    convert_kaikki_translations_to_sqlite,
)


class TestKaikkiSqliteConversion(unittest.TestCase):
    def test_converter_supports_german_to_english_gloss_exports(self) -> None:
        records = [
            {
                "word": "Haus",
                "lang": "German",
                "lang_code": "de",
                "pos": "noun",
                "forms": [{"form": "Häuser", "tags": ["plural"]}],
                "senses": [
                    {
                        "glosses": ["house", "building"],
                        "raw_glosses": ["house", "building"],
                        "topics": ["architecture"],
                    }
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "raw-wiktextract-data-de-en.jsonl.gz"
            output_path = Path(tmp) / "wiktionary-de-en.sqlite"
            with gzip.open(input_path, "wt", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            metadata = convert_kaikki_glosses_to_sqlite(
                input_path,
                output_path,
                source_lang_code="de",
                gloss_language="en",
                source_provider="wiktionary-de-en",
                source_dump="enwiktionary",
                overwrite=True,
            )
            records_by_headword = load_freedict_sqlite_gloss_records_ordered(output_path)
            self.assertEqual(metadata["selected_records"], 1)
            self.assertEqual(metadata["inserted_sense_rows"], 2)
            self.assertIn("Haus", records_by_headword)
            self.assertEqual(
                [entry.translation for entry in records_by_headword["Haus"]],
                ["house", "building"],
            )
            self.assertEqual(records_by_headword["Haus"][0].pos_raw, "noun")

    def test_converter_emits_compatibility_entries_and_preserves_metadata(self) -> None:
        records = [
            {
                "word": "casa",
                "lang": "Spanish",
                "lang_code": "es",
                "pos": "noun",
                "forms": [{"form": "casas", "tags": ["plural"]}],
                "synonyms": [{"word": "hogar"}],
                "sounds": [{"ipa": "ˈkasa"}],
                "senses": [
                    {
                        "glosses": ["house", "home"],
                        "raw_glosses": ["house", "home"],
                        "topics": ["architecture"],
                    }
                ],
            },
            {
                "word": "casa",
                "lang": "Spanish",
                "lang_code": "es",
                "pos": "verb",
                "senses": [
                    {
                        "glosses": ["inflection of casar"],
                        "tags": ["form-of"],
                    }
                ],
            },
            {
                "word": "movimiento",
                "lang": "Spanish",
                "lang_code": "es",
                "pos": "noun",
                "senses": [
                    {"glosses": ["movement"], "topics": ["physics"]},
                    {"glosses": ["movement"], "topics": ["music"]},
                ],
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "raw-wiktextract-data.jsonl.gz"
            output_path = Path(tmp) / "wiktionary-es-en.sqlite"
            with gzip.open(input_path, "wt", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            metadata = convert_kaikki_glosses_to_sqlite(
                input_path,
                output_path,
                source_lang_code="es",
                gloss_language="en",
                source_provider="wiktionary-es-en",
                source_dump="enwiktionary",
                overwrite=True,
            )
            records_by_headword = load_freedict_sqlite_gloss_records_ordered(output_path)
            self.assertEqual(metadata["selected_records"], 2)
            self.assertEqual(metadata["inserted_entry_meta"], 2)
            self.assertEqual(metadata["inserted_sense_rows"], 4)
            self.assertIn("casa", records_by_headword)
            self.assertEqual(
                [entry.translation for entry in records_by_headword["casa"]],
                ["house", "home"],
            )
            self.assertEqual(records_by_headword["casa"][0].pos_raw, "noun")
            self.assertIn("movimiento", records_by_headword)
            self.assertEqual(
                [entry.translation for entry in records_by_headword["movimiento"]],
                ["movement"],
            )
            self.assertEqual(records_by_headword["movimiento"][0].pos_raw, "noun")
            with sqlite3.connect(output_path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                self.assertTrue({"meta", "entry_meta", "sense_glosses", "entries"}.issubset(tables))
                row = conn.execute(
                    "SELECT forms_json, synonyms_json, sounds_json FROM entry_meta "
                    "WHERE headword_lc = 'casa' LIMIT 1"
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertIn("casas", row[0] or "")
                self.assertIn("hogar", row[1] or "")
                self.assertIn("ipa", row[2] or "")

    def test_converter_preserves_kaikki_sense_order_in_runtime_entries(self) -> None:
        records = [
            {
                "word": "agua",
                "lang": "Spanish",
                "lang_code": "es",
                "pos": "noun",
                "senses": [
                    {"glosses": ["water"]},
                    {"glosses": ["body of water"]},
                    {"glosses": ["infusion"]},
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "raw-wiktextract-data.jsonl.gz"
            output_path = Path(tmp) / "wiktionary-es-en.sqlite"
            with gzip.open(input_path, "wt", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            convert_kaikki_glosses_to_sqlite(
                input_path,
                output_path,
                source_lang_code="es",
                gloss_language="en",
                source_provider="wiktionary-es-en",
                source_dump="enwiktionary",
                overwrite=True,
            )
            records_by_headword = load_freedict_sqlite_gloss_records_ordered(output_path)
            self.assertEqual(
                [entry.translation for entry in records_by_headword["agua"]],
                ["water", "body of water", "infusion"],
            )

    def test_loader_hydrates_kaikki_auxiliary_metadata_for_runtime_consumers(self) -> None:
        records = [
            {
                "word": "ese",
                "lang": "Spanish",
                "lang_code": "es",
                "pos": "det",
                "pos_title": "determiner",
                "tags": ["demonstrative"],
                "categories": ["Spanish determiners"],
                "senses": [
                    {
                        "glosses": ["that"],
                        "examples": [
                            {
                                "text": "Ese libro es mío.",
                                "translation": "That book is mine.",
                            }
                        ],
                        "tags": ["masculine", "singular"],
                        "topics": ["grammar"],
                        "categories": ["Spanish demonstratives"],
                    }
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "raw-wiktextract-data.jsonl.gz"
            output_path = Path(tmp) / "wiktionary-es-en.sqlite"
            with gzip.open(input_path, "wt", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            convert_kaikki_glosses_to_sqlite(
                input_path,
                output_path,
                source_lang_code="es",
                gloss_language="en",
                source_provider="wiktionary-es-en",
                source_dump="enwiktionary",
                overwrite=True,
            )
            records_by_headword = load_freedict_sqlite_gloss_records_ordered(output_path)
            self.assertEqual([entry.translation for entry in records_by_headword["ese"]], ["that"])
            metadata = records_by_headword["ese"][0].metadata
            self.assertEqual(metadata["entry_pos_title"], "determiner")
            self.assertEqual(metadata["entry_tags"], ["demonstrative"])
            self.assertEqual(metadata["entry_categories"], ["Spanish determiners"])
            self.assertEqual(
                metadata["sense_examples"],
                [
                    {
                        "text": "Ese libro es mío.",
                        "translation": "That book is mine.",
                    }
                ],
            )
            self.assertEqual(metadata["sense_tags"], ["masculine", "singular"])
            self.assertEqual(metadata["sense_topics"], ["grammar"])
            self.assertEqual(metadata["sense_categories"], ["Spanish demonstratives"])

    def test_converter_persists_kaikki_sense_examples_in_auxiliary_metadata(self) -> None:
        records = [
            {
                "word": "captar",
                "lang": "Spanish",
                "lang_code": "es",
                "pos": "verb",
                "senses": [
                    {
                        "glosses": ["to perceive"],
                        "examples": [
                            {
                                "text": "No logro captar la señal.",
                                "translation": "I can't pick up the signal.",
                            },
                            "Capta el mensaje al instante.",
                        ],
                    }
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "raw-wiktextract-data.jsonl.gz"
            output_path = Path(tmp) / "wiktionary-es-en.sqlite"
            with gzip.open(input_path, "wt", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            convert_kaikki_glosses_to_sqlite(
                input_path,
                output_path,
                source_lang_code="es",
                gloss_language="en",
                source_provider="wiktionary-es-en",
                source_dump="enwiktionary",
                overwrite=True,
            )
            records_by_headword = load_freedict_sqlite_gloss_records_ordered(output_path)
            metadata = records_by_headword["captar"][0].metadata
            self.assertEqual(
                metadata["sense_examples"],
                [
                    {
                        "text": "No logro captar la señal.",
                        "translation": "I can't pick up the signal.",
                    },
                    "Capta el mensaje al instante.",
                ],
            )
            with sqlite3.connect(output_path) as conn:
                row = conn.execute(
                    "SELECT examples_json FROM sense_glosses "
                    "WHERE headword_lc = 'captar' AND sense_ord = 0 AND gloss_ord = 0"
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertIn("No logro captar la señal.", row[0] or "")

    def test_translation_converter_emits_reverse_compatibility_entries_and_metadata(self) -> None:
        records = [
            {
                "word": "hello",
                "lang": "English",
                "lang_code": "en",
                "pos": "intj",
                "forms": [{"form": "hullo", "tags": ["alternative"]}],
                "sounds": [{"ipa": "həˈləʊ"}],
                "translations": [
                    {
                        "word": "hola",
                        "code": "es",
                        "lang_code": "es",
                        "lang": "Spanish",
                        "sense": "greeting",
                    },
                    {
                        "word": "buenos días",
                        "code": "es",
                        "lang_code": "es",
                        "lang": "Spanish",
                        "sense": "greeting",
                    },
                    {
                        "word": "aló",
                        "code": "es",
                        "lang_code": "es",
                        "lang": "Spanish",
                        "sense": "when answering the telephone",
                        "tags": ["Latin-America"],
                    },
                    {
                        "word": "bonjour",
                        "code": "fr",
                        "lang_code": "fr",
                        "lang": "French",
                        "sense": "greeting",
                    },
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "raw-wiktextract-data-en-es.jsonl.gz"
            output_path = Path(tmp) / "wiktionary-en-es.sqlite"
            with gzip.open(input_path, "wt", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            metadata = convert_kaikki_translations_to_sqlite(
                input_path,
                output_path,
                source_lang_code="en",
                target_lang_code="es",
                translation_language="es",
                source_provider="wiktionary-en-es",
                source_dump="enwiktionary",
                overwrite=True,
            )
            records_by_headword = load_freedict_sqlite_gloss_records_ordered(output_path)
            self.assertEqual(metadata["selected_records"], 1)
            self.assertEqual(metadata["inserted_sense_rows"], 3)
            self.assertEqual(metadata["inserted_translation_meta"], 3)
            self.assertIn("hello", records_by_headword)
            self.assertEqual(
                [entry.translation for entry in records_by_headword["hello"]],
                ["hola", "buenos días", "aló"],
            )
            self.assertEqual(records_by_headword["hello"][0].pos_raw, "intj")
            with sqlite3.connect(output_path) as conn:
                row = conn.execute(
                    "SELECT sense_text, tags_json, lang_code FROM translation_meta "
                    "WHERE entry_ord = 1 AND sense_ord = 1 AND gloss_ord = 0"
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], "when answering the telephone")
                self.assertIn("Latin-America", row[1] or "")
                self.assertEqual(row[2], "es")


if __name__ == "__main__":
    unittest.main()
